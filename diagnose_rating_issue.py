#!/usr/bin/env python3
"""
Diagnostic script to help troubleshoot rating submission issues.
"""

import requests
import json

# API base URL
BASE_URL = "http://127.0.0.1:5000"

def diagnose_rating_issue():
    """Diagnose potential rating submission issues."""
    print("🔍 Diagnosing Rating Submission Issues")
    print("=" * 60)
    
    # Step 1: Check API health
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("❌ API health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API - make sure the server is running")
        return
    
    # Step 2: Test authentication
    print("\n🔐 Testing authentication...")
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return
    
    # Step 3: Get a recipe to test with
    print("\n📋 Getting a recipe to test rating...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/recommend", 
                               json={"ingredients": ["chicken", "rice"], "limit": 1},
                               headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok' and data.get('recipes'):
                recipe = data['recipes'][0]
                recipe_id = recipe.get('id')
                recipe_name = recipe.get('name')
                print(f"✅ Got test recipe: {recipe_name} (ID: {recipe_id})")
            else:
                print("❌ No recipes returned")
                return
        else:
            print(f"❌ Failed to get recipes: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting recipes: {e}")
        return
    
    # Step 4: Test rating submission
    print(f"\n⭐ Testing rating submission for recipe {recipe_id}...")
    
    rating_data = {
        "rating": 5,
        "review_text": "Test review from diagnostic script"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/recipe/{recipe_id}/review", 
                               json=rating_data,
                               headers=headers)
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Rating submission successful!")
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Rating submission failed")
            print(f"   Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"   Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error submitting rating: {e}")
    
    # Step 5: Check if the rating was saved
    print(f"\n🔍 Checking if rating was saved...")
    try:
        response = requests.get(f"{BASE_URL}/api/recipe/{recipe_id}/reviews")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                reviews = data.get('reviews', [])
                print(f"✅ Found {len(reviews)} reviews for this recipe")
                for review in reviews:
                    print(f"   - {review.get('user_name')}: {review.get('rating')}⭐ - \"{review.get('review_text')}\"")
            else:
                print(f"❌ Error getting reviews: {data.get('message')}")
        else:
            print(f"❌ Failed to get reviews: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking reviews: {e}")

def print_troubleshooting_guide():
    """Print troubleshooting guide for common issues."""
    print("\n🛠️  Troubleshooting Guide")
    print("=" * 60)
    print("If you're having trouble submitting ratings, check these common issues:")
    print()
    print("1. **Not Logged In**")
    print("   • Make sure you're logged in to your account")
    print("   • The star button should be visible (only shows for logged-in users)")
    print("   • Try refreshing the page and logging in again")
    print()
    print("2. **No Rating Selected**")
    print("   • You must click on the stars to select a rating (1-5)")
    print("   • The submit button is disabled until you select a rating")
    print("   • Make sure the stars turn yellow when you click them")
    print()
    print("3. **Recipe ID Missing**")
    print("   • Some recipes might not have proper IDs")
    print("   • Try rating a different recipe")
    print("   • Refresh the page to get fresh recipe data")
    print()
    print("4. **Network/Server Issues**")
    print("   • Check that the API server is running")
    print("   • Look for error messages in the browser console (F12)")
    print("   • Try refreshing the page")
    print()
    print("5. **Browser Issues**")
    print("   • Clear browser cache and cookies")
    print("   • Try in an incognito/private window")
    print("   • Check browser console for JavaScript errors")
    print()
    print("🎯 **How to Submit a Rating:**")
    print("   1. Go to dashboard or search results")
    print("   2. Find a recipe card")
    print("   3. Click the ⭐ star icon (only visible when logged in)")
    print("   4. Click on stars to select rating (1-5)")
    print("   5. Optionally write a review text")
    print("   6. Click 'Submit Rating' button")
    print("   7. You should see a success message")

if __name__ == "__main__":
    diagnose_rating_issue()
    print_troubleshooting_guide()
    
    print("\n" + "=" * 60)
    print("🎯 **Quick Test Steps:**")
    print("   1. Make sure you're logged in")
    print("   2. Go to: http://127.0.0.1:5000/dashboard")
    print("   3. Click ⭐ on any recipe card")
    print("   4. Click stars to rate, then click 'Submit Rating'")
    print("   5. Look for success/error messages")
