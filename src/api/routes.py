"""
API Routes for Recipe Recommender

This module defines the API routes for the recipe recommendation system.
"""

from flask import jsonify, request, render_template, redirect, url_for, current_app, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

# Create a blueprint for the main routes
main_bp = Blueprint('main', __name__)
from api.decorators import login_required
from api.models.recipe import (
    get_recipe_by_id,
    get_recipe_by_original_id,
    save_recipe_to_db,
    get_saved_recipes_for_user,
    save_recipe_for_user,
    remove_saved_recipe_for_user,
    create_community_recipe,
    get_community_recipes,
    get_user_community_recipes,
    update_recipe_status,
    get_community_recipe_stats,
    get_community_recipe_by_id,
    delete_community_recipe
)
from api.models.user import (
    save_search_history,
    get_dashboard_data,
    clear_search_history,
    remove_search_from_history,
    update_user_analytics,
    get_user_analytics
)
from api.models.community import (
    add_recipe_review,
    get_recipe_reviews,
    get_recipe_rating_summary,
    vote_on_review,
    add_recipe_verification,
    get_recipe_verifications,
    get_verification_photo,
    get_user_review_for_recipe,
    get_user_verification_for_recipe,
    create_community_indexes,
    # Social features
    create_community_post,
    get_community_posts,
    update_community_post,
    delete_community_post,
    like_community_post,
    add_post_comment,
    get_post_comments,
    like_comment,
    update_post_comment,
    delete_post_comment,
    get_user_posts
)

# Import ingredient filter for analytics
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import ingredient_filter, with fallback if not found
try:
    from ingredient_filter import filter_ingredients_list, is_main_ingredient
except ImportError:
    # Fallback functions if ingredient_filter is not available
    def filter_ingredients_list(ingredients):
        return ingredients

    def is_main_ingredient(ingredient):
        return True

def _simple_fuzzy_match(str1, str2, threshold=0.6):
    """Simple fuzzy matching for ingredient names."""
    if not str1 or not str2:
        return False

    # Check for common variations (plural/singular)
    variations = [
        (str1, str2),
        (str1.rstrip('s'), str2),
        (str1, str2.rstrip('s')),
        (str1.rstrip('es'), str2),
        (str1, str2.rstrip('es'))
    ]

    for v1, v2 in variations:
        if v1 == v2:
            return True

    # Simple similarity check
    longer = str1 if len(str1) > len(str2) else str2
    shorter = str2 if len(str1) > len(str2) else str1

    if len(longer) == 0:
        return True

    # Count matching characters
    matches = sum(1 for c in shorter if c in longer)
    similarity = matches / len(longer)

    return similarity >= threshold

@main_bp.route('/', methods=['GET'])
def home():
    """Home page for the recipe recommendation system."""
    return render_template('home.html')

@main_bp.route('/welcome', methods=['GET'])
def welcome():
    """Welcome page with analytics and recipe information."""
    return render_template('welcome.html')

@main_bp.route('/login', methods=['GET'])
def login():
    """Login page for the recipe recommendation system."""
    return render_template('login.html')

@main_bp.route('/signup', methods=['GET'])
def signup():
    """Sign up page for the recipe recommendation system."""
    return render_template('signup.html')

@main_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Dashboard page for the recipe recommendation system."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('dashboard.html')

@main_bp.route('/save-recipe', methods=['GET'])
def save_recipe_page():
    """Saved recipes page for the recipe recommendation system."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('save-recipe.html')

@main_bp.route('/profile', methods=['GET'])
def profile_page():
    """Profile page for the recipe recommendation system."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('profile.html')

@main_bp.route('/search-results', methods=['GET'])
def search_results_page():
    """Search results page for displaying all recommended recipes."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('search-results.html')

@main_bp.route('/share-recipe', methods=['GET'])
def share_recipe_page():
    """Share recipe page for community recipe submission."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('share-recipe.html')



