"""
Database schema definitions for the recommendation system.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class UserProfile(Base):
    """
    SQL table for storing user profile information.
    """
    __tablename__ = 'user_profile'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    age = Column(Integer)
    gender = Column(String(20))
    location = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, username='{self.username}')>"


class Product(Base):
    """
    SQL table for storing product catalog.
    """
    __tablename__ = 'product'
    
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100))
    subcategory = Column(String(100))
    price = Column(Float, nullable=False)
    brand = Column(String(100))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Product(product_id={self.product_id}, product_name='{self.product_name}')>"


# MongoDB Document Structure for Purchase History
"""
Purchase History Collection (MongoDB):
{
    "_id": ObjectId,
    "user_id": int,
    "purchase_id": str,
    "purchase_date": datetime,
    "items": [
        {
            "product_id": int,
            "quantity": int,
            "price_at_purchase": float,
            "discount": float
        }
    ],
    "total_amount": float,
    "payment_method": str,
    "shipping_address": str,
    "status": str  # "completed", "pending", "cancelled"
}

Why MongoDB for Purchase History?
- Flexible schema allows varying transaction attributes
- Easy to add new fields (e.g., coupon codes, gift wrapping) without migrations
- Nested documents naturally represent multiple items per purchase
- Excellent for high-volume write operations (frequent purchases)
- Time-series data with efficient date-based queries
- Horizontal scaling for growing purchase data
"""


def create_sql_tables(engine):
    """
    Create all SQL tables in the database.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(engine)
    print("SQL tables created successfully")


def get_purchase_history_schema():
    """
    Returns the MongoDB document schema for purchase history.
    
    Returns:
        dict: Example purchase history document structure
    """
    return {
        "_id": "ObjectId (auto-generated)",
        "user_id": "int (references user_profile.user_id)",
        "purchase_id": "str (unique purchase identifier)",
        "purchase_date": "datetime",
        "items": [
            {
                "product_id": "int (references product.product_id)",
                "quantity": "int",
                "price_at_purchase": "float",
                "discount": "float (optional)"
            }
        ],
        "total_amount": "float",
        "payment_method": "str",
        "shipping_address": "str",
        "status": "str (completed/pending/cancelled)"
    }


# Pydantic models for API requests/responses
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ChatRequest(BaseModel):
    """Request model for chatbot queries"""
    query: str = Field(..., description="Natural language query from user", min_length=1)
    user_id: Optional[int] = Field(None, description="Optional user ID for personalization")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    n_results: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    use_recommendations: bool = Field(default=True, description="Whether to use recommendation engine for personalization")


class SearchRequest(BaseModel):
    """Request model for search queries"""
    query: str = Field(..., description="Search query", min_length=1)
    user_id: Optional[int] = Field(None, description="Optional user ID for personalization")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    n_results: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    use_recommendations: bool = Field(default=True, description="Use collaborative filtering")


class ChatResponse(BaseModel):
    """Response model for chatbot interactions"""
    query: str = Field(..., description="Original user query")
    intent: str = Field(..., description="Detected intent (search, recommendation, question, greeting)")
    response: str = Field(..., description="Natural language response")
    products: List[Dict[str, Any]] = Field(..., description="List of recommended products")
    count: int = Field(..., description="Number of products returned")
    query_analysis: Optional[Dict[str, Any]] = Field(None, description="Detailed query analysis")
    suggestions: Optional[List[str]] = Field(None, description="Suggested follow-up queries")


class SearchResponse(BaseModel):
    """Response model for search results"""
    query: str = Field(..., description="Original search query")
    intent: str = Field(..., description="Detected query intent")
    response: str = Field(..., description="Natural language summary of results")
    products: List[Dict[str, Any]] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results")
    query_analysis: Dict[str, Any] = Field(..., description="Query processing details")
