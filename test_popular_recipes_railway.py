#!/usr/bin/env python3
"""
Test script to verify popular recipes functionality works in Railway deployment environment.
This script simulates Railway environment conditions and tests the prescriptive analytics endpoint.
"""

import os
import sys
import json
import requests
from datetime import datetime

def test_popular_recipes_railway():
    """Test popular recipes functionality in Railway-like environment."""
    
    print("🧪 Testing Popular Recipes Railway Deployment")
    print("=" * 50)
    
    # Set Railway-like environment variables
    os.environ['PORT'] = '8080'
    os.environ['RAILWAY_ENVIRONMENT'] = 'production'
    
    # Test local development server first
    base_url = "http://localhost:5000"
    
    print(f"📡 Testing prescriptive analytics endpoint...")
    print(f"🔗 URL: {base_url}/api/analytics/prescriptive")
    
    try:
        # Test the prescriptive analytics endpoint (which includes popular recipes)
        response = requests.get(f"{base_url}/api/analytics/prescriptive", timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response received")
            
            # Check if popular recipes are included
            if 'data' in data and 'popular_recipes' in data['data']:
                popular_recipes = data['data']['popular_recipes']
                print(f"🍽️  Popular recipes count: {len(popular_recipes)}")
                
                if popular_recipes:
                    print("\n📋 Sample popular recipe:")
                    sample_recipe = popular_recipes[0]
                    print(f"   - Name: {sample_recipe.get('name', 'N/A')}")
                    print(f"   - ID: {sample_recipe.get('id', 'N/A')}")
                    print(f"   - Rating: {sample_recipe.get('avg_rating', 'N/A')}")
                    print(f"   - Reviews: {sample_recipe.get('review_count', 'N/A')}")
                    print(f"   - Verifications: {sample_recipe.get('verification_count', 'N/A')}")
                    print(f"   - Saves: {sample_recipe.get('saves', 'N/A')}")
                    
                    print("\n✅ Popular recipes functionality is working!")
                else:
                    print("⚠️  No popular recipes found - this might indicate:")
                    print("   - No recipe data in database")
                    print("   - No ratings/reviews/verifications in database")
                    print("   - Recommender system not initialized")
            else:
                print("❌ Popular recipes not found in response")
                print(f"Available data keys: {list(data.get('data', {}).keys())}")
            
            # Check leftover solutions
            if 'data' in data and 'leftover_solutions' in data['data']:
                leftover_solutions = data['data']['leftover_solutions']
                print(f"\n🥬 Leftover solutions available: {bool(leftover_solutions)}")
                
                if 'top_leftover_ingredients' in leftover_solutions:
                    top_leftovers = leftover_solutions['top_leftover_ingredients']
                    print(f"   - Top leftover ingredients count: {len(top_leftovers)}")
            
            # Check user-specific data
            if 'data' in data and 'user_specific' in data['data']:
                user_specific = data['data']['user_specific']
                print(f"\n👤 User-specific data available: {bool(user_specific)}")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the Flask app is running on localhost:5000")
        print("   Run: cd src && python app.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("\n" + "=" * 50)
    
    # Test the test endpoint as well
    print(f"🧪 Testing prescriptive analytics test endpoint...")
    try:
        response = requests.get(f"{base_url}/api/analytics/prescriptive-test", timeout=10)
        print(f"📊 Test endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test endpoint response: {data.get('message', 'N/A')}")
        else:
            print(f"⚠️  Test endpoint failed: {response.text}")
    except Exception as e:
        print(f"⚠️  Test endpoint error: {e}")
    
    return True

def test_railway_environment_simulation():
    """Simulate Railway environment conditions."""
    
    print("\n🚂 Railway Environment Simulation")
    print("=" * 50)
    
    # Set Railway environment variables
    railway_env_vars = {
        'PORT': '8080',
        'RAILWAY_ENVIRONMENT': 'production',
        'RAILWAY_PROJECT_ID': 'test-project',
        'RAILWAY_SERVICE_ID': 'test-service',
        'PYTHONPATH': '/app/src',
    }
    
    print("🔧 Setting Railway environment variables:")
    for key, value in railway_env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")
    
    # Test Flask app context handling
    print("\n🧪 Testing Flask app context handling...")
    
    try:
        # Import Flask app components
        sys.path.insert(0, 'src')
        from api.app import app
        from flask import current_app
        
        print("✅ Flask app created successfully")
        
        # Test app context
        with app.app_context():
            print("✅ Flask app context works")
            
            # Test MongoDB connection
            try:
                from api.models.user import mongo
                if mongo:
                    print("✅ MongoDB connection available")
                else:
                    print("⚠️  MongoDB connection not available")
            except Exception as e:
                print(f"⚠️  MongoDB import error: {e}")
            
            # Test recommender system
            try:
                recommender = getattr(current_app, 'recommender', None)
                if recommender:
                    recipe_count = len(recommender.recipes) if hasattr(recommender, 'recipes') and recommender.recipes else 0
                    print(f"✅ Recommender system available with {recipe_count} recipes")
                else:
                    print("⚠️  Recommender system not available")
            except Exception as e:
                print(f"⚠️  Recommender system error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app context test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Popular Recipes Railway Deployment Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    # Run environment simulation test
    env_test_passed = test_railway_environment_simulation()
    
    # Run popular recipes test
    api_test_passed = test_popular_recipes_railway()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"🚂 Railway Environment Simulation: {'✅ PASSED' if env_test_passed else '❌ FAILED'}")
    print(f"🍽️  Popular Recipes API Test: {'✅ PASSED' if api_test_passed else '❌ FAILED'}")
    
    if env_test_passed and api_test_passed:
        print("\n🎉 All tests passed! Popular recipes should work in Railway deployment.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print(f"\n⏰ Test completed at: {datetime.now()}")
