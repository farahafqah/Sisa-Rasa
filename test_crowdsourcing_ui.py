#!/usr/bin/env python3
"""
Test script for crowd sourcing UI features.
This script tests the rating and review functionality through API calls.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_crowdsourcing_features():
    """Test the crowd sourcing features"""
    print("🧪 Testing Sisa Rasa Crowd Sourcing Features")
    print("=" * 50)
    
    # Test 1: Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ API is running")
            data = response.json()
            print(f"   - Recipes loaded: {data.get('recipes_loaded', 'Unknown')}")
            print(f"   - Ingredients loaded: {data.get('ingredients_loaded', 'Unknown')}")
        else:
            print("❌ API is not responding")
            return
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return
    
    # Test 2: Get sample recipe recommendations
    print("\n🔍 Getting sample recipes...")
    try:
        response = requests.post(f"{BASE_URL}/api/recommend", 
                               json={"ingredients": ["chicken", "rice"], "limit": 5})
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok' and data.get('recipes'):
                recipe = data['recipes'][0]
                recipe_id = recipe['id']
                recipe_name = recipe['name']
                print(f"✅ Found sample recipe: {recipe_name} (ID: {recipe_id})")
                
                # Test 3: Get recipe reviews
                print(f"\n📝 Testing reviews for recipe {recipe_id}...")
                response = requests.get(f"{BASE_URL}/api/recipe/{recipe_id}/reviews")
                if response.status_code == 200:
                    reviews_data = response.json()
                    if reviews_data.get('status') == 'success':
                        reviews = reviews_data.get('reviews', [])
                        print(f"✅ Reviews endpoint working - Found {len(reviews)} reviews")
                        
                        if reviews:
                            print("   Sample reviews:")
                            for i, review in enumerate(reviews[:3]):
                                print(f"   {i+1}. {review['user_name']}: {review['rating']}⭐")
                                if review.get('review_text'):
                                    print(f"      \"{review['review_text'][:50]}...\"")
                        else:
                            print("   No reviews found for this recipe")
                    else:
                        print(f"❌ Reviews endpoint error: {reviews_data.get('message')}")
                else:
                    print(f"❌ Reviews endpoint failed: {response.status_code}")
                
                # Test 4: Get rating summary
                print(f"\n⭐ Testing rating summary for recipe {recipe_id}...")
                response = requests.get(f"{BASE_URL}/api/recipe/{recipe_id}/rating-summary")
                if response.status_code == 200:
                    rating_data = response.json()
                    if rating_data.get('status') == 'success':
                        avg_rating = rating_data.get('average_rating', 0)
                        total_reviews = rating_data.get('total_reviews', 0)
                        print(f"✅ Rating summary working - {avg_rating}/5 stars ({total_reviews} reviews)")
                        
                        distribution = rating_data.get('rating_distribution', {})
                        if any(int(count) > 0 for count in distribution.values()):
                            print("   Rating distribution:")
                            for stars, count in distribution.items():
                                if int(count) > 0:
                                    print(f"   {stars}⭐: {count} reviews")
                    else:
                        print(f"❌ Rating summary error: {rating_data.get('message')}")
                else:
                    print(f"❌ Rating summary failed: {response.status_code}")
                
                # Test 5: Get verifications
                print(f"\n✅ Testing verifications for recipe {recipe_id}...")
                response = requests.get(f"{BASE_URL}/api/recipe/{recipe_id}/verifications")
                if response.status_code == 200:
                    verif_data = response.json()
                    if verif_data.get('status') == 'success':
                        verifications = verif_data.get('verifications', [])
                        print(f"✅ Verifications endpoint working - Found {len(verifications)} verifications")
                        
                        if verifications:
                            print("   Sample verifications:")
                            for i, verif in enumerate(verifications[:3]):
                                print(f"   {i+1}. {verif['user_name']} verified this recipe")
                                if verif.get('notes'):
                                    print(f"      Notes: \"{verif['notes'][:50]}...\"")
                        else:
                            print("   No verifications found for this recipe")
                    else:
                        print(f"❌ Verifications error: {verif_data.get('message')}")
                else:
                    print(f"❌ Verifications failed: {response.status_code}")
                
            else:
                print("❌ No recipes found in recommendation response")
        else:
            print(f"❌ Recipe recommendation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing recipes: {e}")
    
    print("\n🎯 UI Testing Instructions:")
    print("=" * 50)
    print("1. Open your browser to: http://127.0.0.1:5000")
    print("2. Login with your account")
    print("3. Go to Dashboard and search for ingredients (e.g., 'chicken, rice')")
    print("4. Click 'Search Recipes' to go to search results page")
    print("5. On a recipe card, click the ⭐ star icon to rate and review")
    print("6. Fill out the rating modal and submit")
    print("7. Click the 💬 comment icon to view all reviews")
    print("8. Check that ratings and reviews appear correctly")
    
    print("\n✨ Features to Test:")
    print("- ⭐ Rating recipes (1-5 stars)")
    print("- 📝 Writing text reviews")
    print("- ✅ Marking recipes as verified")
    print("- 👀 Viewing all reviews for a recipe")
    print("- 👍👎 Voting on reviews as helpful/unhelpful")
    print("- 🔄 Updating existing reviews")
    
    print("\n🎉 Crowd sourcing features are ready to test!")

if __name__ == "__main__":
    test_crowdsourcing_features()
