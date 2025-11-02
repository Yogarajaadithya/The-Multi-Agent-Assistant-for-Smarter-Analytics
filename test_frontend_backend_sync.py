# Frontend-Backend Integration Test

# This script tests the frontend-backend synchronization
# ensuring all questions route through the Planner Agent

import requests
import json
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5174"

# Test colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def test_backend_health() -> bool:
    """Test if backend is running and healthy."""
    print_info("Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Backend is healthy")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend. Is it running?")
        print_info("Start backend with: cd backend-repo && uvicorn app.main:app --reload --port 8000")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_what_question() -> bool:
    """Test WHAT question routing through Planner Agent."""
    print_info("Testing WHAT question (Descriptive Analytics)...")
    
    question = "What is the attrition rate by department?"
    payload = {
        "question": question,
        "include_visualization": True
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/analyze", json=payload, timeout=30)
        
        if response.status_code != 200:
            print_error(f"Request failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Validate response structure
        if not data.get("success"):
            print_error("Response indicates failure")
            return False
        
        if data.get("question_type") != "WHAT":
            print_error(f"Expected question_type='WHAT', got '{data.get('question_type')}'")
            return False
        
        if not data.get("sql"):
            print_error("Missing SQL query in response")
            return False
        
        if not data.get("data"):
            print_error("Missing data in response")
            return False
        
        print_success("WHAT question processed correctly")
        print_info(f"  Question Type: {data.get('question_type')}")
        print_info(f"  SQL Generated: {data.get('sql')[:50]}...")
        print_info(f"  Rows Returned: {len(data.get('data', []))}")
        print_info(f"  Visualization: {'✓' if data.get('visualization', {}).get('success') else '✗'}")
        
        return True
        
    except requests.exceptions.Timeout:
        print_error("Request timed out (LLM might be slow or not running)")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_why_question() -> bool:
    """Test WHY question routing through Planner Agent."""
    print_info("Testing WHY question (Causal Analytics)...")
    
    question = "Why do employees leave the company?"
    payload = {
        "question": question,
        "include_visualization": True
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/analyze", json=payload, timeout=60)
        
        if response.status_code != 200:
            print_error(f"Request failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Validate response structure
        if not data.get("success"):
            print_error("Response indicates failure")
            return False
        
        if data.get("question_type") != "WHY":
            print_error(f"Expected question_type='WHY', got '{data.get('question_type')}'")
            return False
        
        if not data.get("hypotheses"):
            print_error("Missing hypotheses in response")
            return False
        
        if not data.get("statistical_results"):
            print_error("Missing statistical_results in response")
            return False
        
        num_hypotheses = len(data.get("hypotheses", {}).get("hypotheses", []))
        num_tests = len(data.get("statistical_results", {}).get("hypothesis_results", []))
        
        # Count significant results
        significant_count = sum(
            1 for result in data.get("statistical_results", {}).get("hypothesis_results", [])
            if result.get("statistical_results", {}).get("p_value", 1) < 0.05
        )
        
        print_success("WHY question processed correctly")
        print_info(f"  Question Type: {data.get('question_type')}")
        print_info(f"  Hypotheses Generated: {num_hypotheses}")
        print_info(f"  Statistical Tests: {num_tests}")
        print_info(f"  Significant Results: {significant_count}/{num_tests} (p < 0.05)")
        
        return True
        
    except requests.exceptions.Timeout:
        print_error("Request timed out (Statistical tests can take longer)")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_planner_classification() -> bool:
    """Test that Planner Agent correctly classifies various questions."""
    print_info("Testing Planner Agent classification accuracy...")
    
    test_cases = [
        ("What is the average salary?", "WHAT"),
        ("Show me attrition by department", "WHAT"),
        ("How many employees left?", "WHAT"),
        ("Why is attrition high?", "WHY"),
        ("What causes employee turnover?", "WHY"),
        ("Explain the relationship between overtime and attrition", "WHY"),
    ]
    
    passed = 0
    failed = 0
    
    for question, expected_type in test_cases:
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/analyze",
                json={"question": question, "include_visualization": False},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                actual_type = data.get("question_type")
                
                if actual_type == expected_type:
                    print_success(f"'{question[:40]}...' → {actual_type}")
                    passed += 1
                else:
                    print_error(f"'{question[:40]}...' → Expected {expected_type}, got {actual_type}")
                    failed += 1
            else:
                print_error(f"Request failed for: '{question[:40]}...'")
                failed += 1
                
        except Exception as e:
            print_error(f"Error testing: '{question[:40]}...' - {e}")
            failed += 1
    
    print_info(f"Classification Results: {passed} passed, {failed} failed")
    return failed == 0

def test_frontend_accessibility() -> bool:
    """Test if frontend is accessible."""
    print_info("Testing frontend accessibility...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print_success("Frontend is accessible")
            return True
        else:
            print_error(f"Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_warning("Cannot connect to frontend. Is it running?")
        print_info("Start frontend with: cd frontend-repo && npm run dev")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("  FRONTEND-BACKEND INTEGRATION TEST SUITE")
    print("="*60 + "\n")
    
    results = {}
    
    # Test 1: Backend Health
    results["Backend Health"] = test_backend_health()
    print()
    
    if not results["Backend Health"]:
        print_error("Backend is not running. Cannot proceed with tests.")
        print_info("Please start the backend first.")
        return
    
    # Test 2: WHAT Question
    results["WHAT Question"] = test_what_question()
    print()
    
    # Test 3: WHY Question
    results["WHY Question"] = test_why_question()
    print()
    
    # Test 4: Planner Classification
    results["Planner Classification"] = test_planner_classification()
    print()
    
    # Test 5: Frontend Accessibility
    results["Frontend Accessibility"] = test_frontend_accessibility()
    print()
    
    # Summary
    print("="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name:<30} [{status}]")
    
    total = len(results)
    passed_count = sum(results.values())
    
    print("\n" + "="*60)
    print(f"  Results: {passed_count}/{total} tests passed")
    print("="*60 + "\n")
    
    if passed_count == total:
        print_success("🎉 All integration tests passed! Frontend and backend are synchronized.")
    else:
        print_error(f"⚠️  {total - passed_count} test(s) failed. Please review the errors above.")
    
    # Next steps
    print("\n" + "="*60)
    print("  NEXT STEPS")
    print("="*60)
    print("  1. Open frontend: http://localhost:5174")
    print("  2. Try example prompts:")
    print("     - What is the attrition rate by department?")
    print("     - Why do employees leave the company?")
    print("  3. Check browser console for 'Question type detected' logs")
    print("  4. Verify UI shows appropriate components for each question type")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
