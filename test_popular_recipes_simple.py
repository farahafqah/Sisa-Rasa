#!/usr/bin/env python3
"""
Simple test script to verify popular recipes functionality works.
This script tests the prescriptive analytics endpoint directly.
"""

import requests
import json
from datetime import datetime

def test_popular_recipes_endpoint():
    """Test popular recipes functionality via API endpoint."""
    
    print("🧪 Testing Popular Recipes Endpoint")
    print("=" * 50)
    
    # Test local development server
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
            
            # Pretty print the response structure
            print(f"\n📋 Response structure:")
            if 'status' in data:
                print(f"   Status: {data['status']}")
            
            if 'data' in data:
                data_keys = list(data['data'].keys())
                print(f"   Data keys: {data_keys}")
                
                # Check popular recipes specifically
                if 'popular_recipes' in data['data']:
                    popular_recipes = data['data']['popular_recipes']
                    print(f"\n🍽️  Popular recipes count: {len(popular_recipes)}")
                    
                    if popular_recipes:
                        print("\n📋 Sample popular recipe:")
                        sample_recipe = popular_recipes[0]
                        for key, value in sample_recipe.items():
                            if key == 'ingredients' and isinstance(value, list):
                                print(f"   - {key}: {value[:3]}..." if len(value) > 3 else f"   - {key}: {value}")
                            else:
                                print(f"   - {key}: {value}")
                        
                        print("\n✅ Popular recipes functionality is working!")
                        
                        # Check if we have real data vs fallback data
                        has_real_ratings = any(recipe.get('avg_rating', 0) > 0 for recipe in popular_recipes)
                        has_real_reviews = any(recipe.get('review_count', 0) > 0 for recipe in popular_recipes)
                        has_real_verifications = any(recipe.get('verification_count', 0) > 0 for recipe in popular_recipes)
                        
                        print(f"\n📊 Data quality check:")
                        print(f"   - Has real ratings: {'✅' if has_real_ratings else '❌'}")
                        print(f"   - Has real reviews: {'✅' if has_real_reviews else '❌'}")
                        print(f"   - Has real verifications: {'✅' if has_real_verifications else '❌'}")
                        
                        if has_real_ratings or has_real_reviews or has_real_verifications:
                            print("   🎉 Using real database data!")
                        else:
                            print("   ⚠️  Using fallback/default data")
                    else:
                        print("⚠️  No popular recipes found - this might indicate:")
                        print("   - No recipe data in database")
                        print("   - No ratings/reviews/verifications in database")
                        print("   - Recommender system not initialized")
                else:
                    print("❌ Popular recipes not found in response")
                    print(f"Available data keys: {data_keys}")
                
                # Check other data sections
                if 'leftover_solutions' in data['data']:
                    leftover_solutions = data['data']['leftover_solutions']
                    print(f"\n🥬 Leftover solutions available: {bool(leftover_solutions)}")
                    
                    if 'top_leftover_ingredients' in leftover_solutions:
                        top_leftovers = leftover_solutions['top_leftover_ingredients']
                        print(f"   - Top leftover ingredients count: {len(top_leftovers)}")
                        if top_leftovers:
                            print(f"   - Sample: {top_leftovers[0]}")
                
                if 'user_specific' in data['data']:
                    user_specific = data['data']['user_specific']
                    print(f"\n👤 User-specific data available: {bool(user_specific)}")
                    if user_specific:
                        print(f"   - Keys: {list(user_specific.keys())}")
            
            return True
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the Flask app is running on localhost:5000")
        print("   To start the app:")
        print("   1. Open a new terminal")
        print("   2. cd src")
        print("   3. python app.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_prescriptive_test_endpoint():
    """Test the prescriptive analytics test endpoint."""
    
    print(f"\n🧪 Testing prescriptive analytics test endpoint...")
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/api/analytics/prescriptive-test", timeout=10)
        print(f"📊 Test endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test endpoint response:")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Debug: {data.get('debug', 'N/A')}")
            return True
        else:
            print(f"⚠️  Test endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"⚠️  Test endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Popular Recipes Simple Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    # Run popular recipes test
    main_test_passed = test_popular_recipes_endpoint()
    
    # Run test endpoint
    test_endpoint_passed = test_prescriptive_test_endpoint()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"🍽️  Popular Recipes API Test: {'✅ PASSED' if main_test_passed else '❌ FAILED'}")
    print(f"🧪 Test Endpoint: {'✅ PASSED' if test_endpoint_passed else '❌ FAILED'}")
    
    if main_test_passed:
        print("\n🎉 Popular recipes endpoint is working!")
        print("   This means the Railway deployment fixes should work.")
    else:
        print("\n⚠️  Popular recipes endpoint failed.")
        print("   Make sure the Flask app is running locally first.")
    
    print(f"\n⏰ Test completed at: {datetime.now()}")