@main_bp.route('/community-recipes', methods=['GET'])
def community_recipes_page():
    """Community recipes page for viewing shared recipes."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('community-recipes.html')



@main_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    """Forgot password page for password reset requests."""
    return render_template('forgot-password.html')

@main_bp.route('/reset-password', methods=['GET'])
def reset_password_page():
    """Reset password page for setting new password with token."""
    return render_template('reset-password.html')



@main_bp.route('/api/docs', methods=['GET'])
def api_docs():
    """API documentation page."""
    return render_template('api_docs.html')

@main_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    # Get recommender from current_app
    recommender = getattr(current_app, 'recommender', None)
    if recommender is None:
        return jsonify({
            'status': 'error',
            'message': 'Recommender not initialized'
        }), 500

    return jsonify({
        'status': 'ok',
        'message': 'API is running',
        'recipes_loaded': len(recommender.recipes),
        'ingredients_loaded': len(recommender.ingredient_names)
    })

@main_bp.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    """
    Get all available ingredients.

    Query Parameters:
    ----------------
    search : str, optional
        Search term to filter ingredients by name
    limit : int, optional
        Maximum number of ingredients to return (default: 100)
    """
    # Get recommender from current_app
    recommender = getattr(current_app, 'recommender', None)
    if recommender is None:
        return jsonify({
            'status': 'error',
            'message': 'Recommender not initialized'
        }), 500

    # Get query parameters
    search = request.args.get('search', '').lower()
    limit = int(request.args.get('limit', 100))

    # Filter ingredients by search term
    ingredients = []
    count = 0

    for ingredient_name in recommender.ingredient_names:
        if count >= limit:
            break

        if search and search not in str(ingredient_name).lower():
            continue

        ingredients.append({
            'id': ingredient_name,  # Use the name as ID for clean recipes
            'name': ingredient_name
        })
        count += 1

    return jsonify({
        'status': 'ok',
        'count': len(ingredients),
        'ingredients': ingredients
    })

@main_bp.route('/api/recommend', methods=['POST'])
def recommend_recipes():
    """
    Recommend recipes based on ingredients.

    Request Body:
    ------------
    {
        "ingredients": ["egg", "chicken", "rice"],
        "limit": 10,
        "min_score": 0.05,
        "strict": false
    }

    Returns:
    --------
    {
        "status": "ok",
        "count": 5,
        "recipes": [
            {
                "id": "123",
                "name": "Chicken Fried Rice",
                "ingredients": ["egg", "chicken", "rice", "soy sauce", "onion"],
                "steps": ["Step 1...", "Step 2..."],
                "techniques": ["frying", "boiling"],
                "calorie_level": 1,
                "score": 0.85,
                "ingredient_match_percentage": 75.0
            },
            ...
        ]
    }
    """
    # Get recommender from current_app
    recommender = getattr(current_app, 'recommender', None)
    if recommender is None:
        return jsonify({
            'status': 'error',
            'message': 'Recommender not initialized'
        }), 500

    # Get request body
    data = request.get_json()

    if not data or 'ingredients' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Missing required parameter: ingredients'
        }), 400

    # Get parameters
    ingredients = data.get('ingredients', [])
    limit = int(data.get('limit', 10))
    min_score = float(data.get('min_score', 0.05))
    strict = data.get('strict', False)

    if not ingredients:
        return jsonify({
            'status': 'error',
            'message': 'No ingredients provided'
        }), 400

    try:
        # Create ingredient string from the list
        ingredient_string = ', '.join(ingredients)

        # Get user ID if authenticated (optional for hybrid recommendations)
        user_id = None
        user_preferences = None
        try:
            user_id = get_jwt_identity()
            # You could load user preferences from database here if needed
            # user_preferences = get_user_preferences(user_id)
        except:
            pass  # User not authenticated, continue with anonymous recommendations

        # Get recommendations using the hybrid recommender
        recommendations = recommender.recommend_recipes(
            user_input=ingredient_string,
            user_id=user_id,
            user_preferences=user_preferences,
            num_recommendations=limit,
            explanation=False  # Disable explanation for better performance
        )



        if not recommendations:
            return jsonify({
                'status': 'ok',
                'count': 0,
                'recipes': []
            })

        # Format the response
        recipes = []
        total_user_ingredients = len(ingredients)

        for recipe in recommendations:


            # Get matched ingredients from the recipe (provided by the recommender)
            matched_ingredients = recipe.get('matched_ingredients', [])

            # If matched_ingredients is empty, calculate it manually using enhanced matching
            if not matched_ingredients:
                matched_ingredients = []
                recipe_ingredients = recipe['ingredients']

                # Access the KNN recommender's enhanced matching methods
                knn_recommender = recommender.knn_recommender

                for user_ing in ingredients:
                    user_ing_lower = user_ing.lower().strip()

                    # Use enhanced ingredient matching from KNN recommender
                    best_match, similarity, match_type = knn_recommender._find_best_ingredient_match(
                        user_ing_lower, similarity_threshold=0.6
                    )

                    # Check if the best match is in this recipe's ingredients
                    if best_match and similarity > 0.6:
                        # Normalize recipe ingredients for comparison
                        recipe_ingredients_normalized = [
                            knn_recommender._normalize_ingredient(ing) for ing in recipe_ingredients
                        ]
                        best_match_normalized = knn_recommender._normalize_ingredient(best_match)

                        # Check if the matched ingredient appears in this recipe
                        for recipe_ing, recipe_ing_norm in zip(recipe_ingredients, recipe_ingredients_normalized):
                            if (best_match_normalized in recipe_ing_norm or
                                recipe_ing_norm in best_match_normalized or
                                best_match.lower() in recipe_ing.lower() or
                                recipe_ing.lower() in best_match.lower()):
                                matched_ingredients.append(user_ing)
                                break

            # Calculate ingredient match percentage correctly
            matched_user_ingredients = len(matched_ingredients)
            match_percentage = (matched_user_ingredients / total_user_ingredients * 100) if total_user_ingredients > 0 else 0

            # Filter out recipes with 0% match at the backend level
            if match_percentage <= 0:

                continue

            # Determine if values are estimated (using default values)
            prep_time = recipe.get('prep_time', 30)
            cook_time = recipe.get('cook_time', 45)
            servings = recipe.get('servings', 4)
            cuisine = recipe.get('cuisine', 'International')
            difficulty = recipe.get('difficulty', 'Medium')

            # Check if values are defaults (indicating estimation)
            prep_time_estimated = prep_time == 30
            cook_time_estimated = cook_time == 45
            servings_estimated = servings == 4
            cuisine_estimated = cuisine == 'International'
            difficulty_estimated = difficulty == 'Medium'

            # Get rating data for this recipe
            rating_summary = get_recipe_rating_summary(str(recipe['id']))
            rating_data = None
            verification_data = None

            if rating_summary['status'] == 'success':
                rating_data = {
                    'average_rating': rating_summary['average_rating'],
                    'total_reviews': rating_summary['total_reviews'],
                    'rating_distribution': rating_summary['rating_distribution']
                }

            # Get verification data for this recipe
            from api.models.community import mongo
            verification_count = mongo.db.recipe_verifications.count_documents({'recipe_id': str(recipe['id'])})
            if verification_count > 0:
                verification_data = {
                    'verification_count': verification_count
                }

            # Prepare recipe data
            recipe_data = {
                'id': recipe['id'],
                'name': recipe['name'],
                'ingredients': recipe['ingredients'],
                'matched_ingredients': matched_ingredients,  # Add matched ingredients to response
                'steps': recipe.get('instructions', []),
                'techniques': [],  # Clean recipes don't have techniques field
                'calorie_level': 1,  # Default calorie level for clean recipes
                'score': recipe.get('score', recipe.get('hybrid_score', 0.5)),  # Use hybrid score if available
                'hybrid_score': recipe.get('hybrid_score', 0.5),
                'ingredient_match_percentage': round(match_percentage, 1),
                'prep_time': prep_time,
                'prep_time_estimated': prep_time_estimated,
                'cook_time': cook_time,
                'cook_time_estimated': cook_time_estimated,
                'servings': servings,
                'servings_estimated': servings_estimated,
                'cuisine': cuisine,
                'cuisine_estimated': cuisine_estimated,
                'difficulty': difficulty,
                'difficulty_estimated': difficulty_estimated,
                'rating_data': rating_data,
                'verification_data': verification_data,
                'is_community_recipe': recipe.get('is_community_recipe', False),  # Add community recipe flag
                'contributor_name': recipe.get('contributor_name', None)  # Add contributor name if available
            }



            recipes.append(recipe_data)

        # Sort recipes by hybrid score first (highest first), then by ingredient match percentage
        recipes.sort(key=lambda x: (x['hybrid_score'], x['ingredient_match_percentage']), reverse=True)

        return jsonify({
            'status': 'ok',
            'count': len(recipes),
            'recipes': recipes
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error recommending recipes: {str(e)}'
        }), 500

@main_bp.route('/api/recipe/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """
    Get details for a specific recipe.

    Parameters:
    -----------
    recipe_id : str
        ID of the recipe to get
    """
    # Get recommender from current_app
    recommender = getattr(current_app, 'recommender', None)
    if recommender is None:
        return jsonify({
            'status': 'error',
            'message': 'Recommender not initialized'
        }), 500

    try:
        # Find the recipe by ID
        recipe = None
        for r in recommender.recipes:
            if str(r['id']) == recipe_id:
                recipe = r
                break

        if recipe is None:
            return jsonify({
                'status': 'error',
                'message': f'Recipe not found: {recipe_id}'
            }), 404

        # Format the response for clean recipes
        prep_time = recipe.get('prep_time', 30)
        cook_time = recipe.get('cook_time', 45)
        servings = recipe.get('servings', 4)
        cuisine = recipe.get('cuisine', 'International')
        difficulty = recipe.get('difficulty', 'Medium')

        # Get rating data for this recipe
        rating_summary = get_recipe_rating_summary(str(recipe['id']))
        rating_data = None
        verification_data = None

        if rating_summary['status'] == 'success':
            rating_data = {
                'average_rating': rating_summary['average_rating'],
                'total_reviews': rating_summary['total_reviews'],
                'rating_distribution': rating_summary['rating_distribution']
            }

        # Get verification data for this recipe
        from api.models.community import mongo
        verification_count = mongo.db.recipe_verifications.count_documents({'recipe_id': str(recipe['id'])})
        if verification_count > 0:
            verification_data = {
                'verification_count': verification_count
            }

        recipe_data = {
            'id': recipe['id'],
            'name': recipe['name'],
            'ingredients': recipe['ingredients'],
            'steps': recipe.get('instructions', []),
            'techniques': [],  # Clean recipes don't have techniques
            'calorie_level': 1,  # Default for clean recipes
            'prep_time': prep_time,
            'prep_time_estimated': prep_time == 30,
            'cook_time': cook_time,
            'cook_time_estimated': cook_time == 45,
            'servings': servings,
            'servings_estimated': servings == 4,
            'cuisine': cuisine,
            'cuisine_estimated': cuisine == 'International',
            'difficulty': difficulty,
            'difficulty_estimated': difficulty == 'Medium',
            'rating_data': rating_data,
            'verification_data': verification_data
        }

        return jsonify({
            'status': 'ok',
            'recipe': recipe_data
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting recipe: {str(e)}'
        }), 500

@main_bp.route('/api/recipe/<recipe_id>/save', methods=['POST'])
@jwt_required()
def save_recipe_api(recipe_id):
    """
    Save a recipe to the user's saved recipes.

    Parameters:
    -----------
    recipe_id : str
        ID of the recipe to save
    """
    # Get recommender from current_app
    recommender = getattr(current_app, 'recommender', None)
    if recommender is None:
        return jsonify({
            'status': 'error',
            'message': 'Recommender not initialized'
        }), 500

    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Find the recipe by ID
        recipe = None
        for r in recommender.recipes:
            if str(r['id']) == recipe_id:
                recipe = r
                break

        if recipe is None:
            return jsonify({
                'status': 'error',
                'message': f'Recipe not found: {recipe_id}'
            }), 404

        # Format the recipe data for saving (clean recipes)
        recipe_data = {
            'original_id': recipe['id'],
            'name': recipe['name'],
            'ingredients': recipe['ingredients'],
            'steps': recipe.get('instructions', []),
            'techniques': [],  # Clean recipes don't have techniques
            'calorie_level': 1,  # Default for clean recipes
            'prep_time': recipe.get('prep_time', 30),
            'cook_time': recipe.get('cook_time', 45),
            'servings': recipe.get('servings', 4),
            'cuisine': recipe.get('cuisine', 'International'),
            'difficulty': recipe.get('difficulty', 'Medium')
        }

        # Save the recipe for the user
        success = save_recipe_for_user(user_id, recipe_data)

        if success:
            # Track analytics for recipe save
            try:
                update_user_analytics(user_id, 'recipe_save', {
                    'recipe_id': recipe_id,
                    'recipe_name': recipe['name']
                })
                print(f"Analytics tracked for recipe save: user={user_id}, recipe={recipe_id}")
            except Exception as e:
                print(f"Warning: Could not track recipe save analytics: {e}")

            return jsonify({
                'status': 'success',
                'message': 'Recipe saved successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save recipe'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error saving recipe: {str(e)}'
        }), 500

@main_bp.route('/api/recipes/saved', methods=['GET'])
@jwt_required()
def get_saved_recipes_api():
    """
    Get all recipes saved by the current user.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get saved recipes
        recipes = get_saved_recipes_for_user(user_id)

        # Format the response
        formatted_recipes = []
        for recipe in recipes:
            formatted_recipes.append({
                'id': str(recipe['_id']),
                'name': recipe['name'],
                'ingredients': recipe['ingredients'],
                'steps': recipe['steps'],
                'techniques': recipe['techniques'],
                'calorie_level': recipe['calorie_level'],
                'ingredient_match_percentage': 100  # Always 100% for saved recipes
            })

        return jsonify({
            'status': 'success',
            'count': len(formatted_recipes),
            'recipes': formatted_recipes
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting saved recipes: {str(e)}'
        }), 500

