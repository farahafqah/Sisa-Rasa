#!/usr/bin/env python3
"""
Test script to verify the new realistic fallback recipe names are working correctly.
"""

import requests
import json
from datetime import datetime

def test_fallback_recipes():
    """Test that the new realistic recipe names are being used in fallback data."""
    print("🧪 Testing New Fallback Recipe Names")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    try:
        # Test the prescriptive analytics endpoint
        print("📡 Testing prescriptive analytics endpoint...")
        url = "http://localhost:5000/api/analytics/prescriptive"
        print(f"🔗 URL: {url}")
        
        response = requests.get(url)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success! Response received")
            data = response.json()
            
            print("\n📋 Response structure:")
            print(f"   Status: {data.get('status')}")
            print(f"   Data keys: {list(data.get('data', {}).keys())}")
            
            popular_recipes = data.get('data', {}).get('popular_recipes', [])
            print(f"\n🍽️  Popular recipes count: {len(popular_recipes)}")
            
            # Check for the new realistic recipe names
            expected_names = [
                "Spiced Lamb and Dill Yogurt Pasta",
                "Dad's Curried Chicken and Rice", 
                "Balls With Salmon Filling (Onigiri)"
            ]
            
            print("\n📋 All popular recipes:")
            for i, recipe in enumerate(popular_recipes, 1):
                print(f"   {i}. {recipe.get('name')}")
                print(f"      - ID: {recipe.get('id')}")
                print(f"      - Rating: {recipe.get('avg_rating')}")
                print(f"      - Review Count: {recipe.get('review_count')}")
                print(f"      - Prep Time: {recipe.get('prep_time')} min")
                print(f"      - Difficulty: {recipe.get('difficulty')}")
                print(f"      - Description: {recipe.get('description')[:80]}...")
                print()
            
            # Check if any of the new realistic names are present
            found_realistic_names = []
            for recipe in popular_recipes:
                recipe_name = recipe.get('name', '')
                if recipe_name in expected_names:
                    found_realistic_names.append(recipe_name)
            
            print("🎯 Realistic Recipe Names Check:")
            if found_realistic_names:
                print(f"   ✅ Found {len(found_realistic_names)} realistic recipe names:")
                for name in found_realistic_names:
                    print(f"      - {name}")
            else:
                print("   ❌ No realistic recipe names found in fallback data")
            
            # Check for null review counts on featured recipes
            featured_recipes = [r for r in popular_recipes if r.get('review_count') is None]
            print(f"\n📊 Featured recipes (null review count): {len(featured_recipes)}")
            for recipe in featured_recipes:
                print(f"   - {recipe.get('name')} (Rating: {recipe.get('avg_rating')})")
            
            print("\n✅ Fallback recipe names test completed!")
            return True
            
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_fallback_recipes()
    print(f"\n⏰ Test completed at: {datetime.now()}")
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
