#!/usr/bin/env python3
"""
Test script for SisaRasa web application
"""

import os
import sys
import requests
import time

def test_local_app():
    """Test the local application."""
    print("🧪 Testing SisaRasa Web Application")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test basic endpoints
    endpoints = [
        ("/", "Home page"),
        ("/welcome", "Welcome page"),
        ("/login", "Login page"),
        ("/signup", "Signup page"),
        ("/dashboard", "Dashboard"),
        ("/health", "Health check"),
        ("/api/status", "API status"),
        ("/api/health", "API health")
    ]
    
    print("Testing endpoints...")
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            print(f"{status} {endpoint} - {description}")
        except requests.exceptions.RequestException as e:
            print(f"❌ FAIL {endpoint} - Connection error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Local testing complete!")

def test_deployed_app(app_url):
    """Test the deployed application."""
    print(f"🌐 Testing Deployed SisaRasa at {app_url}")
    print("=" * 60)

    # Test basic endpoints
    endpoints = [
        ("/", "Home page"),
        ("/welcome", "Welcome page"),
        ("/login", "Login page"),
        ("/signup", "Signup page"),
        ("/dashboard", "Dashboard"),
        ("/health", "Health check"),
        ("/api/status", "API status"),
        ("/api/health", "API health")
    ]

    print("Testing web pages...")
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{app_url}{endpoint}", timeout=10)
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            print(f"{status} {endpoint} - {description}")

            # Check if it's an HTML response
            if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
                if 'SisaRasa' in response.text:
                    print(f"    ✅ Contains SisaRasa branding")
                else:
                    print(f"    ⚠️  Missing SisaRasa branding")

        except requests.exceptions.RequestException as e:
            print(f"❌ FAIL {endpoint} - Connection error: {e}")

    # Test authentication system
    print("\n🔐 Testing Authentication System...")

    # Test signup API
    try:
        test_user = {
            "name": "Test User",
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpass123"
        }

        response = requests.post(f"{app_url}/api/auth/signup", json=test_user, timeout=10)
        if response.status_code == 201:
            print("✅ PASS /api/auth/signup - User registration works")

            # Test login with the created user
            login_data = {"email": test_user["email"], "password": test_user["password"]}
            login_response = requests.post(f"{app_url}/api/auth/login", json=login_data, timeout=10)

            if login_response.status_code == 200:
                login_result = login_response.json()
                if 'token' in login_result:
                    print("✅ PASS /api/auth/login - User login works and returns JWT token")
                else:
                    print("❌ FAIL /api/auth/login - No JWT token returned")
            else:
                print(f"❌ FAIL /api/auth/login - Status: {login_response.status_code}")

        else:
            print(f"❌ FAIL /api/auth/signup - Status: {response.status_code}")
            if response.status_code == 400:
                error_data = response.json()
                print(f"    Error: {error_data.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"❌ FAIL Authentication test - Error: {e}")

    # Test API endpoints
    print("\n🍳 Testing Recipe API functionality...")

    # Test recipe recommendation
    try:
        response = requests.post(f"{app_url}/api/recommend",
                               json={"ingredients": ["chicken", "rice"]},
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS /api/recommend - Got {data.get('count', 0)} recipes")
        else:
            print(f"❌ FAIL /api/recommend - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL /api/recommend - Error: {e}")

    # Test ingredients API
    try:
        response = requests.get(f"{app_url}/api/ingredients?search=chicken", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS /api/ingredients - Got {data.get('count', 0)} ingredients")
        else:
            print(f"❌ FAIL /api/ingredients - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL /api/ingredients - Error: {e}")

    # Test community recipes
    try:
        response = requests.get(f"{app_url}/api/community/recipes", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS /api/community/recipes - Got {data.get('count', 0)} recipes")
        else:
            print(f"❌ FAIL /api/community/recipes - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL /api/community/recipes - Error: {e}")

    # Test system initialization
    print("\n🚀 Testing System Initialization...")
    try:
        response = requests.post(f"{app_url}/api/initialize", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS /api/initialize - {data.get('message', 'System initialized')}")
        else:
            print(f"❌ FAIL /api/initialize - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL /api/initialize - Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Comprehensive testing complete!")
    print("\n📋 Summary:")
    print("- If authentication tests pass: Users can register and login")
    print("- If recipe API tests pass: Recipe recommendations work")
    print("- If web pages load: Users can access the interface")
    print("- If initialization passes: Full ML system is available")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test deployed app
        app_url = sys.argv[1].rstrip('/')
        test_deployed_app(app_url)
    else:
        # Test local app
        test_local_app()
