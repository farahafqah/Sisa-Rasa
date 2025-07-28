#!/usr/bin/env python3
"""
Test script to verify analytics tracking functionality.
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "password123"

def test_analytics_tracking():
    """Test the analytics tracking system."""
    print("🧪 Testing Analytics Tracking System")
    print("=" * 50)

    # Step 0: Create a test user first
    print("0. Creating test user...")
    signup_response = requests.post(f"{BASE_URL}/api/auth/signup", json={
        "name": "Test User",
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })

    if signup_response.status_code == 200:
        signup_data = signup_response.json()
        print(f"✅ User created: {signup_data}")
    elif signup_response.status_code == 400:
        print("ℹ️ User already exists, continuing...")
    else:
        print(f"❌ Failed to create user: {signup_response.status_code}")
        print(f"Response: {signup_response.text}")

    # Step 1: Login to get a token
    print("\n1. Logging in...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False

    login_data = login_response.json()
    if login_data.get('status') != 'success':
        print(f"❌ Login failed: {login_data}")
        return False

    token = login_data.get('token') or login_data.get('access_token')
    if not token:
        print(f"❌ No token received: {login_data}")
        return False

    print(f"✅ Login successful, token: {token[:20]}...")
    
    # Step 2: Get current analytics data
    print("\n2. Getting current analytics...")
    analytics_response = requests.get(f"{BASE_URL}/api/analytics/leftover-ingredients")
    
    if analytics_response.status_code == 200:
        analytics_data = analytics_response.json()
        print(f"✅ Current analytics: {analytics_data}")
        
        # Find chicken count
        chicken_count_before = 0
        if analytics_data.get('status') == 'success':
            for item in analytics_data.get('data', {}).get('most_searched_leftovers', []):
                if item.get('name', '').lower() == 'chicken':
                    chicken_count_before = item.get('count', 0)
                    break
        
        print(f"🔍 Chicken count before: {chicken_count_before}")
    else:
        print(f"❌ Failed to get analytics: {analytics_response.status_code}")
        return False
    
    # Step 3: Save a search with chicken
    print("\n3. Saving search with chicken...")
    search_data = {
        "title": "Test Search",
        "ingredients": "chicken, rice, tomato",
        "ingredientsList": ["chicken", "rice", "tomato"],
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    search_response = requests.post(
        f"{BASE_URL}/api/dashboard/search-history",
        json=search_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if search_response.status_code == 200:
        search_result = search_response.json()
        print(f"✅ Search saved: {search_result}")
    else:
        print(f"❌ Failed to save search: {search_response.status_code}")
        print(f"Response: {search_response.text}")
        return False
    
    # Step 4: Track analytics event
    print("\n4. Tracking analytics event...")
    track_response = requests.post(
        f"{BASE_URL}/api/analytics/track",
        json={
            "event_type": "search",
            "event_data": {
                "ingredients": ["chicken", "rice", "tomato"],
                "ingredient_count": 3
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Track response status: {track_response.status_code}")
    print(f"Track response headers: {dict(track_response.headers)}")

    if track_response.status_code == 200:
        track_result = track_response.json()
        print(f"✅ Analytics tracked: {track_result}")
    else:
        print(f"❌ Failed to track analytics: {track_response.status_code}")
        print(f"Response: {track_response.text}")

        # Try to get more details about the error
        try:
            error_data = track_response.json()
            print(f"Error details: {error_data}")
        except:
            print("Could not parse error response as JSON")

        # Continue with the test to see if search history was saved properly
        print("⚠️ Analytics tracking failed, but continuing to check if search was saved...")
        pass  # Don't return False, continue with the test
    
    # Step 5: Wait and check analytics again
    print("\n5. Waiting 2 seconds and checking analytics again...")
    time.sleep(2)
    
    analytics_response2 = requests.get(f"{BASE_URL}/api/analytics/leftover-ingredients")
    
    if analytics_response2.status_code == 200:
        analytics_data2 = analytics_response2.json()
        print(f"✅ Updated analytics: {analytics_data2}")
        
        # Find chicken count after
        chicken_count_after = 0
        if analytics_data2.get('status') == 'success':
            for item in analytics_data2.get('data', {}).get('most_searched_leftovers', []):
                if item.get('name', '').lower() == 'chicken':
                    chicken_count_after = item.get('count', 0)
                    break
        
        print(f"🔍 Chicken count after: {chicken_count_after}")
        
        # Check if count increased
        if chicken_count_after > chicken_count_before:
            print(f"🎉 SUCCESS! Chicken count increased from {chicken_count_before} to {chicken_count_after}")
            return True
        else:
            print(f"❌ FAILED! Chicken count did not increase (before: {chicken_count_before}, after: {chicken_count_after})")
            return False
    else:
        print(f"❌ Failed to get updated analytics: {analytics_response2.status_code}")
        return False

if __name__ == "__main__":
    success = test_analytics_tracking()
    if success:
        print("\n🎉 Analytics tracking test PASSED!")
    else:
        print("\n❌ Analytics tracking test FAILED!")
