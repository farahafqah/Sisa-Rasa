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
    
    print("Testing endpoints...")
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{app_url}{endpoint}", timeout=10)
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            print(f"{status} {endpoint} - {description}")
        except requests.exceptions.RequestException as e:
            print(f"❌ FAIL {endpoint} - Connection error: {e}")
    
    # Test API endpoints
    print("\nTesting API functionality...")
    
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
    
    print("\n" + "=" * 60)
    print("✅ Deployed app testing complete!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test deployed app
        app_url = sys.argv[1].rstrip('/')
        test_deployed_app(app_url)
    else:
        # Test local app
        test_local_app()
