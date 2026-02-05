#!/usr/bin/env python
"""
Test script to verify homepage accessibility at root path
"""

import requests
import sys

def test_homepage_access():
    """Test that homepage is accessible at root path"""
    try:
        # Test homepage access
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        print(f"Homepage Status Code: {response.status_code}")
        print(f"Homepage Content Length: {len(response.text)}")
        
        # Check if it's the MelonMind homepage
        if 'MelonMind' in response.text and '智能运维助手' in response.text:
            print("✅ Homepage content verified - MelonMind homepage loaded successfully")
        else:
            print("❌ Homepage content doesn't match expected template")
            return False
            
        # Test health check endpoint
        health_response = requests.get('http://127.0.0.1:8000/health/', timeout=5)
        print(f"Health Check Status Code: {health_response.status_code}")
        
        if health_response.status_code == 200:
            print("✅ Health check endpoint working")
        else:
            print("❌ Health check endpoint not working")
            return False
            
        # Test that API endpoints are still accessible under /api/
        api_response = requests.get('http://127.0.0.1:8000/api/', timeout=5)
        print(f"API Root Status Code: {api_response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error testing homepage: {e}")
        return False

if __name__ == "__main__":
    print("Testing MelonMind homepage accessibility...")
    success = test_homepage_access()
    sys.exit(0 if success else 1)