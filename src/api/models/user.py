"""
User model for the recipe recommendation system.

This module defines the User model and authentication functions.
"""

import bcrypt
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from flask_pymongo import PyMongo
from flask import current_app
import sys
import os
import secrets
import hashlib

# Add the project root to the path to import ingredient_filter
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try to import ingredient_filter, with fallback if not found
try:
    from ingredient_filter import filter_ingredient_stats, filter_ingredients_list
except ImportError:
    # Fallback functions if ingredient_filter is not available
    def filter_ingredient_stats(stats):
        return stats

    def filter_ingredients_list(ingredients):
        return ingredients

# Initialize PyMongo
mongo = PyMongo()

def init_db(app):
    """Initialize the database connection."""
    try:
        mongo.init_app(app)
        # Test the connection first
        with app.app_context():
            # Try to ping the database
            mongo.db.command('ping')
            print("✅ MongoDB connection successful!")
            
            # Create indexes for user collection
            try:
                mongo.db.users.create_index('email', unique=True)
                print("✅ Database indexes created successfully!")
            except Exception as index_error:
                print(f"⚠️ Warning: Could not create indexes: {index_error}")
                
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("⚠️ App will continue without database connection")
        # Don't crash the app, just log the error

def get_user_by_id(user_id):
    """Get a user by ID."""
    try:
        if not mongo.db:
            print("MongoDB connection not initialized")
            return None
        # Handle both string and ObjectId inputs
        if isinstance(user_id, str):
            if ObjectId.is_valid(user_id):
                user_id = ObjectId(user_id)
            else:
                return None
        return mongo.db.users.find_one({'_id': user_id})
    except Exception as e:
        print(f"Error in get_user_by_id: {e}")
        return None

def get_user_by_email(email):
    """Get a user by email."""
    try:
        if not mongo.db:
            print("MongoDB connection not initialized")
            return None
        return mongo.db.users.find_one({'email': email.lower()})
    except Exception as e:
        print(f"Error in get_user_by_email: {e}")
        return None

def create_user(name, email, password):
    """
    Create a new user.

    Args:
        name (str): User's full name
        email (str): User's email address
        password (str): User's password (will be hashed)

    Returns:
        dict: The created user document or None if creation failed
    """
    # Check if user already exists
    if get_user_by_email(email):
        return None

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Create user document
    user = {
        'name': name,
        'email': email.lower(),
        'password': hashed_password,
        'profile_image': None,  # Will store the image ID or path
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'preferences': {
            'favorite_ingredients': [],
            'dietary_restrictions': []
        },
        'saved_recipes': [],
        'dashboard_data': {
            'recent_searches': [],
            'ingredient_history': [],
            'search_stats': {
                'total_searches': 0,
                'most_used_ingredients': {},
                'last_search_date': None
            }
        },
        'analytics': {
            'total_recipe_views': 0,
            'total_recipe_saves': 0,
            'total_reviews_given': 0,
            'cuisine_preferences': {},
            'cooking_streak': {
                'current_streak': 0,
                'longest_streak': 0,
                'last_activity_date': None
            },
            'monthly_activity': {},
            'discovery_stats': {
                'unique_ingredients_tried': 0,
                'recipe_diversity_score': 0
            }
        }
    }

    # Insert user into database
    result = mongo.db.users.insert_one(user)

    # Return the created user
    if result.inserted_id:
        user['_id'] = result.inserted_id
        # Don't return the password
        user.pop('password', None)
        return user

    return None

def verify_password(user, password):
    """
    Verify a user's password.

    Args:
        user (dict): User document from database
        password (str): Password to verify

    Returns:
        bool: True if password is correct, False otherwise
    """
    if not user or 'password' not in user:
        return False

    stored_password = user['password']

    # Check if stored_password is already bytes, if not convert it
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')

    return bcrypt.checkpw(password.encode('utf-8'), stored_password)

def update_user(user_id, update_data):
    """
    Update a user's information.

    Args:
        user_id (str): User ID
        update_data (dict): Data to update

    Returns:
        dict: Updated user document or None if update failed
    """
    # Don't allow updating email or password through this function
    if 'email' in update_data:
        del update_data['email']
    if 'password' in update_data:
        del update_data['password']

    # Add updated_at timestamp
    update_data['updated_at'] = datetime.utcnow()

    # Update user
    result = mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': update_data}
    )

    # Return updated user
    if result.modified_count:
        return get_user_by_id(user_id)

    return None

def change_password(user_id, current_password, new_password):
    """
    Change a user's password.

    Args:
        user_id (str): User ID
        current_password (str): Current password
        new_password (str): New password

    Returns:
        bool: True if password was changed, False otherwise
    """
    # Get user
    user = get_user_by_id(user_id)

    # Verify current password
    if not verify_password(user, current_password):
        return False

    # Hash new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    # Update password
    result = mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {
                'password': hashed_password,
                'updated_at': datetime.utcnow()
            }
        }
    )

    return result.modified_count > 0

