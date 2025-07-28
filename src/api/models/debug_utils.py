"""
Debug utilities for inspecting user data in the Sisa Rasa system.

This module provides functions for developers to inspect and debug user data
directly from Python code or interactive sessions.
"""

from api.models.user import mongo, get_user_by_id, get_user_by_email
from api.models.recipe import get_saved_recipes_for_user
from bson.objectid import ObjectId
from datetime import datetime
import json

def get_all_users_summary():
    """
    Get a summary of all users in the system.
    
    Returns:
        list: List of user summaries with basic info
    """
    try:
        users = list(mongo.db.users.find({}, {
            'name': 1, 
            'email': 1, 
            'created_at': 1,
            'analytics.total_reviews_given': 1,
            'analytics.total_recipe_saves': 1,
            'is_admin': 1
        }).sort('created_at', -1))
        
        summary = []
        for user in users:
            summary.append({
                'id': str(user['_id']),
                'name': user.get('name', 'N/A'),
                'email': user.get('email', 'N/A'),
                'created_at': user.get('created_at'),
                'total_reviews': user.get('analytics', {}).get('total_reviews_given', 0),
                'total_saves': user.get('analytics', {}).get('total_recipe_saves', 0),
                'is_admin': user.get('is_admin', False)
            })
        
        return summary
    except Exception as e:
        print(f"Error getting users summary: {e}")
        return []

def inspect_user(user_identifier):
    """
    Get comprehensive data for a specific user.
    
    Args:
        user_identifier (str): User email or ID
        
    Returns:
        dict: Complete user data including all related records
    """
    try:
        # Find user
        user = None
        if '@' in user_identifier:
            user = get_user_by_email(user_identifier)
        else:
            user = get_user_by_id(user_identifier)
        
        if not user:
            return {'error': f'User not found: {user_identifier}'}
        
        user_id = str(user['_id'])
        
        # Get related data
        saved_recipes = get_saved_recipes_for_user(user_id)
        reviews = list(mongo.db.recipe_reviews.find({'user_id': user_id}).sort('created_at', -1))
        verifications = list(mongo.db.recipe_verifications.find({'user_id': user_id}).sort('created_at', -1))
        review_votes = list(mongo.db.review_votes.find({'user_id': user_id}).sort('created_at', -1))
        
        # Prepare comprehensive data
        user_data = {
            'basic_info': {
                'id': user_id,
                'name': user.get('name'),
                'email': user.get('email'),
                'created_at': user.get('created_at'),
                'updated_at': user.get('updated_at'),
                'is_admin': user.get('is_admin', False),
                'has_profile_image': bool(user.get('profile_image'))
            },
            'preferences': user.get('preferences', {}),
            'analytics': user.get('analytics', {}),
            'dashboard_data': user.get('dashboard_data', {}),
            'activity_summary': {
                'saved_recipes_count': len(saved_recipes),
                'reviews_count': len(reviews),
                'verifications_count': len(verifications),
                'review_votes_count': len(review_votes)
            },
            'saved_recipes': [
                {
                    'id': str(recipe['_id']),
                    'name': recipe.get('name'),
                    'ingredients_count': len(recipe.get('ingredients', [])),
                    'saved_at': recipe.get('created_at')
                } for recipe in saved_recipes
            ],
            'reviews': [
                {
                    'id': str(review['_id']),
                    'recipe_id': review.get('recipe_id'),
                    'rating': review.get('rating'),
                    'review_text': review.get('review_text'),
                    'helpful_votes': review.get('helpful_votes', 0),
                    'unhelpful_votes': review.get('unhelpful_votes', 0),
                    'created_at': review.get('created_at'),
                    'updated_at': review.get('updated_at')
                } for review in reviews
            ],
            'verifications': [
                {
                    'id': str(verification['_id']),
                    'recipe_id': verification.get('recipe_id'),
                    'notes': verification.get('notes'),
                    'has_photo': 'photo_data' in verification,
                    'created_at': verification.get('created_at')
                } for verification in verifications
            ],
            'review_votes': [
                {
                    'id': str(vote['_id']),
                    'review_id': vote.get('review_id'),
                    'vote_type': vote.get('vote_type'),
                    'created_at': vote.get('created_at')
                } for vote in review_votes
            ]
        }
        
        return user_data
        
    except Exception as e:
        return {'error': f'Error inspecting user: {str(e)}'}

def get_user_reviews_detailed(user_identifier):
    """
    Get detailed review information for a user.
    
    Args:
        user_identifier (str): User email or ID
        
    Returns:
        list: Detailed review data
    """
    try:
        # Find user
        user = None
        if '@' in user_identifier:
            user = get_user_by_email(user_identifier)
        else:
            user = get_user_by_id(user_identifier)
        
        if not user:
            return {'error': f'User not found: {user_identifier}'}
        
        user_id = str(user['_id'])
        reviews = list(mongo.db.recipe_reviews.find({'user_id': user_id}).sort('created_at', -1))
        
        detailed_reviews = []
        for review in reviews:
            detailed_reviews.append({
                'review_id': str(review['_id']),
                'recipe_id': review.get('recipe_id'),
                'rating': review.get('rating'),
                'review_text': review.get('review_text'),
                'helpful_votes': review.get('helpful_votes', 0),
                'unhelpful_votes': review.get('unhelpful_votes', 0),
                'created_at': review.get('created_at'),
                'updated_at': review.get('updated_at'),
                'user_name': review.get('user_name')
            })
        
        return {
            'user': {
                'id': user_id,
                'name': user.get('name'),
                'email': user.get('email')
            },
            'total_reviews': len(detailed_reviews),
            'reviews': detailed_reviews
        }
        
    except Exception as e:
        return {'error': f'Error getting user reviews: {str(e)}'}

