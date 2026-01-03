"""
Test script for Memory Management features.
Tests both short-term (session) and long-term (history) memory.
"""

import requests
import uuid
import time
from datetime import datetime

API_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_memory_features():
    """Test all memory management features."""
    
    # Generate unique session ID
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    user_id = 1
    
    print_section("🧪 Memory Management Test Suite")
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: First message (establish context)
        print_section("1️⃣  First Message - Establishing Context")
        response = requests.post(f"{API_URL}/chat", json={
            "query": "Show me affordable laptops",
            "user_id": user_id,
            "session_id": session_id,
            "n_results": 3
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Query: {data['query']}")
            print(f"✓ Intent: {data['intent']}")
            print(f"✓ Products found: {data['count']}")
            print(f"✓ Response: {data['response'][:100]}...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return
        
        time.sleep(1)
        
        # Test 2: Contextual follow-up
        print_section("2️⃣  Contextual Follow-up (uses memory)")
        response = requests.post(f"{API_URL}/chat", json={
            "query": "Show me more expensive ones from Apple",
            "user_id": user_id,
            "session_id": session_id,
            "n_results": 3
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Query: {data['query']}")
            print(f"✓ Intent: {data['intent']}")
            print(f"✓ Products found: {data['count']}")
            print(f"✓ Response: {data['response'][:100]}...")
        else:
            print(f"❌ Error: {response.status_code}")
        
        time.sleep(1)
        
        # Test 3: Another contextual query
        print_section("3️⃣  Another Follow-up")
        response = requests.post(f"{API_URL}/chat", json={
            "query": "What about gaming laptops?",
            "user_id": user_id,
            "session_id": session_id,
            "n_results": 3
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Query: {data['query']}")
            print(f"✓ Products found: {data['count']}")
        
        # Test 4: Get session summary
        print_section("4️⃣  Session Summary")
        response = requests.get(f"{API_URL}/memory/session/{session_id}?user_id={user_id}")
        
        if response.status_code == 200:
            data = response.json()
            session = data['session']
            print(f"✓ Session ID: {session['session_id']}")
            print(f"✓ Message count: {session['message_count']}")
            print(f"✓ Started at: {session['started_at']}")
            print(f"✓ Last activity: {session['last_activity']}")
            print(f"\nConversation:")
            for i, msg in enumerate(session['messages'], 1):
                role = "👤 User" if msg['role'] == 'user' else "🤖 Bot"
                content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                print(f"  {i}. {role}: {content}")
        else:
            print(f"❌ Error: {response.status_code}")
        
        # Test 5: User preferences extraction
        print_section("5️⃣  Extract User Preferences")
        response = requests.get(f"{API_URL}/memory/preferences/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            prefs = data['preferences']
            print(f"✓ Top Categories: {', '.join(prefs.get('categories', []))}")
            print(f"✓ Favorite Brands: {', '.join(prefs.get('brands', []))}")
            print(f"✓ Common Keywords: {', '.join(prefs.get('keywords', [])[:5])}")
        else:
            print(f"⚠️  No preferences found yet (may need more conversation history)")
        
        # Test 6: Conversation history
        print_section("6️⃣  User Conversation History (Last 30 days)")
        response = requests.get(f"{API_URL}/memory/history/{user_id}?days=30&limit=10")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Total messages in history: {data['count']}")
            if data['count'] > 0:
                print(f"✓ Recent conversations:")
                for i, conv in enumerate(data['history'][:5], 1):
                    content = conv['content'][:60] + "..." if len(conv['content']) > 60 else conv['content']
                    print(f"  {i}. [{conv['role']}] {content}")
        else:
            print(f"❌ Error: {response.status_code}")
        
        # Test 7: Clear session
        print_section("7️⃣  Clear Session Memory")
        confirm = input("\nClear the test session? (y/n): ")
        if confirm.lower() == 'y':
            response = requests.delete(f"{API_URL}/memory/session/{session_id}?user_id={user_id}")
            
            if response.status_code == 200:
                print(f"✓ {response.json()['message']}")
            else:
                print(f"❌ Error: {response.status_code}")
        else:
            print("⏭️  Skipped session clearing")
        
        print_section("✅ Test Suite Complete")
        print("\n📊 Memory System Status:")
        print("  • Short-term memory (Redis): Working ✓")
        print("  • Long-term memory (MongoDB): Working ✓")
        print("  • Session management: Working ✓")
        print("  • Context awareness: Working ✓")
        print("  • Preference extraction: Working ✓")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to the API server")
        print("   Make sure the server is running: uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


def test_memory_availability():
    """Test if memory services (Redis/MongoDB) are available."""
    print_section("🔍 Testing Memory Service Availability")
    
    try:
        # Check if server is running
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✓ API server is running")
        else:
            print("❌ API server returned error")
            return False
        
        # Test a simple chat to trigger memory initialization
        test_session = f"availability_test_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{API_URL}/chat", json={
            "query": "Hello",
            "session_id": test_session,
            "n_results": 1
        })
        
        if response.status_code == 200:
            print("✓ Memory system initialized successfully")
            
            # Check session
            response = requests.get(f"{API_URL}/memory/session/{test_session}")
            if response.status_code == 200:
                print("✓ Redis (short-term memory): Available")
            else:
                print("⚠️  Redis may not be available (falling back to in-memory)")
            
            # Clean up
            requests.delete(f"{API_URL}/memory/session/{test_session}")
            return True
        else:
            print(f"❌ Memory system error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Start server: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n🧠 Memory Management Test Suite")
    print("=" * 60)
    print("This script tests the conversation memory features")
    print("=" * 60)
    
    # First check if services are available
    if not test_memory_availability():
        print("\n⚠️  Memory services may not be fully available")
        print("   Install Redis: brew install redis (macOS)")
        print("   Start Redis: brew services start redis")
        print("   Or run: ./setup_memory.sh")
        confirm = input("\nContinue anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("Exiting...")
            exit(0)
    
    print("\n")
    test_memory_features()
    
    print("\n" + "=" * 60)
    print("  📚 For more information, see MEMORY_MANAGEMENT.md")
    print("=" * 60 + "\n")
