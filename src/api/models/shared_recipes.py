"""
Shared Recipes Model

This module handles shared recipes for the community page in the SisaRasa application.
"""

from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import os

# MongoDB connection - Use same connection as main application
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client.get_default_database()
recipes_collection = db['recipes']
users_collection = db['users']

def get_user_info(user_id):
    """Get user information for recipes."""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return {
                'user_id': str(user['_id']),
                'user_name': user.get('name', 'Anonymous User'),
                'user_profile_image': user.get('profile_image', None)
            }
        return {
            'user_id': user_id,
            'user_name': 'Anonymous User',
            'user_profile_image': None
        }
    except Exception as e:
        print(f"Error getting user info: {e}")
        return {
            'user_id': user_id,
            'user_name': 'Anonymous User',
            'user_profile_image': None
        }

def get_all_shared_recipes(current_user_id):
    """Get all user-submitted recipes for the community page."""
    try:
        # Find all user-submitted recipes (those with original_id starting with 'user_')
        recipes_cursor = recipes_collection.find({
            'original_id': {'$regex': '^user_'}
        }).sort("created_at", -1)
        
        recipes = []
        
        for recipe in recipes_cursor:
            try:
                # Get user info
                user_info = get_user_info(recipe.get('submitted_by', recipe.get('submitter_id', '')))
                
                # Parse ingredients and instructions if they're strings
                ingredients = recipe.get('ingredients', [])
                if isinstance(ingredients, str):
                    try:
                        import json
                        ingredients = json.loads(ingredients)
                    except:
                        ingredients = [ingredients] if ingredients else []
                
                instructions = recipe.get('instructions', [])
                if isinstance(instructions, str):
                    try:
                        import json
                        instructions = json.loads(instructions)
                    except:
                        instructions = [instructions] if instructions else []
                
                # Handle image field - check both 'image' and 'image_data'
                image_data = recipe.get('image') or recipe.get('image_data', '')

                recipe_data = {
                    'id': str(recipe['_id']),
                    'original_id': recipe.get('original_id', ''),
                    'name': recipe.get('name', 'Untitled Recipe'),
                    'description': recipe.get('description', ''),
                    'cuisine': recipe.get('cuisine', 'Unknown'),
                    'image': image_data,
                    'image_data': image_data,  # Include both for compatibility
                    'ingredients': ingredients,
                    'instructions': instructions,
                    'recipe_details': recipe.get('recipe_details', ''),
                    'prep_time': recipe.get('prep_time', 30),
                    'cook_time': recipe.get('cook_time', 45),
                    'servings': recipe.get('servings', 4),
                    'difficulty': recipe.get('difficulty', 'Medium'),
                    'submitted_by': recipe.get('submitted_by', ''),
                    'created_at': recipe.get('created_at', datetime.utcnow()).isoformat() if isinstance(recipe.get('created_at'), datetime) else str(recipe.get('created_at', '')),
                    # Add user info fields
                    'user_id': user_info.get('user_id', ''),
                    'user_name': user_info.get('user_name', 'Anonymous User'),
                    'username': user_info.get('user_name', 'Anonymous User'),  # Frontend expects 'username'
                    'user_profile_image': user_info.get('user_profile_image', None),
                    'profile_picture': user_info.get('user_profile_image', None)  # Alternative field name
                }
                
                recipes.append(recipe_data)
                
            except Exception as e:
                print(f"Error processing recipe {recipe.get('_id', 'unknown')}: {e}")
                continue
        
        return {
            'status': 'success',
            'recipes': recipes
        }
        
    except Exception as e:
        print(f"Error getting shared recipes: {e}")
        return {
            'status': 'error',
            'message': f'Error getting shared recipes: {str(e)}',
            'recipes': []
        }

