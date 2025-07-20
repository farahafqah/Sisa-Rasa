"""
Recipe model for the recipe recommendation system.

This module defines the Recipe model and related functions.
"""

from bson.objectid import ObjectId
from datetime import datetime
from flask import current_app
from api.models.user import mongo
import uuid

def get_recipe_by_id(recipe_id):
    """
    Get a recipe by ID from MongoDB.
    
    Args:
        recipe_id (str): Recipe ID
        
    Returns:
        dict: Recipe document or None if not found
    """
    try:
        return mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})
    except:
        return None

def get_recipe_by_original_id(original_id):
    """
    Get a recipe by its original ID from the dataset.
    
    Args:
        original_id (str): Original recipe ID from the dataset
        
    Returns:
        dict: Recipe document or None if not found
    """
    return mongo.db.recipes.find_one({'original_id': original_id})

def save_recipe_to_db(recipe_data):
    """
    Save a recipe to the database.
    
    Args:
        recipe_data (dict): Recipe data to save
        
    Returns:
        str: ID of the saved recipe or None if save failed
    """
    # Check if recipe already exists by original_id
    existing_recipe = get_recipe_by_original_id(recipe_data['original_id'])
    
    if existing_recipe:
        return str(existing_recipe['_id'])
    
    # Add timestamps
    recipe_data['created_at'] = datetime.utcnow()
    recipe_data['updated_at'] = datetime.utcnow()
    
    # Insert recipe into database
    result = mongo.db.recipes.insert_one(recipe_data)
    
    # Return the ID of the inserted recipe
    if result.inserted_id:
        return str(result.inserted_id)
    
    return None

def get_saved_recipes_for_user(user_id):
    """
    Get all recipes saved by a user.
    
    Args:
        user_id (str): User ID
        
    Returns:
        list: List of recipe documents
    """
    from api.models.user import get_user_by_id
    
    # Get user
    user = get_user_by_id(user_id)
    
    if not user or 'saved_recipes' not in user:
        return []
    
    # Get recipe IDs
    recipe_ids = user['saved_recipes']
    
    if not recipe_ids:
        return []
    
    # Convert string IDs to ObjectId
    object_ids = []
    for recipe_id in recipe_ids:
        try:
            object_ids.append(ObjectId(recipe_id))
        except:
            # Skip invalid IDs
            continue
    
    if not object_ids:
        return []
    
    # Get recipes
    recipes = list(mongo.db.recipes.find({'_id': {'$in': object_ids}}))
    
    return recipes

def save_recipe_for_user(user_id, recipe_data):
    """
    Save a recipe for a user.
    
    Args:
        user_id (str): User ID
        recipe_data (dict): Recipe data to save
        
    Returns:
        bool: True if recipe was saved, False otherwise
    """
    from api.models.user import save_recipe
    
    # First save the recipe to the database
    recipe_id = save_recipe_to_db(recipe_data)
    
    if not recipe_id:
        return False
    
    # Then save the recipe ID to the user's saved recipes
    return save_recipe(user_id, recipe_id)

def remove_saved_recipe_for_user(user_id, recipe_id):
    """
    Remove a recipe from a user's saved recipes.
    
    Args:
        user_id (str): User ID
        recipe_id (str): Recipe ID
        
    Returns:
        bool: True if recipe was removed, False otherwise
    """
    from api.models.user import remove_saved_recipe
    
    return remove_saved_recipe(user_id, recipe_id)


# ==================== COMMUNITY RECIPE FUNCTIONS ====================

def create_community_recipe(user_id, recipe_data):
    """
    Create a new community-contributed recipe.

    Args:
        user_id (str): ID of the user contributing the recipe
        recipe_data (dict): Recipe data including name, ingredients, instructions, etc.

    Returns:
        dict: Result with status and recipe_id if successful
    """
    try:
        # Generate a unique original_id for community recipes
        community_recipe_id = f"community_{uuid.uuid4().hex[:12]}"

        # Prepare the recipe document
        recipe_doc = {
            'original_id': community_recipe_id,
            'name': recipe_data['name'],
            'ingredients': recipe_data['ingredients'],
            'instructions': recipe_data.get('instructions', []),
            'prep_time': recipe_data.get('prep_time', 30),
            'cook_time': recipe_data.get('cook_time', 45),
            'servings': recipe_data.get('servings', 4),
            'cuisine': recipe_data.get('cuisine', 'International'),
            'difficulty': recipe_data.get('difficulty', 'Medium'),
            'description': recipe_data.get('description', ''),
            'image_url': recipe_data.get('image_url', None),  # Recipe image URL

            # Community-specific fields
            'is_community_recipe': True,
            'contributed_by': ObjectId(user_id),
            'submission_status': 'approved',  # Auto-approve for now, can be changed to 'pending'
            'submission_date': datetime.utcnow(),
            'approval_date': datetime.utcnow(),  # Auto-approve
            'approved_by': None,

            # Standard fields
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),

            # Initialize rating data
            'rating_data': {
                'average_rating': 0.0,
                'total_reviews': 0,
                'rating_distribution': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0},
                'last_updated': datetime.utcnow()
            }
        }

        # Insert the recipe
        result = mongo.db.recipes.insert_one(recipe_doc)

        if result.inserted_id:
            return {
                'status': 'success',
                'message': 'Recipe shared successfully!',
                'recipe_id': str(result.inserted_id),
                'original_id': community_recipe_id
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to save recipe'
            }

    except Exception as e:
        print(f"Error creating community recipe: {e}")
        return {
            'status': 'error',
            'message': 'An error occurred while saving the recipe'
        }


