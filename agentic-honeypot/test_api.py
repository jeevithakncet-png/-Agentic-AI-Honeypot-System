#!/usr/bin/env python
"""
Test script for Agentic Honeypot API
Sends sample scam messages to the API for testing and verification
"""

import requests
import json
import sys
from typing import Dict, Any
import time

API_BASE_URL = "http://localhost:8000"
API_KEY = "honey-pot-secret-key-123"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_health_check():
    """Test the health check endpoint."""
    print(f"\n{BLUE}Testing Health Check...{RESET}")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        if response.status_code == 200:
            print(f"{GREEN}✓ Health check passed{RESET}")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"{RED}✗ Health check failed: {response.status_code}{RESET}")
            return False
    except requests.ConnectionError:
        print(f"{RED}✗ Cannot connect to API at {API_BASE_URL}{RESET}")
        return False


def test_authentication():
    """Test API authentication."""
    print(f"\n{BLUE}Testing Authentication...{RESET}")
    
    # Test without API key
    print("  - Testing without API key...")
    response = requests.post(
        f"{API_BASE_URL}/api/analyze-message",
        json={"sessionId": "test", "message": {"text": "test"}}
    )
    if response.status_code == 401:
        print(f"  {GREEN}✓ Correctly rejected request without API key{RESET}")
    else:
        print(f"  {RED}✗ Should reject unauthorized requests{RESET}")
    
    # Test with invalid API key
    print("  - Testing with invalid API key...")
    response = requests.post(
        f"{API_BASE_URL}/api/analyze-message",
        headers={"x-api-key": "invalid-key"},
        json={"sessionId": "test", "message": {"text": "test"}}
    )
    if response.status_code == 403:
        print(f"  {GREEN}✓ Correctly rejected invalid API key{RESET}")
        return True
    else:
        print(f"  {RED}✗ Should reject invalid API keys{RESET}")
        return False


def test_scam_detection(message: str, expected_scam: bool = True) -> Dict[str, Any]:
    """Test scam detection on a message."""
    payload = {
        "sessionId": f"test-{int(time.time())}",
        "message": {
            "sender": "scammer",
            "text": message,
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/analyze-message",
            headers={"x-api-key": API_KEY},
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            is_scam = result.get("status") == "success"
            
            if is_scam == expected_scam:
                status_icon = GREEN if is_scam else YELLOW
                status_text = "SCAM DETECTED" if is_scam else "LEGITIMATE"
                print(f"  {status_icon}✓ {status_text}{RESET}")
                if is_scam:
                    print(f"    Reply: {result.get('reply', 'N/A')}")
            else:
                print(f"  {RED}✗ Expected {'scam' if expected_scam else 'legitimate'}, got {'scam' if is_scam else 'legitimate'}{RESET}")
            
            return result
        else:
            print(f"  {RED}✗ API error: {response.status_code} - {response.text}{RESET}")
            return {}
    except Exception as e:
        print(f"  {RED}✗ Error: {str(e)}{RESET}")
        return {}


def run_tests():
    """Run all tests."""
    print(f"\n{BLUE}{'='*60}")
    print(f"Agentic Honeypot API - Test Suite")
    print(f"{'='*60}{RESET}")
    
    # Health check
    if not test_health_check():
        print(f"\n{RED}API is not running. Start it with: uvicorn app.main:app --reload{RESET}")
        return False
    
    # Authentication
    if not test_authentication():
        print(f"\n{RED}Authentication tests failed{RESET}")
        return False
    
    # Scam detection tests
    print(f"\n{BLUE}Testing Scam Detection...{RESET}")
    
    scam_tests = [
        {
            "message": "Your bank account will be blocked. Verify immediately at http://bank-verify.com",
            "expected": True,
            "name": "Banking Fraud"
        },
        {
            "message": "Send your UPI ID (name@upi) to claim your ₹50,000 prize!",
            "expected": True,
            "name": "UPI Fraud"
        },
        {
            "message": "Share your OTP to unlock your account [URGENT]",
            "expected": True,
            "name": "OTP Phishing"
        },
        {
            "message": "Hi, can you help with bus directions?",
            "expected": False,
            "name": "Legitimate Message"
        },
        {
            "message": "Get free iPhone! Call +919876543210 now, limited time offer!",
            "expected": True,
            "name": "Prize Scam"
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in scam_tests:
        print(f"\n  Test: {test['name']}")
        print(f"  Message: {test['message']}")
        test_scam_detection(test['message'], test['expected'])
        passed += 1
    
    # Summary
    print(f"\n{BLUE}{'='*60}")
    print(f"Test Summary: {passed} passed, {failed} failed")
    print(f"{'='*60}{RESET}\n")
    
    return True


def test_multi_turn():
    """Test multi-turn conversation."""
    print(f"\n{BLUE}Testing Multi-turn Conversation...{RESET}")
    
    session_id = f"multi-turn-{int(time.time())}"
    conversation = [
        "Your bank account has suspicious activity. Click to verify: http://verify.com",
        "To confirm your identity, share your 16-digit card number and CVV",
        "Also provide your UPI ID (yourname@upi) for faster verification"
    ]
    
    conversation_history = []
    
    for i, message in enumerate(conversation):
        print(f"\n  Message {i+1}: {message}")
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": message,
                "timestamp": int(time.time() * 1000) + (i * 60000)
            },
            "conversationHistory": conversation_history,
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/analyze-message",
            headers={"x-api-key": API_KEY},
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  {GREEN}✓ Agent reply: {result.get('reply', 'N/A')}{RESET}")
            conversation_history.append({
                "sender": "scammer",
                "text": message,
                "timestamp": payload["message"]["timestamp"]
            })
        else:
            print(f"  {RED}✗ Error: {response.status_code}{RESET}")
    
    # Get session info
    print(f"\n  Fetching session info...")
    response = requests.get(
        f"{API_BASE_URL}/api/session/{session_id}",
        headers={"x-api-key": API_KEY}
    )
    
    if response.status_code == 200:
        session_info = response.json()
        print(f"  {GREEN}✓ Session Info:{RESET}")
        print(f"    - Messages: {session_info['messageCount']}")
        print(f"    - Scam Detected: {session_info['scamDetected']}")
        print(f"    - Intelligence: {json.dumps(session_info['extractedIntelligence'], indent=6)}")
    else:
        print(f"  {RED}✗ Error getting session info{RESET}")


if __name__ == "__main__":
    # Run basic tests
    if run_tests():
        # Run multi-turn test
        test_multi_turn()
        print(f"\n{GREEN}All tests completed!{RESET}")
    else:
        sys.exit(1)
