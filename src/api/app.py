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
from api.config import MONGO_URI, JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES

# Create Flask app
app = Flask(__name__,
           static_folder='static',
           static_url_path='/static',
           template_folder='templates')

# Configure app
# Use the MongoDB URI from the environment variable
app.config['MONGO_URI'] = MONGO_URI
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES

# Initialize extensions
CORS(app)  # Enable CORS for all routes
jwt = JWTManager(app)  # Initialize JWT

# Initialize MongoDB
from api.models.user import init_db
from api.models.community import create_community_indexes
try:
    print(f"Attempting to connect to MongoDB with URI: {MONGO_URI}")
    init_db(app)
    print("MongoDB connection successful!")

    # Initialize community indexes
    create_community_indexes()
    print("Community indexes initialized!")
except Exception as e:
    print(f"MongoDB connection error: {e}")

# Initialize the recommender
recommender = None

def initialize_recommender(num_recipes=10, max_recipes=10000):
    """
    Initialize the hybrid recipe recommender.

    Parameters:
    -----------
    num_recipes : int, default=10
        Number of recipes to recommend
    max_recipes : int, default=10000
        Maximum number of recipes to load
    """
    global recommender

    # Create a hybrid recipe recommender
    # KNN is primary (50%), content-based (25%), collaborative (15%), popularity (10%)
    recommender = HybridRecipeRecommender(
        knn_weight=0.5,
        content_weight=0.25,
        collaborative_weight=0.15,
        popularity_weight=0.1,
        k=num_recipes,
        metric='cosine'
    )

    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    clean_recipes_path = os.path.join(base_dir, 'data', 'clean_recipes.json')

    # Check if clean recipes file exists
    if not os.path.exists(clean_recipes_path):
        print(f"Error: Clean recipes dataset not found at {clean_recipes_path}")
        print("Please run the dataset download script to get the clean recipes dataset.")
        return False

    try:
        # Load recipes
        print("Loading clean recipes...")
        recommender.load_recipes(clean_recipes_path, max_rows=max_recipes)

        # Load user interaction data from MongoDB
        try:
            from api.models.user import mongo
            recommender.load_user_interaction_data(mongo.db)
            print("User interaction data loaded successfully!")
        except Exception as e:
            print(f"Warning: Could not load user interaction data: {e}")
            print("Continuing with default popularity scores...")

        # Print some stats about loaded recipes
        print(f"Loaded {len(recommender.recipes)} recipes")
        print(f"Found {len(recommender.ingredient_names)} unique ingredients")

        return True

    except Exception as e:
        print(f"Error initializing recommender: {e}")
        return False

# Initialize the recommender
initialize_recommender()

# Import and register blueprints
from api.routes import *
from api.auth import auth_bp

# Register blueprints
try:
    app.register_blueprint(auth_bp)
except ValueError:
    # Blueprint already registered, skip
    pass

if __name__ == '__main__':
    # Initialize the recommender
    initialize_recommender()

    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
