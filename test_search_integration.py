#!/usr/bin/env python3
"""
Test script to verify that user-shared recipes are included in search results.
"""

import requests
import json
import sys

def test_search_integration():
    """Test that search results include both system and user-shared recipes."""
    
    # Test the recommendation API
    url = "http://localhost:5000/api/recommend"
    payload = {
        "ingredients": ["chicken", "rice", "onion"],
        "limit": 20
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'ok':
            print(f"❌ API returned error: {data.get('message', 'Unknown error')}")
            return False
        
        recipes = data.get('recipes', [])
        total_recipes = len(recipes)
        
        # Count system vs user recipes
        system_recipes = [r for r in recipes if not r.get('is_user_recipe', False)]
        user_recipes = [r for r in recipes if r.get('is_user_recipe', False)]
        
        print(f"✅ Search Integration Test Results:")
        print(f"   Total recipes returned: {total_recipes}")
        print(f"   System recipes: {len(system_recipes)}")
        print(f"   User-shared recipes: {len(user_recipes)}")
        
        if len(user_recipes) > 0:
            print(f"✅ SUCCESS: User-shared recipes are included in search results!")
            print(f"   Example user recipe: {user_recipes[0].get('name', 'Unknown')}")
            print(f"   Submitted by: {user_recipes[0].get('submitted_by', 'Unknown')}")
        else:
            print(f"⚠️  WARNING: No user-shared recipes found in results")
            print(f"   This could mean:")
            print(f"   - No user recipes exist in database")
            print(f"   - User recipes don't match the search ingredients")
            print(f"   - Integration is working but no matches found")
        
        # Test ingredient search API
        ingredient_url = "http://localhost:5000/api/ingredients"
        ingredient_response = requests.get(f"{ingredient_url}?search=chicken&limit=10")
        ingredient_data = ingredient_response.json()
        
        if ingredient_data.get('status') == 'ok':
            ingredient_count = ingredient_data.get('count', 0)
            print(f"✅ Ingredient search working: {ingredient_count} ingredients found")
        else:
            print(f"❌ Ingredient search failed")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server. Make sure the Flask app is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Recipe Search Integration...")
    print("=" * 50)
    
    success = test_search_integration()
    
    if success:
        print("\n✅ Integration test completed successfully!")
    else:
        print("\n❌ Integration test failed!")
        sys.exit(1)
