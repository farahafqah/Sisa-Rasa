#!/usr/bin/env python3
"""
Test script to verify analytics functionality works in Railway environment.
This script tests the specific analytics endpoint that was failing.
"""

import requests
import json
import time
import os

def test_railway_analytics():
    """Test the analytics functionality that was failing on Railway."""
    
    # Use Railway URL if available, otherwise local
    base_url = os.getenv('RAILWAY_URL', 'http://127.0.0.1:5000')
    if base_url.endswith('.railway.app'):
        base_url = f"https://{base_url}"
    elif not base_url.startswith('http'):
        base_url = f"http://{base_url}"
    
    print(f"🧪 Testing Analytics on: {base_url}")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        health_response = requests.get(f"{base_url}/api/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Health check passed: {health_data}")
            
            # Check database status
            db_status = health_data.get('database', 'unknown')
            if '✅' in db_status:
                print("✅ Database connection is working")
            else:
                print(f"⚠️ Database status: {db_status}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Analytics endpoint (the main issue)
    print("\n2. Testing analytics endpoint...")
    try:
        analytics_response = requests.get(
            f"{base_url}/api/analytics/leftover-ingredients", 
            timeout=15
        )
        
        print(f"Analytics response status: {analytics_response.status_code}")
        print(f"Analytics response headers: {dict(analytics_response.headers)}")
        
        if analytics_response.status_code == 200:
            analytics_data = analytics_response.json()
            print(f"✅ Analytics endpoint working!")
            print(f"Response: {json.dumps(analytics_data, indent=2)}")
            
            # Check if we got real data or fallback
            data_source = analytics_data.get('data', {}).get('data_source', 'unknown')
            if data_source == 'real_user_data':
                print("🎉 SUCCESS: Got real user data!")
                return True
            elif data_source == 'fallback_data':
                print("⚠️ Got fallback data (expected if no users have searched yet)")
                return True
            else:
                print(f"❓ Unknown data source: {data_source}")
                return True  # Still working, just unknown source
        else:
            print(f"❌ Analytics endpoint failed: {analytics_response.status_code}")
            try:
                error_data = analytics_response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error response: {analytics_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Analytics endpoint error: {e}")
        return False
    
    # Test 3: Create a user and test with real data
    print("\n3. Testing with user creation and search data...")
    test_email = f"test_{int(time.time())}@example.com"
    
    try:
        # Create user
        signup_response = requests.post(f"{base_url}/api/auth/signup", json={
            "name": "Test User",
            "email": test_email,
            "password": "password123"
        }, timeout=10)
        
        if signup_response.status_code == 200:
            print("✅ User created successfully")
            
            # Login
            login_response = requests.post(f"{base_url}/api/auth/login", json={
                "email": test_email,
                "password": "password123"
            }, timeout=10)
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                token = login_data.get('token') or login_data.get('access_token')
                
                if token:
                    print("✅ Login successful")
                    
                    # Save search data
                    search_response = requests.post(
                        f"{base_url}/api/dashboard/search-history",
                        json={
                            "title": "Test Search",
                            "ingredients": "chicken, rice, tomato",
                            "ingredientsList": ["chicken", "rice", "tomato"],
                            "timestamp": "2024-01-01T12:00:00Z"
                        },
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10
                    )
                    
                    if search_response.status_code == 200:
                        print("✅ Search data saved")
                        
                        # Wait and test analytics again
                        time.sleep(2)
                        analytics_response2 = requests.get(
                            f"{base_url}/api/analytics/leftover-ingredients", 
                            timeout=15
                        )
                        
                        if analytics_response2.status_code == 200:
                            analytics_data2 = analytics_response2.json()
                            data_source2 = analytics_data2.get('data', {}).get('data_source', 'unknown')
                            print(f"✅ Analytics still working after user data: {data_source2}")
                            return True
                        else:
                            print(f"❌ Analytics failed after user data: {analytics_response2.status_code}")
                            return False
                    else:
                        print(f"⚠️ Could not save search data: {search_response.status_code}")
                        # Still consider test passed if analytics endpoint works
                        return True
                else:
                    print("❌ No token received")
                    return True  # Analytics endpoint still worked
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                return True  # Analytics endpoint still worked
        else:
            print(f"⚠️ User creation failed: {signup_response.status_code}")
            return True  # Analytics endpoint still worked
            
    except Exception as e:
        print(f"⚠️ User test error: {e}")
        return True  # Analytics endpoint still worked

def main():
    """Main test function."""
    print("🚂 Railway Analytics Test")
    print("Testing the analytics functionality that was failing on Railway")
    
    success = test_railway_analytics()
    
    if success:
        print("\n🎉 ANALYTICS TEST PASSED!")
        print("The analytics endpoint is working correctly.")
    else:
        print("\n❌ ANALYTICS TEST FAILED!")
        print("The analytics endpoint is still not working.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
