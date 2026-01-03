"""
Collaborative Filtering implementation for product recommendations.
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict


class CollaborativeFiltering:
    """
    Implements user-based and item-based collaborative filtering.
    """
    
    def __init__(self, user_item_matrix: pd.DataFrame):
        """
        Initialize collaborative filtering with user-item interaction matrix.
        
        Args:
            user_item_matrix: DataFrame with users as rows, products as columns
        """
        self.user_item_matrix = user_item_matrix
        self.user_similarity_matrix = None
        self.item_similarity_matrix = None
    
    def compute_user_similarity(self) -> np.ndarray:
        """
        Compute user-user similarity matrix using cosine similarity.
        
        Returns:
            User similarity matrix
        """
        if self.user_similarity_matrix is None:
            self.user_similarity_matrix = cosine_similarity(self.user_item_matrix)
        return self.user_similarity_matrix
    
    def compute_item_similarity(self) -> np.ndarray:
        """
        Compute item-item similarity matrix using cosine similarity.
        
        Returns:
            Item similarity matrix
        """
        if self.item_similarity_matrix is None:
            # Transpose to get items as rows
            self.item_similarity_matrix = cosine_similarity(self.user_item_matrix.T)
        return self.item_similarity_matrix
    
    def get_similar_users(self, user_id: int, n_similar: int = 10) -> List[Tuple[int, float]]:
        """
        Find most similar users to a given user.
        
        Args:
            user_id: Target user ID
            n_similar: Number of similar users to return
            
        Returns:
            List of tuples (user_id, similarity_score)
        """
        if user_id not in self.user_item_matrix.index:
            return []
        
        user_similarity = self.compute_user_similarity()
        user_idx = self.user_item_matrix.index.get_loc(user_id)
        
        # Get similarity scores for this user
        similarity_scores = user_similarity[user_idx]
        
        # Get indices of most similar users (excluding self)
        similar_indices = np.argsort(similarity_scores)[::-1][1:n_similar+1]
        
        # Return user IDs and their similarity scores
        similar_users = [
            (self.user_item_matrix.index[idx], similarity_scores[idx])
            for idx in similar_indices
        ]
        
        return similar_users
    
    def get_similar_items(self, product_id: int, n_similar: int = 10) -> List[Tuple[int, float]]:
        """
        Find most similar items to a given product.
        
        Args:
            product_id: Target product ID
            n_similar: Number of similar items to return
            
        Returns:
            List of tuples (product_id, similarity_score)
        """
        if product_id not in self.user_item_matrix.columns:
            return []
        
        item_similarity = self.compute_item_similarity()
        item_idx = self.user_item_matrix.columns.get_loc(product_id)
        
        # Get similarity scores for this item
        similarity_scores = item_similarity[item_idx]
        
        # Get indices of most similar items (excluding self)
        similar_indices = np.argsort(similarity_scores)[::-1][1:n_similar+1]
        
        # Return product IDs and their similarity scores
        similar_items = [
            (self.user_item_matrix.columns[idx], similarity_scores[idx])
            for idx in similar_indices
        ]
        
        return similar_items
    
    def user_based_recommendations(
        self, 
        user_id: int, 
        n_recommendations: int = 10,
        exclude_purchased: List[int] = None
    ) -> List[Tuple[int, float]]:
        """
        Generate recommendations using user-based collaborative filtering.
        
        Args:
            user_id: Target user ID
            n_recommendations: Number of recommendations to return
            exclude_purchased: List of product IDs to exclude (already purchased)
            
        Returns:
            List of tuples (product_id, predicted_score)
        """
        if user_id not in self.user_item_matrix.index:
            return []
        
        # Get similar users
        similar_users = self.get_similar_users(user_id, n_similar=20)
        
        if not similar_users:
            return []
        
        # Aggregate product scores from similar users
        product_scores = {}
        for similar_user_id, similarity_score in similar_users:
            # Get products purchased by similar user
            user_products = self.user_item_matrix.loc[similar_user_id]
            
            for product_id, interaction_value in user_products.items():
                if interaction_value > 0:
                    # Weight by similarity and interaction value
                    if product_id not in product_scores:
                        product_scores[product_id] = 0
                    product_scores[product_id] += similarity_score * interaction_value
        
        # Exclude already purchased products
        if exclude_purchased:
            for product_id in exclude_purchased:
                product_scores.pop(product_id, None)
        
        # Sort by score and return top N
        recommendations = sorted(
            product_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:n_recommendations]
        
        return recommendations
    
    def item_based_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 10,
        exclude_purchased: List[int] = None
    ) -> List[Tuple[int, float]]:
        """
        Generate recommendations using item-based collaborative filtering.
        
        Args:
            user_id: Target user ID
            n_recommendations: Number of recommendations to return
            exclude_purchased: List of product IDs to exclude (already purchased)
            
        Returns:
            List of tuples (product_id, predicted_score)
        """
        if user_id not in self.user_item_matrix.index:
            return []
        
        # Get products the user has purchased
        user_products = self.user_item_matrix.loc[user_id]
        purchased_products = user_products[user_products > 0].index.tolist()
        
        if not purchased_products:
            return []
        
        # Aggregate scores from similar items
        product_scores = {}
        for product_id in purchased_products:
            similar_items = self.get_similar_items(product_id, n_similar=20)
            
            for similar_product_id, similarity_score in similar_items:
                # Weight by similarity and user's interaction with the original product
                if similar_product_id not in product_scores:
                    product_scores[similar_product_id] = 0
                product_scores[similar_product_id] += similarity_score * user_products[product_id]
        
        # Exclude already purchased products
        if exclude_purchased:
            for product_id in exclude_purchased:
                product_scores.pop(product_id, None)
        
        # Sort by score and return top N
        recommendations = sorted(
            product_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n_recommendations]
        
        return recommendations
