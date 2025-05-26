"""
Decorators for the API.

This module defines decorators for the API routes.
"""

from functools import wraps
from flask import jsonify, request, redirect, url_for, session, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

def login_required(f):
    """
    Decorator to require login for routes.

    This decorator checks if the user is logged in by verifying the JWT token.
    If the user is not logged in, they are redirected to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try to verify JWT token
        try:
            # First try to verify from cookies or headers
            verify_jwt_in_request(optional=True)

            # If no JWT found in cookies/headers, check for token in localStorage via JavaScript
            # This is done by returning a special HTML that checks localStorage and redirects
            if not get_jwt_identity():
                return render_template('check_auth.html', redirect_url=request.path)

            return f(*args, **kwargs)
        except Exception as e:
            print(f"JWT verification error: {e}")
            # Redirect to login page
            return redirect(url_for('login'))
    return decorated_function