@main_bp.route('/api/recipe/<recipe_id>/unsave', methods=['POST'])
@jwt_required()
def unsave_recipe_api(recipe_id):
    """
    Remove a recipe from the user's saved recipes.

    Parameters:
    -----------
    recipe_id : str
        ID of the recipe to remove
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Remove the recipe from the user's saved recipes
        success = remove_saved_recipe_for_user(user_id, recipe_id)

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Recipe removed from saved recipes'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to remove recipe from saved recipes'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error removing recipe from saved recipes: {str(e)}'
        }), 500

# Dashboard API endpoints
@main_bp.route('/api/dashboard/data', methods=['GET'])
@jwt_required()
def get_dashboard_data_api():
    """
    Get dashboard data for the current user.

    Returns:
    --------
    {
        "status": "success",
        "data": {
            "recent_searches": [...],
            "ingredient_history": [...],
            "search_stats": {...}
        }
    }
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get dashboard data
        dashboard_data = get_dashboard_data(user_id)

        if dashboard_data is None:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        return jsonify({
            'status': 'success',
            'data': dashboard_data
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting dashboard data: {str(e)}'
        }), 500

@main_bp.route('/api/dashboard/search-history', methods=['POST'])
@jwt_required()
def save_search_history_api():
    """
    Save a search to user's search history.

    Request Body:
    ------------
    {
        "ingredients": "egg, rice, chicken",
        "ingredientsList": ["egg", "rice", "chicken"],
        "title": "Search Results",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        # Validate required fields
        if 'ingredientsList' not in data or not data['ingredientsList']:
            return jsonify({
                'status': 'error',
                'message': 'ingredientsList is required'
            }), 400

        # Debug logging
        print(f"🔍 DEBUG: Saving search history for user {user_id}")
        print(f"🔍 DEBUG: Search data: {data}")

        # Save search history
        success = save_search_history(user_id, data)

        print(f"🔍 DEBUG: Search history save success: {success}")

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Search history saved'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save search history'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error saving search history: {str(e)}'
        }), 500

@main_bp.route('/api/dashboard/search-history/clear', methods=['POST'])
@jwt_required()
def clear_search_history_api():
    """
    Clear all search history for the current user.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Clear search history
        success = clear_search_history(user_id)

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Search history cleared'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to clear search history'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error clearing search history: {str(e)}'
        }), 500

@main_bp.route('/api/dashboard/search-history/<int:search_index>', methods=['DELETE'])
@jwt_required()
def remove_search_from_history_api(search_index):
    """
    Remove a specific search from user's search history.

    Parameters:
    -----------
    search_index : int
        Index of the search to remove
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Remove search from history
        success = remove_search_from_history(user_id, search_index)

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Search removed from history'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to remove search from history'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error removing search from history: {str(e)}'
        }), 500

# User Analytics API endpoints
@main_bp.route('/api/analytics/personal', methods=['GET'])
@jwt_required()
def get_personal_analytics():
    """
    Get personal analytics for the current user.

    Returns:
    --------
    {
        "status": "success",
        "analytics": {
            "personal_stats": {...},
            "favorite_ingredients": {...},
            "cuisine_preferences": {...},
            "cooking_streak": {...},
            "monthly_activity": {...},
            "recent_searches": [...]
        }
    }
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get user analytics
        analytics = get_user_analytics(user_id)

        if analytics is None:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        return jsonify({
            'status': 'success',
            'analytics': analytics
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting personal analytics: {str(e)}'
        }), 500

