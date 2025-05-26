"""
API Routes for Recipe Recommender

This module defines the API routes for the recipe recommendation system.
"""

from flask import jsonify, request, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api.app import app, recommender
from api.decorators import login_required
from api.models.recipe import (
    get_recipe_by_id,
    get_recipe_by_original_id,
    save_recipe_to_db,
    get_saved_recipes_for_user,
    save_recipe_for_user,
    remove_saved_recipe_for_user
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
    create_community_indexes
)

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

@app.route('/', methods=['GET'])
def welcome():
    """Welcome page for the recipe recommendation system."""
    return render_template('welcome.html')

@app.route('/login', methods=['GET'])
def login():
    """Login page for the recipe recommendation system."""
    return render_template('login.html')

@app.route('/signup', methods=['GET'])
def signup():
    """Sign up page for the recipe recommendation system."""
    return render_template('signup.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Dashboard page for the recipe recommendation system."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('dashboard.html')

@app.route('/save-recipe', methods=['GET'])
def save_recipe_page():
    """Saved recipes page for the recipe recommendation system."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('save-recipe.html')

@app.route('/profile', methods=['GET'])
def profile_page():
    """Profile page for the recipe recommendation system."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('profile.html')

@app.route('/search-results', methods=['GET'])
def search_results_page():
    """Search results page for displaying all recommended recipes."""
    # We'll handle authentication in the client-side JavaScript
    return render_template('search-results.html')

@app.route('/test-redirect', methods=['GET'])
def test_redirect_page():
    """Test page for redirect functionality."""
    return render_template('test-redirect.html')

@app.route('/test', methods=['GET'])
def test_page():
    """Test page for static file serving."""
    return render_template('test.html')

@app.route('/test-api', methods=['GET'])
def test_api_page():
    """Test page for API functionality."""
    return render_template('test-api.html')

@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API documentation page."""
    return render_template('api_docs.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
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

@app.route('/api/ingredients', methods=['GET'])
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

@app.route('/api/recommend', methods=['POST'])
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
            explanation=True  # Include explanation for debugging
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

            # If matched_ingredients is empty, calculate it manually
            if not matched_ingredients:
                matched_ingredients = []
                recipe_ingredients = [ing.lower().strip() for ing in recipe['ingredients']]

                for user_ing in ingredients:
                    user_ing_lower = user_ing.lower().strip()
                    for recipe_ing in recipe_ingredients:
                        # Simple matching: check if ingredients are similar
                        if (user_ing_lower in recipe_ing or recipe_ing in user_ing_lower):
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
                'difficulty_estimated': difficulty_estimated
            }

            # Add recommendation explanation if available (for debugging)
            if 'recommendation_explanation' in recipe:
                recipe_data['recommendation_explanation'] = recipe['recommendation_explanation']

            recipes.append(recipe_data)

        # Sort recipes by hybrid score first, then by ingredient match percentage
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

@app.route('/api/recipe/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """
    Get details for a specific recipe.

    Parameters:
    -----------
    recipe_id : str
        ID of the recipe to get
    """
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
            'difficulty_estimated': difficulty == 'Medium'
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

@app.route('/api/recipe/<recipe_id>/save', methods=['POST'])
@jwt_required()
def save_recipe_api(recipe_id):
    """
    Save a recipe to the user's saved recipes.

    Parameters:
    -----------
    recipe_id : str
        ID of the recipe to save
    """
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

@app.route('/api/recipes/saved', methods=['GET'])
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

@app.route('/api/recipe/<recipe_id>/unsave', methods=['POST'])
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
@app.route('/api/dashboard/data', methods=['GET'])
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

@app.route('/api/dashboard/search-history', methods=['POST'])
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

        # Save search history
        success = save_search_history(user_id, data)

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

@app.route('/api/dashboard/search-history/clear', methods=['POST'])
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

@app.route('/api/dashboard/search-history/<int:search_index>', methods=['DELETE'])
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
@app.route('/api/analytics/personal', methods=['GET'])
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

@app.route('/api/analytics/track', methods=['POST'])
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

@app.route('/api/recipe/<recipe_id>/review', methods=['POST'])
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
        print(f"DEBUG: User ID from JWT: {user_id}")

        # Get request data
        data = request.get_json()
        print(f"DEBUG: Request data: {data}")

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
        review_text = data.get('review_text', '').strip()
        print(f"DEBUG: recipe_id={recipe_id}, rating={rating}, review_text='{review_text}'")

        # Validate rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({
                'status': 'error',
                'message': 'Rating must be an integer between 1 and 5'
            }), 400

        print(f"DEBUG: About to call add_recipe_review with user_id={user_id}, recipe_id={recipe_id}, rating={rating}")

        # Add the review
        result = add_recipe_review(user_id, recipe_id, rating, review_text if review_text else None)
        print(f"DEBUG: add_recipe_review result: {result}")

        # Update hybrid recommender with new rating
        if result['status'] == 'success' and recommender:
            try:
                recommender.update_user_preference(user_id, recipe_id, rating)
                print(f"Updated hybrid recommender with rating: user={user_id}, recipe={recipe_id}, rating={rating}")
            except Exception as e:
                print(f"Warning: Could not update hybrid recommender: {e}")

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error adding review: {str(e)}'
        }), 500

@app.route('/api/recipe/<recipe_id>/reviews', methods=['GET'])
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

@app.route('/api/recipe/<recipe_id>/rating-summary', methods=['GET'])
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

@app.route('/api/review/<review_id>/vote', methods=['POST'])
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

@app.route('/api/recipe/<recipe_id>/verify', methods=['POST'])
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
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()

        # Get request data
        data = request.get_json()

        notes = data.get('notes', '').strip() if data else ''
        photo_data = data.get('photo') if data else None

        # Add the verification
        result = add_recipe_verification(user_id, recipe_id, photo_data, notes if notes else None)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error adding verification: {str(e)}'
        }), 500

@app.route('/api/recipe/<recipe_id>/verifications', methods=['GET'])
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

@app.route('/api/verification/<verification_id>/photo', methods=['GET'])
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

@app.route('/api/recipe/<recipe_id>/user-review', methods=['GET'])
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

@app.route('/api/recipe/<recipe_id>/user-verification', methods=['GET'])
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