def get_shared_recipe_by_id(recipe_id, current_user_id):
    """Get a specific shared recipe by ID."""
    try:
        recipe = recipes_collection.find_one({'_id': ObjectId(recipe_id)})
        
        if not recipe:
            return {
                'status': 'error',
                'message': 'Recipe not found'
            }
        
        # Get user info
        user_info = get_user_info(recipe.get('submitted_by', recipe.get('submitter_id', '')))
        
        # Parse ingredients and instructions if they're strings
        ingredients = recipe.get('ingredients', [])
        if isinstance(ingredients, str):
            try:
                import json
                ingredients = json.loads(ingredients)
            except:
                ingredients = [ingredients] if ingredients else []
        
        instructions = recipe.get('instructions', [])
        if isinstance(instructions, str):
            try:
                import json
                instructions = json.loads(instructions)
            except:
                instructions = [instructions] if instructions else []
        
        # Handle image field - check both 'image' and 'image_data'
        image_data = recipe.get('image') or recipe.get('image_data', '')

        recipe_data = {
            'id': str(recipe['_id']),
            'original_id': recipe.get('original_id', ''),
            'name': recipe.get('name', 'Untitled Recipe'),
            'description': recipe.get('description', ''),
            'cuisine': recipe.get('cuisine', 'Unknown'),
            'image': image_data,
            'image_data': image_data,  # Include both for compatibility
            'ingredients': ingredients,
            'instructions': instructions,
            'recipe_details': recipe.get('recipe_details', ''),
            'prep_time': recipe.get('prep_time', 30),
            'cook_time': recipe.get('cook_time', 45),
            'servings': recipe.get('servings', 4),
            'difficulty': recipe.get('difficulty', 'Medium'),
            'submitted_by': recipe.get('submitted_by', ''),
            'created_at': recipe.get('created_at', datetime.utcnow()).isoformat() if isinstance(recipe.get('created_at'), datetime) else str(recipe.get('created_at', '')),
            # Add user info fields
            'user_id': user_info.get('user_id', ''),
            'user_name': user_info.get('user_name', 'Anonymous User'),
            'username': user_info.get('user_name', 'Anonymous User'),  # Frontend expects 'username'
            'user_profile_image': user_info.get('user_profile_image', None),
            'profile_picture': user_info.get('user_profile_image', None)  # Alternative field name
        }
        
        return {
            'status': 'success',
            'recipe': recipe_data
        }
        
    except Exception as e:
        print(f"Error getting shared recipe: {e}")
        return {
            'status': 'error',
            'message': f'Error getting shared recipe: {str(e)}'
        }

def get_user_shared_recipes(user_id):
    """Get all recipes shared by a specific user."""
    try:
        # Find all recipes submitted by the user
        recipes_cursor = recipes_collection.find({
            'submitted_by': user_id,
            'original_id': {'$regex': '^user_'}
        }).sort("created_at", -1)
        
        recipes = []
        
        for recipe in recipes_cursor:
            try:
                # Parse ingredients and instructions if they're strings
                ingredients = recipe.get('ingredients', [])
                if isinstance(ingredients, str):
                    try:
                        import json
                        ingredients = json.loads(ingredients)
                    except:
                        ingredients = [ingredients] if ingredients else []
                
                instructions = recipe.get('instructions', [])
                if isinstance(instructions, str):
                    try:
                        import json
                        instructions = json.loads(instructions)
                    except:
                        instructions = [instructions] if instructions else []
                
                # Handle image field - check both 'image' and 'image_data'
                image_data = recipe.get('image') or recipe.get('image_data', '')

                recipe_data = {
                    'id': str(recipe['_id']),
                    'original_id': recipe.get('original_id', ''),
                    'name': recipe.get('name', 'Untitled Recipe'),
                    'description': recipe.get('description', ''),
                    'cuisine': recipe.get('cuisine', 'Unknown'),
                    'image': image_data,
                    'image_data': image_data,  # Include both for compatibility
                    'ingredients': ingredients,
                    'instructions': instructions,
                    'recipe_details': recipe.get('recipe_details', ''),
                    'prep_time': recipe.get('prep_time', 30),
                    'cook_time': recipe.get('cook_time', 45),
                    'servings': recipe.get('servings', 4),
                    'difficulty': recipe.get('difficulty', 'Medium'),
                    'submitted_by': recipe.get('submitted_by', ''),
                    'created_at': recipe.get('created_at', datetime.utcnow()).isoformat() if isinstance(recipe.get('created_at'), datetime) else str(recipe.get('created_at', '')),
                }
                
                recipes.append(recipe_data)
                
            except Exception as e:
                print(f"Error processing user recipe {recipe.get('_id', 'unknown')}: {e}")
                continue
        
        return {
            'status': 'success',
            'recipes': recipes
        }
        
    except Exception as e:
        print(f"Error getting user shared recipes: {e}")
        return {
            'status': 'error',
            'message': f'Error getting user shared recipes: {str(e)}',
            'recipes': []
        }

