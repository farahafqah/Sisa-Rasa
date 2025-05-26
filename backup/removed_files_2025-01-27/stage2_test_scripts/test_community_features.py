#!/usr/bin/env python3
"""
Test script for community features (reviews and verifications).

This script tests the crowd sourcing functionality by:
1. Creating sample reviews and ratings
2. Creating sample verifications
3. Testing the API endpoints
"""

import requests
import json
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configuration
API_BASE_URL = "http://localhost:5000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "password123"
TEST_USER_NAME = "Test User"

def create_test_user():
    """Create a test user for testing community features."""
    signup_data = {
        "name": TEST_USER_NAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(f"{API_BASE_URL}/api/auth/signup", json=signup_data)
    if response.status_code == 201:
        print("✓ Test user created successfully")
        return True
    elif response.status_code == 400 and "already exists" in response.json().get('message', ''):
        print("✓ Test user already exists")
        return True
    else:
        print(f"✗ Failed to create test user: {response.text}")
        return False

def login_test_user():
    """Login the test user and return the JWT token."""
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(f"{API_BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get('access_token')
        print("✓ Test user logged in successfully")
        return token
    else:
        print(f"✗ Failed to login test user: {response.text}")
        return None

def test_recipe_review(token, recipe_id):
    """Test adding a review to a recipe."""
    headers = {"Authorization": f"Bearer {token}"}
    review_data = {
        "rating": 5,
        "review_text": "Amazing recipe! Easy to follow and delicious results. Highly recommended!"
    }
    
    response = requests.post(f"{API_BASE_URL}/api/recipe/{recipe_id}/review", 
                           json=review_data, headers=headers)
    
    if response.status_code == 200:
        print(f"✓ Review added successfully for recipe {recipe_id}")
        return True
    else:
        print(f"✗ Failed to add review: {response.text}")
        return False

def test_recipe_verification(token, recipe_id):
    """Test adding a verification to a recipe."""
    headers = {"Authorization": f"Bearer {token}"}
    verification_data = {
        "notes": "I tried this recipe and it turned out great! Added a bit more garlic for extra flavor."
    }
    
    response = requests.post(f"{API_BASE_URL}/api/recipe/{recipe_id}/verify", 
                           json=verification_data, headers=headers)
    
    if response.status_code == 200:
        print(f"✓ Verification added successfully for recipe {recipe_id}")
        return True
    else:
        print(f"✗ Failed to add verification: {response.text}")
        return False

def test_get_recipe_reviews(recipe_id):
    """Test getting reviews for a recipe."""
    response = requests.get(f"{API_BASE_URL}/api/recipe/{recipe_id}/reviews")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved {len(data.get('reviews', []))} reviews for recipe {recipe_id}")
        return True
    else:
        print(f"✗ Failed to get reviews: {response.text}")
        return False

def test_get_rating_summary(recipe_id):
    """Test getting rating summary for a recipe."""
    response = requests.get(f"{API_BASE_URL}/api/recipe/{recipe_id}/rating-summary")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('total_reviews', 0) > 0:
            print(f"✓ Rating summary: {data['average_rating']}/5 stars ({data['total_reviews']} reviews)")
        else:
            print("✓ No reviews yet for this recipe")
        return True
    else:
        print(f"✗ Failed to get rating summary: {response.text}")
        return False

def test_get_verifications(recipe_id):
    """Test getting verifications for a recipe."""
    response = requests.get(f"{API_BASE_URL}/api/recipe/{recipe_id}/verifications")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved {len(data.get('verifications', []))} verifications for recipe {recipe_id}")
        return True
    else:
        print(f"✗ Failed to get verifications: {response.text}")
        return False

def test_api_health():
    """Test if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        if response.status_code == 200:
            print("✓ API is running")
            return True
        else:
            print(f"✗ API health check failed: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Make sure the server is running.")
        return False

def get_sample_recipe_id():
    """Get a sample recipe ID for testing."""
    try:
        # Try to get recommendations to find a recipe ID
        response = requests.post(f"{API_BASE_URL}/api/recommend", json={
            "ingredients": ["egg", "rice"],
            "limit": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('recipes') and len(data['recipes']) > 0:
                recipe_id = data['recipes'][0]['id']
                print(f"✓ Using recipe ID: {recipe_id}")
                return recipe_id
        
        # Fallback to a common recipe ID format
        print("⚠ Using fallback recipe ID")
        return "recipe_001"
        
    except Exception as e:
        print(f"⚠ Error getting recipe ID: {e}, using fallback")
        return "recipe_001"

def main():
    """Run all community feature tests."""
    print("🧪 Testing Sisa Rasa Community Features")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("❌ API is not running. Please start the server first.")
        return
    
    # Create and login test user
    if not create_test_user():
        return
    
    token = login_test_user()
    if not token:
        return
    
    # Get a sample recipe ID
    recipe_id = get_sample_recipe_id()
    
    print(f"\n🧪 Testing community features with recipe: {recipe_id}")
    print("-" * 50)
    
    # Test review functionality
    print("\n📝 Testing Reviews:")
    test_recipe_review(token, recipe_id)
    test_get_recipe_reviews(recipe_id)
    test_get_rating_summary(recipe_id)
    
    # Test verification functionality
    print("\n✅ Testing Verifications:")
    test_recipe_verification(token, recipe_id)
    test_get_verifications(recipe_id)
    
    print("\n🎉 Community features testing completed!")
    print("\nTo test the UI:")
    print("1. Start the Flask server: python src/api/app.py")
    print("2. Open http://localhost:5000/dashboard")
    print("3. Login with your account")
    print("4. Click the star icon on any recipe to rate and review")

if __name__ == "__main__":
    main()
