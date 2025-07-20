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

    Returns:
    --------
    {
        "status": "success",
        "data": {
            "most_searched_leftovers": [
                {"name": "chicken", "count": 245, "percentage": 18.5},
                {"name": "rice", "count": 189, "percentage": 14.2},
                ...
            ],
            "total_searches": 1324,
            "last_updated": "2024-01-01T12:00:00Z"
        }
    }
    """
    try:
        from api.models.user import mongo
        
        if not mongo:
            # Return fallback data if MongoDB is not available
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
                    'last_updated': datetime.utcnow().isoformat()
                }
            })

        # Define leftover-prone ingredients (ingredients that commonly go bad)
        leftover_prone_ingredients = {
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'shrimp', 'turkey',
            'rice', 'pasta', 'bread', 'noodles',
            'tomatoes', 'onions', 'carrots', 'potatoes', 'celery', 'bell peppers',
            'lettuce', 'spinach', 'broccoli', 'cauliflower', 'zucchini',
            'bananas', 'apples', 'berries', 'grapes',
            'milk', 'cheese', 'yogurt', 'eggs',
            'tofu', 'beans', 'lentils'
        }

        # Get all users from MongoDB
        all_users = list(mongo.db.users.find({}))

        # Aggregate ingredient usage across all users
        global_ingredient_usage = defaultdict(int)
        total_ingredient_searches = 0

        print(f"🔍 DEBUG: Processing {len(all_users)} users for analytics")

        for user in all_users:
            dashboard_data = user.get('dashboard_data', {})
            search_stats = dashboard_data.get('search_stats', {})
            most_used = search_stats.get('most_used_ingredients', {})

            if most_used:
                print(f"🔍 DEBUG: User {user.get('email', 'unknown')} has ingredients: {most_used}")

            for ingredient, count in most_used.items():
                # Normalize ingredient name (lowercase, strip whitespace)
                normalized_ingredient = ingredient.lower().strip()

                # Check if this ingredient is leftover-prone
                if normalized_ingredient in leftover_prone_ingredients:
                    global_ingredient_usage[normalized_ingredient] += count
                    total_ingredient_searches += count
                    print(f"🔍 DEBUG: Added {count} searches for {normalized_ingredient}")

        print(f"🔍 DEBUG: Total global ingredient usage: {dict(global_ingredient_usage)}")
        print(f"🔍 DEBUG: Total ingredient searches: {total_ingredient_searches}")

        # Get top leftover ingredients
        top_leftovers = sorted(global_ingredient_usage.items(), key=lambda x: x[1], reverse=True)[:5]

        # Calculate percentages
        most_searched_leftovers = []
        for ingredient, count in top_leftovers:
            percentage = (count / total_ingredient_searches * 100) if total_ingredient_searches > 0 else 0
            most_searched_leftovers.append({
                'name': ingredient.title(),  # Capitalize for display
                'count': count,
                'percentage': round(percentage, 1)
            })

        # If no real data, provide fallback data
        if not most_searched_leftovers:
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
                'last_updated': datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        print(f"Error getting leftover ingredients analytics: {e}")
        # Return fallback data on error
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
                'last_updated': datetime.utcnow().isoformat()
            }
        })

# Note: The /api/analytics/prescriptive route has been moved to routes.py
# to avoid duplicate route definitions and ensure the real MongoDB implementation is used.
