"""
Test script for the Recommendation System API.
Run the FastAPI server first: uvicorn main:app --reload
"""

import requests
import json
import sys
from typing import Optional

BASE_URL = "http://localhost:8000"


def print_response(title: str, response: requests.Response, show_full: bool = True):
    """Pretty print API response"""
    print(f"\n{'='*70}")
    print(f"🧪 {title}")
    print(f"{'='*70}")
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            if show_full:
                print(f"\n{json.dumps(data, indent=2)}")
            else:
                # Show truncated version for large responses
                if isinstance(data, dict):
                    print(f"\nResponse keys: {list(data.keys())}")
                    if 'count' in data:
                        print(f"Count: {data['count']}")
                    if 'recommendations' in data and data['recommendations']:
                        print(f"First recommendation: {json.dumps(data['recommendations'][0], indent=2)}")
                    elif 'similar_users' in data and data['similar_users']:
                        print(f"First similar user: {json.dumps(data['similar_users'][0], indent=2)}")
                    elif 'similar_products' in data and data['similar_products']:
                        print(f"First similar product: {json.dumps(data['similar_products'][0], indent=2)}")
        except json.JSONDecodeError:
            print(f"Response: {response.text}")
    else:
        print(f"❌ Error: {response.text}")
    
    print("✓ Test passed" if response.status_code == 200 else "✗ Test failed")


