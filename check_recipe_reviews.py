#!/usr/bin/env python3
"""
Check reviews for Weekend Egg Wrap recipe.
"""

import sys
import os
from bson import ObjectId

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_recipe_reviews():
    """Check reviews for the Weekend Egg Wrap recipe."""
    
    print("🔍 CHECKING RECIPE REVIEWS")
    print("=" * 60)
    
    try:
        # Import Flask app and MongoDB
        from api.app import app
        from flask_pymongo import PyMongo
        
        with app.app_context():
            mongo = PyMongo(app)
            
            recipe_id = "6884d5c899a606fd6ec589ae"
            print(f"🎯 Target Recipe ID: {recipe_id}")
            
            # Check if this is a valid ObjectId
            try:
                obj_id = ObjectId(recipe_id)
                print(f"✅ Valid ObjectId: {obj_id}")
            except Exception as e:
                print(f"❌ Invalid ObjectId: {e}")
                return
            
            # 1. Check if the recipe exists
            print("\n📋 CHECKING RECIPE EXISTENCE")
            print("-" * 40)
            
            recipe = mongo.db.recipes.find_one({"_id": obj_id})
            if recipe:
                print(f"✅ Recipe found: {recipe.get('name', 'Unknown')}")
                print(f"📝 Recipe details:")
                print(f"   - ID: {recipe['_id']}")
                print(f"   - Name: {recipe.get('name', 'N/A')}")
                print(f"   - Original ID: {recipe.get('original_id', 'N/A')}")
            else:
                print(f"❌ Recipe not found in recipes collection")
                
                # Check if it exists with original_id
                recipe_by_original = mongo.db.recipes.find_one({"original_id": recipe_id})
                if recipe_by_original:
                    print(f"✅ Found by original_id: {recipe_by_original.get('name', 'Unknown')}")
                    recipe = recipe_by_original
                    recipe_id = str(recipe['_id'])
                else:
                    print(f"❌ Recipe not found by original_id either")
                    return
            
            # 2. Check reviews for this recipe
            print(f"\n📝 CHECKING REVIEWS FOR RECIPE ID: {recipe_id}")
            print("-" * 40)
            
            # Try both string and ObjectId formats
            review_queries = [
                {"recipe_id": recipe_id},  # String format
                {"recipe_id": obj_id},     # ObjectId format
            ]
            
            all_reviews = []
            for i, query in enumerate(review_queries):
                print(f"\n🔍 Query {i+1}: {query}")
                reviews = list(mongo.db.recipe_reviews.find(query))
                print(f"   Found {len(reviews)} reviews")
                all_reviews.extend(reviews)
                
                if reviews:
                    for review in reviews:
                        print(f"   📝 Review by {review.get('user_name', 'Unknown')}: {review.get('rating', 'N/A')}/5")
                        if review.get('review_text'):
                            print(f"      💬 \"{review['review_text'][:100]}...\"")
            
            # Remove duplicates
            unique_reviews = []
            seen_ids = set()
            for review in all_reviews:
                if review['_id'] not in seen_ids:
                    unique_reviews.append(review)
                    seen_ids.add(review['_id'])
            
            print(f"\n📊 SUMMARY")
            print("-" * 40)
            print(f"Total unique reviews found: {len(unique_reviews)}")
            
            if len(unique_reviews) == 0:
                print("❌ No reviews found for this recipe")
                
                # Check if there are any reviews in the collection at all
                total_reviews = mongo.db.recipe_reviews.count_documents({})
                print(f"📊 Total reviews in database: {total_reviews}")
                
                if total_reviews > 0:
                    # Show a sample of recipe IDs that do have reviews
                    sample_reviews = list(mongo.db.recipe_reviews.find({}, {"recipe_id": 1, "user_name": 1}).limit(5))
                    print(f"\n📋 Sample recipe IDs with reviews:")
                    for review in sample_reviews:
                        print(f"   - Recipe ID: {review.get('recipe_id')} (by {review.get('user_name', 'Unknown')})")
            else:
                print("✅ Reviews found!")
                
            # 3. Test the API endpoint
            print(f"\n🧪 TESTING API ENDPOINT")
            print("-" * 40)

            import requests
            try:
                response = requests.get(f'http://127.0.0.1:5000/api/recipe/{recipe_id}/reviews')
                print(f"API Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"API Response: {data.get('status', 'unknown')}")
                    reviews = data.get('reviews', [])
                    print(f"API Reviews count: {len(reviews)}")

                    if reviews:
                        print(f"\n📝 API Reviews:")
                        for i, review in enumerate(reviews[:3]):
                            print(f"   {i+1}. {review.get('user_name', 'Unknown')}: {review.get('rating', 'N/A')}/5")
                            if review.get('review_text'):
                                print(f"      💬 \"{review['review_text'][:80]}...\"")
                else:
                    print(f"API Error: {response.text}")

            except Exception as e:
                print(f"API Test failed: {e}")

            # 4. Test rating summary endpoint
            print(f"\n🧪 TESTING RATING SUMMARY ENDPOINT")
            print("-" * 40)

            try:
                response = requests.get(f'http://127.0.0.1:5000/api/recipe/{recipe_id}/rating-summary')
                print(f"Rating Summary Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"Average Rating: {data.get('average_rating', 'N/A')}")
                    print(f"Total Reviews: {data.get('total_reviews', 'N/A')}")
                else:
                    print(f"Rating Summary Error: {response.text}")

            except Exception as e:
                print(f"Rating Summary Test failed: {e}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recipe_reviews()
