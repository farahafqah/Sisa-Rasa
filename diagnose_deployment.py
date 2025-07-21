#!/usr/bin/env python3
"""
Comprehensive diagnostic script for SisaRasa deployment issues
Tests all critical functionality and provides detailed error reporting
"""

import requests
import time
import json
import sys

def test_home_page(base_url):
    """Test home page functionality."""
    print("🏠 Testing Home Page...")
    
    endpoints_to_test = [
        ('/', 'Root home page'),
        ('/home', 'Alternative home route')
    ]
    
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - {description} loads successfully")
                
                # Check content
                if 'Sisa Rasa' in response.text:
                    print(f"   ✅ Contains Sisa Rasa branding")
                else:
                    print(f"   ⚠️  Missing Sisa Rasa branding")
                
                if 'Login' in response.text and 'Sign Up' in response.text:
                    print(f"   ✅ Contains navigation links")
                else:
                    print(f"   ⚠️  Missing navigation links")
                    
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def test_authentication_system(base_url):
    """Test authentication system comprehensively."""
    print("\n🔐 Testing Authentication System...")
    
    # Test signup page
    try:
        response = requests.get(f"{base_url}/signup", timeout=10)
        if response.status_code == 200:
            print("✅ Signup page loads")
        else:
            print(f"❌ Signup page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Signup page error: {e}")
    
    # Test login page
    try:
        response = requests.get(f"{base_url}/login", timeout=10)
        if response.status_code == 200:
            print("✅ Login page loads")
        else:
            print(f"❌ Login page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Login page error: {e}")
    
    # Test auth API endpoints
    auth_endpoints = [
        '/api/auth/signup',
        '/api/auth/login'
    ]
    
    for endpoint in auth_endpoints:
        try:
            # Test with invalid data to see if endpoint exists
            response = requests.post(f"{base_url}{endpoint}", 
                                   json={'test': 'data'}, 
                                   timeout=10)
            
            if response.status_code in [400, 401, 422]:  # Expected error codes
                print(f"✅ {endpoint} - API endpoint is accessible")
            elif response.status_code == 404:
                print(f"❌ {endpoint} - API endpoint not found (blueprint not registered)")
            else:
                print(f"⚠️  {endpoint} - Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Connection error: {e}")

def test_user_registration(base_url):
    """Test actual user registration process."""
    print("\n📝 Testing User Registration Process...")
    
    # Create test user data
    test_user = {
        'name': 'Test User',
        'email': f'test_{int(time.time())}@example.com',
        'password': 'testpass123'
    }
    
    try:
        # Test API registration
        response = requests.post(f"{base_url}/api/auth/signup", 
                               json=test_user, 
                               timeout=15)
        
        if response.status_code == 201:
            print("✅ API registration successful")
            
            # Test login with created user
            login_response = requests.post(f"{base_url}/api/auth/login",
                                         json={
                                             'email': test_user['email'],
                                             'password': test_user['password']
                                         },
                                         timeout=15)
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                if 'token' in login_data:
                    print("✅ API login successful - JWT token received")
                else:
                    print("❌ API login failed - No JWT token")
            else:
                print(f"❌ API login failed: {login_response.status_code}")
                try:
                    error_data = login_response.json()
                    print(f"   Error: {error_data.get('message', 'Unknown error')}")
                except:
                    pass
                    
        else:
            print(f"❌ API registration failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}...")
                
    except Exception as e:
        print(f"❌ Registration test failed: {e}")

def test_database_connection(base_url):
    """Test database connectivity through API."""
    print("\n🗄️  Testing Database Connection...")
    
    try:
        # Check system status
        response = requests.get(f"{base_url}/api/status", timeout=10)
        
        if response.status_code == 200:
            status_data = response.json()
            
            db_status = status_data.get('features', {}).get('database', False)
            if db_status:
                print("✅ Database connection reported as working")
            else:
                print("❌ Database connection reported as failed")
            
            print(f"   System initialized: {status_data.get('system_initialized', False)}")
            print(f"   Authentication available: {status_data.get('features', {}).get('user_authentication', False)}")
            
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")

def test_system_health(base_url):
    """Test overall system health."""
    print("\n🏥 Testing System Health...")
    
    health_endpoints = [
        ('/health', 'Basic health check'),
        ('/api/health', 'Detailed health check'),
        ('/api/status', 'System status')
    ]
    
    for endpoint, description in health_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - {description}")
                
                try:
                    data = response.json()
                    if 'status' in data:
                        print(f"   Status: {data['status']}")
                    if 'system_initialized' in data:
                        print(f"   System initialized: {data['system_initialized']}")
                except:
                    pass
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def main():
    """Main diagnostic function."""
    if len(sys.argv) != 2:
        print("Usage: python diagnose_deployment.py <your-railway-app-url>")
        print("Example: python diagnose_deployment.py https://sisa-rasa-production.up.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🔍 SisaRasa Deployment Diagnostic Tool")
    print("=" * 60)
    print(f"Testing deployment at: {base_url}")
    print("=" * 60)
    
    # Run all tests
    test_system_health(base_url)
    test_home_page(base_url)
    test_authentication_system(base_url)
    test_database_connection(base_url)
    test_user_registration(base_url)
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print("If you see ✅ for most tests, your deployment is working correctly.")
    print("If you see ❌ for authentication tests, check Railway logs for MongoDB connection issues.")
    print("If you see ❌ for home page tests, check template loading and static file serving.")
    print("\nNext steps:")
    print("1. Fix any ❌ issues shown above")
    print("2. Check Railway deployment logs for detailed error messages")
    print("3. Verify environment variables (MONGO_URI, JWT_SECRET_KEY)")
    print("4. Test the application manually in your browser")

if __name__ == "__main__":
    main()
