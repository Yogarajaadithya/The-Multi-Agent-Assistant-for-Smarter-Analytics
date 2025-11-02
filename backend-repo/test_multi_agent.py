"""
Test script for Multi-Agent System
Run this after starting the backend server to verify all agents work correctly.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_health():
    """Test health endpoint."""
    print("\n" + "="*70)
    print("🏥 TESTING HEALTH ENDPOINT")
    print("="*70)
    
    response = requests.get(f"{BASE_URL.replace('/api', '')}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_what_question():
    """Test WHAT question (descriptive analytics)."""
    print("\n" + "="*70)
    print("📊 TESTING WHAT QUESTION (Descriptive Analytics)")
    print("="*70)
    
    payload = {
        "question": "What is the attrition rate by department?",
        "include_visualization": True
    }
    
    print(f"\nRequest: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Success!")
        print(f"Question Type: {result.get('question_type')}")
        print(f"Analysis Type: {result.get('analysis_type')}")
        print(f"SQL Generated: {result.get('sql', 'N/A')[:100]}...")
        print(f"Rows Returned: {result.get('rows', 0)}")
        print(f"Visualization: {'✓' if result.get('visualization') else '✗'}")
        return True
    else:
        print(f"\n❌ Failed: {response.text}")
        return False


def test_why_question():
    """Test WHY question (causal analytics)."""
    print("\n" + "="*70)
    print("🔍 TESTING WHY QUESTION (Causal Analytics)")
    print("="*70)
    
    payload = {
        "question": "Why do employees leave the company?",
        "num_hypotheses": 3
    }
    
    print(f"\nRequest: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Success!")
        print(f"Question Type: {result.get('question_type')}")
        print(f"Analysis Type: {result.get('analysis_type')}")
        
        hypotheses = result.get('hypotheses', {}).get('hypotheses', [])
        print(f"Hypotheses Generated: {len(hypotheses)}")
        
        if hypotheses:
            print(f"\nFirst Hypothesis:")
            print(f"  H0: {hypotheses[0].get('null_hypothesis', 'N/A')[:80]}...")
            print(f"  H1: {hypotheses[0].get('alternative_hypothesis', 'N/A')[:80]}...")
            print(f"  Test: {hypotheses[0].get('recommended_test', 'N/A')}")
        
        stats = result.get('statistical_results', {})
        if stats.get('hypothesis_results'):
            print(f"\nStatistical Tests: {len(stats['hypothesis_results'])} completed")
            
            first_test = stats['hypothesis_results'][0].get('statistical_results', {})
            if 'p_value' in first_test:
                print(f"  First test p-value: {first_test['p_value']}")
                print(f"  Interpretation: {first_test.get('interpretation', 'N/A')[:80]}...")
        
        return True
    else:
        print(f"\n❌ Failed: {response.text}")
        return False


def test_direct_what():
    """Test direct WHAT endpoint."""
    print("\n" + "="*70)
    print("⚡ TESTING DIRECT WHAT ENDPOINT (Bypass Planner)")
    print("="*70)
    
    payload = {
        "question": "How many employees work overtime?",
        "include_visualization": False
    }
    
    print(f"\nRequest: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/analyze/what", json=payload)
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Success!")
        print(f"SQL: {result.get('sql', 'N/A')[:100]}...")
        print(f"Rows: {result.get('rows', 0)}")
        return True
    else:
        print(f"\n❌ Failed: {response.text}")
        return False


def test_legacy_query():
    """Test legacy query endpoint (backward compatibility)."""
    print("\n" + "="*70)
    print("🔄 TESTING LEGACY QUERY ENDPOINT (Backward Compatibility)")
    print("="*70)
    
    payload = {
        "question": "Show average monthly income by gender",
        "include_visualization": True
    }
    
    print(f"\nRequest: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/query", json=payload)
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Success!")
        print(f"SQL: {result.get('sql', 'N/A')[:100]}...")
        print(f"Rows: {result.get('rows', 0)}")
        return True
    else:
        print(f"\n❌ Failed: {response.text}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 MULTI-AGENT SYSTEM TEST SUITE")
    print("="*70)
    print("\nMake sure the backend server is running:")
    print("  cd backend-repo")
    print("  uvicorn app.main:app --reload --port 8000")
    print("\n" + "="*70)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("WHAT Question", test_what_question()))
    results.append(("WHY Question", test_why_question()))
    results.append(("Direct WHAT", test_direct_what()))
    results.append(("Legacy Query", test_legacy_query()))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} {test_name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print("\n" + "="*70)
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed. Check server logs.")
    print("="*70 + "\n")
    
    return passed_count == total_count


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server.")
        print("Please start the server first:")
        print("  cd backend-repo")
        print("  uvicorn app.main:app --reload --port 8000")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