def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_response("Health Check", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_root():
    """Test root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print_response("Root Endpoint", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False


def test_api_info():
    """Test API info endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/info")
        print_response("API Info", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API info failed: {e}")
        return False


def test_user_recommendations(user_id: int = 1, method: str = "user-based", n: int = 5):
    """Test recommendations endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations/{user_id}",
            params={
                "method": method,
                "n_recommendations": n,
                "include_details": True
            }
        )
        print_response(
            f"Recommendations for User {user_id} ({method}, n={n})", 
            response,
            show_full=False
        )
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Recommendations test failed: {e}")
        return False


def test_similar_users(user_id: int = 1, n: int = 5):
    """Test similar users endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/users/{user_id}/similar",
            params={"n_similar": n}
        )
        print_response(
            f"Similar Users to User {user_id} (n={n})", 
            response,
            show_full=False
        )
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Similar users test failed: {e}")
        return False


def test_similar_products(product_id: int = 1, n: int = 5):
    """Test similar products endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/products/{product_id}/similar",
            params={"n_similar": n}
        )
        print_response(
            f"Similar Products to Product {product_id} (n={n})", 
            response,
            show_full=False
        )
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Similar products test failed: {e}")
        return False


def test_user_statistics(user_id: int = 1):
    """Test user statistics endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/users/{user_id}/statistics")
        print_response(f"Statistics for User {user_id}", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ User statistics test failed: {e}")
        return False


def test_reload_data():
    """Test reload data endpoint"""
    try:
        response = requests.post(f"{BASE_URL}/reload-data")
        print_response("Reload Data", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Reload data test failed: {e}")
        return False


def test_error_handling():
    """Test error handling with invalid requests"""
    print(f"\n{'='*70}")
    print("🧪 Testing Error Handling")
    print(f"{'='*70}")
    
    tests = [
        ("Invalid user ID (0)", f"{BASE_URL}/recommendations/0"),
        ("Invalid user ID (-1)", f"{BASE_URL}/recommendations/-1"),
        ("Invalid method", f"{BASE_URL}/recommendations/1?method=invalid"),
        ("Invalid n_recommendations (too high)", f"{BASE_URL}/recommendations/1?n_recommendations=100"),
        ("Non-existent user (999999)", f"{BASE_URL}/recommendations/999999"),
        ("Non-existent product (999999)", f"{BASE_URL}/products/999999/similar"),
    ]
    
    passed = 0
    for test_name, url in tests:
        try:
            response = requests.get(url)
            # We expect 4xx errors for these
            if 400 <= response.status_code < 500:
                print(f"✓ {test_name}: Got expected error {response.status_code}")
                passed += 1
            else:
                print(f"✗ {test_name}: Unexpected status {response.status_code}")
        except Exception as e:
            print(f"✗ {test_name}: Exception - {e}")
    
    print(f"\nError handling tests: {passed}/{len(tests)} passed")
    return passed == len(tests)


def test_parameter_variations():
    """Test different parameter combinations"""
    print(f"\n{'='*70}")
    print("🧪 Testing Parameter Variations")
    print(f"{'='*70}")
    
    tests = [
        ("Min recommendations (n=1)", 1, "user-based", 1),
        ("Max recommendations (n=50)", 1, "user-based", 50),
        ("Item-based method", 1, "item-based", 10),
        ("Different user", 2, "user-based", 5),
    ]
    
    passed = 0
    for test_name, user_id, method, n in tests:
        try:
            response = requests.get(
                f"{BASE_URL}/recommendations/{user_id}",
                params={
                    "method": method,
                    "n_recommendations": n,
                    "include_details": False
                }
            )
            if response.status_code == 200:
                data = response.json()
                actual_count = len(data.get('recommendations', []))
                expected_count = min(n, actual_count)  # May return fewer if not enough data
                print(f"✓ {test_name}: Status {response.status_code}, got {actual_count} recommendations")
                passed += 1
            else:
                print(f"✗ {test_name}: Status {response.status_code}")
        except Exception as e:
            print(f"✗ {test_name}: Exception - {e}")
    
    print(f"\nParameter variation tests: {passed}/{len(tests)} passed")
    return passed > 0  # At least some should pass


def run_all_tests():
    """Run all API tests"""
    print("\n" + "🚀 Testing Recommendation System API".center(70, "="))
    print(f"Base URL: {BASE_URL}\n")
    
    test_results = []
    
    try:
        # Check if server is running
        print("📡 Checking server connectivity...")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            return
        print("✓ Server is online and responding\n")
        
        # Run basic endpoint tests
        print("\n" + "📋 Basic Endpoint Tests".center(70, "-"))
        test_results.append(("Root Endpoint", test_root()))
        test_results.append(("Health Check", test_health_check()))
        test_results.append(("API Info", test_api_info()))
        
        # Run main feature tests
        print("\n" + "🎯 Recommendation Tests".center(70, "-"))
        test_results.append(("User-based Recommendations", test_user_recommendations(1, "user-based", 5)))
        test_results.append(("Item-based Recommendations", test_user_recommendations(1, "item-based", 5)))
        
        print("\n" + "👥 Similarity Tests".center(70, "-"))
        test_results.append(("Similar Users", test_similar_users(1, 5)))
        test_results.append(("Similar Products", test_similar_products(1, 5)))
        
        print("\n" + "📊 Statistics Tests".center(70, "-"))
        test_results.append(("User Statistics", test_user_statistics(1)))
        
        # Run advanced tests
        print("\n" + "🔧 Advanced Tests".center(70, "-"))
        test_results.append(("Parameter Variations", test_parameter_variations()))
        test_results.append(("Error Handling", test_error_handling()))
        
        # Optional: Test reload (commented out as it may be disruptive)
        # test_results.append(("Reload Data", test_reload_data()))
        
        # Print summary
        print("\n" + "📈 Test Summary".center(70, "="))
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n{'='*70}")
        print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print(f"{'='*70}\n")
        
        if passed == total:
            print("🎉 All tests passed!")
        elif passed > total * 0.7:
            print("⚠️  Most tests passed, but some failures detected")
        else:
            print("❌ Multiple test failures detected")
        
    except requests.exceptions.ConnectionError:
        print("\n" + "❌ Error: Could not connect to the API".center(70, "="))
        print("\nMake sure the server is running:")
        print("  python main.py")
        print("or")
        print("  uvicorn main:app --reload\n")
    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timed out\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Allow testing specific endpoints
        command = sys.argv[1].lower()
        
        if command == "health":
            test_health_check()
        elif command == "info":
            test_api_info()
        elif command == "recommend":
            user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            test_user_recommendations(user_id)
        elif command == "similar-users":
            user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            test_similar_users(user_id)
        elif command == "similar-products":
            product_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            test_similar_products(product_id)
        elif command == "stats":
            user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            test_user_statistics(user_id)
        else:
            print(f"Unknown command: {command}")
            print("Available commands: health, info, recommend, similar-users, similar-products, stats")
    else:
        # Run all tests
        run_all_tests()


if __name__ == "__main__":
    main()
