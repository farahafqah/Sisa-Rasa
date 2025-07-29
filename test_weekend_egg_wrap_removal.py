#!/usr/bin/env python3
"""
Test script to verify that "Weekend Egg Wrap" has been removed 
and "highly rated" text has been eliminated from popular recipes.
"""

import requests
import json
from datetime import datetime

def test_weekend_egg_wrap_removal():
    """Test that Weekend Egg Wrap is excluded and highly rated text is removed."""
    print("🧪 Testing Weekend Egg Wrap Removal & Highly Rated Text Elimination")
    print("=" * 70)
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
            
            popular_recipes = data.get('data', {}).get('popular_recipes', [])
            print(f"\n🍽️  Popular recipes count: {len(popular_recipes)}")
            
            # Check for Weekend Egg Wrap
            weekend_egg_wrap_found = False
            highly_rated_text_found = False
            
            print("\n📋 All popular recipes:")
            for i, recipe in enumerate(popular_recipes, 1):
                recipe_name = recipe.get('name', '')
                description = recipe.get('description', '')
                
                print(f"   {i}. {recipe_name}")
                print(f"      - Description: {description}")
                print(f"      - Rating: {recipe.get('avg_rating')}")
                print(f"      - Review Count: {recipe.get('review_count')}")
                print()
                
                # Check for Weekend Egg Wrap
                if recipe_name == "Weekend Egg Wrap":
                    weekend_egg_wrap_found = True
                
                # Check for "highly rated" text (case insensitive)
                if "highly rated" in description.lower():
                    highly_rated_text_found = True
            
            # Results
            print("🎯 Removal Tests:")
            if not weekend_egg_wrap_found:
                print("   ✅ Weekend Egg Wrap successfully removed")
            else:
                print("   ❌ Weekend Egg Wrap still found in results")
            
            if not highly_rated_text_found:
                print("   ✅ 'Highly rated' text successfully removed")
            else:
                print("   ❌ 'Highly rated' text still found in descriptions")
            
            # Check that we still have recipes
            if len(popular_recipes) >= 3:
                print("   ✅ Still serving adequate number of recipes")
            else:
                print(f"   ⚠️  Only {len(popular_recipes)} recipes found (expected 3)")
            
            # Check for realistic recipe names
            realistic_names = [
                "Spiced Lamb and Dill Yogurt Pasta",
                "Dad's Curried Chicken and Rice", 
                "Balls With Salmon Filling (Onigiri)"
            ]
            
            found_realistic = []
            for recipe in popular_recipes:
                if recipe.get('name') in realistic_names:
                    found_realistic.append(recipe.get('name'))
            
            print(f"\n📊 Realistic recipes found: {len(found_realistic)}")
            for name in found_realistic:
                print(f"   - {name}")
            
            # Overall test result
            success = (not weekend_egg_wrap_found and 
                      not highly_rated_text_found and 
                      len(popular_recipes) >= 3)
            
            if success:
                print("\n🎉 All removal tests passed!")
                return True
            else:
                print("\n❌ Some removal tests failed!")
                return False
            
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_weekend_egg_wrap_removal()
    print(f"\n⏰ Test completed at: {datetime.now()}")
    if success:
        print("🎉 Weekend Egg Wrap removal successful!")
    else:
        print("❌ Weekend Egg Wrap removal failed!")
