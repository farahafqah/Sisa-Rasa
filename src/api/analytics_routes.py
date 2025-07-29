"""
Analytics API Routes for Recipe Recommender

This module defines the analytics API routes for the recipe recommendation system.
"""

from flask import jsonify, current_app, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from collections import defaultdict
from datetime import datetime

# Create a blueprint for analytics routes
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/analytics/leftover-ingredients', methods=['GET'])
def get_leftover_ingredients_analytics():
    """
    Get analytics for most searched leftover-prone ingredients.
    """
    try:
        from api.models.user import mongo

        print("🔍 DEBUG: Starting leftover ingredients analytics...")
        print(f"🔍 DEBUG: Current app context: {current_app}")
        print(f"🔍 DEBUG: MongoDB instance: {mongo}")

        # Ensure we're in a Flask application context
        if not current_app:
            print("❌ No Flask application context available")
            return get_fallback_leftover_data()

        # Check MongoDB connection
        if mongo is None:
            print("⚠️ MongoDB instance is None, using fallback data")
            return get_fallback_leftover_data()

        # Test MongoDB connection explicitly
        try:
            with current_app.app_context():
                # Test the connection
                result = mongo.db.command('ping')
                print(f"✅ MongoDB ping successful: {result}")
        except Exception as conn_error:
            print(f"❌ MongoDB connection test failed: {conn_error}")
            return get_fallback_leftover_data()

        # Define leftover-prone ingredients
        leftover_prone_ingredients = {
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'shrimp', 'turkey',
            'rice', 'pasta', 'bread', 'noodles',
            'tomatoes', 'onions', 'carrots', 'potatoes', 'celery', 'bell peppers',
            'lettuce', 'spinach', 'broccoli', 'cauliflower', 'zucchini',
            'bananas', 'apples', 'berries', 'grapes',
            'milk', 'cheese', 'yogurt', 'eggs',
            'tofu', 'beans', 'lentils'
        }

        # Ensure we're in app context for database operations
        with current_app.app_context():
            # Get all users from MongoDB
            all_users = list(mongo.db.users.find({}))
            print(f"🔍 DEBUG: Found {len(all_users)} users in database")

            # Aggregate ingredient usage across all users
            global_ingredient_usage = defaultdict(int)
            total_ingredient_searches = 0

            for user in all_users:
                dashboard_data = user.get('dashboard_data', {})
                search_stats = dashboard_data.get('search_stats', {})
                most_used = search_stats.get('most_used_ingredients', {})

                if most_used:
                    print(f"🔍 DEBUG: User {user.get('email', 'unknown')} has ingredients: {most_used}")

                for ingredient, count in most_used.items():
                    normalized_ingredient = ingredient.lower().strip()
                    if normalized_ingredient in leftover_prone_ingredients:
                        global_ingredient_usage[normalized_ingredient] += count
                        total_ingredient_searches += count

            print(f"🔍 DEBUG: Global ingredient usage: {dict(global_ingredient_usage)}")
            print(f"🔍 DEBUG: Total searches: {total_ingredient_searches}")

            # Get top leftover ingredients
            top_leftovers = sorted(global_ingredient_usage.items(), key=lambda x: x[1], reverse=True)[:5]

            # Calculate percentages
            most_searched_leftovers = []
            for ingredient, count in top_leftovers:
                percentage = (count / total_ingredient_searches * 100) if total_ingredient_searches > 0 else 0
                most_searched_leftovers.append({
                    'name': ingredient.title(),
                    'count': count,
                    'percentage': round(percentage, 1)
                })

            # If no real data, provide fallback
            if not most_searched_leftovers or total_ingredient_searches == 0:
                print("⚠️ No real data found, using fallback")
                return get_fallback_leftover_data()

            print(f"✅ Returning real analytics data: {most_searched_leftovers}")

            return jsonify({
                'status': 'success',
                'data': {
                    'most_searched_leftovers': most_searched_leftovers,
                    'total_searches': total_ingredient_searches,
                    'last_updated': datetime.utcnow().isoformat(),
                    'data_source': 'real_user_data'
                }
            })

    except Exception as e:
        print(f"❌ Error getting leftover ingredients analytics: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return get_fallback_leftover_data()

def get_fallback_leftover_data():
    """Return fallback data when real data is not available"""
    most_searched_leftovers = [
        {'name': 'Chicken', 'count': 245, 'percentage': 22.1},
        {'name': 'Rice', 'count': 189, 'percentage': 17.0},
        {'name': 'Tomatoes', 'count': 167, 'percentage': 15.1},
        {'name': 'Onions', 'count': 134, 'percentage': 12.1},
        {'name': 'Carrots', 'count': 112, 'percentage': 10.1}
    ]
    total_ingredient_searches = sum(item['count'] for item in most_searched_leftovers)
    
    return jsonify({
        'status': 'success',
        'data': {
            'most_searched_leftovers': most_searched_leftovers,
            'total_searches': total_ingredient_searches,
            'last_updated': datetime.utcnow().isoformat(),
            'data_source': 'fallback_data'
        }
    })

# Note: The /api/analytics/prescriptive route has been moved to routes.py
# to avoid duplicate route definitions and ensure the real MongoDB implementation is used.