@main_bp.route('/api/analytics/prescriptive', methods=['GET'])
def get_prescriptive_analytics():
    """
    Get prescriptive analytics data for the welcome/dashboard pages.

    Returns:
    --------
    {
        "status": "success",
        "data": {
            "trending_recipes": [...],
            "popular_recipes": [...],
            "leftover_solutions": {...},
            "user_specific": {...} // Only if authenticated
        }
    }
    """
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict, Counter
        import random

        # Import with error handling
        try:
            from api.models.user import mongo
        except ImportError as e:
            print(f"Warning: Could not import mongo: {e}")
            mongo = None

        try:
            from bson.objectid import ObjectId
        except ImportError as e:
            print(f"Warning: Could not import ObjectId: {e}")
            ObjectId = None

        # Get user ID if authenticated (optional)
        user_id = None
        try:
            user_id = get_jwt_identity()
        except:
            pass  # User not authenticated

        # Get trending recipes (recipes with recent high engagement)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        # Get recent reviews and verifications with error handling
        recent_reviews = []
        recent_verifications = []

        if mongo:
            try:
                recent_reviews = list(mongo.db.recipe_reviews.find({
                    'created_at': {'$gte': seven_days_ago}
                }))

                recent_verifications = list(mongo.db.recipe_verifications.find({
                    'created_at': {'$gte': seven_days_ago}
                }))
            except Exception as e:
                print(f"Warning: Could not fetch reviews/verifications: {e}")
                recent_reviews = []
                recent_verifications = []

        # Calculate trending scores
        trending_scores = defaultdict(float)

        # Score based on recent reviews
        for review in recent_reviews:
            recipe_id = review.get('recipe_id')
            rating = review.get('rating', 3)
            # Higher weight for recent reviews, bonus for high ratings
            trending_scores[recipe_id] += (rating / 5.0) * 2.0

        # Score based on recent verifications
        for verification in recent_verifications:
            recipe_id = verification.get('recipe_id')
            trending_scores[recipe_id] += 1.5

        # Get popular recipes using aggregation for better performance
        recipe_ratings = defaultdict(list)
        recipe_verification_counts = defaultdict(int)
        recipe_saves = defaultdict(int)

        if mongo:
            try:
                # Use aggregation to get recipe ratings efficiently
                rating_pipeline = [
                    {'$group': {
                        '_id': '$recipe_id',
                        'ratings': {'$push': '$rating'},
                        'count': {'$sum': 1}
                    }},
                    {'$limit': 1000}  # Limit for performance
                ]
                rating_results = list(mongo.db.recipe_reviews.aggregate(rating_pipeline))

                for result in rating_results:
                    recipe_id = result['_id']
                    recipe_ratings[recipe_id] = result['ratings']

                # Get verification counts efficiently
                verification_pipeline = [
                    {'$group': {
                        '_id': '$recipe_id',
                        'count': {'$sum': 1}
                    }},
                    {'$limit': 1000}  # Limit for performance
                ]
                verification_results = list(mongo.db.recipe_verifications.aggregate(verification_pipeline))

                for result in verification_results:
                    recipe_id = result['_id']
                    recipe_verification_counts[recipe_id] = result['count']

            except Exception as e:
                pass  # Continue with empty data

        # Verification counts are already handled in the aggregation above

        # Get recipe saves data from users
        if mongo:
            try:
                saved_recipes = list(mongo.db.saved_recipes.find())
                for saved_recipe in saved_recipes:
                    recipe_name = saved_recipe.get('name', '')
                    # Try to match saved recipe name to recipe ID
                    if recommender and recommender.recipes:
                        matching_recipe = next((r for r in recommender.recipes if r['name'].lower() == recipe_name.lower()), None)
                        if matching_recipe:
                            recipe_saves[str(matching_recipe['id'])] += 1
            except Exception as e:
                print(f"Warning: Could not fetch saved recipes data: {e}")

        # Calculate average ratings and popularity scores
        popular_scores = {}
        for recipe_id, ratings in recipe_ratings.items():
            avg_rating = sum(ratings) / len(ratings)
            review_count = len(ratings)
            verification_count = recipe_verification_counts.get(recipe_id, 0)
            saves_count = recipe_saves.get(recipe_id, 0)

            # Enhanced popularity score: rating (40%), review count (25%), verifications (20%), saves (15%)
            popularity_score = (
                (avg_rating * 0.4) +
                (min(review_count, 20) * 0.25) +
                (min(verification_count, 10) * 0.2) +
                (min(saves_count, 15) * 0.15)
            )
            popular_scores[recipe_id] = {
                'score': popularity_score,
                'avg_rating': avg_rating,
                'review_count': review_count,
                'verification_count': verification_count,
                'saves': saves_count
            }

        # Get top trending and popular recipe IDs
        top_trending_ids = sorted(trending_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        top_popular_ids = sorted(popular_scores.items(), key=lambda x: x[1]['score'], reverse=True)[:10]

        print(f"🔍 DEBUG: Found {len(popular_scores)} recipes with real ratings/reviews")
        print(f"🔍 DEBUG: Top popular recipe scores: {[(rid, data['score']) for rid, data in top_popular_ids[:3]]}")

        # Get recipe details from recommender
        trending_recipes = []
        popular_recipes = []

        # Get recommender from current_app
        recommender = getattr(current_app, 'recommender', None)
        if recommender and recommender.recipes:
            # Get trending recipes
            for recipe_id, score in top_trending_ids:
                recipe = next((r for r in recommender.recipes if str(r['id']) == str(recipe_id)), None)
                if recipe:
                    recipe_data = {
                        'id': recipe['id'],
                        'name': recipe['name'],
                        'ingredients': recipe['ingredients'][:5],  # First 5 ingredients
                        'description': f"Trending recipe with {score:.1f} engagement score",
                        'trending_score': score,
                        'prep_time': recipe.get('prep_time', 30),
                        'difficulty': recipe.get('difficulty', 'Medium')
                    }
                    trending_recipes.append(recipe_data)

            # Get popular recipes with enhanced data
            for recipe_id, data in top_popular_ids:
                recipe = next((r for r in recommender.recipes if str(r['id']) == str(recipe_id)), None)
                if recipe:
                    # Get latest review for this recipe
                    latest_review = None
                    if mongo:
                        try:
                            latest_review_doc = mongo.db.recipe_reviews.find_one(
                                {'recipe_id': str(recipe_id)},
                                sort=[('created_at', -1)]
                            )
                            if latest_review_doc:
                                latest_review = {
                                    'text': latest_review_doc.get('review_text', ''),
                                    'user_name': latest_review_doc.get('user_name', 'Anonymous'),
                                    'rating': latest_review_doc.get('rating', 5)
                                }
                        except Exception as e:
                            print(f"Warning: Could not fetch latest review for recipe {recipe_id}: {e}")

                    recipe_data = {
                        'id': recipe['id'],
                        'name': recipe['name'],
                        'ingredients': recipe['ingredients'][:5],  # First 5 ingredients
                        'description': f"Highly rated recipe ({data['avg_rating']:.1f}/5 stars) with {data['review_count']} reviews",
                        'avg_rating': data['avg_rating'],
                        'rating': data['avg_rating'],  # Alias for compatibility
                        'review_count': data['review_count'],
                        'total_reviews': data['review_count'],  # Alias for compatibility
                        'verification_count': data['verification_count'],
                        'prep_time': recipe.get('prep_time', 30),
                        'difficulty': recipe.get('difficulty', 'Medium'),
                        'saves': data.get('saves', 0),
                        'total_saves': data.get('saves', 0),  # Alias for compatibility
                        'latest_review': latest_review
                    }
                    popular_recipes.append(recipe_data)

        # Only use fallback data if we have insufficient real data
        print(f"🔍 DEBUG: Real popular recipes found: {len(popular_recipes)}")

        if len(popular_recipes) < 3:
            fallback_popular = [
                {
                    'id': 'popular-1',
                    'name': 'Classic Chicken Curry',
                    'ingredients': ['chicken', 'curry powder', 'coconut milk', 'onion', 'garlic'],
                    'description': 'Highly rated recipe (4.8/5 stars) with 156 reviews',
                    'avg_rating': 4.8,
                    'rating': 4.8,
                    'review_count': 156,
                    'total_reviews': 156,
                    'verification_count': 23,
                    'prep_time': 45,
                    'difficulty': 'Medium',
                    'saves': 234,
                    'total_saves': 234,
                    'latest_review': {
                        'text': 'Amazing flavor! Used leftover chicken and it was perfect.',
                        'user_name': 'Sarah K.',
                        'rating': 5
                    }
                },
                {
                    'id': 'popular-2',
                    'name': 'Perfect Pancakes',
                    'ingredients': ['flour', 'egg', 'milk', 'sugar', 'baking powder'],
                    'description': 'Community favorite (4.9/5 stars) with 203 reviews',
                    'avg_rating': 4.9,
                    'rating': 4.9,
                    'review_count': 203,
                    'total_reviews': 203,
                    'verification_count': 45,
                    'prep_time': 15,
                    'difficulty': 'Easy',
                    'saves': 189,
                    'total_saves': 189,
                    'latest_review': {
                        'text': 'Fluffy and delicious! Kids loved them.',
                        'user_name': 'Mike R.',
                        'rating': 5
                    }
                },
                {
                    'id': 'popular-3',
                    'name': 'Homemade Fried Rice',
                    'ingredients': ['rice', 'egg', 'soy sauce', 'vegetables', 'garlic'],
                    'description': 'Perfect for leftovers (4.6/5 stars) with 142 reviews',
                    'avg_rating': 4.6,
                    'rating': 4.6,
                    'review_count': 142,
                    'total_reviews': 142,
                    'verification_count': 31,
                    'prep_time': 20,
                    'difficulty': 'Easy',
                    'saves': 167,
                    'total_saves': 167,
                    'latest_review': {
                        'text': 'Great way to use leftover rice. So tasty!',
                        'user_name': 'Lisa T.',
                        'rating': 4
                    }
                }
            ]

            # Only add fallback recipes if we need more to reach 3 recipes
            needed_recipes = 3 - len(popular_recipes)
            if needed_recipes > 0:
                popular_recipes.extend(fallback_popular[:needed_recipes])
                print(f"🔍 DEBUG: Added {needed_recipes} fallback recipes to supplement real data")
        else:
            # We have enough real data, just take the top 3
            popular_recipes = popular_recipes[:3]
            print(f"🔍 DEBUG: Using {len(popular_recipes)} real popular recipes")

        # Get leftover solutions data
        leftover_solutions = {}

        # Get most frequently searched ingredients from all users
        all_users = []

        if mongo:
            try:
                all_users = list(mongo.db.users.find({}, {
                    'dashboard_data.search_stats.most_used_ingredients': 1,
                    'dashboard_data.ingredient_history': 1
                }))
            except Exception as e:
                print(f"Warning: Could not fetch user data: {e}")
                all_users = []

        # Aggregate ingredient usage across all users
        global_ingredient_usage = defaultdict(int)
        for user in all_users:
            dashboard_data = user.get('dashboard_data', {})
            search_stats = dashboard_data.get('search_stats', {})
            most_used = search_stats.get('most_used_ingredients', {})

            for ingredient, count in most_used.items():
                global_ingredient_usage[ingredient] += count

        # Get top leftover ingredients
        top_leftovers = sorted(global_ingredient_usage.items(), key=lambda x: x[1], reverse=True)[:10]

        # Common leftover combinations and their recipe suggestions
        leftover_combinations = {
            'rice_egg': {
                'ingredients': ['rice', 'egg'],
                'recipes': ['Fried Rice', 'Egg Rice Bowl', 'Rice Omelette'],
                'description': 'Perfect for using leftover rice'
            },
            'chicken_vegetables': {
                'ingredients': ['chicken', 'vegetables'],
                'recipes': ['Chicken Stir Fry', 'Chicken Soup', 'Chicken Salad'],
                'description': 'Great way to use leftover chicken'
            },
            'bread_milk': {
                'ingredients': ['bread', 'milk'],
                'recipes': ['French Toast', 'Bread Pudding', 'Milk Toast'],
                'description': 'Transform stale bread into delicious meals'
            },
            'pasta_cheese': {
                'ingredients': ['pasta', 'cheese'],
                'recipes': ['Mac and Cheese', 'Pasta Bake', 'Cheesy Pasta'],
                'description': 'Quick pasta solutions'
            }
        }

        leftover_solutions = {
            'top_leftover_ingredients': [{'name': ing, 'usage_count': count} for ing, count in top_leftovers],
            'common_combinations': leftover_combinations
        }

        # User-specific analytics (only if authenticated)
        user_specific = {}
        if user_id and mongo and ObjectId:
            try:
                user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
                if user:
                    dashboard_data = user.get('dashboard_data', {})
                    analytics = user.get('analytics', {})

                    # User's most used ingredients
                    user_ingredients = dashboard_data.get('search_stats', {}).get('most_used_ingredients', {})
                    top_user_ingredients = sorted(user_ingredients.items(), key=lambda x: x[1], reverse=True)[:5]

                    # Recent search patterns
                    recent_searches = dashboard_data.get('recent_searches', [])

                    # Personalized leftover suggestions based on user history
                    user_leftover_suggestions = []
                    for ingredient, count in top_user_ingredients:
                        # Find recipes that use this ingredient
                        if recommender and recommender.recipes:
                            matching_recipes = [
                                r for r in recommender.recipes[:100]  # Limit search
                                if ingredient.lower() in [ing.lower() for ing in r.get('ingredients', [])]
                            ][:3]  # Top 3 matches

                            if matching_recipes:
                                user_leftover_suggestions.append({
                                    'ingredient': ingredient,
                                    'usage_count': count,
                                    'suggested_recipes': [
                                        {
                                            'id': r['id'],
                                            'name': r['name'],
                                            'ingredients': r['ingredients'][:4]  # First 4 ingredients
                                        } for r in matching_recipes
                                    ]
                                })

                    user_specific = {
                        'most_used_ingredients': [{'name': ing, 'count': count} for ing, count in top_user_ingredients],
                        'total_searches': dashboard_data.get('search_stats', {}).get('total_searches', 0),
                        'recent_search_count': len(recent_searches),
                        'personalized_leftover_suggestions': user_leftover_suggestions,
                        'cooking_streak': analytics.get('cooking_streak', {}),
                        'total_recipe_saves': analytics.get('total_recipe_saves', 0)
                    }
            except Exception as e:
                print(f"Error getting user-specific analytics: {e}")
                user_specific = {}

        return jsonify({
            'status': 'success',
            'data': {
                'popular_recipes': popular_recipes,
                'leftover_solutions': leftover_solutions,
                'user_specific': user_specific
            }
        })

    except Exception as e:
        print(f"Error getting prescriptive analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting prescriptive analytics: {str(e)}'
        }), 500

