"""
Main Recommendation Engine service.
"""

import pandas as pd
from typing import List, Dict, Tuple
from services.data_loader import DataLoader
from services.collaborative_filtering import CollaborativeFiltering


class RecommendationEngine:
    """
    Main recommendation service that orchestrates data loading and algorithm execution.
    """
    
    def __init__(self):
        """
        Initialize the recommendation engine.
        """
        self.data_loader = DataLoader()
        self.cf_model = None
        self.user_item_matrix = None
        self.products_df = None
    
    def load_data(self):
        """
        Load and prepare data for recommendations.
        """
        print("Loading data from databases...")
        
        # Load user-item matrix
        self.user_item_matrix = self.data_loader.create_user_item_matrix()
        
        if self.user_item_matrix.empty:
            raise ValueError("No purchase history data available. Cannot generate recommendations.")
        
        # Load product catalog
        self.products_df = self.data_loader.load_products()
        
        # Initialize collaborative filtering model
        self.cf_model = CollaborativeFiltering(self.user_item_matrix)
        
        print(f"Loaded {len(self.user_item_matrix)} users and {len(self.user_item_matrix.columns)} products")
    
    def get_recommendations(
        self,
        user_id: int,
        method: str = 'user-based',
        n_recommendations: int = 10,
        include_product_details: bool = True
    ) -> List[Dict]:
        """
        Get product recommendations for a user.
        
        Args:
            user_id: Target user ID
            method: 'user-based' or 'item-based'
            n_recommendations: Number of recommendations to return
            include_product_details: Whether to include full product details
            
        Returns:
            List of recommendation dictionaries with product info and scores
        """
        # Load data if not already loaded
        if self.cf_model is None:
            self.load_data()
        
        # Check if user exists
        if user_id not in self.user_item_matrix.index:
            return []
        
        # Get products already purchased by user
        purchased_products = self.data_loader.get_user_purchased_products(user_id)
        
        # Generate recommendations based on method
        if method == 'user-based':
            recommendations = self.cf_model.user_based_recommendations(
                user_id=user_id,
                n_recommendations=n_recommendations,
                exclude_purchased=purchased_products
            )
        elif method == 'item-based':
            recommendations = self.cf_model.item_based_recommendations(
                user_id=user_id,
                n_recommendations=n_recommendations,
                exclude_purchased=purchased_products
            )
        else:
            raise ValueError(f"Unknown method: {method}. Use 'user-based' or 'item-based'")
        
        # Format recommendations
        if include_product_details and self.products_df is not None:
            formatted_recommendations = []
            for product_id, score in recommendations:
                product_info = self.products_df[self.products_df['product_id'] == product_id]
                if not product_info.empty:
                    product_dict = product_info.iloc[0].to_dict()
                    product_dict['recommendation_score'] = round(score, 4)
                    formatted_recommendations.append(product_dict)
                else:
                    formatted_recommendations.append({
                        'product_id': product_id,
                        'recommendation_score': round(score, 4)
                    })
            return formatted_recommendations
        else:
            return [
                {'product_id': product_id, 'recommendation_score': round(score, 4)}
                for product_id, score in recommendations
            ]
    
    def get_similar_users(self, user_id: int, n_similar: int = 10) -> List[Dict]:
        """
        Get users similar to a given user.
        
        Args:
            user_id: Target user ID
            n_similar: Number of similar users to return
            
        Returns:
            List of similar users with similarity scores
        """
        if self.cf_model is None:
            self.load_data()
        
        similar_users = self.cf_model.get_similar_users(user_id, n_similar)
        return [
            {'user_id': uid, 'similarity_score': round(score, 4)}
            for uid, score in similar_users
        ]
    
    def get_similar_products(self, product_id: int, n_similar: int = 10) -> List[Dict]:
        """
        Get products similar to a given product.
        
        Args:
            product_id: Target product ID
            n_similar: Number of similar products to return
            
        Returns:
            List of similar products with similarity scores
        """
        if self.cf_model is None:
            self.load_data()
        
        similar_items = self.cf_model.get_similar_items(product_id, n_similar)
        
        # Add product details
        similar_products = []
        for pid, score in similar_items:
            product_info = self.products_df[self.products_df['product_id'] == pid]
            if not product_info.empty:
                product_dict = product_info.iloc[0].to_dict()
                product_dict['similarity_score'] = round(score, 4)
                similar_products.append(product_dict)
        
        return similar_products
    
    def get_user_statistics(self, user_id: int) -> Dict:
        """
        Get statistics about a user's purchase history.
        
        Args:
            user_id: Target user ID
            
        Returns:
            Dictionary with user statistics
        """
        purchase_history = self.data_loader.load_purchase_history(user_id=user_id)
        
        if purchase_history.empty:
            return {
                'user_id': user_id,
                'total_purchases': 0,
                'unique_products': 0,
                'total_items': 0,
                'total_spent': 0.0
            }
        
        return {
            'user_id': user_id,
            'total_purchases': purchase_history['purchase_id'].nunique(),
            'unique_products': purchase_history['product_id'].nunique(),
            'total_items': purchase_history['quantity'].sum(),
            'total_spent': (purchase_history['price_at_purchase'] * purchase_history['quantity']).sum()
        }
