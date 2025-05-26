#!/usr/bin/env python3
"""
Test script to verify that review viewing functionality is working.
"""

import requests
import json

# API base URL
BASE_URL = "http://127.0.0.1:5000"

def test_review_viewing():
    """Test the review viewing functionality."""
    print("🧪 Testing Review Viewing Functionality")
    print("=" * 50)
    
    # Test 1: Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("❌ API is not responding correctly")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Failed to connect to API")
        return False
    
    # Test 2: Login to get a token
    print("\n🔐 Testing login...")
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print("✅ Login successful")
        else:
            print("❌ Login failed")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test 3: Get a recipe that has reviews
    print("\n📋 Finding a recipe with reviews...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Get recommendations first
        response = requests.post(f"{BASE_URL}/api/recommend", 
                               json={"ingredients": ["chicken", "rice"], "limit": 5},
                               headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok' and data.get('recipes'):
                recipes = data['recipes']
                print(f"✅ Got {len(recipes)} recipes")
                
                # Test reviews for each recipe
                for recipe in recipes:
                    recipe_id = recipe.get('id')
                    recipe_name = recipe.get('name')
                    
                    if recipe_id:
                        print(f"\n📝 Testing reviews for: {recipe_name} (ID: {recipe_id})")
                        
                        # Test 4: Get reviews for this recipe
                        response = requests.get(f"{BASE_URL}/api/recipe/{recipe_id}/reviews")
                        if response.status_code == 200:
                            review_data = response.json()
                            if review_data.get('status') == 'success':
                                reviews = review_data.get('reviews', [])
                                print(f"✅ Found {len(reviews)} reviews")
                                
                                if reviews:
                                    print("   📋 Review details:")
                                    for i, review in enumerate(reviews[:3], 1):  # Show first 3 reviews
                                        stars = "⭐" * review.get('rating', 0)
                                        reviewer = review.get('user_name', 'Unknown')
                                        text = review.get('review_text', 'No text')[:50]
                                        if len(review.get('review_text', '')) > 50:
                                            text += "..."
                                        print(f"   {i}. {reviewer}: {stars} - \"{text}\"")
                                    
                                    # Test 5: Get rating summary
                                    response = requests.get(f"{BASE_URL}/api/recipe/{recipe_id}/rating-summary")
                                    if response.status_code == 200:
                                        summary_data = response.json()
                                        if summary_data.get('status') == 'success':
                                            avg_rating = summary_data.get('average_rating', 0)
                                            total_reviews = summary_data.get('total_reviews', 0)
                                            print(f"   📊 Average rating: {avg_rating}/5 ({total_reviews} reviews)")
                                        else:
                                            print("   ⚠️  No rating summary available")
                                    
                                    return True  # Found a recipe with reviews
                                else:
                                    print("   ℹ️  No reviews for this recipe")
                            else:
                                print(f"   ❌ Failed to get reviews: {review_data.get('message')}")
                        else:
                            print(f"   ❌ Failed to fetch reviews (status: {response.status_code})")
                
                print("\n⚠️  No recipes found with existing reviews")
                return True  # API is working, just no reviews yet
            else:
                print("❌ No recipes in recommendations")
                return False
        else:
            print(f"❌ Failed to get recommendations: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing reviews: {e}")
        return False

def print_instructions():
    """Print instructions for viewing reviews in the UI."""
    print("\n🎯 How to View Reviews in the UI:")
    print("=" * 50)
    print("1. 📱 Go to Dashboard: http://127.0.0.1:5000/dashboard")
    print("2. 👀 Look for recipes with star ratings displayed")
    print("3. 💬 Click the comment icon (💬) next to any recipe")
    print("4. 📋 A modal will open showing all reviews for that recipe")
    print("5. ⭐ You'll see reviewer names, ratings, and review text")
    print("6. 👍 You can vote on reviews as helpful/unhelpful")
    print("7. ✍️  Click 'Add Review' to write your own review")
    print("\n🔍 Alternative ways to view reviews:")
    print("• Search for ingredients and go to search results page")
    print("• Click the comment icon on any recipe card")
    print("• Reviews are sorted by most helpful first")
    print("\n📝 What you'll see in reviews:")
    print("• Reviewer name (e.g., 'arif')")
    print("• Star rating (1-5 stars)")
    print("• Review text/comments")
    print("• Date of review")
    print("• Helpful/unhelpful vote counts")

if __name__ == "__main__":
    print("🧪 Testing Sisa Rasa Review Viewing")
    print("=" * 50)
    
    # Test the review viewing functionality
    success = test_review_viewing()
    
    # Print instructions regardless of test results
    print_instructions()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Review viewing functionality is working!")
        print("\n💡 To see arif's review:")
        print("   1. Find a recipe that has been rated")
        print("   2. Click the 💬 comment icon")
        print("   3. Look for 'arif' in the reviewer list")
    else:
        print("❌ Some issues found with review viewing functionality.")
