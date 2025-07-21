#!/usr/bin/env python3
"""
Critical authentication fix testing script
Tests the authentication system locally before deployment
"""

import os
import sys
import importlib.util

def test_auth_import():
    """Test if authentication blueprint can be imported."""
    print("🔧 Testing Authentication Blueprint Import...")
    
    # Get the current directory (should be project root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, 'src')
    api_dir = os.path.join(src_dir, 'api')
    
    print(f"Current dir: {current_dir}")
    print(f"Src dir: {src_dir}")
    print(f"API dir: {api_dir}")
    print(f"API dir exists: {os.path.exists(api_dir)}")
    print(f"Auth file exists: {os.path.exists(os.path.join(api_dir, 'auth.py'))}")
    
    # Test import methods
    success = False
    
    # Method 1: Add api to path and import
    try:
        sys.path.insert(0, api_dir)
        from auth import auth_bp
        print("✅ Method 1 SUCCESS: Imported from auth")
        print(f"   Blueprint name: {auth_bp.name}")
        print(f"   Blueprint URL prefix: {auth_bp.url_prefix}")
        success = True
    except Exception as e:
        print(f"❌ Method 1 FAILED: {e}")
    
    # Method 2: Import with api prefix
    if not success:
        try:
            sys.path.insert(0, src_dir)
            from api.auth import auth_bp
            print("✅ Method 2 SUCCESS: Imported from api.auth")
            print(f"   Blueprint name: {auth_bp.name}")
            print(f"   Blueprint URL prefix: {auth_bp.url_prefix}")
            success = True
        except Exception as e:
            print(f"❌ Method 2 FAILED: {e}")
    
    # Method 3: Manual module loading
    if not success:
        try:
            auth_file_path = os.path.join(api_dir, 'auth.py')
            spec = importlib.util.spec_from_file_location("auth", auth_file_path)
            auth_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(auth_module)
            auth_bp = auth_module.auth_bp
            print("✅ Method 3 SUCCESS: Manual module loading")
            print(f"   Blueprint name: {auth_bp.name}")
            print(f"   Blueprint URL prefix: {auth_bp.url_prefix}")
            success = True
        except Exception as e:
            print(f"❌ Method 3 FAILED: {e}")
    
    return success

def test_mongodb_config():
    """Test MongoDB configuration."""
    print("\n🔧 Testing MongoDB Configuration...")
    
    # Check environment variable
    mongo_uri = os.getenv('MONGO_URI')
    if mongo_uri:
        print("✅ MONGO_URI environment variable is set")
        # Mask the URI for security
        if '@' in mongo_uri:
            masked = mongo_uri.split('@')[0].split('//')[1]
            masked_uri = mongo_uri.replace(masked, '***:***')
            print(f"   URI: {masked_uri}")
        else:
            print(f"   URI: {mongo_uri}")
    else:
        print("❌ MONGO_URI environment variable is NOT set")
        return False
    
    # Test config import
    try:
        src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
        api_dir = os.path.join(src_dir, 'api')
        sys.path.insert(0, api_dir)
        
        from config import MONGO_URI as CONFIG_MONGO_URI
        print("✅ Successfully imported MONGO_URI from config.py")
        return True
    except Exception as e:
        print(f"❌ Failed to import from config.py: {e}")
        return False

def test_user_model_import():
    """Test user model import."""
    print("\n🔧 Testing User Model Import...")
    
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    api_dir = os.path.join(src_dir, 'api')
    models_dir = os.path.join(api_dir, 'models')
    
    print(f"Models dir: {models_dir}")
    print(f"Models dir exists: {os.path.exists(models_dir)}")
    print(f"User model exists: {os.path.exists(os.path.join(models_dir, 'user.py'))}")
    
    success = False
    
    # Method 1: Direct import
    try:
        sys.path.insert(0, models_dir)
        from user import init_db, mongo, create_user, get_user_by_email
        print("✅ Method 1 SUCCESS: Imported from user module")
        success = True
    except Exception as e:
        print(f"❌ Method 1 FAILED: {e}")
    
    # Method 2: Import with path
    if not success:
        try:
            sys.path.insert(0, api_dir)
            from models.user import init_db, mongo, create_user, get_user_by_email
            print("✅ Method 2 SUCCESS: Imported from models.user")
            success = True
        except Exception as e:
            print(f"❌ Method 2 FAILED: {e}")
    
    return success

def test_flask_app_creation():
    """Test Flask app creation and blueprint registration."""
    print("\n🔧 Testing Flask App Creation...")
    
    try:
        from flask import Flask
        
        # Create test app
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Test blueprint registration
        src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
        api_dir = os.path.join(src_dir, 'api')
        sys.path.insert(0, api_dir)
        
        from auth import auth_bp
        app.register_blueprint(auth_bp)
        
        # Check registered routes
        with app.app_context():
            auth_routes = [rule.rule for rule in app.url_map.iter_rules() if rule.rule.startswith('/api/auth')]
            print(f"✅ Flask app created and blueprint registered")
            print(f"   Registered auth routes: {auth_routes}")
            
            if len(auth_routes) > 0:
                print("✅ Authentication routes are available")
                return True
            else:
                print("❌ No authentication routes found")
                return False
                
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚨 CRITICAL AUTHENTICATION FIX TESTING")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Auth Import", test_auth_import()))
    results.append(("MongoDB Config", test_mongodb_config()))
    results.append(("User Model Import", test_user_model_import()))
    results.append(("Flask App Creation", test_flask_app_creation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Ready for deployment!")
        print("The authentication system should work correctly.")
    else:
        print("🚨 SOME TESTS FAILED - DO NOT DEPLOY YET!")
        print("Fix the failing tests before deploying to Railway.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
