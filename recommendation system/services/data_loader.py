"""
Data loading utilities for the recommendation system.
"""

import pandas as pd
from typing import List, Dict
from config.database import db_config
from models.schemas import UserProfile, Product


class DataLoader:
    """
    Handles loading and preprocessing data from databases.
    """
    
    def __init__(self):
        self.db_config = db_config
    
    def load_users(self) -> pd.DataFrame:
        """
        Load user profiles from SQL database.
        
        Returns:
            DataFrame with user information
        """
        session = self.db_config.get_sql_session()
        try:
            users = session.query(UserProfile).all()
            users_data = [{
                'user_id': u.user_id,
                'username': u.username,
                'email': u.email,
                'age': u.age,
                'gender': u.gender,
                'location': u.location
            } for u in users]
            return pd.DataFrame(users_data)
        finally:
            session.close()
    
    def load_products(self) -> pd.DataFrame:
        """
        Load product catalog from SQL database.
        
        Returns:
            DataFrame with product information
        """
        session = self.db_config.get_sql_session()
        try:
            products = session.query(Product).all()
            products_data = [{
                'product_id': p.product_id,
                'product_name': p.product_name,
                'category': p.category,
                'subcategory': p.subcategory,
                'price': p.price,
                'brand': p.brand,
                'description': p.description
            } for p in products]
            return pd.DataFrame(products_data)
        finally:
            session.close()
    
    def load_purchase_history(self, user_id: int = None) -> pd.DataFrame:
        """
        Load purchase history from MongoDB.
        
        Args:
            user_id: Optional user_id to filter purchases
            
        Returns:
            DataFrame with purchase history (flattened by item)
        """
        collection = self.db_config.get_purchase_history_collection()
        
        # Build query
        query = {'status': 'completed'}
        if user_id:
            query['user_id'] = user_id
        
        # Fetch purchases
        purchases = list(collection.find(query))
        
        # Flatten purchases (one row per item)
        flattened = []
        for purchase in purchases:
            for item in purchase.get('items', []):
                flattened.append({
                    'user_id': purchase['user_id'],
                    'purchase_id': purchase['purchase_id'],
                    'purchase_date': purchase['purchase_date'],
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'price_at_purchase': item['price_at_purchase'],
                    'discount': item.get('discount', 0.0)
                })
        
        return pd.DataFrame(flattened)
    
    def create_user_item_matrix(self) -> pd.DataFrame:
        """
        Create a user-item interaction matrix for collaborative filtering.
        
        Returns:
            DataFrame with users as rows, products as columns, and interaction values
            (e.g., purchase count or implicit rating)
        """
        purchase_history = self.load_purchase_history()
        
        if purchase_history.empty:
            return pd.DataFrame()
        
        # Aggregate purchases: count how many times each user bought each product
        user_item_matrix = purchase_history.groupby(['user_id', 'product_id'])['quantity'].sum().unstack(fill_value=0)
        
        return user_item_matrix
    
    def get_user_purchased_products(self, user_id: int) -> List[int]:
        """
        Get list of products a user has already purchased.
        
        Args:
            user_id: User ID
            
        Returns:
            List of product IDs
        """
        purchase_history = self.load_purchase_history(user_id=user_id)
        return purchase_history['product_id'].unique().tolist()
