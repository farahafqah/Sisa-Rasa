"""
Recipe Recommender API

This module provides a Flask-based API for the recipe recommendation system.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import sys
import json

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the hybrid recipe recommender
from hybrid_recipe_recommender import HybridRecipeRecommender

# Import configuration
from api.config import (
    MONGO_URI, JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES,
    MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USE_SSL,
    MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER
)

# Import database initialization
from api.models.user import init_db

# Create Flask app
app = Flask(__name__,
           static_folder='static',
           static_url_path='/static',
           template_folder='templates')

# Configure app
app.config['MONGO_URI'] = MONGO_URI
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES

# Email configuration
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

# Initialize extensions
CORS(app)
jwt = JWTManager(app)

# Initialize database
init_db(app)

# Import and register blueprints
from api.auth import auth_bp
from api.routes import main_bp

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

if __name__ == '__main__':
    # Initialize the recommender with small dataset for testing
    initialize_recommender(num_recipes=5, max_recipes=100)

    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)


