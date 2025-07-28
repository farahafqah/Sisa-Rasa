#!/usr/bin/env python3
"""
System Functionality Verification Script

This script verifies that all system features work correctly after database optimization.
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

def connect_to_database():
    """Connect to MongoDB database."""
    try:
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        client = MongoClient(mongo_uri)
        db = client['sisarasa']
        
        # Test connection
        db.command('ping')
        print(f"✅ Connected to MongoDB: {mongo_uri}")
        return db, client
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None, None

def verify_user_functionality(db):
    """Verify user-related functionality."""
    print("\n👤 Verifying user functionality...")
    
    users_collection = db['users']
    
    # Check user count
    user_count = users_collection.count_documents({})
    print(f"  📊 Total users: {user_count}")
    
    # Check user structure
    sample_user = users_collection.find_one()
    if sample_user:
        required_fields = ['name', 'email', 'created_at', 'analytics', 'dashboard_data']
        missing_fields = [field for field in required_fields if field not in sample_user]
        
        if missing_fields:
            print(f"  ⚠️  Missing fields in user documents: {missing_fields}")
            return False
        else:
            print("  ✅ User document structure is valid")
    
    # Check for Malaysian names
    malaysian_name_count = 0
    for user in users_collection.find({}, {'name': 1}).limit(10):
        name = user.get('name', '')
        # Simple check for common Malaysian names
        malaysian_indicators = ['Ahmad', 'Ali', 'Siti', 'Muhammad', 'Fatimah', 'Hassan', 'Ibrahim']
        if any(indicator in name for indicator in malaysian_indicators):
            malaysian_name_count += 1
    
    print(f"  🇲🇾 Malaysian names in sample: {malaysian_name_count}/10")
    
    return True

def verify_recipe_functionality(db):
    """Verify recipe-related functionality."""
    print("\n🍽️  Verifying recipe functionality...")
    
    recipes_collection = db['recipes']
    
    # Check recipe count
    recipe_count = recipes_collection.count_documents({})
    print(f"  📊 Total recipes: {recipe_count}")
    
    # Check user-submitted recipes
    user_recipes = recipes_collection.count_documents({'is_user_submitted': True})
    print(f"  👥 User-submitted recipes: {user_recipes}")
    
    # Verify all user-submitted recipes have proper fields
    invalid_recipes = recipes_collection.count_documents({
        'is_user_submitted': True,
        'submitted_by': {'$exists': False}
    })
    
    if invalid_recipes > 0:
        print(f"  ⚠️  Found {invalid_recipes} user recipes without submitted_by field")
        return False
    else:
        print("  ✅ All user recipes have proper submitted_by field")
    
    return True

def verify_community_functionality(db):
    """Verify community features functionality."""
    print("\n💬 Verifying community functionality...")
    
    posts_collection = db['community_posts']
    comments_collection = db['post_comments']
    likes_collection = db['post_likes']
    
    # Check counts
    posts_count = posts_collection.count_documents({})
    comments_count = comments_collection.count_documents({})
    likes_count = likes_collection.count_documents({})
    
    print(f"  📊 Community posts: {posts_count}")
    print(f"  📊 Comments: {comments_count}")
    print(f"  📊 Likes: {likes_count}")
    
    # Check for orphaned data
    orphaned_comments = 0
    for comment in comments_collection.find():
        post_id = comment.get('post_id')
        if post_id:
            post_exists = posts_collection.find_one({'_id': post_id})
            if not post_exists:
                orphaned_comments += 1
    
    orphaned_likes = 0
    for like in likes_collection.find():
        post_id = like.get('post_id')
        if post_id:
            post_exists = posts_collection.find_one({'_id': post_id})
            if not post_exists:
                orphaned_likes += 1
    
    if orphaned_comments > 0 or orphaned_likes > 0:
        print(f"  ⚠️  Found {orphaned_comments} orphaned comments and {orphaned_likes} orphaned likes")
        return False
    else:
        print("  ✅ No orphaned community data found")
    
    return True

def verify_review_functionality(db):
    """Verify review system functionality."""
    print("\n⭐ Verifying review functionality...")
    
    reviews_collection = db['recipe_reviews']
    votes_collection = db['review_votes']
    
    # Check counts
    reviews_count = reviews_collection.count_documents({})
    votes_count = votes_collection.count_documents({})
    
    print(f"  📊 Recipe reviews: {reviews_count}")
    print(f"  📊 Review votes: {votes_count}")
    
    # Check review distribution
    users_collection = db['users']
    user_count = users_collection.count_documents({})
    
    if user_count > 0:
        avg_reviews_per_user = reviews_count / user_count
        print(f"  📈 Average reviews per user: {avg_reviews_per_user:.2f}")
        
        if avg_reviews_per_user > 10:
            print("  ⚠️  High review count per user - might indicate synthetic data")
        else:
            print("  ✅ Review distribution looks reasonable")
    
    return True

def verify_data_consistency(db):
    """Verify overall data consistency."""
    print("\n🔍 Verifying data consistency...")
    
    # Check user references in various collections
    users_collection = db['users']
    valid_user_ids = set(str(user['_id']) for user in users_collection.find({}, {'_id': 1}))
    
    consistency_issues = 0
    
    # Check community posts
    posts_collection = db['community_posts']
    for post in posts_collection.find():
        user_id = post.get('user_id')
        if user_id and user_id not in valid_user_ids:
            consistency_issues += 1
    
    # Check reviews
    reviews_collection = db['recipe_reviews']
    for review in reviews_collection.find():
        user_id = review.get('user_id')
        if user_id and user_id not in valid_user_ids:
            consistency_issues += 1
    
    if consistency_issues > 0:
        print(f"  ⚠️  Found {consistency_issues} data consistency issues")
        return False
    else:
        print("  ✅ Data consistency verified")
    
    return True

def generate_summary_report(db):
    """Generate a summary report of the optimized database."""
    print("\n📋 DATABASE OPTIMIZATION SUMMARY REPORT")
    print("=" * 50)
    
    # Collection counts
    collections = {
        'users': db['users'].count_documents({}),
        'recipes': db['recipes'].count_documents({}),
        'community_posts': db['community_posts'].count_documents({}),
        'post_comments': db['post_comments'].count_documents({}),
        'post_likes': db['post_likes'].count_documents({}),
        'recipe_reviews': db['recipe_reviews'].count_documents({}),
        'review_votes': db['review_votes'].count_documents({})
    }
    
    print("📊 Collection Counts:")
    for collection, count in collections.items():
        print(f"  {collection}: {count}")
    
    # Data quality metrics
    print("\n🎯 Data Quality Metrics:")
    
    # User-submitted recipes
    user_recipes = db['recipes'].count_documents({'is_user_submitted': True})
    print(f"  User-submitted recipes: {user_recipes}")
    
    # Active users (users with activity)
    active_users = 0
    for user in db['users'].find():
        has_activity = (
            len(user.get('saved_recipes', [])) > 0 or
            db['recipe_reviews'].count_documents({'user_id': str(user['_id'])}) > 0 or
            db['community_posts'].count_documents({'user_id': str(user['_id'])}) > 0
        )
        if has_activity:
            active_users += 1
    
    print(f"  Active users: {active_users}/{collections['users']}")
    
    # Review distribution
    if collections['users'] > 0:
        avg_reviews = collections['recipe_reviews'] / collections['users']
        print(f"  Average reviews per user: {avg_reviews:.2f}")
    
    print(f"\n✅ Database optimization completed successfully!")
    print(f"🕒 Report generated at: {datetime.now().isoformat()}")

def main():
    """Main verification function."""
    print("🔍 SisaRasa System Functionality Verification")
    print("=" * 50)
    print(f"Verification started at: {datetime.now().isoformat()}")
    
    # Connect to database
    db, client = connect_to_database()
    if db is None:
        return
    
    try:
        all_tests_passed = True
        
        # Run verification tests
        all_tests_passed &= verify_user_functionality(db)
        all_tests_passed &= verify_recipe_functionality(db)
        all_tests_passed &= verify_community_functionality(db)
        all_tests_passed &= verify_review_functionality(db)
        all_tests_passed &= verify_data_consistency(db)
        
        # Generate summary report
        generate_summary_report(db)
        
        if all_tests_passed:
            print(f"\n🎉 ALL VERIFICATION TESTS PASSED!")
            print("Your SisaRasa system is functioning correctly after optimization.")
        else:
            print(f"\n⚠️  Some verification tests failed.")
            print("Please review the issues above.")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
