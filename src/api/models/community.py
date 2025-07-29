"""
Community features model for the recipe recommendation system.

This module defines models and functions for crowd sourcing features:
- Recipe reviews and ratings
- Recipe verification system
- Review voting system
"""

from bson.objectid import ObjectId
from datetime import datetime
from flask import current_app
from api.models.user import mongo
import base64
import os

def create_community_indexes():
    """Create indexes for community collections for better performance."""
    try:
        # Recipe reviews indexes
        mongo.db.recipe_reviews.create_index([('recipe_id', 1), ('user_id', 1)], unique=True)
        mongo.db.recipe_reviews.create_index([('recipe_id', 1), ('created_at', -1)])
        mongo.db.recipe_reviews.create_index([('rating', -1)])
        mongo.db.recipe_reviews.create_index([('helpful_votes', -1)])

        # Recipe verifications indexes
        mongo.db.recipe_verifications.create_index([('recipe_id', 1), ('user_id', 1)], unique=True)
        mongo.db.recipe_verifications.create_index([('recipe_id', 1), ('created_at', -1)])

        # Review votes indexes
        mongo.db.review_votes.create_index([('review_id', 1), ('user_id', 1)], unique=True)
        mongo.db.review_votes.create_index([('review_id', 1)])

        # Community posts indexes
        mongo.db.community_posts.create_index([('created_at', -1)])
        mongo.db.community_posts.create_index([('user_id', 1)])

        # Community comments indexes
        mongo.db.community_comments.create_index([('post_id', 1), ('created_at', 1)])
        mongo.db.community_comments.create_index([('user_id', 1)])

        print("Community indexes created successfully!")
        return True
    except Exception as e:
        print(f"Error creating community indexes: {e}")
        return False

# ==================== RECIPE REVIEWS AND RATINGS ====================

def add_recipe_review(user_id, recipe_id, rating, review_text=None):
    """
    Add or update a recipe review.

    Args:
        user_id (str): User ID
        recipe_id (str): Recipe ID (can be original_id or MongoDB _id)
        rating (int): Rating from 1-5
        review_text (str, optional): Review text

    Returns:
        dict: Result with status and message
    """
    import time
    start_time = time.time()

    try:
        print(f"DEBUG: add_recipe_review called with user_id={user_id}, recipe_id={recipe_id}, rating={rating}")

        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            print(f"ERROR: Invalid rating: {rating}")
            return {'status': 'error', 'message': 'Rating must be between 1 and 5'}

        # Get user info for review with retry logic
        from api.models.user import get_user_by_id
        user = None
        for attempt in range(3):
            try:
                user = get_user_by_id(user_id)
                if user:
                    break
                print(f"WARNING: User not found on attempt {attempt + 1}")
                time.sleep(0.5)  # Brief delay before retry
            except Exception as e:
                print(f"ERROR: Failed to get user on attempt {attempt + 1}: {e}")
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.5)

        if not user:
            print(f"ERROR: User {user_id} not found after retries")
            return {'status': 'error', 'message': 'User not found'}

        print(f"DEBUG: User found: {user['name']}")

        # Check if review already exists with retry logic
        existing_review = None
        for attempt in range(3):
            try:
                existing_review = mongo.db.recipe_reviews.find_one({
                    'recipe_id': recipe_id,
                    'user_id': user_id
                })
                break
            except Exception as e:
                print(f"ERROR: Failed to check existing review on attempt {attempt + 1}: {e}")
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.5)

        review_data = {
            'recipe_id': recipe_id,
            'user_id': user_id,
            'user_name': user['name'],
            'rating': rating,
            'review_text': review_text.strip() if review_text and isinstance(review_text, str) else None,
            'helpful_votes': existing_review.get('helpful_votes', 0) if existing_review else 0,
            'unhelpful_votes': existing_review.get('unhelpful_votes', 0) if existing_review else 0,
            'updated_at': datetime.utcnow()
        }

        print(f"DEBUG: Review data prepared: {review_data}")

        # Perform database operation with retry logic
        success = False
        review_id = None
        action = None

        for attempt in range(3):
            try:
                if existing_review:
                    # Update existing review
                    result = mongo.db.recipe_reviews.update_one(
                        {'_id': existing_review['_id']},
                        {'$set': review_data}
                    )
                    review_id = str(existing_review['_id'])
                    action = 'updated'
                    success = result.modified_count > 0 or result.matched_count > 0  # Consider matched as success too
                    print(f"DEBUG: Update result - matched: {result.matched_count}, modified: {result.modified_count}")
                else:
                    # Create new review
                    review_data['created_at'] = datetime.utcnow()
                    result = mongo.db.recipe_reviews.insert_one(review_data)
                    review_id = str(result.inserted_id)
                    action = 'created'
                    success = result.inserted_id is not None
                    print(f"DEBUG: Insert result - inserted_id: {result.inserted_id}")

                if success:
                    break
                else:
                    print(f"WARNING: Database operation failed on attempt {attempt + 1}")

            except Exception as e:
                print(f"ERROR: Database operation failed on attempt {attempt + 1}: {e}")
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.5)

        if success:
            # Update recipe rating aggregation (non-blocking)
            try:
                update_recipe_rating_aggregation(recipe_id)
                print(f"DEBUG: Rating aggregation updated for recipe {recipe_id}")
            except Exception as e:
                print(f"WARNING: Failed to update rating aggregation: {e}")

            processing_time = time.time() - start_time
            print(f"DEBUG: Review {action} successfully in {processing_time:.2f} seconds")

            return {
                'status': 'success',
                'message': f'Review {action} successfully',
                'review_id': review_id
            }
        else:
            print(f"ERROR: Failed to save review after retries")
            return {'status': 'error', 'message': 'Failed to save review'}

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"ERROR: Exception in add_recipe_review after {processing_time:.2f} seconds: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': f'Error saving review: {str(e)}'}

