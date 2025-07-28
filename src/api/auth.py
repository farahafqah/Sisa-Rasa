"""
Authentication routes for the recipe recommendation system.

This module defines the authentication routes for the API.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime, timedelta
from functools import wraps

from api.models.user import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    verify_password,
    change_password,
    update_user,
    save_profile_image,
    get_profile_image,
    generate_password_reset_token,
    verify_password_reset_token,
    reset_password_with_token
)
from api.utils.email import send_password_reset_email, is_email_configured

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def admin_required(fn):
    """Decorator to require admin role."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        # Get JWT claims
        claims = get_jwt()

        # Check if user is admin
        if claims.get('is_admin', False):
            return fn(*args, **kwargs)

        return jsonify({
            'status': 'error',
            'message': 'Admin privileges required'
        }), 403

    return wrapper

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Register a new user.

    Request Body:
    ------------
    {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123"
    }

    Returns:
    --------
    {
        "status": "success",
        "message": "User registered!",
        "user": {
            "id": "123",
            "name": "John Doe",
            "email": "john@example.com"
        }
    }
    """
    # Get request data
    data = request.get_json()

    # Validate request data
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400

    # Check required fields
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400

    # Check if email is already registered
    if get_user_by_email(data['email']):
        return jsonify({
            'status': 'error',
            'message': 'Email already registered.'
        }), 409

    # Validate password length
    if len(data['password']) < 6:
        return jsonify({
            'status': 'error',
            'message': 'Password must be at least 6 characters long'
        }), 400

    # Create user
    user = create_user(
        name=data['name'],
        email=data['email'],
        password=data['password']
    )

    if not user:
        return jsonify({
            'status': 'error',
            'message': 'Failed to create user'
        }), 500

    # Return success response
    return jsonify({
        'status': 'success',
        'message': 'User registered!',
        'user': {
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email']
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login a user.

    Request Body:
    ------------
    {
        "email": "john@example.com",
        "password": "password123",
        "rememberMe": false
    }

    Returns:
    --------
    {
        "status": "success",
        "token": "jwt-token",
        "user": {
            "id": "123",
            "name": "John Doe",
            "email": "john@example.com"
        }
    }
    """
    # Get request data
    data = request.get_json()

    # Validate request data
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400

    # Check required fields
    if 'email' not in data or not data['email']:
        return jsonify({
            'status': 'error',
            'message': 'Email is required'
        }), 400

    if 'password' not in data or not data['password']:
        return jsonify({
            'status': 'error',
            'message': 'Password is required'
        }), 400

    # Get user by email
    user = get_user_by_email(data['email'])

    # Check if user exists and password is correct
    if not user or not verify_password(user, data['password']):
        return jsonify({
            'status': 'error',
            'message': 'Invalid email or password'
        }), 401

    # Create access token
    remember_me = data.get('rememberMe', False)
    expires_delta = timedelta(days=30) if remember_me else None

    # Create JWT claims
    additional_claims = {
        'name': user['name'],
        'email': user['email'],
        'is_admin': user.get('is_admin', False)
    }

    access_token = create_access_token(
        identity=str(user['_id']),
        additional_claims=additional_claims,
        expires_delta=expires_delta
    )

    # Return success response
    return jsonify({
        'status': 'success',
        'token': access_token,
        'user': {
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email']
        }
    })

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get the current user's information.

    Returns:
    --------
    {
        "status": "success",
        "user": {
            "id": "123",
            "name": "John Doe",
            "email": "john@example.com"
        }
    }
    """
    # Get user ID from JWT
    user_id = get_jwt_identity()

    # Get user from database
    user = get_user_by_id(user_id)

    if not user:
        return jsonify({
            'status': 'error',
            'message': 'User not found'
        }), 404

    # Return user information
    return jsonify({
        'status': 'success',
        'user': {
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email'],
            'profile_image': user.get('profile_image', None),
            'preferences': user.get('preferences', {}),
            'saved_recipes': user.get('saved_recipes', [])
        }
    })

@auth_bp.route('/update-profile', methods=['POST'])
@jwt_required()
def update_profile():
    """
    Update the current user's profile information.

    Request Body:
    ------------
    {
        "name": "New Name"
    }

    Returns:
    --------
    {
        "status": "success",
        "message": "Profile updated successfully",
        "user": {
            "id": "123",
            "name": "New Name",
            "email": "john@example.com"
        }
    }
    """
    # Get user ID from JWT
    user_id = get_jwt_identity()

    # Get request data
    data = request.get_json()

    # Validate request data
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400

    # Check required fields
    if 'name' not in data or not data['name']:
        return jsonify({
            'status': 'error',
            'message': 'Name is required'
        }), 400

    # Create update data
    update_data = {
        'name': data['name']
    }

    # Update user
    user = update_user(user_id, update_data)

    if not user:
        return jsonify({
            'status': 'error',
            'message': 'Failed to update profile'
        }), 500

    # Return success response
    return jsonify({
        'status': 'success',
        'message': 'Profile updated successfully',
        'user': {
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email']
        }
    })

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def update_password():
    """
    Change the current user's password.

    Request Body:
    ------------
    {
        "currentPassword": "password123",
        "newPassword": "newpassword123"
    }

    Returns:
    --------
    {
        "status": "success",
        "message": "Password updated successfully"
    }
    """
    # Get user ID from JWT
    user_id = get_jwt_identity()

    # Get request data
    data = request.get_json()

    # Validate request data
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400

    # Check required fields
    if 'currentPassword' not in data or not data['currentPassword']:
        return jsonify({
            'status': 'error',
            'message': 'Current password is required'
        }), 400

    if 'newPassword' not in data or not data['newPassword']:
        return jsonify({
            'status': 'error',
            'message': 'New password is required'
        }), 400

    # Validate new password length
    if len(data['newPassword']) < 6:
        return jsonify({
            'status': 'error',
            'message': 'New password must be at least 6 characters long'
        }), 400

    # Change password
    success = change_password(
        user_id=user_id,
        current_password=data['currentPassword'],
        new_password=data['newPassword']
    )

    if not success:
        return jsonify({
            'status': 'error',
            'message': 'Failed to change password. Current password may be incorrect.'
        }), 400

    # Return success response
    return jsonify({
        'status': 'success',
        'message': 'Password updated successfully'
    })

@auth_bp.route('/upload-profile-image', methods=['POST'])
@jwt_required()
def upload_profile_image():
    """
    Upload a profile image for the current user.

    Request Body:
    ------------
    Multipart form data with 'image' field containing the image file.

    Returns:
    --------
    {
        "status": "success",
        "message": "Profile image uploaded successfully",
        "image_url": "/api/auth/profile-image/{image_id}"
    }
    """
    # Get user ID from JWT
    user_id = get_jwt_identity()

    # Check if request has the file part
    if 'image' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No image file provided'
        }), 400

    file = request.files['image']

    # Check if file is empty
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No image file selected'
        }), 400

    # Check if file is an allowed image type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({
            'status': 'error',
            'message': 'Invalid image file format. Allowed formats: PNG, JPG, JPEG, GIF'
        }), 400

    # Read the file data
    file_data = file.read()

    # Save the profile image
    image_id = save_profile_image(user_id, file_data, file.filename)

    if not image_id:
        return jsonify({
            'status': 'error',
            'message': 'Failed to save profile image'
        }), 500

    # Return success response
    return jsonify({
        'status': 'success',
        'message': 'Profile image uploaded successfully',
        'profile_image': image_id  # This is now the data URI
    })

@auth_bp.route('/profile-image/current', methods=['GET'])
@jwt_required()
def get_current_user_profile_image():
    """
    Get the current user's profile image.

    Returns:
    --------
    The image data URI or a 404 error if not found.
    """
    # Get user ID from JWT
    user_id = get_jwt_identity()

    # Get profile image
    profile_image = get_profile_image(user_id)

    if not profile_image:
        return jsonify({
            'status': 'error',
            'message': 'Profile image not found'
        }), 404

    # Return the image data URI
    return jsonify({
        'status': 'success',
        'profile_image': profile_image
    })

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Initiate password reset process by generating a reset token.

    Request Body:
    ------------
    {
        "email": "user@example.com"
    }

    Returns:
    --------
    {
        "status": "success",
        "message": "If the email exists, a password reset link has been sent."
    }
    """
    # Get request data
    data = request.get_json()

    # Validate request data
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400

    # Check required fields
    if 'email' not in data or not data['email']:
        return jsonify({
            'status': 'error',
            'message': 'Email is required'
        }), 400

    email = data['email'].lower().strip()

    # Generate reset token (this will return None if email doesn't exist)
    reset_token = generate_password_reset_token(email)

    # Always return success message for security (don't reveal if email exists)
    if reset_token:
        # Get user info for personalized email
        user = get_user_by_email(email)
        user_name = user.get('name') if user else None

        # Try to send email if configured
        email_sent = False
        if is_email_configured():
            email_sent = send_password_reset_email(email, reset_token, user_name)

        # Response for development/testing
        response_data = {
            'status': 'success',
            'message': 'If the email exists, a password reset link has been sent.'
        }

        # In development mode, include additional info
        if not email_sent:
            response_data.update({
                'dev_info': 'Email not configured. Using development mode.',
                'reset_token': reset_token,  # Remove this in production
                'reset_link': f'/reset-password?token={reset_token}'  # Remove this in production
            })

        return jsonify(response_data)
    else:
        # Still return success to not reveal if email exists
        return jsonify({
            'status': 'success',
            'message': 'If the email exists, a password reset link has been sent.'
        })

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password using a valid reset token.

    Request Body:
    ------------
    {
        "token": "reset-token-from-email",
        "password": "newpassword123"
    }

    Returns:
    --------
    {
        "status": "success",
        "message": "Password has been reset successfully"
    }
    """
    # Get request data
    data = request.get_json()

    # Validate request data
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400

    # Check required fields
    if 'token' not in data or not data['token']:
        return jsonify({
            'status': 'error',
            'message': 'Reset token is required'
        }), 400

    if 'password' not in data or not data['password']:
        return jsonify({
            'status': 'error',
            'message': 'New password is required'
        }), 400

    # Validate password length
    if len(data['password']) < 6:
        return jsonify({
            'status': 'error',
            'message': 'Password must be at least 6 characters long'
        }), 400

    # Reset password with token
    success = reset_password_with_token(data['token'], data['password'])

    if not success:
        return jsonify({
            'status': 'error',
            'message': 'Invalid or expired reset token'
        }), 400

    # Return success response
    return jsonify({
        'status': 'success',
        'message': 'Password has been reset successfully'
    })

@auth_bp.route('/verify-reset-token', methods=['POST'])
def verify_reset_token():
    """
    Verify if a reset token is valid without resetting the password.

    Request Body:
    ------------
    {
        "token": "reset-token-from-email"
    }

    Returns:
    --------
    {
        "status": "success",
        "valid": true,
        "email": "user@example.com"
    }
    """
    # Get request data
    data = request.get_json()

    # Validate request data
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400

    # Check required fields
    if 'token' not in data or not data['token']:
        return jsonify({
            'status': 'error',
            'message': 'Reset token is required'
        }), 400

    # Verify the token
    user = verify_password_reset_token(data['token'])

    if user:
        return jsonify({
            'status': 'success',
            'valid': True,
            'email': user['email']
        })
    else:
        return jsonify({
            'status': 'success',
            'valid': False
        })
