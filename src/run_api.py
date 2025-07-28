"""
Run the Recipe Recommender API

This script runs the Flask API for the recipe recommendation system.
"""

import os
from api.app import app, initialize_recommender

if __name__ == '__main__':
    # Initialize recommender with smaller dataset for Railway
    max_recipes = int(os.environ.get('MAX_RECIPES', 1000))
    num_recipes = int(os.environ.get('NUM_RECIPES', 10))
    
    print(f"Initializing with {max_recipes} max recipes, {num_recipes} recommendations")
    initialize_recommender(num_recipes=num_recipes, max_recipes=max_recipes)
    
    # Railway provides PORT automatically
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)