def generate_password_reset_token(email):
    """
    Generate a secure password reset token for a user.

    Args:
        email (str): User's email address

    Returns:
        str: Reset token if user exists, None otherwise
    """
    # Get user by email
    user = get_user_by_email(email)
    if not user:
        return None

    # Generate a secure random token
    token = secrets.token_urlsafe(32)

    # Hash the token for storage (security best practice)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Set expiration time (1 hour from now)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Update user with reset token
    result = mongo.db.users.update_one(
        {'_id': user['_id']},
        {
            '$set': {
                'reset_token': token_hash,
                'reset_token_expires': expires_at,
                'updated_at': datetime.utcnow()
            }
        }
    )

    if result.modified_count > 0:
        return token  # Return the unhashed token for the email

    return None

def verify_password_reset_token(token):
    """
    Verify a password reset token and return the user if valid.

    Args:
        token (str): Reset token from the email link

    Returns:
        dict: User document if token is valid, None otherwise
    """
    if not token:
        return None

    # Hash the provided token to match stored hash
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Find user with matching token that hasn't expired
    user = mongo.db.users.find_one({
        'reset_token': token_hash,
        'reset_token_expires': {'$gt': datetime.utcnow()}
    })

    return user

def reset_password_with_token(token, new_password):
    """
    Reset a user's password using a valid reset token.

    Args:
        token (str): Reset token from the email link
        new_password (str): New password to set

    Returns:
        bool: True if password was reset, False otherwise
    """
    # Verify the token
    user = verify_password_reset_token(token)
    if not user:
        return False

    # Hash the new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    # Update password and clear reset token
    result = mongo.db.users.update_one(
        {'_id': user['_id']},
        {
            '$set': {
                'password': hashed_password,
                'updated_at': datetime.utcnow()
            },
            '$unset': {
                'reset_token': '',
                'reset_token_expires': ''
            }
        }
    )

    return result.modified_count > 0

def save_recipe(user_id, recipe_id):
    """
    Save a recipe to a user's saved recipes.

    Args:
        user_id (str): User ID
        recipe_id (str): Recipe ID

    Returns:
        bool: True if recipe was saved, False otherwise
    """
    result = mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$addToSet': {'saved_recipes': recipe_id},
            '$set': {'updated_at': datetime.utcnow()}
        }
    )

    return result.modified_count > 0

def remove_saved_recipe(user_id, recipe_id):
    """
    Remove a recipe from a user's saved recipes.

    Args:
        user_id (str): User ID
        recipe_id (str): Recipe ID

    Returns:
        bool: True if recipe was removed, False otherwise
    """
    result = mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$pull': {'saved_recipes': recipe_id},
            '$set': {'updated_at': datetime.utcnow()}
        }
    )

    return result.modified_count > 0

def save_profile_image(user_id, image_data, filename):
    """
    Save a profile image for a user.

    Args:
        user_id (str): User ID
        image_data (bytes): Binary image data
        filename (str): Original filename

    Returns:
        str: Base64 encoded image data or None if save failed
    """
    import base64

    # Convert binary image data to base64
    base64_image = base64.b64encode(image_data).decode('utf-8')

    # Get file extension
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'

    # Create data URI
    data_uri = f"data:image/{ext};base64,{base64_image}"

    # Update the user's profile_image field
    result = mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {
                'profile_image': data_uri,
                'updated_at': datetime.utcnow()
            }
        }
    )

    if result.modified_count > 0:
        return data_uri

    return None

def get_profile_image(user_id):
    """
    Get a profile image for a user.

    Args:
        user_id (str): User ID

    Returns:
        str: Data URI of the profile image or None if not found
    """
    try:
        user = get_user_by_id(user_id)
        if user and 'profile_image' in user:
            return user['profile_image']
        return None
    except:
        return None