def get_community_recipes(limit=20, skip=0, status='approved'):
    """
    Get community recipes with pagination.

    Args:
        limit (int): Number of recipes to return
        skip (int): Number of recipes to skip
        status (str): Recipe status filter ('approved', 'pending', 'all')

    Returns:
        list: List of community recipes
    """
    try:
        # Build query
        query = {'is_community_recipe': True}
        if status != 'all':
            query['submission_status'] = status

        # Get recipes with user information
        pipeline = [
            {'$match': query},
            {'$sort': {'submission_date': -1}},
            {'$skip': skip},
            {'$limit': limit},
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

        recipes = list(mongo.db.recipes.aggregate(pipeline))

        # Convert ObjectId and datetime to string for JSON serialization
        for recipe in recipes:
            recipe['_id'] = str(recipe['_id'])
            if recipe.get('contributor_id'):
                recipe['contributor_id'] = str(recipe['contributor_id'])
                # Also set contributed_by for frontend compatibility
                recipe['contributed_by'] = str(recipe['contributor_id'])

            # Convert datetime fields to ISO format strings
            datetime_fields = ['submission_date', 'created_at', 'updated_at']
            for field in datetime_fields:
                if recipe.get(field):
                    recipe[field] = recipe[field].isoformat()

        return recipes

    except Exception as e:
        print(f"Error getting community recipes: {e}")
        return []


def get_user_community_recipes(user_id, limit=20, skip=0):
    """
    Get recipes contributed by a specific user.

    Args:
        user_id (str): User ID
        limit (int): Number of recipes to return
        skip (int): Number of recipes to skip

    Returns:
        list: List of user's community recipes
    """
    try:
        query = {
            'is_community_recipe': True,
            'contributed_by': ObjectId(user_id)
        }

        recipes = list(mongo.db.recipes.find(query)
                      .sort('submission_date', -1)
                      .skip(skip)
                      .limit(limit))

        # Convert ObjectId and datetime to string for JSON serialization
        for recipe in recipes:
            recipe['_id'] = str(recipe['_id'])
            recipe['contributed_by'] = str(recipe['contributed_by'])

            # Convert datetime fields to ISO format strings
            datetime_fields = ['submission_date', 'created_at', 'updated_at']
            for field in datetime_fields:
                if recipe.get(field):
                    recipe[field] = recipe[field].isoformat()

        return recipes

    except Exception as e:
        print(f"Error getting user community recipes: {e}")
        return []


def update_recipe_status(recipe_id, status):
    """
    Update the status of a community recipe (for moderation).

    Args:
        recipe_id (str): Recipe ID
        status (str): New status ('approved', 'rejected', 'pending')

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        update_data = {
            'submission_status': status,
            'updated_at': datetime.utcnow()
        }

        if status == 'approved':
            update_data['approval_date'] = datetime.utcnow()

        result = mongo.db.recipes.update_one(
            {'_id': ObjectId(recipe_id)},
            {'$set': update_data}
        )

        return result.modified_count > 0

    except Exception as e:
        print(f"Error updating recipe status: {e}")
        return False


def get_community_recipe_stats():
    """
    Get statistics about community recipes.

    Returns:
        dict: Statistics including total recipes, pending approval, etc.
    """
    try:
        pipeline = [
            {'$match': {'is_community_recipe': True}},
            {
                '$group': {
                    '_id': '$submission_status',
                    'count': {'$sum': 1}
                }
            }
        ]

        status_counts = list(mongo.db.recipes.aggregate(pipeline))

        stats = {
            'total': 0,
            'approved': 0,
            'pending': 0,
            'rejected': 0
        }

        for item in status_counts:
            status = item['_id']
            count = item['count']
            stats['total'] += count
            if status in stats:
                stats[status] = count

        return stats

    except Exception as e:
        print(f"Error getting community recipe stats: {e}")
        return {'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0}


def get_community_recipe_by_id(recipe_id, user_id=None):
    """
    Get a specific community recipe by ID.

    Args:
        recipe_id (str): Recipe ID (ObjectId or original_id)
        user_id (str, optional): User ID for ownership verification

    Returns:
        dict: Recipe data or None if not found
    """
    try:
        # Build query to find recipe by either _id or original_id
        query = {
            'is_community_recipe': True,
            '$or': [
                {'_id': ObjectId(recipe_id) if ObjectId.is_valid(recipe_id) else None},
                {'original_id': recipe_id}
            ]
        }

        # If user_id provided, also check ownership
        if user_id:
            query['contributed_by'] = ObjectId(user_id)

        recipe = mongo.db.recipes.find_one(query)

        if recipe:
            # Convert ObjectId to string for JSON serialization
            recipe['_id'] = str(recipe['_id'])
            recipe['contributed_by'] = str(recipe['contributed_by'])

            # Convert datetime fields to ISO format strings
            datetime_fields = ['submission_date', 'created_at', 'updated_at', 'approval_date']
            for field in datetime_fields:
                if recipe.get(field):
                    recipe[field] = recipe[field].isoformat()

            # Handle rating_data datetime
            if recipe.get('rating_data', {}).get('last_updated'):
                recipe['rating_data']['last_updated'] = recipe['rating_data']['last_updated'].isoformat()

            return recipe

        return None

    except Exception as e:
        print(f"Error getting community recipe by ID: {e}")
        return None





def delete_community_recipe(recipe_id, user_id):
    """
    Delete a community recipe.

    Args:
        recipe_id (str): Recipe ID (ObjectId or original_id)
        user_id (str): User ID (must be the recipe owner)

    Returns:
        dict: Result with status and message
    """
    try:
        # First verify the recipe exists and user owns it
        existing_recipe = get_community_recipe_by_id(recipe_id, user_id)
        if not existing_recipe:
            return {
                'status': 'error',
                'message': 'Recipe not found or you do not have permission to delete it'
            }

        # Delete the recipe
        result = mongo.db.recipes.delete_one({
            'is_community_recipe': True,
            'contributed_by': ObjectId(user_id),
            '$or': [
                {'_id': ObjectId(recipe_id) if ObjectId.is_valid(recipe_id) else None},
                {'original_id': recipe_id}
            ]
        })

        if result.deleted_count > 0:
            # Also delete related data (reviews, verifications, etc.)
            _cleanup_recipe_related_data(recipe_id)

            # Refresh KNN system to reflect changes
            refresh_knn_system()

            return {
                'status': 'success',
                'message': 'Recipe deleted successfully!',
                'recipe_id': recipe_id
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to delete recipe'
            }

    except Exception as e:
        print(f"Error deleting community recipe: {e}")
        return {
            'status': 'error',
            'message': 'An error occurred while deleting the recipe'
        }


def _cleanup_recipe_related_data(recipe_id):
    """
    Clean up related data when a recipe is deleted.

    Args:
        recipe_id (str): Recipe ID
    """
    try:
        # Delete reviews
        mongo.db.recipe_reviews.delete_many({'recipe_id': recipe_id})

        # Delete verifications
        mongo.db.recipe_verifications.delete_many({'recipe_id': recipe_id})

        # Remove from user saved recipes
        mongo.db.users.update_many(
            {},
            {'$pull': {'saved_recipes': recipe_id}}
        )

        print(f"Cleaned up related data for recipe {recipe_id}")

    except Exception as e:
        print(f"Error cleaning up recipe related data: {e}")


def refresh_knn_system():
    """
    Refresh the KNN recommendation system to reflect recipe changes.
    This should be called after recipe updates or deletions.
    """
    try:
        # Import here to avoid circular imports
        from flask import current_app

        # Check if the app has a recommender instance
        if hasattr(current_app, 'recommender'):
            print("Refreshing KNN recommendation system...")

            # Reload recipes from database
            recipes_file = 'data/clean_recipes.json'
            current_app.recommender.knn_recommender.load_recipes(recipes_file)

            # Reinitialize the hybrid system components
            current_app.recommender._initialize_content_based_filtering()
            current_app.recommender._initialize_popularity_scores()

            print("KNN system refreshed successfully")
            return True
        else:
            print("No recommender instance found in app context")
            return False

    except Exception as e:
        print(f"Error refreshing KNN system: {e}")
        return False
