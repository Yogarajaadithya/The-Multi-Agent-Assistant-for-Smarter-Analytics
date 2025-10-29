"""
Test script for FastAPI Text-to-SQL + Visualization endpoints
"""

import requests
import json

# API base URL
BASE_URL = "http://127.0.0.1:8000/api"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)
    
    response = requests.get("http://127.0.0.1:8000/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_query_with_viz():
    """Test query endpoint with visualization"""
    print("\n" + "="*60)
    print("Testing Query Endpoint (with visualization)")
    print("="*60)
    
    payload = {
        "question": "What is the attrition rate by department?",
        "include_visualization": True
    }
    
    print(f"Request: {payload}")
    
    response = requests.post(f"{BASE_URL}/query", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"SQL: {data['sql']}")
        print(f"Rows returned: {data['rows']}")
        print(f"Columns: {data['columns']}")
        print(f"\nFirst 3 rows of data:")
        for i, row in enumerate(data['data'][:3], 1):
            print(f"  {i}. {row}")
        
        if data['visualization']:
            print(f"\nVisualization generated: {data['visualization']['success']}")
            if data['visualization']['success']:
                print(f"Visualization type: Plotly chart (JSON format)")
        
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_sql_only():
    """Test SQL-only endpoint"""
    print("\n" + "="*60)
    print("Testing SQL-Only Endpoint")
    print("="*60)
    
    payload = {
        "question": "Show average monthly income by gender",
        "include_visualization": False
    }
    
    print(f"Request: {payload}")
    
    response = requests.post(f"{BASE_URL}/sql-only", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"SQL: {data['sql']}")
        print(f"Rows returned: {data['rows']}")
        print(f"\nData:")
        for row in data['data']:
            print(f"  {row}")
        
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_chat_endpoint():
    """Test existing chat endpoint"""
    print("\n" + "="*60)
    print("Testing Chat Endpoint")
    print("="*60)
    
    payload = {
        "messages": [
            {"role": "user", "content": "Hello! Can you explain what is employee attrition?"}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    print(f"Request: Sending chat message...")
    
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['content'][:200]}...")
        return True
    else:
        print(f"Error: {response.text}")
        return False


if __name__ == "__main__":
    print("\n🚀 Testing FastAPI Endpoints with Combined Agent")
    print("="*60)
    
    # Run tests
    results = {
        "Health Check": test_health(),
        "Query with Visualization": test_query_with_viz(),
        "SQL Only": test_sql_only(),
        "Chat Endpoint": test_chat_endpoint()
    }
    
    # Summary
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    print("="*60)
