"""
Community Posts Model

This module handles community posts, comments, and interactions for the SisaRasa application.
"""

import uuid
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import os

# MongoDB connection - Use same connection as main application
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client.get_default_database()
posts_collection = db['community_posts']
comments_collection = db['post_comments']
likes_collection = db['post_likes']
comment_likes_collection = db['comment_likes']
users_collection = db['users']

def create_indexes():
    """Create necessary indexes for community posts collections."""
    try:
        # Posts indexes
        posts_collection.create_index([("created_at", -1)])
        posts_collection.create_index([("user_id", 1)])
        
        # Comments indexes
        comments_collection.create_index([("post_id", 1), ("created_at", 1)])
        comments_collection.create_index([("user_id", 1)])
        
        # Likes indexes
        likes_collection.create_index([("post_id", 1), ("user_id", 1)], unique=True)
        comment_likes_collection.create_index([("comment_id", 1), ("user_id", 1)], unique=True)
        
        print("Community posts indexes created successfully")
    except Exception as e:
        print(f"Error creating community posts indexes: {e}")

def get_user_info(user_id):
    """Get user information for posts and comments."""
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

def create_post(user_id, content):
    """Create a new community post."""
    try:
        post_id = str(uuid.uuid4())
        post_data = {
            '_id': post_id,
            'user_id': user_id,
            'content': content,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'like_count': 0,
            'comment_count': 0
        }
        
        posts_collection.insert_one(post_data)
        
        # Get user info and add to post data
        user_info = get_user_info(user_id)
        post_data.update(user_info)
        post_data['id'] = post_id
        post_data['user_liked'] = False

        # Convert datetime objects to ISO strings for frontend
        post_data['created_at'] = post_data['created_at'].isoformat()
        post_data['updated_at'] = post_data['updated_at'].isoformat()

        return {
            'status': 'success',
            'post': post_data
        }
        
    except Exception as e:
        print(f"Error creating post: {e}")
        return {
            'status': 'error',
            'message': f'Error creating post: {str(e)}'
        }

def get_all_posts(current_user_id):
    """Get all community posts with user information and like status, excluding shared recipe posts."""
    try:
        # Get all posts except shared recipe posts, sorted by creation date (newest first)
        posts_cursor = posts_collection.find({
            'post_type': {'$ne': 'shared_recipe'}  # Exclude shared recipe posts
        }).sort("created_at", -1)
        posts = []

        for post in posts_cursor:
            # Get user info
            user_info = get_user_info(post['user_id'])

            # Check if current user liked this post
            user_liked = likes_collection.find_one({
                'post_id': post['_id'],
                'user_id': current_user_id
            }) is not None

            # Get like count
            like_count = likes_collection.count_documents({'post_id': post['_id']})

            # Get comment count
            comment_count = comments_collection.count_documents({'post_id': post['_id']})

            post_data = {
                'id': post['_id'],
                'content': post['content'],
                'created_at': post['created_at'].isoformat(),
                'updated_at': post['updated_at'].isoformat(),
                'like_count': like_count,
                'comment_count': comment_count,
                'user_liked': user_liked,
                **user_info
            }

            posts.append(post_data)

        return {
            'status': 'success',
            'posts': posts
        }

    except Exception as e:
        print(f"Error getting posts: {e}")
        return {
            'status': 'error',
            'message': f'Error getting posts: {str(e)}',
            'posts': []
        }

def get_recipe_posts(current_user_id):
    """Get only shared recipe posts for the recipe sharing section."""
    try:
        # Get only shared recipe posts, sorted by creation date (newest first)
        posts_cursor = posts_collection.find({
            'post_type': 'shared_recipe'
        }).sort("created_at", -1)
        posts = []

        for post in posts_cursor:
            # Get user info
            user_info = get_user_info(post['user_id'])

            # Check if current user liked this post
            user_liked = likes_collection.find_one({
                'post_id': post['_id'],
                'user_id': current_user_id
            }) is not None

            # Get like count
            like_count = likes_collection.count_documents({'post_id': post['_id']})

            # Get comment count
            comment_count = comments_collection.count_documents({'post_id': post['_id']})

            post_data = {
                'id': post['_id'],
                'content': post['content'],
                'created_at': post['created_at'].isoformat(),
                'updated_at': post['updated_at'].isoformat(),
                'like_count': like_count,
                'comment_count': comment_count,
                'user_liked': user_liked,
                **user_info
            }

            # Add recipe-specific fields for shared recipe posts
            post_data.update({
                'post_type': post.get('post_type'),
                'recipe_id': post.get('recipe_id'),
                'recipe_name': post.get('recipe_name'),
                'recipe_image': post.get('recipe_image')
            })

            posts.append(post_data)

        return {
            'status': 'success',
            'posts': posts
        }

    except Exception as e:
        print(f"Error getting recipe posts: {e}")
        return {
            'status': 'error',
            'message': f'Error getting recipe posts: {str(e)}',
            'posts': []
        }