def get_recipe_stats():
    """Get statistics about shared recipes."""
    try:
        total_shared = recipes_collection.count_documents({
            'original_id': {'$regex': '^user_'}
        })
        
        # Get unique users who have shared recipes
        unique_contributors = len(recipes_collection.distinct('submitted_by', {
            'original_id': {'$regex': '^user_'}
        }))
        
        # Get most recent recipes
        recent_recipes = list(recipes_collection.find({
            'original_id': {'$regex': '^user_'}
        }).sort("created_at", -1).limit(5))
        
        return {
            'status': 'success',
            'stats': {
                'total_shared_recipes': total_shared,
                'unique_contributors': unique_contributors,
                'recent_recipes_count': len(recent_recipes)
            }
        }
        
    except Exception as e:
        print(f"Error getting recipe stats: {e}")
        return {
            'status': 'error',
            'message': f'Error getting recipe stats: {str(e)}',
            'stats': {
                'total_shared_recipes': 0,
                'unique_contributors': 0,
                'recent_recipes_count': 0
            }
        }

def get_recipe_details(recipe_id, current_user_id):
    """Get detailed information for a specific shared recipe."""
    try:
        from bson import ObjectId

        # Find the recipe
        recipe = recipes_collection.find_one({'_id': ObjectId(recipe_id)})

        if not recipe:
            return {
                'status': 'error',
                'message': 'Recipe not found'
            }

        # Get user info
        user_info = get_user_info(recipe.get('submitter_id', recipe.get('submitted_by', '')))

        # Format ingredients
        ingredients = recipe.get('ingredients', [])
        if isinstance(ingredients, str):
            try:
                import json
                ingredients = json.loads(ingredients)
            except:
                ingredients = [ingredients] if ingredients else []

        # Format instructions
        instructions = recipe.get('instructions', [])
        if isinstance(instructions, str):
            try:
                import json
                instructions = json.loads(instructions)
            except:
                instructions = [instructions] if instructions else []

        recipe_data = {
            'id': str(recipe['_id']),
            'original_id': recipe.get('original_id', ''),
            'name': recipe.get('name', 'Untitled Recipe'),
            'description': recipe.get('description', ''),
            'cuisine': recipe.get('cuisine', 'Unknown'),
            'image': recipe.get('image') or recipe.get('image_data', ''),
            'image_data': recipe.get('image') or recipe.get('image_data', ''),  # Include both for compatibility
            'ingredients': ingredients,
            'instructions': instructions,
            'prep_time': recipe.get('prep_time', 0),
            'cook_time': recipe.get('cook_time', 0),
            'servings': recipe.get('servings', 1),
            'difficulty': recipe.get('difficulty', 'Medium'),
            'recipe_details': recipe.get('recipe_details', ''),
            'created_at': recipe.get('created_at', datetime.utcnow()).isoformat() if isinstance(recipe.get('created_at'), datetime) else str(recipe.get('created_at', '')),
            **user_info
        }

        return {
            'status': 'success',
            'recipe': recipe_data
        }

    except Exception as e:
        print(f"Error getting recipe details: {e}")
        return {
            'status': 'error',
            'message': f'Error getting recipe details: {str(e)}'
        }

