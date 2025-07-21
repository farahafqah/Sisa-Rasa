#!/usr/bin/env python3
"""
Comprehensive deployment verification script
Tests all critical functionality after deployment
"""

import requests
import time
import json
import sys

def test_system_status(base_url):
    """Test system status and initialization."""
    print("🔍 Testing System Status...")
    
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ System status endpoint accessible")
            print(f"   System initialized: {data.get('system_initialized', False)}")
            print(f"   Authentication available: {data.get('features', {}).get('user_authentication', False)}")
            print(f"   Database available: {data.get('features', {}).get('database', False)}")
            return data
        else:
            print(f"❌ System status failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ System status error: {e}")
        return None

def test_auth_endpoints(base_url):
    """Test authentication endpoints availability."""
    print("\n🔐 Testing Authentication Endpoints...")
    
    auth_endpoints = [
        '/api/auth/signup',
        '/api/auth/login'
    ]
    
    available_endpoints = []
    
    for endpoint in auth_endpoints:
        try:
            # Send invalid data to test if endpoint exists
            response = requests.post(f"{base_url}{endpoint}", 
                                   json={'test': 'data'}, 
                                   timeout=10)
            
            if response.status_code == 404:
                print(f"❌ {endpoint} - NOT FOUND (blueprint not registered)")
            elif response.status_code in [400, 401, 422]:
                print(f"✅ {endpoint} - AVAILABLE (expected error for invalid data)")
                available_endpoints.append(endpoint)
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                available_endpoints.append(endpoint)
                
        except Exception as e:
            print(f"❌ {endpoint} - Connection error: {e}")
    
    return available_endpoints

def test_user_registration(base_url):
    """Test complete user registration process."""
    print("\n📝 Testing User Registration...")
    
    # Create unique test user
    timestamp = int(time.time())
    test_user = {
        'name': f'Test User {timestamp}',
        'email': f'test{timestamp}@example.com',
        'password': 'testpass123'
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/signup", 
                               json=test_user, 
                               timeout=15)
        
        print(f"Registration response status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ User registration SUCCESSFUL")
            print(f"   User ID: {data.get('user', {}).get('id', 'N/A')}")
            print(f"   User name: {data.get('user', {}).get('name', 'N/A')}")
            return test_user, True
        else:
            print(f"❌ User registration FAILED: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}...")
            return test_user, False
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return test_user, False

def test_user_login(base_url, test_user):
    """Test user login process."""
    print("\n🔑 Testing User Login...")
    
    try:
        login_data = {
            'email': test_user['email'],
            'password': test_user['password']
        }
        
        response = requests.post(f"{base_url}/api/auth/login", 
                               json=login_data, 
                               timeout=15)
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User login SUCCESSFUL")
            
            if 'token' in data:
                print("✅ JWT token received")
                print(f"   Token length: {len(data['token'])} characters")
                return data['token'], True
            else:
                print("❌ No JWT token in response")
                return None, False
        else:
            print(f"❌ User login FAILED: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}...")
            return None, False
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return None, False

def test_web_pages(base_url):
    """Test web page accessibility."""
    print("\n🌐 Testing Web Pages...")
    
    pages = [
        ('/', 'Home page'),
        ('/welcome', 'Welcome page'),
        ('/login', 'Login page'),
        ('/signup', 'Signup page'),
        ('/dashboard', 'Dashboard')
    ]
    
    accessible_pages = []
    
    for path, name in pages:
        try:
            response = requests.get(f"{base_url}{path}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {path} - {name} accessible")
                
                # Check for key content
                if 'Sisa Rasa' in response.text or 'SisaRasa' in response.text:
                    print(f"   ✅ Contains branding")
                else:
                    print(f"   ⚠️  Missing branding")
                
                accessible_pages.append(path)
            else:
                print(f"❌ {path} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {path} - Error: {e}")
    
    return accessible_pages

def test_form_submissions(base_url):
    """Test form submissions on web pages."""
    print("\n📋 Testing Form Submissions...")
    
    # Test signup form
    try:
        timestamp = int(time.time())
        form_data = {
            'name': f'Form Test User {timestamp}',
            'email': f'formtest{timestamp}@example.com',
            'password': 'formtest123'
        }
        
        response = requests.post(f"{base_url}/signup", 
                               data=form_data,
                               allow_redirects=False,
                               timeout=15)
        
        print(f"Signup form response: {response.status_code}")
        
        if response.status_code in [200, 302]:  # 302 = redirect after success
            print("✅ Signup form submission works")
            
            # Test login form with same user
            login_response = requests.post(f"{base_url}/login",
                                         data={
                                             'email': form_data['email'],
                                             'password': form_data['password']
                                         },
                                         allow_redirects=False,
                                         timeout=15)
            
            print(f"Login form response: {login_response.status_code}")
            
            if login_response.status_code in [200, 302]:
                print("✅ Login form submission works")
                return True
            else:
                print("❌ Login form submission failed")
                return False
        else:
            print("❌ Signup form submission failed")
            return False
            
    except Exception as e:
        print(f"❌ Form submission test failed: {e}")
        return False

def main():
    """Main verification function."""
    if len(sys.argv) != 2:
        print("Usage: python verify_deployment.py <your-railway-app-url>")
        print("Example: python verify_deployment.py https://sisa-rasa-production.up.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🚨 COMPREHENSIVE DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print(f"Testing deployment at: {base_url}")
    print("=" * 70)
    
    # Run all tests
    results = {}
    
    # Test 1: System Status
    system_status = test_system_status(base_url)
    results['system_status'] = system_status is not None
    
    # Test 2: Auth Endpoints
    auth_endpoints = test_auth_endpoints(base_url)
    results['auth_endpoints'] = len(auth_endpoints) >= 2
    
    # Test 3: Web Pages
    web_pages = test_web_pages(base_url)
    results['web_pages'] = len(web_pages) >= 4
    
    # Test 4: User Registration (only if auth endpoints work)
    if results['auth_endpoints']:
        test_user, reg_success = test_user_registration(base_url)
        results['registration'] = reg_success
        
        # Test 5: User Login (only if registration works)
        if reg_success:
            token, login_success = test_user_login(base_url, test_user)
            results['login'] = login_success
        else:
            results['login'] = False
    else:
        results['registration'] = False
        results['login'] = False
    
    # Test 6: Form Submissions
    form_success = test_form_submissions(base_url)
    results['forms'] = form_success
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 VERIFICATION RESULTS SUMMARY")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your SisaRasa deployment is fully functional")
        print("✅ Users can register, login, and access all features")
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠️  MOSTLY WORKING")
        print("✅ Core functionality works")
        print("⚠️  Some minor issues detected")
    else:
        print("\n🚨 CRITICAL ISSUES DETECTED")
        print("❌ Major functionality is broken")
        print("❌ Users cannot use the application properly")
    
    print("\n" + "=" * 70)
    print("Next steps:")
    if results['auth_endpoints'] and results['registration'] and results['login']:
        print("✅ Authentication system is working correctly")
    else:
        print("❌ Fix authentication system issues")
        print("   - Check Railway logs for blueprint registration errors")
        print("   - Verify MongoDB connection")
        print("   - Ensure environment variables are set")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