def update_post(post_id, user_id, content):
    """Update a post (only by the author)."""
    try:
        # Check if post exists and user is the author
        post = posts_collection.find_one({'_id': post_id, 'user_id': user_id})
        if not post:
            return {
                'status': 'error',
                'message': 'Post not found or unauthorized'
            }
        
        # Update the post
        posts_collection.update_one(
            {'_id': post_id},
            {
                '$set': {
                    'content': content,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return {
            'status': 'success',
            'message': 'Post updated successfully'
        }
        
    except Exception as e:
        print(f"Error updating post: {e}")
        return {
            'status': 'error',
            'message': f'Error updating post: {str(e)}'
        }

def delete_post(post_id, user_id):
    """Delete a post (only by the author)."""
    try:
        # Check if post exists and user is the author
        post = posts_collection.find_one({'_id': post_id, 'user_id': user_id})
        if not post:
            return {
                'status': 'error',
                'message': 'Post not found or unauthorized'
            }
        
        # Delete the post
        posts_collection.delete_one({'_id': post_id})
        
        # Delete associated comments and likes
        comments_collection.delete_many({'post_id': post_id})
        likes_collection.delete_many({'post_id': post_id})
        
        return {
            'status': 'success',
            'message': 'Post deleted successfully'
        }
        
    except Exception as e:
        print(f"Error deleting post: {e}")
        return {
            'status': 'error',
            'message': f'Error deleting post: {str(e)}'
        }

def toggle_like(post_id, user_id):
    """Toggle like on a post."""
    try:
        # Check if user already liked this post
        existing_like = likes_collection.find_one({
            'post_id': post_id,
            'user_id': user_id
        })
        
        if existing_like:
            # Unlike the post
            likes_collection.delete_one({
                'post_id': post_id,
                'user_id': user_id
            })
            liked = False
        else:
            # Like the post
            likes_collection.insert_one({
                'post_id': post_id,
                'user_id': user_id,
                'created_at': datetime.utcnow()
            })
            liked = True
        
        # Get updated like count
        like_count = likes_collection.count_documents({'post_id': post_id})
        
        # Update post like count
        posts_collection.update_one(
            {'_id': post_id},
            {'$set': {'like_count': like_count}}
        )
        
        return {
            'status': 'success',
            'liked': liked,
            'like_count': like_count
        }
        
    except Exception as e:
        print(f"Error toggling like: {e}")
        return {
            'status': 'error',
            'message': f'Error toggling like: {str(e)}'
        }

def get_comments(post_id, current_user_id):
    """Get all comments for a post."""
    try:
        # Get all comments for the post sorted by creation date
        comments_cursor = comments_collection.find({'post_id': post_id}).sort("created_at", 1)
        comments = []
        
        for comment in comments_cursor:
            # Get user info
            user_info = get_user_info(comment['user_id'])
            
            # Check if current user liked this comment
            user_liked = comment_likes_collection.find_one({
                'comment_id': comment['_id'],
                'user_id': current_user_id
            }) is not None
            
            # Get like count
            like_count = comment_likes_collection.count_documents({'comment_id': comment['_id']})
            
            comment_data = {
                'id': comment['_id'],
                'content': comment['content'],
                'created_at': comment['created_at'].isoformat(),
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
        print(f"Error getting comments: {e}")
        return {
            'status': 'error',
            'message': f'Error getting comments: {str(e)}',
            'comments': []
        }

def create_comment(post_id, user_id, content):
    """Create a new comment on a post."""
    try:
        comment_id = str(uuid.uuid4())
        comment_data = {
            '_id': comment_id,
            'post_id': post_id,
            'user_id': user_id,
            'content': content,
            'created_at': datetime.utcnow(),
            'like_count': 0
        }
        
        comments_collection.insert_one(comment_data)
        
        # Update post comment count
        comment_count = comments_collection.count_documents({'post_id': post_id})
        posts_collection.update_one(
            {'_id': post_id},
            {'$set': {'comment_count': comment_count}}
        )
        
        # Get user info and add to comment data
        user_info = get_user_info(user_id)
        comment_data.update(user_info)
        comment_data['id'] = comment_id
        comment_data['user_liked'] = False
        
        return {
            'status': 'success',
            'comment': comment_data
        }
        
    except Exception as e:
        print(f"Error creating comment: {e}")
        return {
            'status': 'error',
            'message': f'Error creating comment: {str(e)}'
        }

def toggle_comment_like(comment_id, user_id):
    """Toggle like on a comment."""
    try:
        # Check if user already liked this comment
        existing_like = comment_likes_collection.find_one({
            'comment_id': comment_id,
            'user_id': user_id
        })
        
        if existing_like:
            # Unlike the comment
            comment_likes_collection.delete_one({
                'comment_id': comment_id,
                'user_id': user_id
            })
            liked = False
        else:
            # Like the comment
            comment_likes_collection.insert_one({
                'comment_id': comment_id,
                'user_id': user_id,
                'created_at': datetime.utcnow()
            })
            liked = True
        
        # Get updated like count
        like_count = comment_likes_collection.count_documents({'comment_id': comment_id})
        
        return {
            'status': 'success',
            'liked': liked,
            'like_count': like_count
        }
        
    except Exception as e:
        print(f"Error toggling comment like: {e}")
        return {
            'status': 'error',
            'message': f'Error toggling comment like: {str(e)}'
        }

# Initialize indexes when module is imported
create_indexes()
