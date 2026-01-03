"""
Search Engine service that combines natural language queries with recommendation engine.
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
from services.chatbot import Chatbot
from services.data_loader import DataLoader
from services.collaborative_filtering import CollaborativeFiltering


class SearchEngine:
    """
    Intelligent search engine that combines:
    - Natural language query understanding
    - User's shopping history
    - Collaborative filtering recommendations
    - Product catalog filtering
    """
    
    def __init__(self, recommendation_engine=None):
        """
        Initialize the search engine.
        
        Args:
            recommendation_engine: Instance of RecommendationEngine (optional)
        """
        self.chatbot = Chatbot()
        self.data_loader = DataLoader()
        self.recommendation_engine = recommendation_engine
        self.products_df = None
        self.user_item_matrix = None
        self.cf_model = None
    
    def load_data(self):
        """Load product catalog and user-item data."""
        self.products_df = self.data_loader.load_products()
        self.user_item_matrix = self.data_loader.create_user_item_matrix()
        
        if not self.user_item_matrix.empty:
            self.cf_model = CollaborativeFiltering(self.user_item_matrix)
    
    def search(
        self,
        query: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        n_results: int = 10,
        use_recommendations: bool = True
    ) -> Dict:
        """
        Perform intelligent search combining query and user history.
        
        Args:
            query: Natural language search query
            user_id: User ID for personalization
            session_id: Session ID for conversation context
            n_results: Number of results to return
            use_recommendations: Whether to use recommendation engine
            
        Returns:
            Dictionary with search results and metadata
        """
        # Ensure data is loaded
        if self.products_df is None:
            self.load_data()
        
        # Process the query using chatbot with session context
        query_analysis = self.chatbot.process_query(query, user_id, session_id)
        
        # Handle greeting intent
        if query_analysis['intent'] == 'greeting':
            return {
                'query': query,
                'intent': query_analysis['intent'],
                'response': self.chatbot.generate_response(query_analysis, [], session_id),
                'products': [],
                'count': 0
            }
        
        # Get candidate products based on query
        candidate_products = self._filter_products_by_query(query_analysis)
        
        # If user_id provided and recommendations enabled, combine with personalization
        if user_id and use_recommendations and self.cf_model is not None:
            candidate_products = self._personalize_results(
                candidate_products,
                user_id,
                query_analysis
            )
        
        # Rank and limit results
        ranked_products = self._rank_products(candidate_products, query_analysis, user_id)
        final_results = ranked_products[:n_results]
        
        # Generate natural language response with session context
        response_text = self.chatbot.generate_response(query_analysis, final_results, session_id)
        
        return {
            'query': query,
            'intent': query_analysis['intent'],
            'response': response_text,
            'query_analysis': query_analysis,
            'products': final_results,
            'count': len(final_results)
        }
    
    def _filter_products_by_query(self, query_analysis: Dict) -> pd.DataFrame:
        """
        Filter products based on query analysis.
        
        Args:
            query_analysis: Processed query information
            
        Returns:
            Filtered DataFrame of products
        """
        filtered_products = self.products_df.copy()
        
        # Filter by categories
        if query_analysis.get('categories'):
            category_filter = filtered_products['category'].str.lower().isin(
                [cat.lower() for cat in query_analysis['categories']]
            )
            filtered_products = filtered_products[category_filter]
        
        # Filter by brands
        if query_analysis.get('brands'):
            brand_filter = filtered_products['brand'].str.lower().isin(
                [brand.lower() for brand in query_analysis['brands']]
            ) if 'brand' in filtered_products.columns else pd.Series([False] * len(filtered_products))
            filtered_products = filtered_products[brand_filter]
        
        # Filter by price range
        if query_analysis.get('price_range'):
            min_price, max_price = query_analysis['price_range']
            # Handle infinity values
            if max_price == 999999 or max_price == float('inf'):
                filtered_products = filtered_products[filtered_products['price'] >= min_price]
            else:
                filtered_products = filtered_products[
                    (filtered_products['price'] >= min_price) &
                    (filtered_products['price'] <= max_price)
                ]
        
        # Filter by keywords (search in product name, description, and brand)
        if query_analysis.get('keywords'):
            keyword_filter = pd.Series([False] * len(filtered_products))
            
            for keyword in query_analysis['keywords']:
                keyword_lower = keyword.lower()
                
                name_match = filtered_products['product_name'].str.lower().str.contains(
                    keyword_lower, na=False, regex=False
                )
                
                desc_match = filtered_products['description'].str.lower().str.contains(
                    keyword_lower, na=False, regex=False
                ) if 'description' in filtered_products.columns else pd.Series([False] * len(filtered_products))
                
                brand_match = filtered_products['brand'].str.lower().str.contains(
                    keyword_lower, na=False, regex=False
                ) if 'brand' in filtered_products.columns else pd.Series([False] * len(filtered_products))
                
                category_match = filtered_products['category'].str.lower().str.contains(
                    keyword_lower, na=False, regex=False
                ) if 'category' in filtered_products.columns else pd.Series([False] * len(filtered_products))
                
                keyword_filter = keyword_filter | name_match | desc_match | brand_match | category_match
            
            filtered_products = filtered_products[keyword_filter]
        
        return filtered_products
    
    def _personalize_results(
        self,
        candidate_products: pd.DataFrame,
        user_id: int,
        query_analysis: Dict
    ) -> pd.DataFrame:
        """
        Personalize search results using user's shopping history and recommendations.
        
        Args:
            candidate_products: DataFrame of candidate products
            user_id: User ID
            query_analysis: Query analysis information
            
        Returns:
            Enhanced DataFrame with personalization scores
        """
        # Get user's purchase history
        user_purchases = self.data_loader.get_user_purchased_products(user_id)
        
        # Add personalization score based on recommendations
        if user_id in self.user_item_matrix.index and not candidate_products.empty:
            # Get recommendation scores for candidate products
            personalization_scores = []
            
            for _, product in candidate_products.iterrows():
                product_id = product['product_id']
                
                # Skip products already purchased (unless it's a recommendation query)
                if product_id in user_purchases and query_analysis['intent'] != 'recommendation':
                    score = 0.0
                else:
                    # Calculate recommendation score
                    if product_id in self.user_item_matrix.columns:
                        # Use user-based collaborative filtering
                        similar_users = self.cf_model.get_similar_users(user_id, n_similar=20)
                        
                        if similar_users:
                            # Weighted average of similar users' interactions
                            total_score = 0
                            total_weight = 0
                            
                            for similar_user_id, similarity in similar_users:
                                if similar_user_id in self.user_item_matrix.index:
                                    interaction = self.user_item_matrix.loc[similar_user_id, product_id]
                                    total_score += interaction * similarity
                                    total_weight += similarity
                            
                            score = total_score / total_weight if total_weight > 0 else 0
                        else:
                            score = 0.5  # Neutral score
                    else:
                        score = 0.5  # New product - neutral score
                
                personalization_scores.append(score)
            
            candidate_products = candidate_products.copy()
            candidate_products['personalization_score'] = personalization_scores
        else:
            candidate_products = candidate_products.copy()
            candidate_products['personalization_score'] = 0.5  # Neutral for new users
        
        return candidate_products
    
    def _rank_products(
        self,
        products: pd.DataFrame,
        query_analysis: Dict,
        user_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Rank products by relevance combining multiple factors.
        
        Args:
            products: DataFrame of products to rank
            query_analysis: Query analysis information
            user_id: Optional user ID
            
        Returns:
            Sorted list of product dictionaries
        """
        if products.empty:
            return []
        
        products = products.copy()
        
        # Calculate relevance score
        products['relevance_score'] = 0.0
        
        # Keyword matching score (how many keywords match)
        if query_analysis['keywords']:
            for keyword in query_analysis['keywords']:
                name_match = products['product_name'].str.lower().str.contains(
                    keyword, na=False, regex=False
                ).astype(float)
                products['relevance_score'] += name_match * 2.0  # Name matches worth more
                
                if 'description' in products.columns:
                    desc_match = products['description'].str.lower().str.contains(
                        keyword, na=False, regex=False
                    ).astype(float)
                    products['relevance_score'] += desc_match * 1.0
        
        # Combine relevance with personalization
        if 'personalization_score' in products.columns:
            # Weighted combination (adjust weights as needed)
            products['final_score'] = (
                products['relevance_score'] * 0.6 +
                products['personalization_score'] * 0.4
            )
        else:
            products['final_score'] = products['relevance_score']
        
        # Add small random factor to break ties
        import numpy as np
        products['final_score'] += np.random.uniform(0, 0.01, size=len(products))
        
        # Sort by final score
        products = products.sort_values('final_score', ascending=False)
        
        # Convert to list of dictionaries
        result_list = []
        for _, product in products.iterrows():
            product_dict = product.to_dict()
            
            # Clean up internal scoring columns
            if 'relevance_score' in product_dict:
                product_dict['relevance_score'] = round(product_dict['relevance_score'], 4)
            if 'personalization_score' in product_dict:
                product_dict['personalization_score'] = round(product_dict['personalization_score'], 4)
            if 'final_score' in product_dict:
                product_dict['final_score'] = round(product_dict['final_score'], 4)
            
            result_list.append(product_dict)
        
        return result_list
    
    def get_conversation_suggestions(self, user_id: Optional[int] = None) -> List[str]:
        """
        Generate conversation starters based on user history.
        
        Args:
            user_id: Optional user ID for personalization
            
        Returns:
            List of suggested queries
        """
        suggestions = [
            "Show me affordable laptops",
            "I'm looking for running shoes",
            "Recommend me some books",
            "Find budget-friendly home decor",
        ]
        
        if user_id:
            # Get user's purchase history
            user_purchases = self.data_loader.load_purchase_history(user_id=user_id)
            
            if not user_purchases.empty:
                # Get categories user has purchased from
                products_df = self.data_loader.load_products()
                purchased_products = products_df[
                    products_df['product_id'].isin(user_purchases['product_id'])
                ]
                
                if not purchased_products.empty:
                    categories = purchased_products['category'].unique()[:3]
                    for category in categories:
                        suggestions.append(f"Show me more {category} products")
        
        return suggestions[:5]
