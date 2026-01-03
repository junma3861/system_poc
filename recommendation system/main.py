"""
FastAPI service for the Recommendation System.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from recommendation_engine import RecommendationEngine
from services.search_engine import SearchEngine
from models.schemas import ChatRequest, ChatResponse, SearchRequest, SearchResponse
from services.memory import conversation_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Recommendation System API",
    description="AI-powered product recommendation system using collaborative filtering",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recommendation engine (singleton)
engine = RecommendationEngine()

# Initialize search engine (singleton)
search_engine = SearchEngine(recommendation_engine=engine)


# Pydantic models for request/response
class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    user_id: int = Field(..., description="User ID for which recommendations were generated")
    method: str = Field(..., description="Recommendation method used")
    recommendations: List[Dict[str, Any]] = Field(..., description="List of recommended products")
    count: int = Field(..., description="Number of recommendations returned")


class SimilarUsersResponse(BaseModel):
    """Response model for similar users"""
    user_id: int = Field(..., description="Reference user ID")
    similar_users: List[Dict[str, Any]] = Field(..., description="List of similar users")
    count: int = Field(..., description="Number of similar users returned")


class SimilarProductsResponse(BaseModel):
    """Response model for similar products"""
    product_id: int = Field(..., description="Reference product ID")
    similar_products: List[Dict[str, Any]] = Field(..., description="List of similar products")
    count: int = Field(..., description="Number of similar products returned")


class UserStatisticsResponse(BaseModel):
    """Response model for user statistics"""
    user_id: int = Field(..., description="User ID")
    total_purchases: int = Field(..., description="Total number of purchase transactions")
    unique_products: int = Field(..., description="Number of unique products purchased")
    total_items: int = Field(..., description="Total quantity of items purchased")
    total_spent: float = Field(..., description="Total amount spent")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")


class MessageResponse(BaseModel):
    """Generic message response"""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Operation message")


# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Load data when the API starts"""
    try:
        logger.info("Initializing recommendation engine...")
        engine.load_data()
        logger.info("✓ Recommendation engine initialized successfully")
        
        logger.info("Initializing search engine...")
        search_engine.load_data()
        logger.info("✓ Search engine initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize engines: {e}", exc_info=True)
        logger.warning("API will start but some features may fail until data is loaded")


@app.get(
    "/",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Root endpoint"
)
async def root():
    """Root endpoint - API health check"""
    return HealthResponse(
        status="healthy",
        message="Recommendation System API is running"
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check"
)
async def health_check():
    """
    Health check endpoint to verify service is operational.
    Returns the current status of the recommendation system.
    """
    return HealthResponse(
        status="healthy",
        message="Service is operational"
    )


@app.post(
    "/reload-data",
    response_model=MessageResponse,
    tags=["Admin"],
    summary="Reload training data",
    status_code=status.HTTP_200_OK
)
async def reload_data():
    """
    Reload data from databases.
    Use this endpoint to refresh the recommendation engine with updated data.
    """
    try:
        logger.info("Reloading data...")
        engine.load_data()
        logger.info("Data reloaded successfully")
        return MessageResponse(
            status="success",
            message="Data reloaded successfully"
        )
    except Exception as e:
        logger.error(f"Failed to reload data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload data: {str(e)}"
        )


