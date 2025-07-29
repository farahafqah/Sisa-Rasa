#!/usr/bin/env python3
"""
Test script to verify Railway deployment readiness.
This script simulates the Railway environment and tests key components.
"""

import os
import sys
import json

def test_railway_deployment():
    """Test if the app is ready for Railway deployment."""
    
    print("🚂 Railway Deployment Readiness Test")
    print("=" * 50)
    
    # Test 1: Check required files exist
    print("\n1. Checking required files...")
    required_files = [
        'Procfile',
        'requirements.txt',
        'src/api/app.py',
        'src/run_api.py',
        'data/clean_recipes.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing required files: {missing_files}")
        return False
    
    # Test 2: Check Procfile content
    print("\n2. Checking Procfile...")
    with open('Procfile', 'r') as f:
        procfile_content = f.read().strip()
    
    expected_procfile = "web: cd src && gunicorn api.app:app --host 0.0.0.0 --port $PORT"
    if procfile_content == expected_procfile:
        print(f"✅ Procfile correct: {procfile_content}")
    else:
        print(f"❌ Procfile incorrect:")
        print(f"  Expected: {expected_procfile}")
        print(f"  Found: {procfile_content}")
        return False
    
    # Test 3: Check data file
    print("\n3. Checking data file...")
    try:
        with open('data/clean_recipes.json', 'r', encoding='utf-8') as f:
            recipes_data = json.load(f)
        
        if isinstance(recipes_data, list) and len(recipes_data) > 0:
            print(f"✅ Recipes data loaded: {len(recipes_data)} recipes")
        else:
            print(f"❌ Invalid recipes data format")
            return False
    except Exception as e:
        print(f"❌ Error loading recipes data: {e}")
        return False
    
    # Test 4: Test app import (simulate Railway environment)
    print("\n4. Testing app import with Railway environment...")
    
    # Set Railway environment variables
    os.environ['PORT'] = '8080'
    os.environ['RAILWAY_ENVIRONMENT'] = 'production'
    os.environ['MAX_RECIPES'] = '1000'  # Smaller for faster startup
    os.environ['NUM_RECIPES'] = '5'
    
    # Add src to path
    sys.path.insert(0, 'src')
    
    try:
        # Import the app (this will trigger initialization)
        from api.app import app, recommender
        
        print("✅ App imported successfully")
        
        # Check if recommender was initialized
        if recommender:
            print("✅ Recommender initialized")
        else:
            print("⚠️ Recommender not initialized (may be expected)")
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/api/health')
            if response.status_code == 200:
                health_data = response.get_json()
                print(f"✅ Health endpoint working: {health_data['status']}")
                
                # Check components
                if '✅' in health_data.get('app', ''):
                    print("✅ App component healthy")
                else:
                    print("⚠️ App component issue")
                
                if '✅' in health_data.get('database', ''):
                    print("✅ Database component healthy")
                else:
                    print("⚠️ Database component issue (expected without MONGO_URI)")
                
                if '✅' in health_data.get('recommender', ''):
                    print("✅ Recommender component healthy")
                else:
                    print("⚠️ Recommender component issue")
                    
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
        
        # Test root endpoint
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Root endpoint working")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ App import failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False
    
    # Test 5: Check requirements
    print("\n5. Checking requirements.txt...")
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        required_packages = [
            'flask', 'gunicorn', 'pymongo', 'flask-pymongo', 
            'flask-cors', 'flask-jwt-extended', 'numpy', 
            'pandas', 'scikit-learn'
        ]
        
        missing_packages = []
        for package in required_packages:
            found = any(package in req.lower() for req in requirements if req.strip())
            if found:
                print(f"✅ {package}")
            else:
                print(f"❌ {package}")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n❌ Missing required packages: {missing_packages}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False
    
    print("\n🎉 Railway deployment readiness test PASSED!")
    print("\nNext steps:")
    print("1. Set MONGO_URI environment variable in Railway")
    print("2. Deploy to Railway")
    print("3. Check Railway logs for any startup issues")
    print("4. Test the /api/health endpoint after deployment")
    
    return True

def main():
    """Main test function."""
    success = test_railway_deployment()
    
    if success:
        print("\n✅ Ready for Railway deployment!")
    else:
        print("\n❌ Not ready for Railway deployment!")
        print("Please fix the issues above before deploying.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