def get_system_stats():
    """
    Get overall system statistics.
    
    Returns:
        dict: System statistics
    """
    try:
        stats = {
            'collections': {
                'users': mongo.db.users.count_documents({}),
                'recipe_reviews': mongo.db.recipe_reviews.count_documents({}),
                'recipe_verifications': mongo.db.recipe_verifications.count_documents({}),
                'saved_recipes': mongo.db.saved_recipes.count_documents({}),
                'review_votes': mongo.db.review_votes.count_documents({})
            }
        }
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        stats['recent_activity'] = {
            'new_users_7_days': mongo.db.users.count_documents({'created_at': {'$gte': seven_days_ago}}),
            'new_reviews_7_days': mongo.db.recipe_reviews.count_documents({'created_at': {'$gte': seven_days_ago}}),
            'new_verifications_7_days': mongo.db.recipe_verifications.count_documents({'created_at': {'$gte': seven_days_ago}})
        }
        
        # Top reviewers
        top_reviewers = list(mongo.db.recipe_reviews.aggregate([
            {'$group': {'_id': '$user_id', 'count': {'$sum': 1}, 'user_name': {'$first': '$user_name'}}},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]))
        
        stats['top_reviewers'] = [
            {
                'user_id': reviewer['_id'],
                'user_name': reviewer['user_name'],
                'review_count': reviewer['count']
            } for reviewer in top_reviewers
        ]
        
        # Rating distribution
        rating_dist = list(mongo.db.recipe_reviews.aggregate([
            {'$group': {'_id': '$rating', 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]))
        
        stats['rating_distribution'] = {
            str(rating['_id']): rating['count'] for rating in rating_dist
        }
        
        return stats
        
    except Exception as e:
        return {'error': f'Error getting system stats: {str(e)}'}

def find_users_by_activity(min_reviews=0, min_saves=0):
    """
    Find users based on activity levels.
    
    Args:
        min_reviews (int): Minimum number of reviews
        min_saves (int): Minimum number of saved recipes
        
    Returns:
        list: Users matching criteria
    """
    try:
        query = {}
        if min_reviews > 0:
            query['analytics.total_reviews_given'] = {'$gte': min_reviews}
        if min_saves > 0:
            query['analytics.total_recipe_saves'] = {'$gte': min_saves}
        
        users = list(mongo.db.users.find(query, {
            'name': 1,
            'email': 1,
            'analytics.total_reviews_given': 1,
            'analytics.total_recipe_saves': 1,
            'created_at': 1
        }).sort('analytics.total_reviews_given', -1))
        
        return [
            {
                'id': str(user['_id']),
                'name': user.get('name'),
                'email': user.get('email'),
                'total_reviews': user.get('analytics', {}).get('total_reviews_given', 0),
                'total_saves': user.get('analytics', {}).get('total_recipe_saves', 0),
                'created_at': user.get('created_at')
            } for user in users
        ]
        
    except Exception as e:
        return {'error': f'Error finding users by activity: {str(e)}'}

def export_user_data_json(user_identifier):
    """
    Export complete user data as JSON string.
    
    Args:
        user_identifier (str): User email or ID
        
    Returns:
        str: JSON string of user data
    """
    user_data = inspect_user(user_identifier)
    
    # Convert datetime objects to strings for JSON serialization
    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        return obj
    
    user_data = convert_datetime(user_data)
    return json.dumps(user_data, indent=2, ensure_ascii=False)

# Convenience functions for interactive use
def list_users():
    """Quick function to list all users."""
    users = get_all_users_summary()
    print(f"{'ID':<25} {'Name':<20} {'Email':<30} {'Reviews':<8} {'Saves':<8}")
    print("-" * 100)
    for user in users:
        print(f"{user['id']:<25} {user['name']:<20} {user['email']:<30} {user['total_reviews']:<8} {user['total_saves']:<8}")
    print(f"\nTotal users: {len(users)}")

def show_user(user_identifier):
    """Quick function to show user details."""
    data = inspect_user(user_identifier)
    if 'error' in data:
        print(f"Error: {data['error']}")
        return
    
    basic = data['basic_info']
    activity = data['activity_summary']
    
    print(f"\n👤 User: {basic['name']} ({basic['email']})")
    print(f"   ID: {basic['id']}")
    print(f"   Created: {basic['created_at']}")
    print(f"   Admin: {basic['is_admin']}")
    print(f"\n📊 Activity:")
    print(f"   Reviews: {activity['reviews_count']}")
    print(f"   Saved Recipes: {activity['saved_recipes_count']}")
    print(f"   Verifications: {activity['verifications_count']}")
    print(f"   Review Votes: {activity['review_votes_count']}")

def show_stats():
    """Quick function to show system statistics."""
    stats = get_system_stats()
    if 'error' in stats:
        print(f"Error: {stats['error']}")
        return
    
    print("\n📈 System Statistics")
    print("=" * 30)
    for collection, count in stats['collections'].items():
        print(f"{collection}: {count}")
    
    print(f"\n📅 Recent Activity (7 days):")
    for activity, count in stats['recent_activity'].items():
        print(f"  {activity}: {count}")
    
    print(f"\n🏆 Top Reviewers:")
    for reviewer in stats['top_reviewers']:
        print(f"  {reviewer['user_name']}: {reviewer['review_count']} reviews")