@main_bp.route('/api/analytics/leftover-ingredients', methods=['GET'])
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
        from collections import defaultdict
        from datetime import datetime

        # Define perishable ingredients that commonly become leftovers
        leftover_prone_ingredients = {
            # Fresh vegetables
            'tomato', 'tomatoes', 'lettuce', 'spinach', 'carrot', 'carrots',
            'broccoli', 'cauliflower', 'bell pepper', 'peppers', 'onion', 'onions',
            'celery', 'cucumber', 'zucchini', 'eggplant', 'cabbage', 'kale',
            'mushroom', 'mushrooms', 'potato', 'potatoes', 'sweet potato',

            # Fresh fruits
            'banana', 'bananas', 'apple', 'apples', 'orange', 'oranges',
            'berries', 'strawberry', 'strawberries', 'blueberry', 'blueberries',
            'grapes', 'lemon', 'lemons', 'lime', 'limes', 'avocado', 'avocados',

            # Dairy products
            'milk', 'cheese', 'yogurt', 'yoghurt', 'cream', 'butter',
            'sour cream', 'cottage cheese', 'mozzarella', 'cheddar',

            # Meat and protein
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'shrimp',
            'turkey', 'lamb', 'bacon', 'ham', 'sausage', 'ground beef',
            'chicken breast', 'chicken thigh',

            # Fresh herbs
            'basil', 'cilantro', 'parsley', 'mint', 'dill', 'chives',
            'rosemary', 'thyme', 'oregano', 'sage',

            # Cooked grains and leftovers
            'rice', 'pasta', 'bread', 'noodles', 'quinoa', 'couscous',
            'leftover rice', 'leftover pasta', 'leftover chicken'
        }

        # Get all users' search data
        all_users = []
        if mongo:
            try:
                all_users = list(mongo.db.users.find({}, {
                    'dashboard_data.search_stats.most_used_ingredients': 1,
                    'dashboard_data.ingredient_history': 1,
                    'dashboard_data.recent_searches': 1
                }))
            except Exception as e:
                print(f"Warning: Could not fetch user data: {e}")
                all_users = []

        # Aggregate ingredient usage across all users
        global_ingredient_usage = defaultdict(int)
        total_ingredient_searches = 0

        for user in all_users:
            dashboard_data = user.get('dashboard_data', {})
            search_stats = dashboard_data.get('search_stats', {})
            most_used = search_stats.get('most_used_ingredients', {})

            for ingredient, count in most_used.items():
                # Normalize ingredient name (lowercase, strip whitespace)
                normalized_ingredient = ingredient.lower().strip()

                # Check if this ingredient is leftover-prone
                if normalized_ingredient in leftover_prone_ingredients:
                    global_ingredient_usage[normalized_ingredient] += count
                    total_ingredient_searches += count

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
        return jsonify({
            'status': 'error',
            'message': f'Error getting leftover ingredients analytics: {str(e)}'
        }), 500

@main_bp.route('/api/analytics/track', methods=['POST'])
@jwt_required()
def track_user_event():
    """
    Track a user event for analytics.

    Request Body:
    ------------
    {
        "event_type": "recipe_view|recipe_save|review_given|search",
        "event_data": {
            "recipe_id": "123",
            "cuisine": "italian",
            "ingredients": ["chicken", "rice"]
        }
    }
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        event_type = data.get('event_type')
        event_data = data.get('event_data', {})

        if not event_type:
            return jsonify({
                'status': 'error',
                'message': 'event_type is required'
            }), 400

        # Valid event types
        valid_events = ['recipe_view', 'recipe_save', 'review_given', 'search']
        if event_type not in valid_events:
            return jsonify({
                'status': 'error',
                'message': f'Invalid event_type. Must be one of: {valid_events}'
            }), 400

        # Update user analytics
        success = update_user_analytics(user_id, event_type, event_data)

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Event tracked successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to track event'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error tracking event: {str(e)}'
        }), 500











# ==================== COMMUNITY FEATURES API ROUTES ====================

@main_bp.route('/api/recipe/<recipe_id>/review', methods=['POST'])
@jwt_required()
def add_recipe_review_api(recipe_id):
    """
    Add or update a review for a recipe.

    Request Body:
    ------------
    {
        "rating": 5,
        "review_text": "Great recipe! Easy to follow and delicious."
    }
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Validate user_id
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Invalid authentication token'
            }), 401

        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        # Validate required fields
        if 'rating' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Rating is required'
            }), 400

        rating = data.get('rating')
        # Safely handle review_text - it might be None, empty string, or actual text
        review_text_raw = data.get('review_text')
        if review_text_raw is None:
            review_text = ''
        else:
            review_text = str(review_text_raw).strip()

        # Validate rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError()
        except (ValueError, TypeError):
            print(f"ERROR: Invalid rating value: {rating}")
            return jsonify({
                'status': 'error',
                'message': 'Rating must be an integer between 1 and 5'
            }), 400

        print(f"DEBUG: About to call add_recipe_review with user_id={user_id}, recipe_id={recipe_id}, rating={rating}")

        # Check database connection before proceeding
        try:
            from api.models.user import mongo
            # Test database connection
            mongo.db.command('ping')
            print("DEBUG: Database connection verified")
        except Exception as db_err:
            print(f"ERROR: Database connection failed: {db_err}")
            return jsonify({
                'status': 'error',
                'message': 'Database connection error. Please try again.'
            }), 503

        # Add the review
        result = add_recipe_review(user_id, recipe_id, rating, review_text if review_text else None)
        print(f"DEBUG: add_recipe_review result: {result}")

        # Update hybrid recommender with new rating
        recommender = getattr(current_app, 'recommender', None)
        if result['status'] == 'success' and recommender:
            try:
                recommender.update_user_preference(user_id, recipe_id, rating)
                print(f"DEBUG: Updated hybrid recommender with rating: user={user_id}, recipe={recipe_id}, rating={rating}")
            except Exception as e:
                print(f"WARNING: Could not update hybrid recommender: {e}")

        # Track analytics for review
        if result['status'] == 'success':
            try:
                update_user_analytics(user_id, 'review_given', {
                    'recipe_id': recipe_id,
                    'rating': rating,
                    'has_review_text': bool(review_text)
                })
            except Exception as e:
                pass  # Analytics tracking is not critical

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error adding review: {str(e)}'
        }), 500

