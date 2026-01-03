"""
Example usage of the recommendation system with sample data.
"""

import random
from datetime import datetime, timedelta
from config.database import db_config
from models.schemas import UserProfile, Product, create_sql_tables
from recommendation_engine import RecommendationEngine


def create_sample_data():
    """
    Create sample data for testing the recommendation system.
    """
    print("Creating sample data...")
    
    # Create SQL tables
    engine = db_config.get_sql_engine()
    create_sql_tables(engine)
    
    # Create sample users
    session = db_config.get_sql_session()
    
    sample_users = [
        UserProfile(username='alice', email='alice@example.com', age=28, gender='Female', location='New York'),
        UserProfile(username='bob', email='bob@example.com', age=35, gender='Male', location='San Francisco'),
        UserProfile(username='charlie', email='charlie@example.com', age=42, gender='Male', location='Chicago'),
        UserProfile(username='diana', email='diana@example.com', age=31, gender='Female', location='Boston'),
        UserProfile(username='eve', email='eve@example.com', age=26, gender='Female', location='Seattle'),
        UserProfile(username='frank', email='frank@example.com', age=39, gender='Male', location='Austin'),
        UserProfile(username='grace', email='grace@example.com', age=33, gender='Female', location='Denver'),
        UserProfile(username='henry', email='henry@example.com', age=45, gender='Male', location='Miami'),
        UserProfile(username='iris', email='iris@example.com', age=29, gender='Female', location='Portland'),
        UserProfile(username='jack', email='jack@example.com', age=37, gender='Male', location='Atlanta'),
    ]
    
    try:
        # Check if users already exist
        existing_users = session.query(UserProfile).count()
        if existing_users == 0:
            session.add_all(sample_users)
            session.commit()
            print(f"Created {len(sample_users)} sample users")
        else:
            print(f"Users already exist ({existing_users} users)")
    except Exception as e:
        session.rollback()
        print(f"Error creating users: {e}")
    finally:
        session.close()
    
    # Create sample products
    session = db_config.get_sql_session()
    
    sample_products = [
        Product(product_name='Wireless Headphones', category='Electronics', subcategory='Audio', price=79.99, brand='TechSound'),
        Product(product_name='Running Shoes', category='Sports', subcategory='Footwear', price=89.99, brand='SportFit'),
        Product(product_name='Coffee Maker', category='Home', subcategory='Kitchen', price=49.99, brand='BrewMaster'),
        Product(product_name='Yoga Mat', category='Sports', subcategory='Fitness', price=29.99, brand='FitLife'),
        Product(product_name='Laptop Stand', category='Electronics', subcategory='Accessories', price=39.99, brand='DeskPro'),
        Product(product_name='Water Bottle', category='Sports', subcategory='Accessories', price=19.99, brand='HydroFlow'),
        Product(product_name='Desk Lamp', category='Home', subcategory='Lighting', price=34.99, brand='BrightLight'),
        Product(product_name='Backpack', category='Fashion', subcategory='Bags', price=59.99, brand='TravelGear'),
        Product(product_name='Bluetooth Speaker', category='Electronics', subcategory='Audio', price=69.99, brand='SoundWave'),
        Product(product_name='Protein Powder', category='Health', subcategory='Supplements', price=44.99, brand='NutriBoost'),
        Product(product_name='Notebook Set', category='Office', subcategory='Stationery', price=14.99, brand='WriteWell'),
        Product(product_name='Plant Pot', category='Home', subcategory='Decor', price=24.99, brand='GreenHome'),
        Product(product_name='Phone Case', category='Electronics', subcategory='Accessories', price=19.99, brand='ProtectPlus'),
        Product(product_name='Cooking Pan', category='Home', subcategory='Kitchen', price=54.99, brand='ChefPro'),
        Product(product_name='Resistance Bands', category='Sports', subcategory='Fitness', price=24.99, brand='FitLife'),
    ]
    
    try:
        existing_products = session.query(Product).count()
        if existing_products == 0:
            session.add_all(sample_products)
            session.commit()
            print(f"Created {len(sample_products)} sample products")
        else:
            print(f"Products already exist ({existing_products} products)")
    finally:
        session.close()
    
    # Create sample purchase history in MongoDB
    collection = db_config.get_purchase_history_collection()
    
    # Check if purchase history already exists
    if collection.count_documents({}) == 0:
        purchases = []
        purchase_id_counter = 1
        
        # Create realistic purchase patterns
        # Users with similar interests
        electronics_fans = [1, 2, 6, 10]  # Alice, Bob, Frank, Jack
        fitness_fans = [2, 4, 5, 7]  # Bob, Diana, Eve, Grace
        home_fans = [1, 3, 4, 8, 9]  # Alice, Charlie, Diana, Henry, Iris
        
        for user_id in range(1, 11):
            num_purchases = random.randint(2, 5)
            
            for _ in range(num_purchases):
                # Create purchase based on user interests
                items = []
                
                if user_id in electronics_fans:
                    product_ids = random.sample([1, 5, 9, 13], random.randint(1, 2))
                    items.extend([{'product_id': pid, 'quantity': 1, 'price_at_purchase': random.uniform(20, 80), 'discount': 0.0} for pid in product_ids])
                
                if user_id in fitness_fans:
                    product_ids = random.sample([2, 4, 6, 10, 15], random.randint(1, 2))
                    items.extend([{'product_id': pid, 'quantity': 1, 'price_at_purchase': random.uniform(20, 90), 'discount': 0.0} for pid in product_ids])
                
                if user_id in home_fans:
                    product_ids = random.sample([3, 7, 12, 14], random.randint(1, 2))
                    items.extend([{'product_id': pid, 'quantity': 1, 'price_at_purchase': random.uniform(15, 60), 'discount': 0.0} for pid in product_ids])
                
                # Ensure at least one item
                if not items:
                    product_id = random.randint(1, 15)
                    items.append({'product_id': product_id, 'quantity': 1, 'price_at_purchase': random.uniform(15, 90), 'discount': 0.0})
                
                # Remove duplicates
                unique_items = []
                seen_products = set()
                for item in items:
                    if item['product_id'] not in seen_products:
                        unique_items.append(item)
                        seen_products.add(item['product_id'])
                
                purchase_date = datetime.now() - timedelta(days=random.randint(1, 90))
                total_amount = sum(item['price_at_purchase'] * item['quantity'] for item in unique_items)
                
                purchases.append({
                    'user_id': user_id,
                    'purchase_id': f'PUR{purchase_id_counter:06d}',
                    'purchase_date': purchase_date,
                    'items': unique_items,
                    'total_amount': round(total_amount, 2),
                    'payment_method': random.choice(['credit_card', 'debit_card', 'paypal']),
                    'shipping_address': f'{random.randint(100, 999)} Main St, City, State',
                    'status': 'completed'
                })
                purchase_id_counter += 1
        
        if purchases:
            collection.insert_many(purchases)
            print(f"Created {len(purchases)} sample purchases")
    else:
        print(f"Purchase history already exists ({collection.count_documents({})} purchases)")
    
    print("Sample data creation complete!")


