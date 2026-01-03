"""
Chatbot service for processing natural language queries using LLM.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
from services.memory import conversation_memory

load_dotenv()


class Chatbot:
    """
    LLM-powered chatbot for the recommendation system.
    Uses OpenAI to understand queries and generate responses.
    """
    
    def __init__(self):
        """Initialize the chatbot with OpenAI client."""
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in .env file.")
        
        self.openai_client = OpenAI(api_key=api_key)
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # System prompt for query analysis
        self.query_analysis_prompt = """You are a shopping assistant that analyzes user queries to help them find products.

Your task is to extract structured information from the user's natural language query.

Extract the following:
1. **intent**: One of these values:
   - "search": User wants to find/browse products
   - "recommendation": User wants personalized recommendations based on their history
   - "question": User is asking a general question
   - "greeting": User is saying hello or starting a conversation

2. **categories**: List of product categories mentioned. Common categories include:
   - electronics, clothing, home, sports, books, beauty, toys, food, automotive, health, jewelry, etc.
   - Return empty list if no specific category is mentioned

3. **price_range**: [min_price, max_price] if mentioned, otherwise null
   - "affordable", "cheap", "budget": [0, 100]
   - "expensive", "premium", "luxury": [200, 999999]
   - "under $X": [0, X]
   - "over $X", "more than $X": [X, 999999]
   - "$X to $Y": [X, Y]

4. **keywords**: Important search terms (product names, brands, features, etc.)
   - Extract meaningful words that describe what the user wants
   - Exclude common words like "show", "find", "me", "I", "want"

5. **brands**: Specific brand names mentioned (e.g., Apple, Nike, Samsung)

Return your analysis as a JSON object with these exact keys: intent, categories, price_range, keywords, brands

Examples:

User: "Show me affordable laptops"
{
  "intent": "search",
  "categories": ["electronics"],
  "price_range": [0, 100],
  "keywords": ["laptop"],
  "brands": []
}

User: "I need running shoes under $100 from Nike"
{
  "intent": "search",
  "categories": ["sports", "clothing"],
  "price_range": [0, 100],
  "keywords": ["running", "shoes"],
  "brands": ["Nike"]
}

User: "Recommend me something based on my history"
{
  "intent": "recommendation",
  "categories": [],
  "price_range": null,
  "keywords": ["history", "recommend"],
  "brands": []
}

User: "Hello!"
{
  "intent": "greeting",
  "categories": [],
  "price_range": null,
  "keywords": [],
  "brands": []
}"""
        
        # System prompt for response generation
        self.response_generation_prompt = """You are a friendly AI shopping assistant helping customers find products.

Your role:
- Be conversational and helpful
- Acknowledge their request naturally
- Briefly introduce the results you found
- Be encouraging and positive
- Keep responses concise (2-3 sentences)
- Don't list products - just provide a natural introduction

Tone: Friendly, professional, enthusiastic about helping them find what they need."""
    
    def process_query(self, query: str, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Dict:
        """
        Process a natural language query using LLM to extract intent and parameters.
        
        Args:
            query: User's natural language query
            user_id: Optional user ID for personalization
            session_id: Optional session ID for conversation context
            
        Returns:
            Dictionary with intent, entities, and extracted parameters
        """
        try:
            # Build messages with conversation context
            messages = [{"role": "system", "content": self.query_analysis_prompt}]
            
            # Add conversation history for context
            if session_id:
                context_messages = conversation_memory.format_context_for_llm(user_id, session_id, max_messages=3)
                if context_messages:
                    messages.extend(context_messages)
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Convert price_range to tuple if present
            if analysis.get('price_range') and isinstance(analysis['price_range'], list):
                analysis['price_range'] = tuple(analysis['price_range'])
            
            # Add metadata
            analysis['query'] = query
            analysis['user_id'] = user_id
            analysis['timestamp'] = datetime.utcnow().isoformat()
            analysis['processed_with'] = 'llm'
            
            return analysis
            
        except Exception as e:
            # If LLM fails, return a basic structure
            print(f"LLM query processing failed: {e}")
            return {
                'query': query,
                'intent': 'search',
                'categories': [],
                'price_range': None,
                'keywords': query.lower().split(),
                'brands': [],
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'processed_with': 'fallback',
                'error': str(e)
            }
    
    def generate_response(self, query_analysis: Dict, search_results: List[Dict], session_id: Optional[str] = None) -> str:
        """
        Generate a natural language response using LLM based on query analysis and results.
        
        Args:
            query_analysis: Processed query information
            search_results: List of product recommendations
            session_id: Optional session ID for conversation context
            
        Returns:
            Natural language response string
        """
        query = query_analysis.get('query', '')
        user_id = query_analysis.get('user_id')
        intent = query_analysis.get('intent', 'search')
        num_results = len(search_results)
        
        # Handle greeting separately
        if intent == 'greeting':
            return "Hello! I'm your AI shopping assistant. I can help you find products, make personalized recommendations based on your shopping history, and answer questions about our catalog. What are you looking for today?"
        
        # Handle no results
        if num_results == 0:
            try:
                messages = [{"role": "system", "content": self.response_generation_prompt}]
                
                # Add conversation history
                if session_id:
                    context_messages = conversation_memory.format_context_for_llm(user_id, session_id, max_messages=3)
                    if context_messages:
                        messages.extend(context_messages)
                
                messages.append({"role": "user", "content": f"The user searched for: '{query}' but we found no matching products. Generate a helpful response suggesting they try a different search or be more specific."})
                
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=100
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"LLM response generation failed: {e}")
                return "I couldn't find any products matching your criteria. Try adjusting your search or being more specific about what you're looking for."
        
        # Prepare product summary for context
        product_summary = []
        for i, product in enumerate(search_results[:5], 1):
            summary = f"{i}. {product.get('product_name', 'Product')} - ${product.get('price', 0):.2f}"
            if product.get('category'):
                summary += f" ({product['category']})"
            if product.get('brand'):
                summary += f" by {product['brand']}"
            product_summary.append(summary)
        
        products_text = "\n".join(product_summary)
        
        # Build context for LLM
        context_parts = []
        context_parts.append(f"User Query: \"{query}\"")
        context_parts.append(f"Intent: {intent}")
        context_parts.append(f"Number of Results: {num_results}")
        
        if query_analysis.get('categories'):
            context_parts.append(f"Categories: {', '.join(query_analysis['categories'])}")
        
        if query_analysis.get('price_range'):
            min_p, max_p = query_analysis['price_range']
            if max_p == 999999 or max_p == float('inf'):
                context_parts.append(f"Price Range: Over ${min_p}")
            else:
                context_parts.append(f"Price Range: ${min_p} - ${max_p}")
        
        if query_analysis.get('brands'):
            context_parts.append(f"Brands: {', '.join(query_analysis['brands'])}")
        
        context_parts.append(f"\nTop Products Found:\n{products_text}")
        
        user_prompt = "\n".join(context_parts) + "\n\nGenerate a friendly, natural response introducing these results."
        
        try:
            messages = [{"role": "system", "content": self.response_generation_prompt}]
            
            # Add conversation history for context
            if session_id:
                context_messages = conversation_memory.format_context_for_llm(user_id, session_id, max_messages=3)
                if context_messages:
                    messages.extend(context_messages)
            
            messages.append({"role": "user", "content": user_prompt})
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM response generation failed: {e}")
            # Simple fallback
            if intent == 'recommendation':
                return f"Based on your preferences and shopping history, I found {num_results} products you might like!"
            else:
                return f"Great! I found {num_results} products that match your search."