@app.get(
    "/recommendations/{user_id}",
    response_model=RecommendationResponse,
    tags=["Recommendations"],
    summary="Get product recommendations",
    responses={
        200: {"description": "Recommendations generated successfully"},
        400: {"description": "Invalid parameters"},
        404: {"description": "User not found or no recommendations available"},
        500: {"description": "Internal server error"}
    }
)
async def get_recommendations(
    user_id: int,
    method: str = Query(
        default="user-based",
        description="Recommendation method: 'user-based' or 'item-based'",
        regex="^(user-based|item-based)$"
    ),
    n_recommendations: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Number of recommendations to return (1-50)"
    ),
    include_details: bool = Query(
        default=True,
        description="Include full product details in response"
    )
):
    """
    Get personalized product recommendations for a user.
    
    - **user_id**: The ID of the user to generate recommendations for (path parameter)
    
    This endpoint uses collaborative filtering to generate recommendations based on:
    - **user-based**: Recommendations from users with similar purchase patterns
    - **item-based**: Recommendations based on products similar to user's purchase history
    
    Returns a list of recommended products with similarity scores and optional details.
    """
    try:
        logger.info(f"Generating {method} recommendations for user {user_id}")
        
        recommendations = engine.get_recommendations(
            user_id=user_id,
            method=method,
            n_recommendations=n_recommendations,
            include_product_details=include_details
        )
        
        if not recommendations:
            logger.warning(f"No recommendations found for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No recommendations found for user {user_id}. User may not exist or have insufficient purchase history."
            )
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        return RecommendationResponse(
            user_id=user_id,
            method=method,
            recommendations=recommendations,
            count=len(recommendations)
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating recommendations for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@app.get(
    "/users/{user_id}/similar",
    response_model=SimilarUsersResponse,
    tags=["Users"],
    summary="Find similar users",
    responses={
        200: {"description": "Similar users found successfully"},
        404: {"description": "User not found or insufficient data"},
        500: {"description": "Internal server error"}
    }
)
async def get_similar_users(
    user_id: int,
    n_similar: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Number of similar users to return (1-50)"
    )
):
    """
    Get users with similar purchase patterns.
    
    - **user_id**: The ID of the user to find similar users for (path parameter)
    
    Uses cosine similarity to find users who have bought similar products.
    Returns a list of similar users with similarity scores.
    """
    try:
        logger.info(f"Finding similar users for user {user_id}")
        similar_users = engine.get_similar_users(user_id, n_similar)
        
        if not similar_users:
            logger.warning(f"No similar users found for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found or has insufficient data"
            )
        
        logger.info(f"Found {len(similar_users)} similar users for user {user_id}")
        return SimilarUsersResponse(
            user_id=user_id,
            similar_users=similar_users,
            count=len(similar_users)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar users for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar users"
        )