def save_search_history(user_id, search_data):
    """
    Save a search to user's search history.

    Args:
        user_id (str): User ID
        search_data (dict): Search data containing ingredients, timestamp, etc.

    Returns:
        bool: True if search was saved, False otherwise
    """
    try:
        # Get current user to check existing searches
        user = get_user_by_id(user_id)
        if not user:
            return False

        # Get current dashboard data
        dashboard_data = user.get('dashboard_data', {})
        recent_searches = dashboard_data.get('recent_searches', [])
        ingredient_history = dashboard_data.get('ingredient_history', [])
        search_stats = dashboard_data.get('search_stats', {
            'total_searches': 0,
            'most_used_ingredients': {},
            'last_search_date': None
        })

        # Check if this exact search already exists (same ingredients)
        ingredients_list = search_data.get('ingredientsList', [])
        existing_index = -1
        for i, search in enumerate(recent_searches):
            if sorted(search.get('ingredientsList', [])) == sorted(ingredients_list):
                existing_index = i
                break

        # Remove existing search if found
        if existing_index != -1:
            recent_searches.pop(existing_index)

        # Add new search to the beginning
        recent_searches.insert(0, search_data)

        # Keep only the 8 most recent searches
        recent_searches = recent_searches[:8]

        # Update ingredient history
        for ingredient in ingredients_list:
            if ingredient not in ingredient_history:
                ingredient_history.insert(0, ingredient)

        # Keep only the 15 most recent ingredients
        ingredient_history = ingredient_history[:15]

        # Update search stats
        search_stats['total_searches'] += 1
        search_stats['last_search_date'] = search_data.get('timestamp')

        # Update most used ingredients
        for ingredient in ingredients_list:
            if ingredient in search_stats['most_used_ingredients']:
                search_stats['most_used_ingredients'][ingredient] += 1
            else:
                search_stats['most_used_ingredients'][ingredient] = 1

        # Debug logging
        print(f"🔍 DEBUG: Saving search for user {user_id}")
        print(f"🔍 DEBUG: Ingredients: {ingredients_list}")
        print(f"🔍 DEBUG: Updated search stats: {search_stats}")
        print(f"🔍 DEBUG: Most used ingredients: {search_stats['most_used_ingredients']}")

        # Update user document
        result = mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'dashboard_data.recent_searches': recent_searches,
                    'dashboard_data.ingredient_history': ingredient_history,
                    'dashboard_data.search_stats': search_stats,
                    'updated_at': datetime.utcnow()
                }
            }
        )

        print(f"🔍 DEBUG: MongoDB update result - modified_count: {result.modified_count}")
        return result.modified_count > 0

    except Exception as e:
        print(f"Error saving search history: {e}")
        return False

def get_dashboard_data(user_id):
    """
    Get dashboard data for a user.

    Args:
        user_id (str): User ID

    Returns:
        dict: Dashboard data or None if user not found
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return None

        # Get dashboard data with defaults
        dashboard_data = user.get('dashboard_data', {})

        # Ensure all required fields exist
        default_dashboard_data = {
            'recent_searches': [],
            'ingredient_history': [],
            'search_stats': {
                'total_searches': 0,
                'most_used_ingredients': {},
                'last_search_date': None
            }
        }

        # Merge with defaults
        for key, default_value in default_dashboard_data.items():
            if key not in dashboard_data:
                dashboard_data[key] = default_value

        # Apply ingredient filtering to focus on main ingredients
        if 'search_stats' in dashboard_data and 'most_used_ingredients' in dashboard_data['search_stats']:
            dashboard_data['search_stats']['most_used_ingredients'] = filter_ingredient_stats(
                dashboard_data['search_stats']['most_used_ingredients']
            )

        if 'ingredient_history' in dashboard_data:
            dashboard_data['ingredient_history'] = filter_ingredients_list(
                dashboard_data['ingredient_history']
            )

        return dashboard_data

    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        return None

def clear_search_history(user_id):
    """
    Clear all search history for a user.

    Args:
        user_id (str): User ID

    Returns:
        bool: True if history was cleared, False otherwise
    """
    try:
        result = mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'dashboard_data.recent_searches': [],
                    'updated_at': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    except Exception as e:
        print(f"Error clearing search history: {e}")
        return False

def remove_search_from_history(user_id, search_index):
    """
    Remove a specific search from user's search history.

    Args:
        user_id (str): User ID
        search_index (int): Index of search to remove

    Returns:
        bool: True if search was removed, False otherwise
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False

        dashboard_data = user.get('dashboard_data', {})
        recent_searches = dashboard_data.get('recent_searches', [])

        # Check if index is valid
        if 0 <= search_index < len(recent_searches):
            recent_searches.pop(search_index)

            result = mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$set': {
                        'dashboard_data.recent_searches': recent_searches,
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            return result.modified_count > 0

        return False

    except Exception as e:
        print(f"Error removing search from history: {e}")
        return False

