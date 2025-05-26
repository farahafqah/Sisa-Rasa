"""
Recipe model for the recipe recommendation system.

This module defines the Recipe model and related functions.
"""

from bson.objectid import ObjectId
from datetime import datetime
from flask import current_app
from api.models.user import mongo

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
