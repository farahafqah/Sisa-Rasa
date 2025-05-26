#!/usr/bin/env python3
"""
Test script to debug rating submission issues.
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:5000"

def test_login():
    """Test login to get a token."""
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }

    response = requests.post(f"{API_BASE_URL}/api/auth/login", json=login_data)

    print(f"Login response status: {response.status_code}")
    print(f"Login response: {response.text}")

    if response.status_code == 200:
        data = response.json()
        print(f"Login data: {data}")
        if data.get('status') == 'success':
            print(f"✓ Login successful")
            token = data.get('token')
            print(f"Token: {token}")
            return token
        else:
            print(f"✗ Login failed: {data.get('message')}")
            return None
    else:
        print(f"✗ Login request failed: {response.status_code} - {response.text}")
        return None

def test_rating_submission(token, recipe_id="fallback-fried-rice"):
    """Test submitting a rating for a recipe."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    rating_data = {
        "rating": 4,
        "review_text": "Great recipe! Easy to follow and delicious."
    }

    print(f"Testing rating submission for recipe: {recipe_id}")
    print(f"Rating data: {rating_data}")

    response = requests.post(
        f"{API_BASE_URL}/api/recipe/{recipe_id}/review",
        json=rating_data,
        headers=headers
    )

    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Response text: {response.text}")

    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'success':
            print(f"✓ Rating submitted successfully")
            return True
        else:
            print(f"✗ Rating submission failed: {data.get('message')}")
            return False
    else:
        print(f"✗ Rating submission request failed: {response.status_code}")
        return False

def test_rating_summary(recipe_id="fallback-fried-rice"):
    """Test getting rating summary for a recipe."""
    response = requests.get(f"{API_BASE_URL}/api/recipe/{recipe_id}/rating-summary")

    print(f"Rating summary response status: {response.status_code}")
    print(f"Rating summary response: {response.text}")

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

def main():
    """Main test function."""
    print("=== Testing Rating Submission ===")

    # Test login
    token = test_login()
    if not token:
        print("Cannot proceed without authentication token")
        return

    # Test rating submission
    print("\n=== Testing Rating Submission ===")
    test_rating_submission(token)

    # Test rating summary
    print("\n=== Testing Rating Summary ===")
    test_rating_summary()

if __name__ == "__main__":
    main()