def update_user_analytics(user_id, event_type, event_data=None):
    """
    Update user analytics based on their activity.

    Args:
        user_id (str): User ID
        event_type (str): Type of event ('recipe_view', 'recipe_save', 'review_given', 'search')
        event_data (dict): Additional event data

    Returns:
        bool: True if analytics were updated, False otherwise
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False

        # Get current analytics data
        analytics = user.get('analytics', {})

        # Initialize analytics if not present
        if not analytics:
            analytics = {
                'total_recipe_views': 0,
                'total_recipe_saves': 0,
                'total_reviews_given': 0,
                'cuisine_preferences': {},
                'cooking_streak': {
                    'current_streak': 0,
                    'longest_streak': 0,
                    'last_activity_date': None
                },
                'monthly_activity': {},
                'discovery_stats': {
                    'unique_ingredients_tried': 0,
                    'recipe_diversity_score': 0
                }
            }

        # Update based on event type
        current_date = datetime.utcnow()
        today_str = current_date.strftime('%Y-%m-%d')
        month_str = current_date.strftime('%Y-%m')

        if event_type == 'recipe_view':
            analytics['total_recipe_views'] += 1

        elif event_type == 'recipe_save':
            analytics['total_recipe_saves'] += 1

        elif event_type == 'review_given':
            analytics['total_reviews_given'] += 1

        elif event_type == 'search':
            # Update ingredient discovery stats
            if event_data and 'ingredients' in event_data:
                ingredients = event_data['ingredients']
                # Track unique ingredients tried
                existing_ingredients = set()
                dashboard_data = user.get('dashboard_data', {})
                search_stats = dashboard_data.get('search_stats', {})
                most_used = search_stats.get('most_used_ingredients', {})
                existing_ingredients.update(most_used.keys())

                new_ingredients = set(ingredients) - existing_ingredients
                analytics['discovery_stats']['unique_ingredients_tried'] += len(new_ingredients)

        # Update cuisine preferences if provided
        if event_data and 'cuisine' in event_data:
            cuisine = event_data['cuisine']
            if cuisine in analytics['cuisine_preferences']:
                analytics['cuisine_preferences'][cuisine] += 1
            else:
                analytics['cuisine_preferences'][cuisine] = 1

        # Update monthly activity
        if month_str in analytics['monthly_activity']:
            analytics['monthly_activity'][month_str] += 1
        else:
            analytics['monthly_activity'][month_str] = 1

        # Update cooking streak
        last_activity = analytics['cooking_streak'].get('last_activity_date')
        if last_activity:
            last_date = datetime.fromisoformat(last_activity) if isinstance(last_activity, str) else last_activity
            days_diff = (current_date - last_date).days

            if days_diff == 1:
                # Consecutive day
                analytics['cooking_streak']['current_streak'] += 1
            elif days_diff > 1:
                # Streak broken
                analytics['cooking_streak']['current_streak'] = 1
            # Same day, don't change streak
        else:
            # First activity
            analytics['cooking_streak']['current_streak'] = 1

        # Update longest streak
        current_streak = analytics['cooking_streak']['current_streak']
        longest_streak = analytics['cooking_streak']['longest_streak']
        if current_streak > longest_streak:
            analytics['cooking_streak']['longest_streak'] = current_streak

        analytics['cooking_streak']['last_activity_date'] = current_date.isoformat()

        # Update user document
        result = mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'analytics': analytics,
                    'updated_at': datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    except Exception as e:
        print(f"🔍 DEBUG: Error updating user analytics: {e}")
        print(f"🔍 DEBUG: Error type: {type(e)}")
        import traceback
        print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        return False

def get_user_analytics(user_id):
    """
    Get analytics data for a user.

    Args:
        user_id (str): User ID

    Returns:
        dict: User analytics data or None if user not found
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return None

        analytics = user.get('analytics', {})
        dashboard_data = user.get('dashboard_data', {})

        # Apply ingredient filtering to focus on main ingredients
        filtered_favorite_ingredients = filter_ingredient_stats(
            dashboard_data.get('search_stats', {}).get('most_used_ingredients', {})
        )

        # Combine analytics with dashboard data for comprehensive view
        combined_analytics = {
            'personal_stats': {
                'total_searches': dashboard_data.get('search_stats', {}).get('total_searches', 0),
                'total_recipe_views': analytics.get('total_recipe_views', 0),
                'total_recipe_saves': analytics.get('total_recipe_saves', 0),
                'total_reviews_given': analytics.get('total_reviews_given', 0),
                'unique_ingredients_tried': analytics.get('discovery_stats', {}).get('unique_ingredients_tried', 0)
            },
            'favorite_ingredients': filtered_favorite_ingredients,
            'cuisine_preferences': analytics.get('cuisine_preferences', {}),
            'cooking_streak': analytics.get('cooking_streak', {
                'current_streak': 0,
                'longest_streak': 0,
                'last_activity_date': None
            }),
            'monthly_activity': analytics.get('monthly_activity', {}),
            'recent_searches': dashboard_data.get('recent_searches', [])
        }

        return combined_analytics

    except Exception as e:
        print(f"Error getting user analytics: {e}")
        return None