def get_recipe_reviews(recipe_id, sort_by='helpful', limit=50, skip=0):
    """
    Get reviews for a recipe.

    Args:
        recipe_id (str): Recipe ID
        sort_by (str): Sort criteria ('helpful', 'recent', 'rating_high', 'rating_low')
        limit (int): Maximum number of reviews to return
        skip (int): Number of reviews to skip (for pagination)

    Returns:
        dict: Reviews data with pagination info
    """
    try:
        # Define sort criteria
        sort_options = {
            'helpful': [('helpful_votes', -1), ('created_at', -1)],
            'recent': [('created_at', -1)],
            'rating_high': [('rating', -1), ('created_at', -1)],
            'rating_low': [('rating', 1), ('created_at', -1)]
        }

        sort_criteria = sort_options.get(sort_by, sort_options['helpful'])

        # Get reviews
        reviews_cursor = mongo.db.recipe_reviews.find(
            {'recipe_id': recipe_id}
        ).sort(sort_criteria).skip(skip).limit(limit)

        reviews = list(reviews_cursor)

        # Get total count
        total_count = mongo.db.recipe_reviews.count_documents({'recipe_id': recipe_id})

        # Format reviews
        formatted_reviews = []
        for review in reviews:
            formatted_reviews.append({
                'id': str(review['_id']),
                'user_name': review.get('user_name', 'Anonymous User'),
                'rating': review['rating'],
                'review_text': review.get('review_text'),
                'helpful_votes': review.get('helpful_votes', 0),
                'unhelpful_votes': review.get('unhelpful_votes', 0),
                'created_at': review['created_at'].isoformat(),
                'updated_at': review['updated_at'].isoformat()
            })

        return {
            'status': 'success',
            'reviews': formatted_reviews,
            'total_count': total_count,
            'has_more': (skip + len(reviews)) < total_count
        }

    except Exception as e:
        return {'status': 'error', 'message': f'Error fetching reviews: {str(e)}'}