@main_bp.route('/api/recipe/<recipe_id>/reviews', methods=['GET'])
def get_recipe_reviews_api(recipe_id):
    """
    Get reviews for a recipe.

    Query Parameters:
    ----------------
    sort_by : str, optional
        Sort criteria ('helpful', 'recent', 'rating_high', 'rating_low')
    limit : int, optional
        Maximum number of reviews to return (default: 50)
    skip : int, optional
        Number of reviews to skip for pagination (default: 0)
    """
    try:
        # Get query parameters
        sort_by = request.args.get('sort_by', 'helpful')
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))

        # Get reviews
        result = get_recipe_reviews(recipe_id, sort_by, limit, skip)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching reviews: {str(e)}'
        }), 500

@main_bp.route('/api/recipe/<recipe_id>/rating-summary', methods=['GET'])
def get_recipe_rating_summary_api(recipe_id):
    """
    Get rating summary for a recipe.
    """
    try:
        result = get_recipe_rating_summary(recipe_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching rating summary: {str(e)}'
        }), 500

@main_bp.route('/api/review/<review_id>/vote', methods=['POST'])
@jwt_required()
def vote_on_review_api(review_id):
    """
    Vote on a review as helpful or unhelpful.

    Request Body:
    ------------
    {
        "vote_type": "helpful"  // or "unhelpful"
    }
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get request data
        data = request.get_json()

        if not data or 'vote_type' not in data:
            return jsonify({
                'status': 'error',
                'message': 'vote_type is required'
            }), 400

        vote_type = data.get('vote_type')

        if vote_type not in ['helpful', 'unhelpful']:
            return jsonify({
                'status': 'error',
                'message': 'vote_type must be "helpful" or "unhelpful"'
            }), 400

        # Vote on review
        result = vote_on_review(user_id, review_id, vote_type)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error voting on review: {str(e)}'
        }), 500

@main_bp.route('/api/recipe/<recipe_id>/verify', methods=['POST'])
@jwt_required()
def add_recipe_verification_api(recipe_id):
    """
    Add a recipe verification (mark as tried and tested).

    Request Body:
    ------------
    {
        "notes": "Turned out great! Added extra garlic.",
        "photo": "data:image/jpeg;base64,..."  // optional base64 encoded image
    }
    """
    import time
    start_time = time.time()

    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()
        print(f"DEBUG: Verification submission started - user_id={user_id}, recipe_id={recipe_id}")

        # Validate user_id
        if not user_id:
            print("ERROR: No user_id found in JWT token")
            return jsonify({
                'status': 'error',
                'message': 'Invalid authentication token'
            }), 401

        # Get request data
        data = request.get_json()
        print(f"DEBUG: Verification request data: {data}")

        # Safely handle notes - it might be None, empty string, or actual text
        notes_raw = data.get('notes') if data else None
        if notes_raw is None:
            notes = ''
        else:
            notes = str(notes_raw).strip()
        photo_data = data.get('photo') if data else None

        # Check database connection before proceeding
        try:
            from api.models.user import mongo
            # Test database connection
            mongo.db.command('ping')
            print("DEBUG: Database connection verified for verification")
        except Exception as db_err:
            print(f"ERROR: Database connection failed for verification: {db_err}")
            return jsonify({
                'status': 'error',
                'message': 'Database connection error. Please try again.'
            }), 503

        # Add the verification
        result = add_recipe_verification(user_id, recipe_id, photo_data, notes if notes else None)
        print(f"DEBUG: add_recipe_verification result: {result}")

        processing_time = time.time() - start_time
        print(f"DEBUG: Verification submission completed in {processing_time:.2f} seconds")

        if result['status'] == 'success':
            return jsonify(result)
        else:
            print(f"ERROR: Verification submission failed: {result}")
            return jsonify(result), 400

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"ERROR: Exception in add_recipe_verification_api after {processing_time:.2f} seconds: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'status': 'error',
            'message': f'Error adding verification: {str(e)}'
        }), 500

@main_bp.route('/api/recipe/<recipe_id>/verifications', methods=['GET'])
def get_recipe_verifications_api(recipe_id):
    """
    Get verifications for a recipe.

    Query Parameters:
    ----------------
    limit : int, optional
        Maximum number of verifications to return (default: 20)
    skip : int, optional
        Number of verifications to skip for pagination (default: 0)
    """
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))

        # Get verifications
        result = get_recipe_verifications(recipe_id, limit, skip)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching verifications: {str(e)}'
        }), 500

@main_bp.route('/api/verification/<verification_id>/photo', methods=['GET'])
def get_verification_photo_api(verification_id):
    """
    Get photo for a verification.
    """
    try:
        result = get_verification_photo(verification_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 404 if 'not found' in result['message'].lower() else 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching verification photo: {str(e)}'
        }), 500

@main_bp.route('/api/recipe/<recipe_id>/user-review', methods=['GET'])
@jwt_required()
def get_user_review_for_recipe_api(recipe_id):
    """
    Get the current user's review for a specific recipe.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        result = get_user_review_for_recipe(user_id, recipe_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching user review: {str(e)}'
        }), 500

@main_bp.route('/api/recipe/<recipe_id>/user-verification', methods=['GET'])
@jwt_required()
def get_user_verification_for_recipe_api(recipe_id):
    """
    Get the current user's verification for a specific recipe.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        result = get_user_verification_for_recipe(user_id, recipe_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching user verification: {str(e)}'
        }), 500


# ==================== COMMUNITY RECIPE ROUTES ====================

@main_bp.route('/api/community/submit-recipe', methods=['POST'])
@jwt_required()
def submit_community_recipe():
    """
    Submit a new community recipe.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()
        print(f"DEBUG: Recipe submission by user ID: {user_id}")

        # Get recipe data from request
        data = request.get_json()
        print(f"DEBUG: Recipe data received: {data}")

        # Validate required fields
        required_fields = ['name', 'ingredients', 'instructions']
        for field in required_fields:
            if not data.get(field):
                print(f"DEBUG: Missing required field: {field}")
                return jsonify({
                    'status': 'error',
                    'message': f'{field.title()} is required'
                }), 400

        # Validate ingredients (should be a list)
        if not isinstance(data['ingredients'], list) or len(data['ingredients']) == 0:
            print(f"DEBUG: Invalid ingredients: {data.get('ingredients')}")
            return jsonify({
                'status': 'error',
                'message': 'At least one ingredient is required'
            }), 400

        # Validate instructions (should be a list)
        if not isinstance(data['instructions'], list) or len(data['instructions']) == 0:
            print(f"DEBUG: Invalid instructions: {data.get('instructions')}")
            return jsonify({
                'status': 'error',
                'message': 'At least one instruction step is required'
            }), 400

        print(f"DEBUG: Creating recipe with name: {data['name']}")
        # Create the recipe
        result = create_community_recipe(user_id, data)
        print(f"DEBUG: Recipe creation result: {result}")

        if result['status'] == 'success':
            # Refresh the KNN system to include the new recipe
            try:
                from api.models.recipe import refresh_knn_system
                refresh_knn_system()
                print("DEBUG: KNN system refreshed after recipe creation")
            except Exception as refresh_error:
                print(f"DEBUG: Failed to refresh KNN system: {refresh_error}")

            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        print(f"ERROR: Exception in recipe submission: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Error submitting recipe: {str(e)}'
        }), 500