def get_community_recipes_paginated(user_id, limit=20, skip=0, status='all'):
    """Get community recipes with pagination."""
    try:
        # Get all user-shared recipes (no approval filtering needed)
        query = {'original_id': {'$regex': '^user_'}}

        # Get recipes with pagination
        recipes_cursor = recipes_collection.find(query).sort("created_at", -1).skip(skip).limit(limit + 1)
        recipes = list(recipes_cursor)

        # Check if there are more recipes
        has_more = len(recipes) > limit
        if has_more:
            recipes = recipes[:-1]  # Remove the extra recipe

        # Format recipes for frontend
        formatted_recipes = []
        for recipe in recipes:
            user_info = get_user_info(recipe.get('submitter_id', recipe.get('submitted_by', '')))

            # Format ingredients
            ingredients = recipe.get('ingredients', [])
            if isinstance(ingredients, str):
                try:
                    import json
                    ingredients = json.loads(ingredients)
                except:
                    ingredients = [ingredients] if ingredients else []

            # Format instructions
            instructions = recipe.get('instructions', [])
            if isinstance(instructions, str):
                try:
                    import json
                    instructions = json.loads(instructions)
                except:
                    instructions = [instructions] if instructions else []

            recipe_data = {
                'id': str(recipe['_id']),
                'original_id': recipe.get('original_id', ''),
                'name': recipe.get('name', 'Untitled Recipe'),
                'description': recipe.get('description', ''),
                'cuisine': recipe.get('cuisine', 'Unknown'),
                'image': recipe.get('image') or recipe.get('image_data', ''),
                'image_data': recipe.get('image') or recipe.get('image_data', ''),  # Include both for compatibility
                'ingredients': ingredients,
                'instructions': instructions,
                'prep_time': recipe.get('prep_time', 0),
                'cook_time': recipe.get('cook_time', 0),
                'servings': recipe.get('servings', 1),
                'difficulty': recipe.get('difficulty', 'Medium'),
                'created_at': recipe.get('created_at', datetime.utcnow()).isoformat() if isinstance(recipe.get('created_at'), datetime) else str(recipe.get('created_at', '')),
                'rating': recipe.get('rating', 0),
                'reviews_count': recipe.get('reviews_count', 0),
                # Add user info fields
                'user_id': user_info.get('user_id', ''),
                'user_name': user_info.get('user_name', 'Anonymous User'),
                'username': user_info.get('user_name', 'Anonymous User'),  # Frontend expects 'username'
                'user_profile_image': user_info.get('user_profile_image', None),
                'profile_picture': user_info.get('user_profile_image', None)  # Alternative field name
            }
            formatted_recipes.append(recipe_data)

        return {
            'status': 'success',
            'recipes': formatted_recipes,
            'has_more': has_more
        }

    except Exception as e:
        print(f"Error fetching community recipes: {e}")
        return {
            'status': 'error',
            'message': f'Error fetching community recipes: {str(e)}'
        }

def get_recipe_details_with_interactions(recipe_id, current_user_id):
    """Get detailed recipe information including user interactions."""
    try:
        from bson import ObjectId

        # Get basic recipe details
        result = get_recipe_details(recipe_id, current_user_id)
        if result['status'] != 'success':
            return result

        recipe_data = result['recipe']

        # Add interaction data (likes, user's like status)
        recipe_likes_collection = db['recipe_likes']
        recipe_comments_collection = db['recipe_comments']

        # Get like count and user's like status
        like_count = recipe_likes_collection.count_documents({'recipe_id': recipe_id})
        user_liked = recipe_likes_collection.find_one({
            'recipe_id': recipe_id,
            'user_id': current_user_id
        }) is not None

        # Get comment count
        comment_count = recipe_comments_collection.count_documents({'recipe_id': recipe_id})

        recipe_data.update({
            'like_count': like_count,
            'user_liked': user_liked,
            'comment_count': comment_count
        })

        return {
            'status': 'success',
            'recipe': recipe_data
        }

    except Exception as e:
        print(f"Error getting recipe details with interactions: {e}")
        return {
            'status': 'error',
            'message': f'Error getting recipe details: {str(e)}'
        }

def toggle_recipe_like(recipe_id, user_id):
    """Toggle like on a recipe."""
    try:
        recipe_likes_collection = db['recipe_likes']

        # Check if user already liked this recipe
        existing_like = recipe_likes_collection.find_one({
            'recipe_id': recipe_id,
            'user_id': user_id
        })

        if existing_like:
            # Remove like
            recipe_likes_collection.delete_one({'_id': existing_like['_id']})
            liked = False
        else:
            # Add like
            like_data = {
                'recipe_id': recipe_id,
                'user_id': user_id,
                'created_at': datetime.utcnow()
            }
            recipe_likes_collection.insert_one(like_data)
            liked = True

        # Get updated like count
        like_count = recipe_likes_collection.count_documents({'recipe_id': recipe_id})

        return {
            'status': 'success',
            'liked': liked,
            'like_count': like_count
        }

    except Exception as e:
        print(f"Error toggling recipe like: {e}")
        return {
            'status': 'error',
            'message': f'Error toggling like: {str(e)}'
        }