def get_recipe_rating_summary(recipe_id):
    """
    Get rating summary for a recipe.

    Args:
        recipe_id (str): Recipe ID

    Returns:
        dict: Rating summary data
    """
    try:
        # Aggregate rating data
        pipeline = [
            {'$match': {'recipe_id': recipe_id}},
            {'$group': {
                '_id': None,
                'average_rating': {'$avg': '$rating'},
                'total_reviews': {'$sum': 1},
                'rating_distribution': {
                    '$push': '$rating'
                }
            }}
        ]

        result = list(mongo.db.recipe_reviews.aggregate(pipeline))

        if not result:
            return {
                'status': 'success',
                'average_rating': 0,
                'total_reviews': 0,
                'rating_distribution': {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
            }

        data = result[0]

        # Calculate rating distribution
        distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for rating in data['rating_distribution']:
            distribution[str(rating)] += 1

        return {
            'status': 'success',
            'average_rating': round(data['average_rating'], 1),
            'total_reviews': data['total_reviews'],
            'rating_distribution': distribution
        }

    except Exception as e:
        return {'status': 'error', 'message': f'Error fetching rating summary: {str(e)}'}

def update_recipe_rating_aggregation(recipe_id):
    """
    Update the aggregated rating data for a recipe.

    Args:
        recipe_id (str): Recipe ID
    """
    try:
        rating_summary = get_recipe_rating_summary(recipe_id)

        if rating_summary['status'] == 'success':
            # Update recipe document with aggregated rating data
            mongo.db.recipes.update_one(
                {'$or': [
                    {'_id': ObjectId(recipe_id) if ObjectId.is_valid(recipe_id) else None},
                    {'original_id': recipe_id}
                ]},
                {'$set': {
                    'rating_data': {
                        'average_rating': rating_summary['average_rating'],
                        'total_reviews': rating_summary['total_reviews'],
                        'rating_distribution': rating_summary['rating_distribution'],
                        'last_updated': datetime.utcnow()
                    }
                }}
            )

    except Exception as e:
        print(f"Error updating recipe rating aggregation: {e}")

def vote_on_review(user_id, review_id, vote_type):
    """
    Vote on a review as helpful or unhelpful.

    Args:
        user_id (str): User ID
        review_id (str): Review ID
        vote_type (str): 'helpful' or 'unhelpful'

    Returns:
        dict: Result with status and message
    """
    try:
        if vote_type not in ['helpful', 'unhelpful']:
            return {'status': 'error', 'message': 'Invalid vote type'}

        # Check if user already voted on this review
        existing_vote = mongo.db.review_votes.find_one({
            'review_id': review_id,
            'user_id': user_id
        })

        if existing_vote:
            # Update existing vote
            old_vote_type = existing_vote['vote_type']

            if old_vote_type == vote_type:
                # Remove vote if same type
                mongo.db.review_votes.delete_one({'_id': existing_vote['_id']})

                # Update review vote counts
                if vote_type == 'helpful':
                    mongo.db.recipe_reviews.update_one(
                        {'_id': ObjectId(review_id)},
                        {'$inc': {'helpful_votes': -1}}
                    )
                else:
                    mongo.db.recipe_reviews.update_one(
                        {'_id': ObjectId(review_id)},
                        {'$inc': {'unhelpful_votes': -1}}
                    )

                return {'status': 'success', 'message': 'Vote removed', 'action': 'removed'}
            else:
                # Change vote type
                mongo.db.review_votes.update_one(
                    {'_id': existing_vote['_id']},
                    {'$set': {
                        'vote_type': vote_type,
                        'updated_at': datetime.utcnow()
                    }}
                )

                # Update review vote counts
                if old_vote_type == 'helpful':
                    mongo.db.recipe_reviews.update_one(
                        {'_id': ObjectId(review_id)},
                        {'$inc': {'helpful_votes': -1, 'unhelpful_votes': 1}}
                    )
                else:
                    mongo.db.recipe_reviews.update_one(
                        {'_id': ObjectId(review_id)},
                        {'$inc': {'helpful_votes': 1, 'unhelpful_votes': -1}}
                    )

                return {'status': 'success', 'message': 'Vote updated', 'action': 'updated'}
        else:
            # Create new vote
            vote_data = {
                'review_id': review_id,
                'user_id': user_id,
                'vote_type': vote_type,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            mongo.db.review_votes.insert_one(vote_data)

            # Update review vote counts
            if vote_type == 'helpful':
                mongo.db.recipe_reviews.update_one(
                    {'_id': ObjectId(review_id)},
                    {'$inc': {'helpful_votes': 1}}
                )
            else:
                mongo.db.recipe_reviews.update_one(
                    {'_id': ObjectId(review_id)},
                    {'$inc': {'unhelpful_votes': 1}}
                )

            return {'status': 'success', 'message': 'Vote added', 'action': 'added'}

    except Exception as e:
        return {'status': 'error', 'message': f'Error voting on review: {str(e)}'}

# ==================== RECIPE VERIFICATION SYSTEM ====================

def add_recipe_verification(user_id, recipe_id, photo_data=None, notes=None):
    """
    Add a recipe verification (mark as tried and tested).

    Args:
        user_id (str): User ID
        recipe_id (str): Recipe ID
        photo_data (str, optional): Base64 encoded photo data
        notes (str, optional): User notes about cooking the recipe

    Returns:
        dict: Result with status and message
    """
    try:
        # Get user info
        from api.models.user import get_user_by_id
        user = get_user_by_id(user_id)
        if not user:
            return {'status': 'error', 'message': 'User not found'}

        # Check if verification already exists
        existing_verification = mongo.db.recipe_verifications.find_one({
            'recipe_id': recipe_id,
            'user_id': user_id
        })

        verification_data = {
            'recipe_id': recipe_id,
            'user_id': user_id,
            'user_name': user['name'],
            'notes': notes.strip() if notes and isinstance(notes, str) else None,
            'updated_at': datetime.utcnow()
        }

        # Handle photo upload
        if photo_data:
            try:
                # Save photo (you might want to use a cloud storage service in production)
                photo_filename = f"verification_{recipe_id}_{user_id}_{int(datetime.utcnow().timestamp())}.jpg"
                verification_data['photo_filename'] = photo_filename
                verification_data['photo_data'] = photo_data  # Store as base64 for now
            except Exception as e:
                print(f"Error handling photo: {e}")
                # Continue without photo

        if existing_verification:
            # Update existing verification
            result = mongo.db.recipe_verifications.update_one(
                {'_id': existing_verification['_id']},
                {'$set': verification_data}
            )
            verification_id = str(existing_verification['_id'])
            action = 'updated'
        else:
            # Create new verification
            verification_data['created_at'] = datetime.utcnow()
            result = mongo.db.recipe_verifications.insert_one(verification_data)
            verification_id = str(result.inserted_id)
            action = 'created'

        # Check if operation was successful
        success = False
        if action == 'updated':
            success = result.modified_count > 0
        else:  # action == 'created'
            success = result.inserted_id is not None

        if success:
            # Update recipe verification count
            update_recipe_verification_count(recipe_id)

            return {
                'status': 'success',
                'message': f'Recipe verification {action} successfully',
                'verification_id': verification_id
            }
        else:
            return {'status': 'error', 'message': 'Failed to save verification'}

    except Exception as e:
        return {'status': 'error', 'message': f'Error saving verification: {str(e)}'}

def get_recipe_verifications(recipe_id, limit=20, skip=0):
    """
    Get verifications for a recipe.

    Args:
        recipe_id (str): Recipe ID
        limit (int): Maximum number of verifications to return
        skip (int): Number of verifications to skip

    Returns:
        dict: Verifications data
    """
    try:
        # Get verifications
        verifications_cursor = mongo.db.recipe_verifications.find(
            {'recipe_id': recipe_id}
        ).sort([('created_at', -1)]).skip(skip).limit(limit)

        verifications = list(verifications_cursor)

        # Get total count
        total_count = mongo.db.recipe_verifications.count_documents({'recipe_id': recipe_id})

        # Format verifications
        formatted_verifications = []
        for verification in verifications:
            formatted_verifications.append({
                'id': str(verification['_id']),
                'user_name': verification.get('user_name', 'Anonymous User'),
                'notes': verification.get('notes'),
                'has_photo': 'photo_data' in verification,
                'created_at': verification['created_at'].isoformat(),
                'updated_at': verification['updated_at'].isoformat()
            })

        return {
            'status': 'success',
            'verifications': formatted_verifications,
            'total_count': total_count,
            'has_more': (skip + len(verifications)) < total_count
        }

    except Exception as e:
        return {'status': 'error', 'message': f'Error fetching verifications: {str(e)}'}

def get_verification_photo(verification_id):
    """
    Get photo data for a verification.

    Args:
        verification_id (str): Verification ID

    Returns:
        dict: Photo data or error
    """
    try:
        verification = mongo.db.recipe_verifications.find_one({'_id': ObjectId(verification_id)})

        if not verification:
            return {'status': 'error', 'message': 'Verification not found'}

        if 'photo_data' not in verification:
            return {'status': 'error', 'message': 'No photo available'}

        return {
            'status': 'success',
            'photo_data': verification['photo_data']
        }

    except Exception as e:
        return {'status': 'error', 'message': f'Error fetching photo: {str(e)}'}

def update_recipe_verification_count(recipe_id):
    """
    Update the verification count for a recipe.

    Args:
        recipe_id (str): Recipe ID
    """
    try:
        # Count verifications
        verification_count = mongo.db.recipe_verifications.count_documents({'recipe_id': recipe_id})

        # Update recipe document
        mongo.db.recipes.update_one(
            {'$or': [
                {'_id': ObjectId(recipe_id) if ObjectId.is_valid(recipe_id) else None},
                {'original_id': recipe_id}
            ]},
            {'$set': {
                'verification_data': {
                    'verification_count': verification_count,
                    'last_updated': datetime.utcnow()
                }
            }}
        )

    except Exception as e:
        print(f"Error updating recipe verification count: {e}")

def get_user_review_for_recipe(user_id, recipe_id):
    """
    Get a user's review for a specific recipe.

    Args:
        user_id (str): User ID
        recipe_id (str): Recipe ID

    Returns:
        dict: User's review or None
    """
    try:
        review = mongo.db.recipe_reviews.find_one({
            'recipe_id': recipe_id,
            'user_id': user_id
        })

        if review:
            return {
                'status': 'success',
                'review': {
                    'id': str(review['_id']),
                    'rating': review['rating'],
                    'review_text': review.get('review_text'),
                    'created_at': review['created_at'].isoformat(),
                    'updated_at': review['updated_at'].isoformat()
                }
            }
        else:
            return {'status': 'success', 'review': None}

    except Exception as e:
        return {'status': 'error', 'message': f'Error fetching user review: {str(e)}'}

def get_user_verification_for_recipe(user_id, recipe_id):
    """
    Get a user's verification for a specific recipe.

    Args:
        user_id (str): User ID
        recipe_id (str): Recipe ID

    Returns:
        dict: User's verification or None
    """
    try:
        verification = mongo.db.recipe_verifications.find_one({
            'recipe_id': recipe_id,
            'user_id': user_id
        })

        if verification:
            return {
                'status': 'success',
                'verification': {
                    'id': str(verification['_id']),
                    'notes': verification.get('notes'),
                    'has_photo': 'photo_data' in verification,
                    'created_at': verification['created_at'].isoformat(),
                    'updated_at': verification['updated_at'].isoformat()
                }
            }
        else:
            return {'status': 'success', 'verification': None}

    except Exception as e:
        return {'status': 'error', 'message': f'Error fetching user verification: {str(e)}'}