@main_bp.route('/api/community/recipes', methods=['GET'])
def get_community_recipes_api():
    """
    Get community recipes with pagination.
    """
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        status = request.args.get('status', 'approved')

        # Limit the maximum number of recipes per request
        limit = min(limit, 100)

        # Get recipes
        recipes = get_community_recipes(limit=limit, skip=skip, status=status)

        return jsonify({
            'status': 'success',
            'count': len(recipes),
            'recipes': recipes
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching community recipes: {str(e)}'
        }), 500


@main_bp.route('/api/community/my-recipes', methods=['GET'])
@jwt_required()
def get_my_community_recipes():
    """
    Get recipes contributed by the current user.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get query parameters
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))

        # Limit the maximum number of recipes per request
        limit = min(limit, 100)

        # Get user's recipes
        recipes = get_user_community_recipes(user_id, limit=limit, skip=skip)

        return jsonify({
            'status': 'success',
            'count': len(recipes),
            'recipes': recipes
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching your recipes: {str(e)}'
        }), 500


@main_bp.route('/api/community/recipe/<recipe_id>', methods=['GET'])
@login_required
def get_community_recipe_details_api(recipe_id):
    """
    Get details of a specific community recipe.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get recipe details
        recipe = get_community_recipe_by_id(recipe_id)

        if not recipe:
            return jsonify({
                'status': 'error',
                'message': 'Recipe not found'
            }), 404

        # Check if user owns this recipe
        recipe['is_owner'] = str(recipe['contributed_by']) == user_id

        return jsonify({
            'status': 'success',
            'recipe': recipe
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching recipe details: {str(e)}'
        }), 500





@main_bp.route('/api/community/recipe/<recipe_id>', methods=['DELETE'])
@login_required
def delete_community_recipe_api(recipe_id):
    """
    Delete a community recipe.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Delete the recipe
        result = delete_community_recipe(recipe_id, user_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error deleting recipe: {str(e)}'
        }), 500





@main_bp.route('/api/community/stats', methods=['GET'])
def get_community_stats():
    """
    Get community recipe statistics.
    """
    try:
        stats = get_community_recipe_stats()

        return jsonify({
            'status': 'success',
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching community stats: {str(e)}'
        }), 500


@main_bp.route('/api/community/moderate/<recipe_id>', methods=['PUT'])
@login_required
def moderate_community_recipe(recipe_id):
    """
    Moderate a community recipe.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get status from request
        data = request.get_json()
        status = data.get('status')

        if status not in ['approved', 'rejected', 'pending']:
            return jsonify({
                'status': 'error',
                'message': 'Invalid status. Must be approved, rejected, or pending'
            }), 400

        # Update recipe status
        success = update_recipe_status(recipe_id, status)

        if success:
            return jsonify({
                'status': 'success',
                'message': f'Recipe status updated to {status}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update recipe status'
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error moderating recipe: {str(e)}'
        }), 500


@main_bp.route('/api/community/recipe/<recipe_id>/details', methods=['GET'])
def get_community_recipe_details(recipe_id):
    """
    Get detailed information about a specific community recipe.
    """
    try:
        from bson.objectid import ObjectId
        from api.models.user import mongo

        # Get recipe details with contributor information
        pipeline = [
            {
                '$match': {
                    '$or': [
                        {'_id': ObjectId(recipe_id) if ObjectId.is_valid(recipe_id) else None},
                        {'original_id': recipe_id}
                    ]
                }
            },
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'contributed_by',
                    'foreignField': '_id',
                    'as': 'contributor'
                }
            },
            {
                '$addFields': {
                    'contributor_name': {'$arrayElemAt': ['$contributor.name', 0]},
                    'contributor_id': {'$arrayElemAt': ['$contributor._id', 0]}
                }
            },
            {
                '$project': {
                    'contributor': 0  # Remove the full contributor array
                }
            }
        ]

        recipe = list(mongo.db.recipes.aggregate(pipeline))

        if not recipe:
            return jsonify({
                'status': 'error',
                'message': 'Recipe not found'
            }), 404

        recipe = recipe[0]

        # Convert ObjectId to string for JSON serialization
        recipe['_id'] = str(recipe['_id'])
        if recipe.get('contributor_id'):
            recipe['contributor_id'] = str(recipe['contributor_id'])
        if recipe.get('contributed_by'):
            recipe['contributed_by'] = str(recipe['contributed_by'])

        return jsonify({
            'status': 'success',
            'recipe': recipe
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching recipe details: {str(e)}'
        }), 500


@main_bp.route('/api/community/recipe/<recipe_id>/comments', methods=['GET'])
def get_recipe_comments(recipe_id):
    """
    Get comments for a specific recipe.
    """
    try:
        from bson.objectid import ObjectId
        from api.models.user import mongo

        # Get query parameters
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))

        # Build query to find recipe
        recipe_query = {
            '$or': [
                {'_id': ObjectId(recipe_id) if ObjectId.is_valid(recipe_id) else None},
                {'original_id': recipe_id}
            ]
        }

        recipe = mongo.db.recipes.find_one(recipe_query)
        if not recipe:
            return jsonify({
                'status': 'error',
                'message': 'Recipe not found'
            }), 404

        # Get comments with user information
        pipeline = [
            {'$match': {'recipe_id': str(recipe['_id'])}},
            {'$sort': {'created_at': -1}},
            {'$skip': skip},
            {'$limit': limit},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user'
                }
            },
            {
                '$addFields': {
                    'user_name': {'$arrayElemAt': ['$user.name', 0]},
                    'user_id_str': {'$arrayElemAt': ['$user._id', 0]}
                }
            },
            {
                '$project': {
                    'user': 0  # Remove the full user array
                }
            }
        ]

        comments = list(mongo.db.recipe_comments.aggregate(pipeline))

        # Convert ObjectId to string
        for comment in comments:
            comment['_id'] = str(comment['_id'])
            if comment.get('user_id_str'):
                comment['user_id_str'] = str(comment['user_id_str'])

        return jsonify({
            'status': 'success',
            'comments': comments,
            'count': len(comments)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching comments: {str(e)}'
        }), 500