def delete_shared_recipe(recipe_id, user_id):
    """Delete a shared recipe (only by the author)."""
    try:
        from bson import ObjectId

        # Find the recipe
        recipe = recipes_collection.find_one({'_id': ObjectId(recipe_id)})

        if not recipe:
            return {
                'status': 'error',
                'message': 'Recipe not found'
            }

        # Check if the user is the author
        if recipe.get('submitted_by') != user_id:
            return {
                'status': 'error',
                'message': 'Recipe not found or unauthorized'
            }

        # Delete the recipe
        result = recipes_collection.delete_one({'_id': ObjectId(recipe_id)})

        if result.deleted_count > 0:
            # Also delete related data (likes, comments)
            try:
                recipe_likes_collection = db['recipe_likes']
                recipe_comments_collection = db['recipe_comments']
                recipe_comment_likes_collection = db['recipe_comment_likes']

                # Delete likes
                recipe_likes_collection.delete_many({'recipe_id': recipe_id})

                # Delete comment likes first
                comments = recipe_comments_collection.find({'recipe_id': recipe_id})
                for comment in comments:
                    recipe_comment_likes_collection.delete_many({'comment_id': str(comment['_id'])})

                # Delete comments
                recipe_comments_collection.delete_many({'recipe_id': recipe_id})

            except Exception as cleanup_error:
                print(f"Warning: Error cleaning up related data: {cleanup_error}")

            return {
                'status': 'success',
                'message': 'Recipe deleted successfully'
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to delete recipe'
            }

    except Exception as e:
        print(f"Error deleting shared recipe: {e}")
        return {
            'status': 'error',
            'message': f'Error deleting recipe: {str(e)}'
        }



def get_recipe_comments(recipe_id, current_user_id):
    """Get all comments for a recipe."""
    try:
        recipe_comments_collection = db['recipe_comments']
        comment_likes_collection = db['recipe_comment_likes']

        # Get comments
        comments_cursor = recipe_comments_collection.find({
            'recipe_id': recipe_id
        }).sort('created_at', -1)

        comments = []
        for comment in comments_cursor:
            # Get user info
            user_info = get_user_info(comment['user_id'])

            # Get like count and user's like status for this comment
            like_count = comment_likes_collection.count_documents({
                'comment_id': str(comment['_id'])
            })
            user_liked = comment_likes_collection.find_one({
                'comment_id': str(comment['_id']),
                'user_id': current_user_id
            }) is not None

            comment_data = {
                'id': str(comment['_id']),
                'content': comment['content'],
                'created_at': comment['created_at'].isoformat() if isinstance(comment['created_at'], datetime) else str(comment['created_at']),
                'like_count': like_count,
                'user_liked': user_liked,
                **user_info
            }
            comments.append(comment_data)

        return {
            'status': 'success',
            'comments': comments
        }

    except Exception as e:
        print(f"Error getting recipe comments: {e}")
        return {
            'status': 'error',
            'message': f'Error getting comments: {str(e)}'
        }

def create_recipe_comment(recipe_id, user_id, content):
    """Create a new comment on a recipe."""
    try:
        import uuid
        recipe_comments_collection = db['recipe_comments']

        comment_id = str(uuid.uuid4())
        comment_data = {
            '_id': comment_id,
            'recipe_id': recipe_id,
            'user_id': user_id,
            'content': content,
            'created_at': datetime.utcnow()
        }

        recipe_comments_collection.insert_one(comment_data)

        # Get user info and add to comment data
        user_info = get_user_info(user_id)
        comment_data.update(user_info)
        comment_data['id'] = comment_id
        comment_data['like_count'] = 0
        comment_data['user_liked'] = False
        comment_data['created_at'] = comment_data['created_at'].isoformat()

        return {
            'status': 'success',
            'comment': comment_data
        }

    except Exception as e:
        print(f"Error creating recipe comment: {e}")
        return {
            'status': 'error',
            'message': f'Error creating comment: {str(e)}'
        }
