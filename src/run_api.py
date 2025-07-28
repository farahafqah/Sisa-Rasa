"""
Run the Recipe Recommender API

This script runs the Flask API for the recipe recommendation system.
"""

import os
from api.app import app, initialize_recommender

if __name__ == '__main__':
    # Initialize recommender
    max_recipes = int(os.environ.get('MAX_RECIPES', 10000))
    num_recipes = int(os.environ.get('NUM_RECIPES', 10))
    
    initialize_recommender(num_recipes=num_recipes, max_recipes=max_recipes)
    
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)

