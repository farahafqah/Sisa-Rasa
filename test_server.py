#!/usr/bin/env python3
"""
Test script to check if the SisaRasa server is working properly.
"""

import requests
import time

def test_endpoints():
    """Test various endpoints to see if they're working."""
    base_url = "http://127.0.0.1:5000"
    
    endpoints_to_test = [
        "/",
        "/welcome", 
        "/login",
        "/api/test",
        "/api/analytics/leftover-ingredients"
    ]
    
    print("Testing SisaRasa server endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        try:
            print(f"Testing {url}...")
            response = requests.get(url, timeout=10)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ SUCCESS")
            else:
                print(f"  ❌ FAILED")
                print(f"  Response: {response.text[:200]}...")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ ERROR: {e}")
        print()

if __name__ == "__main__":
    # Wait a bit for server to start
    print("Waiting 5 seconds for server to start...")
    time.sleep(5)
    test_endpoints()
