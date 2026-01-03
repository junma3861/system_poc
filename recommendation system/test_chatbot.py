"""
Test script for the chatbot search engine functionality.

Prerequisites:
1. Set OPENAI_API_KEY in .env file
2. Start the FastAPI server: uvicorn main:app --reload
3. Ensure databases are populated with data
"""

import requests
import json
import sys


BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_health():
    """Test health endpoint."""
    print_section("Testing Health Endpoint")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def test_chat(query, user_id=None, n_results=5):
    """Test chatbot endpoint."""
    print_section(f"Testing Chat: '{query}'")
    
    payload = {
        "query": query,
        "user_id": user_id,
        "n_results": n_results,
        "use_recommendations": True
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nIntent: {data['intent']}")
        print(f"Response: {data['response']}")
        print(f"\nFound {data['count']} products:")
        
        for i, product in enumerate(data['products'][:5], 1):
            print(f"\n{i}. {product.get('product_name', 'N/A')}")
            print(f"   Category: {product.get('category', 'N/A')}")
            print(f"   Price: ${product.get('price', 0):.2f}")
            if 'final_score' in product:
                print(f"   Relevance Score: {product['final_score']:.4f}")
        
        if data.get('suggestions'):
            print(f"\nSuggestions:")
            for suggestion in data['suggestions']:
                print(f"  - {suggestion}")
    else:
        print(f"Error: {response.text}")


def test_search(query, user_id=None, n_results=5):
    """Test search endpoint."""
    print_section(f"Testing Search: '{query}'")
    
    payload = {
        "query": query,
        "user_id": user_id,
        "n_results": n_results,
        "use_recommendations": True
    }
    
    response = requests.post(f"{BASE_URL}/search", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nIntent: {data['intent']}")
        print(f"Response: {data['response']}")
        
        query_analysis = data.get('query_analysis', {})
        if query_analysis.get('categories'):
            print(f"Detected Categories: {', '.join(query_analysis['categories'])}")
        if query_analysis.get('price_range'):
            min_p, max_p = query_analysis['price_range']
            print(f"Price Range: ${min_p} - ${max_p if max_p != float('inf') else '∞'}")
        if query_analysis.get('keywords'):
            print(f"Keywords: {', '.join(query_analysis['keywords'])}")
        
        print(f"\nFound {data['count']} products:")
        
        for i, product in enumerate(data['products'][:5], 1):
            print(f"\n{i}. {product.get('product_name', 'N/A')}")
            print(f"   Category: {product.get('category', 'N/A')}")
            print(f"   Price: ${product.get('price', 0):.2f}")
            if 'final_score' in product:
                print(f"   Score: {product['final_score']:.4f}")
    else:
        print(f"Error: {response.text}")


def test_suggestions(user_id=None):
    """Test chat suggestions endpoint."""
    print_section("Testing Chat Suggestions")
    
    url = f"{BASE_URL}/chat/suggestions"
    if user_id:
        url += f"?user_id={user_id}"
    
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nSuggested queries:")
        for suggestion in data['suggestions']:
            print(f"  • {suggestion}")
    else:
        print(f"Error: {response.text}")


def main():
    """Run all tests."""
    print("=" * 80)
    print("  CHATBOT SEARCH ENGINE TEST SUITE")
    print("=" * 80)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ Server is not responding correctly. Please start the server:")
            print("   uvicorn main:app --reload")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Please start the server:")
        print("   uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error connecting to server: {e}")
        sys.exit(1)
    
    # Test 1: Health check
    try:
        test_health()
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Basic chat queries
    test_queries = [
        "Hello!",
        "Show me affordable laptops",
        "I'm looking for running shoes under $100",
        "Find me some books",
        "Recommend me electronics",
        "What are some luxury items?",
    ]
    
    for query in test_queries:
        try:
            test_chat(query, user_id=1)
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 3: Search with user_id (personalized)
    try:
        test_search("Show me products you think I'd like", user_id=1, n_results=10)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Get suggestions
    try:
        test_suggestions(user_id=1)
    except Exception as e:
        print(f"Error: {e}")
    
    print_section("Tests Complete!")


if __name__ == "__main__":
    main()