@main_bp.route('/api/community/recipe/<recipe_id>/comments', methods=['POST'])
@login_required
def add_recipe_comment(recipe_id):
    """
    Add a comment to a recipe.
    """
    try:
        from bson.objectid import ObjectId
        from datetime import datetime
        from api.models.user import mongo

        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get comment data
        data = request.get_json()
        comment_text = data.get('comment', '').strip()

        if not comment_text:
            return jsonify({
                'status': 'error',
                'message': 'Comment text is required'
            }), 400

        # Verify recipe exists
        recipe_query = {
            '$or': [
                {'_id': ObjectId(recipe_id) if ObjectId.is_valid(recipe_id) else None},
                {'original_id': recipe_id}
            ]
        }

        recipe = mongo.db.recipes.find_one(recipe_query)
        if not recipe:
            return jsonify({
                'status': 'error',
                'message': 'Recipe not found'
            }), 404

        # Create comment document
        comment_doc = {
            'recipe_id': str(recipe['_id']),
            'user_id': ObjectId(user_id),
            'comment': comment_text,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        # Insert comment
        result = mongo.db.recipe_comments.insert_one(comment_doc)

        if result.inserted_id:
            # Get user info for response
            user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

            return jsonify({
                'status': 'success',
                'message': 'Comment added successfully',
                'comment': {
                    '_id': str(result.inserted_id),
                    'recipe_id': str(recipe['_id']),
                    'user_name': user.get('name', 'Anonymous') if user else 'Anonymous',
                    'comment': comment_text,
                    'created_at': comment_doc['created_at'].isoformat()
                }
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to add comment'
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error adding comment: {str(e)}'
        }), 500


@main_bp.route('/api/community/recipe/<recipe_id>/like', methods=['POST'])
@login_required
def toggle_recipe_like(recipe_id):
    """
    Toggle like/unlike for a recipe.
    """
    try:
        from bson.objectid import ObjectId
        from datetime import datetime
        from api.models.user import mongo

        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Verify recipe exists
        recipe_query = {
            '$or': [
                {'_id': ObjectId(recipe_id) if ObjectId.is_valid(recipe_id) else None},
                {'original_id': recipe_id}
            ]
        }

        recipe = mongo.db.recipes.find_one(recipe_query)
        if not recipe:
            return jsonify({
                'status': 'error',
                'message': 'Recipe not found'
            }), 404

        # Check if user already liked this recipe
        existing_like = mongo.db.recipe_likes.find_one({
            'recipe_id': str(recipe['_id']),
            'user_id': ObjectId(user_id)
        })

        if existing_like:
            # Unlike - remove the like
            mongo.db.recipe_likes.delete_one({'_id': existing_like['_id']})
            liked = False
            message = 'Recipe unliked'
        else:
            # Like - add the like
            like_doc = {
                'recipe_id': str(recipe['_id']),
                'user_id': ObjectId(user_id),
                'created_at': datetime.utcnow()
            }
            mongo.db.recipe_likes.insert_one(like_doc)
            liked = True
            message = 'Recipe liked'

        # Get updated like count
        like_count = mongo.db.recipe_likes.count_documents({
            'recipe_id': str(recipe['_id'])
        })

        return jsonify({
            'status': 'success',
            'message': message,
            'liked': liked,
            'like_count': like_count
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error toggling like: {str(e)}'
        }), 500


@main_bp.route('/api/community/recipe/<recipe_id>/likes', methods=['GET'])
def get_recipe_likes(recipe_id):
    """
    Get like count and user's like status for a recipe.
    """
    try:
        from bson.objectid import ObjectId
        from api.models.user import mongo

        # Verify recipe exists
        recipe_query = {
            '$or': [
                {'_id': ObjectId(recipe_id) if ObjectId.is_valid(recipe_id) else None},
                {'original_id': recipe_id}
            ]
        }

        recipe = mongo.db.recipes.find_one(recipe_query)
        if not recipe:
            return jsonify({
                'status': 'error',
                'message': 'Recipe not found'
            }), 404

        # Get like count
        like_count = mongo.db.recipe_likes.count_documents({
            'recipe_id': str(recipe['_id'])
        })

        # Check if current user liked this recipe (if authenticated)
        user_liked = False
        try:
            user_id = get_jwt_identity()
            if user_id:
                user_like = mongo.db.recipe_likes.find_one({
                    'recipe_id': str(recipe['_id']),
                    'user_id': ObjectId(user_id)
                })
                user_liked = bool(user_like)
        except:
            pass  # User not authenticated

        return jsonify({
            'status': 'success',
            'like_count': like_count,
            'user_liked': user_liked
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching likes: {str(e)}'
        }), 500


@main_bp.route('/api/community/upload-image', methods=['POST'])
@jwt_required()
def upload_recipe_image():
    """
    Upload an image for a community recipe.
    """
    try:
        import os
        from werkzeug.utils import secure_filename
        from datetime import datetime

        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided'
            }), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No image file selected'
            }), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Only PNG, JPG, JPEG, and GIF files are allowed.'
            }), 400

        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'recipes')
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{timestamp}_{name}{ext}"

        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # Generate URL for the uploaded image
        image_url = f"/static/uploads/recipes/{unique_filename}"

        return jsonify({
            'status': 'success',
            'message': 'Image uploaded successfully',
            'image_url': image_url,
            'filename': unique_filename
        }), 201

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error uploading image: {str(e)}'
        }), 500


# ==================== SOCIAL COMMUNITY FEATURES API ENDPOINTS ====================

@main_bp.route('/api/community/posts', methods=['POST'])
@login_required
def create_post():
    """
    Create a new community post.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get post data from request
        data = request.get_json()

        # Validate required fields
        if not data or not data.get('content'):
            return jsonify({
                'status': 'error',
                'message': 'Post content is required'
            }), 400

        content = data.get('content', '').strip()
        tags = data.get('tags', [])

        # Create the post
        result = create_community_post(user_id, content, tags)

        if result['status'] == 'success':
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error creating post: {str(e)}'
        }), 500


@main_bp.route('/api/community/posts', methods=['GET'])
def get_posts():
    """
    Get community posts with pagination.
    """
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))

        # Limit the maximum number of posts per request
        limit = min(limit, 100)

        # Get current user ID if authenticated
        user_id = None
        try:
            user_id = get_jwt_identity()
        except:
            pass  # User not authenticated

        # Get posts
        result = get_community_posts(limit=limit, skip=skip, user_id=user_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching posts: {str(e)}'
        }), 500


@main_bp.route('/api/community/posts/<post_id>', methods=['PUT'])
@login_required
def update_post(post_id):
    """
    Update a community post (only by the owner).
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get post data from request
        data = request.get_json()

        # Validate required fields
        if not data or not data.get('content'):
            return jsonify({
                'status': 'error',
                'message': 'Post content is required'
            }), 400

        content = data.get('content', '').strip()
        tags = data.get('tags', [])

        # Update the post
        result = update_community_post(user_id, post_id, content, tags)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error updating post: {str(e)}'
        }), 500


@main_bp.route('/api/community/posts/<post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    """
    Delete a community post (only by the owner).
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Delete the post
        result = delete_community_post(user_id, post_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error deleting post: {str(e)}'
        }), 500


@main_bp.route('/api/community/posts/<post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    """
    Like or unlike a community post.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Like/unlike the post
        result = like_community_post(user_id, post_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error liking post: {str(e)}'
        }), 500


@main_bp.route('/api/community/posts/<post_id>/comments', methods=['POST'])
@login_required
def add_comment(post_id):
    """
    Add a comment to a community post.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get comment data from request
        data = request.get_json()

        # Validate required fields
        if not data or not data.get('content'):
            return jsonify({
                'status': 'error',
                'message': 'Comment content is required'
            }), 400

        content = data.get('content', '').strip()
        parent_comment_id = data.get('parent_comment_id')

        # Add the comment
        result = add_post_comment(user_id, post_id, content, parent_comment_id)

        if result['status'] == 'success':
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error adding comment: {str(e)}'
        }), 500


@main_bp.route('/api/community/posts/<post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """
    Get comments for a community post.
    """
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))

        # Limit the maximum number of comments per request
        limit = min(limit, 100)

        # Get current user ID if authenticated
        user_id = None
        try:
            user_id = get_jwt_identity()
        except:
            pass  # User not authenticated

        # Get comments
        result = get_post_comments(post_id, limit=limit, skip=skip, user_id=user_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching comments: {str(e)}'
        }), 500


@main_bp.route('/api/community/comments/<comment_id>', methods=['PUT'])
@login_required
def update_comment(comment_id):
    """
    Update a comment (only by the owner).
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get comment data from request
        data = request.get_json()

        # Validate required fields
        if not data or not data.get('content'):
            return jsonify({
                'status': 'error',
                'message': 'Comment content is required'
            }), 400

        content = data.get('content', '').strip()

        # Update the comment
        result = update_post_comment(user_id, comment_id, content)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error updating comment: {str(e)}'
        }), 500


@main_bp.route('/api/community/comments/<comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """
    Delete a comment (only by the owner).
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Delete the comment
        result = delete_post_comment(user_id, comment_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error deleting comment: {str(e)}'
        }), 500


@main_bp.route('/api/community/comments/<comment_id>/like', methods=['POST'])
@login_required
def like_comment_api(comment_id):
    """
    Like or unlike a comment.
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Like/unlike the comment
        result = like_comment(user_id, comment_id)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error liking comment: {str(e)}'
        }), 500


@main_bp.route('/api/community/users/<user_id>/posts', methods=['GET'])
def get_user_posts_api(user_id):
    """
    Get posts created by a specific user.
    """
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))

        # Limit the maximum number of posts per request
        limit = min(limit, 100)

        # Get user's posts
        result = get_user_posts(user_id, limit=limit, skip=skip)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching user posts: {str(e)}'
        }), 500