@app.get(
    "/products/{product_id}/similar",
    response_model=SimilarProductsResponse,
    tags=["Products"],
    summary="Find similar products",
    responses={
        200: {"description": "Similar products found successfully"},
        404: {"description": "Product not found or insufficient data"},
        500: {"description": "Internal server error"}
    }
)
async def get_similar_products(
    product_id: int,
    n_similar: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Number of similar products to return (1-50)"
    )
):
    """
    Get products similar to a given product.
    
    - **product_id**: The ID of the product to find similar products for (path parameter)
    
    Uses item-based collaborative filtering to find products frequently
    purchased together or by similar users.
    Returns a list of similar products with similarity scores and details.
    """
    try:
        logger.info(f"Finding similar products for product {product_id}")
        similar_products = engine.get_similar_products(product_id, n_similar)
        
        if not similar_products:
            logger.warning(f"No similar products found for product {product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found or has insufficient data"
            )
        
        logger.info(f"Found {len(similar_products)} similar products for product {product_id}")
        return SimilarProductsResponse(
            product_id=product_id,
            similar_products=similar_products,
            count=len(similar_products)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar products for product {product_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar products"
        )


@app.get(
    "/users/{user_id}/statistics",
    response_model=UserStatisticsResponse,
    tags=["Users"],
    summary="Get user purchase statistics",
    responses={
        200: {"description": "Statistics retrieved successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_user_statistics(user_id: int):
    """
    Get comprehensive purchase statistics for a user.
    
    - **user_id**: The ID of the user to get statistics for (path parameter)
    
    Returns information about the user's purchase history including:
    - Total number of transactions
    - Unique products purchased
    - Total items bought
    - Total amount spent
    """
    try:
        logger.info(f"Fetching statistics for user {user_id}")
        stats = engine.get_user_statistics(user_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        return UserStatisticsResponse(**stats)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching statistics for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["Chatbot"],
    summary="Chat with AI shopping assistant (LLM-powered)",
    responses={
        200: {"description": "Chat response generated successfully"},
        400: {"description": "Invalid request or missing API key"},
        500: {"description": "Internal server error"}
    }
)
async def chat(request: ChatRequest):
    """
    Chat with the AI shopping assistant using natural language powered by OpenAI.
    
    **LLM Features:**
    - Deep understanding of natural language queries
    - Extracts intent, categories, price ranges, keywords, and brands
    - Generates natural, conversational responses
    - Context-aware product recommendations
    
    **Capabilities:**
    - Search by category, price, brand, or features
    - Personalized recommendations based on shopping history
    - Understands complex queries with multiple filters
    - Conversational tone with helpful suggestions
    
    **Example queries:**
    - "Show me affordable laptops" → Finds electronics under $100
    - "I need Nike running shoes under $100" → Filters by brand + price + category
    - "Recommend me something based on what I bought" → Uses collaborative filtering
    - "Find luxury electronics from Apple" → Brand + price tier + category
    - "What are some good books?" → Category-based search
    
    **Note:** Requires OPENAI_API_KEY to be set in environment variables.
    """
    try:
        logger.info(f"💬 Chat query: '{request.query}' | User: {request.user_id} | Session: {request.session_id}")
        
        # Validate query
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        # Store user message in memory
        if request.session_id:
            conversation_memory.add_message(
                user_id=request.user_id,
                session_id=request.session_id,
                role="user",
                content=request.query
            )
        
        # Process the query through search engine
        result = search_engine.search(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            n_results=request.n_results,
            use_recommendations=request.use_recommendations
        )
        
        # Store assistant response in memory
        if request.session_id:
            conversation_memory.add_message(
                user_id=request.user_id,
                session_id=request.session_id,
                role="assistant",
                content=result['response'],
                metadata={
                    'query_analysis': result.get('query_analysis', {}),
                    'products_count': result['count'],
                    'intent': result['intent']
                }
            )
        
        # Get conversation suggestions
        suggestions = search_engine.get_conversation_suggestions(request.user_id)
        
        # Check if LLM was used or fallback
        query_analysis = result.get('query_analysis', {})
        processing_method = query_analysis.get('processed_with', 'llm')
        
        if processing_method == 'fallback':
            logger.warning(f"⚠️  LLM fallback used for query: '{request.query}'")
        
        logger.info(f"✓ Chat processed: {result['count']} products | Intent: {result['intent']} | Method: {processing_method}")
        
        return ChatResponse(
            query=result['query'],
            intent=result['intent'],
            response=result['response'],
            products=result['products'],
            count=result['count'],
            query_analysis=query_analysis,
            suggestions=suggestions
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error processing chat query: {error_msg}", exc_info=True)
        
        # Check if it's an OpenAI API key error
        if "OPENAI_API_KEY" in error_msg or "api_key" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in environment variables."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat query: {error_msg}"
        )


@app.post(
    "/search",
    response_model=SearchResponse,
    tags=["Search"],
    summary="Intelligent product search (LLM-powered)",
    responses={
        200: {"description": "Search completed successfully"},
        400: {"description": "Invalid search query"},
        500: {"description": "Internal server error"}
    }
)
async def search(request: SearchRequest):
    """
    Intelligent product search using LLM for natural language understanding.
    
    **LLM Features:**
    - Understands natural language queries
    - Extracts categories, brands, price ranges, and keywords
    - Semantic search across product catalog
    - Personalized ranking when user_id provided
    
    **Advanced Filters:**
    - Category: electronics, clothing, home, sports, books, beauty, etc.
    - Brands: Specific brand names (e.g., Apple, Nike, Samsung)
    - Price ranges: affordable, budget, luxury, or specific amounts
    - Keywords: Product features, materials, styles
    
    **Example queries:**
    - "laptops under $1000" → Price + category filter
    - "Nike running shoes" → Brand + category + keywords
    - "affordable home decor" → Price tier + category
    - "luxury electronics from Apple" → Brand + price + category
    - "gaming laptop with RTX" → Keywords + category
    """
    try:
        logger.info(f"🔍 Search query: '{request.query}' | User: {request.user_id}")
        
        # Validate query
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        # Process the search through search engine
        result = search_engine.search(
            query=request.query,
            user_id=request.user_id,
            n_results=request.n_results,
            use_recommendations=request.use_recommendations
        )
        
        # Log search analytics
        query_analysis = result.get('query_analysis', {})
        logger.info(
            f"✓ Search: {result['count']} results | "
            f"Intent: {result['intent']} | "
            f"Categories: {query_analysis.get('categories', [])} | "
            f"Brands: {query_analysis.get('brands', [])} | "
            f"Price: {query_analysis.get('price_range', 'any')}"
        )
        
        return SearchResponse(
            query=result['query'],
            intent=result['intent'],
            response=result['response'],
            products=result['products'],
            count=result['count'],
            query_analysis=query_analysis
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Error processing search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process search query"
        )


@app.get(
    "/chat/suggestions",
    tags=["Chatbot"],
    summary="Get conversation starters",
    responses={
        200: {"description": "Suggestions generated successfully"},
        500: {"description": "Internal server error"}
    }
)
async def get_chat_suggestions(
    user_id: Optional[int] = Query(None, description="Optional user ID for personalized suggestions")
):
    """
    Get suggested queries to help users start a conversation with the AI assistant.
    
    **Personalization:**
    - If user_id provided: Suggestions based on purchase history and preferences
    - If no user_id: General popular queries and category suggestions
    
    **Use cases:**
    - Help users discover features
    - Provide conversation starters
    - Show example queries
    - Guide users to relevant products
    
    Returns 5-7 suggested queries that users can click to start chatting.
    """
    try:
        logger.info(f"📝 Generating suggestions for user: {user_id or 'anonymous'}")
        suggestions = search_engine.get_conversation_suggestions(user_id)
        
        logger.info(f"✓ Generated {len(suggestions)} suggestions")
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "personalized": user_id is not None
        }
    except Exception as e:
        logger.error(f"❌ Error generating suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions"
        )


@app.post(
    "/chat/analyze",
    tags=["Chatbot"],
    summary="Analyze query without search (LLM only)",
    responses={
        200: {"description": "Query analyzed successfully"},
        400: {"description": "Invalid query or missing API key"},
        500: {"description": "Internal server error"}
    }
)
async def analyze_query(
    query: str = Query(..., description="Query to analyze", min_length=1),
    user_id: Optional[int] = Query(None, description="Optional user ID")
):
    """
    Analyze a query using LLM without executing the search.
    
    **Purpose:**
    - Debug query understanding
    - See what the LLM extracts from queries
    - Test intent detection
    - Understand how queries are parsed
    
    **Returns:**
    - Intent (search, recommendation, question, greeting)
    - Categories detected
    - Price range extracted
    - Keywords identified
    - Brands mentioned
    - Processing method (llm or fallback)
    
    **Useful for:**
    - Testing query variations
    - Understanding LLM behavior
    - Debugging search issues
    - Query optimization
    
    **Example:**
    ```
    GET /chat/analyze?query=Show me Nike running shoes under $100
    
    Response:
    {
      "query": "Show me Nike running shoes under $100",
      "analysis": {
        "intent": "search",
        "categories": ["sports", "clothing"],
        "price_range": [0, 100],
        "keywords": ["running", "shoes"],
        "brands": ["Nike"],
        "processed_with": "llm"
      }
    }
    ```
    """
    try:
        logger.info(f"🔍 Analyzing query: '{query}'")
        
        # Process query through chatbot
        analysis = search_engine.chatbot.process_query(query, user_id)
        
        logger.info(
            f"✓ Analysis complete: Intent={analysis['intent']}, "
            f"Categories={analysis.get('categories', [])}, "
            f"Brands={analysis.get('brands', [])}, "
            f"Method={analysis.get('processed_with', 'llm')}"
        )
        
        return {
            "query": query,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        logger.error(f"❌ API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Error analyzing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze query"
        )


@app.get(
    "/info",
    tags=["Info"],
    summary="API information"
)
async def api_info():
    """
    Get comprehensive API information including available endpoints,
    supported methods, and usage guidelines.
    """
    return {
        "api_name": "Recommendation System API with AI Chatbot",
        "version": "3.0.0",
        "description": "LLM-powered product recommendation system with intelligent chatbot search engine using OpenAI",
        "llm_powered": True,
        "llm_model": os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        "endpoints": {
            "Health & Admin": {
                "GET /": "Health check",
                "GET /health": "Health check",
                "POST /reload-data": "Reload data from databases",
                "GET /info": "API information and usage guidelines"
            },
            "Chatbot (LLM-Powered)": {
                "POST /chat": "Chat with AI shopping assistant using natural language",
                "POST /search": "Intelligent product search with LLM understanding",
                "GET /chat/suggestions": "Get conversation starters",
                "POST /chat/analyze": "Analyze query without search (debug tool)"
            },
            "Recommendations": {
                "GET /recommendations/{user_id}": "Get product recommendations for a user",
                "GET /users/{user_id}/similar": "Get similar users based on purchase patterns",
                "GET /products/{product_id}/similar": "Get similar products",
                "GET /users/{user_id}/statistics": "Get user purchase statistics"
            },
            "Documentation": {
                "GET /docs": "Interactive API documentation (Swagger UI)",
                "GET /redoc": "Alternative API documentation (ReDoc)"
            }
        },
        "llm_features": {
            "query_understanding": "Deep NLP understanding of natural language queries",
            "intent_detection": "Automatic classification: search, recommendation, question, greeting",
            "entity_extraction": "Extracts categories, brands, price ranges, keywords",
            "response_generation": "Natural conversational responses tailored to context",
            "context_awareness": "Understands user history and preferences",
            "fallback_handling": "Graceful degradation if LLM unavailable"
        },
        "search_capabilities": {
            "categories": "electronics, clothing, home, sports, books, beauty, toys, food, etc.",
            "brands": "Detects and filters by brand names (Nike, Apple, Samsung, etc.)",
            "price_ranges": "Understands 'affordable', 'budget', 'luxury', or specific amounts",
            "keywords": "Semantic search across product names, descriptions, features",
            "personalization": "Ranks results using collaborative filtering when user_id provided"
        },
        "recommendation_methods": {
            "user-based": "Collaborative filtering based on similar users' preferences",
            "item-based": "Collaborative filtering based on similar items and purchase patterns",
            "hybrid": "Combines search with personalization for best results"
        },
        "parameters": {
            "n_recommendations": "Number of recommendations (1-50, default: 10)",
            "n_results": "Number of search results (1-50, default: 10)",
            "n_similar": "Number of similar items/users (1-50, default: 10)",
            "include_details": "Include full product details (default: true)",
            "use_recommendations": "Use collaborative filtering for personalization (default: true)"
        },
        "example_queries": {
            "basic_search": "Show me affordable laptops",
            "brand_filter": "Nike running shoes under $100",
            "luxury_search": "Luxury electronics from Apple",
            "recommendation": "Recommend me products based on my history",
            "multi_filter": "Gaming laptop with RTX under $2000"
        },
        "requirements": {
            "openai_api_key": "Required - Set OPENAI_API_KEY in environment variables",
            "databases": "PostgreSQL for products/users, MongoDB for purchase history, Redis for session memory"
        },
        "memory_management": {
            "short_term": "Redis-based session memory (conversation context)",
            "long_term": "MongoDB conversation history (persistent across sessions)",
            "session_ttl": "1 hour default (configurable via SESSION_TTL)",
            "max_context": "10 messages per session (configurable via MAX_CONTEXT_MESSAGES)"
        }
    }


@app.get(
    "/memory/session/{session_id}",
    tags=["Memory"],
    summary="Get conversation session summary"
)
async def get_session_memory(
    session_id: str,
    user_id: Optional[int] = Query(None, description="User ID")
):
    """Get summary of a conversation session including all messages."""
    try:
        summary = conversation_memory.get_session_summary(user_id, session_id)
        return {
            "success": True,
            "session": summary
        }
    except Exception as e:
        logger.error(f"Error retrieving session memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session memory: {str(e)}"
        )


@app.delete(
    "/memory/session/{session_id}",
    tags=["Memory"],
    summary="Clear conversation session"
)
async def clear_session_memory(
    session_id: str,
    user_id: Optional[int] = Query(None, description="User ID")
):
    """Clear all messages from a conversation session."""
    try:
        conversation_memory.clear_session(user_id, session_id)
        return {
            "success": True,
            "message": f"Session {session_id} cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing session memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session memory: {str(e)}"
        )


@app.get(
    "/memory/history/{user_id}",
    tags=["Memory"],
    summary="Get user's conversation history"
)
async def get_conversation_history(
    user_id: int,
    days: int = Query(default=30, ge=1, le=365, description="Days to look back"),
    limit: int = Query(default=100, ge=1, le=500, description="Max number of messages")
):
    """Get user's conversation history from long-term storage (MongoDB)."""
    try:
        history = conversation_memory.get_conversation_history(user_id, days, limit)
        return {
            "success": True,
            "user_id": user_id,
            "days": days,
            "count": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation history: {str(e)}"
        )


@app.get(
    "/memory/preferences/{user_id}",
    tags=["Memory"],
    summary="Get user preferences from conversation history"
)
async def get_user_preferences(user_id: int):
    """Extract user preferences (categories, brands, keywords) from conversation history."""
    try:
        preferences = conversation_memory.get_user_preferences(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "preferences": preferences
        }
    except Exception as e:
        logger.error(f"Error extracting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract user preferences: {str(e)}"
        )


if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
