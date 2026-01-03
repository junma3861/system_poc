"""
Database connection and configuration utilities.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """
    Manages database connections for both SQL and MongoDB.
    """
    
    def __init__(self):
        # SQL Database Configuration
        self.sql_url = os.getenv('SQL_DATABASE_URL', 'postgresql://user:password@localhost:5432/recommendation_db')
        self.sql_engine = None
        self.sql_session_factory = None
        
        # MongoDB Configuration
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.mongo_db_name = os.getenv('MONGO_DATABASE', 'recommendation_db')
        self.mongo_client = None
        self.mongo_db = None
        
        # OpenAI Configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    def get_sql_engine(self):
        """
        Get or create SQL database engine.
        
        Returns:
            SQLAlchemy engine instance
        """
        if self.sql_engine is None:
            self.sql_engine = create_engine(self.sql_url, echo=False)
        return self.sql_engine
    
    def get_sql_session(self):
        """
        Get a new SQL database session.
        
        Returns:
            SQLAlchemy session instance
        """
        if self.sql_session_factory is None:
            engine = self.get_sql_engine()
            self.sql_session_factory = sessionmaker(bind=engine)
        return self.sql_session_factory()
    
    def get_mongo_db(self):
        """
        Get or create MongoDB database connection.
        
        Returns:
            MongoDB database instance
        """
        if self.mongo_db is None:
            self.mongo_client = MongoClient(self.mongo_uri)
            self.mongo_db = self.mongo_client[self.mongo_db_name]
        return self.mongo_db
    
    def get_purchase_history_collection(self):
        """
        Get the purchase history collection from MongoDB.
        
        Returns:
            MongoDB collection instance
        """
        db = self.get_mongo_db()
        return db['purchase_history']
    
    def close_connections(self):
        """
        Close all database connections.
        """
        if self.sql_engine:
            self.sql_engine.dispose()
        if self.mongo_client:
            self.mongo_client.close()


# Global database configuration instance
db_config = DatabaseConfig()