def demonstrate_recommendations():
    """
    Demonstrate the recommendation system with sample data.
    """
    print("\n" + "="*60)
    print("RECOMMENDATION SYSTEM DEMONSTRATION")
    print("="*60)
    
    # Initialize recommendation engine
    engine = RecommendationEngine()
    
    # Test user ID
    test_user_id = 1  # Alice
    
    # Get user statistics
    print(f"\n--- User Statistics for User {test_user_id} ---")
    stats = engine.get_user_statistics(test_user_id)
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Get user-based recommendations
    print(f"\n--- User-Based Recommendations for User {test_user_id} ---")
    user_based_recs = engine.get_recommendations(
        user_id=test_user_id,
        method='user-based',
        n_recommendations=5
    )
    
    for i, rec in enumerate(user_based_recs, 1):
        print(f"\n{i}. {rec['product_name']} (ID: {rec['product_id']})")
        print(f"   Category: {rec['category']} - {rec['subcategory']}")
        print(f"   Price: ${rec['price']}")
        print(f"   Score: {rec['recommendation_score']}")
    
    # Get item-based recommendations
    print(f"\n--- Item-Based Recommendations for User {test_user_id} ---")
    item_based_recs = engine.get_recommendations(
        user_id=test_user_id,
        method='item-based',
        n_recommendations=5
    )
    
    for i, rec in enumerate(item_based_recs, 1):
        print(f"\n{i}. {rec['product_name']} (ID: {rec['product_id']})")
        print(f"   Category: {rec['category']} - {rec['subcategory']}")
        print(f"   Price: ${rec['price']}")
        print(f"   Score: {rec['recommendation_score']}")
    
    # Get similar users
    print(f"\n--- Similar Users to User {test_user_id} ---")
    similar_users = engine.get_similar_users(test_user_id, n_similar=3)
    for i, user in enumerate(similar_users, 1):
        print(f"{i}. User {user['user_id']} - Similarity: {user['similarity_score']}")
    
    # Get similar products
    print(f"\n--- Products Similar to Product 1 (Wireless Headphones) ---")
    similar_products = engine.get_similar_products(product_id=1, n_similar=3)
    for i, product in enumerate(similar_products, 1):
        print(f"{i}. {product['product_name']} (ID: {product['product_id']})")
        print(f"   Similarity: {product['similarity_score']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    # Create sample data
    create_sample_data()
    
    # Demonstrate recommendations
    demonstrate_recommendations()
