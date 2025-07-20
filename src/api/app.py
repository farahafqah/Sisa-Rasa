"""
Recipe Recommender API

This module provides a Flask-based API for the recipe recommendation system.
"""

import os
import sys
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

def create_app():
    """Create and configure the Flask application."""

    # Create Flask app with proper template and static folder configuration
    app = Flask(__name__,
                template_folder='templates',
                static_folder='templates')  # Static files are in templates folder

    # Enable CORS
    CORS(app)

    # Load configuration
    from api.config import MONGO_URI, JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES, DEBUG

    app.config['MONGO_URI'] = MONGO_URI
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES
    app.config['DEBUG'] = DEBUG

    # Initialize JWT
    jwt = JWTManager(app)

    # Initialize MongoDB
    from api.models.user import init_db
    init_db(app)

    # Register blueprints
    from api.routes import main_bp
    from api.auth import auth_bp
    from api.analytics_routes import analytics_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)

    # Initialize ML recommender system
    with app.app_context():
        initialize_recommender(app)

    return app

def initialize_recommender(app):
    """Initialize the hybrid recipe recommender system."""
    try:
        print("🤖 Initializing Hybrid Recipe Recommender System...")

        # Add the parent directory to Python path for imports
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from hybrid_recipe_recommender import HybridRecipeRecommender

        # Create recommender instance
        recommender = HybridRecipeRecommender(
            knn_weight=0.5,
            content_weight=0.25,
            collaborative_weight=0.15,
            popularity_weight=0.1,
            k=10,
            metric='cosine'
        )

        # Load recipes - fix the path to go up from src/api/app.py to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        recipes_file = os.path.join(project_root, 'data', 'clean_recipes.json')

        if os.path.exists(recipes_file):
            print(f"📚 Loading recipes from: {recipes_file}")
            recommender.load_recipes(recipes_file, max_rows=10000)  # Load up to 10k recipes
            print(f"✅ Loaded {len(recommender.recipes)} recipes successfully!")
        else:
            print(f"⚠️  Warning: Recipe file not found at {recipes_file}")
            print("🔄 Creating empty recommender for development...")
            # Initialize with empty data for development
            recommender.recipes = []
            # Use the KNN recommender's ingredient_names instead of setting directly
            if hasattr(recommender, 'knn_recommender'):
                recommender.knn_recommender.ingredient_names = set()
            else:
                # Create a simple attribute for fallback
                recommender._ingredient_names = set()

        # Attach to app
        app.recommender = recommender
        print("🎉 Hybrid Recipe Recommender System initialized successfully!")

    except Exception as e:
        print(f"❌ Error initializing recommender system: {e}")
        print("🔄 Creating fallback recommender...")
        # Create a minimal fallback recommender
        class FallbackRecommender:
            def __init__(self):
                self.recipes = []
                self.ingredient_names = set()

        app.recommender = FallbackRecommender()

# Create the app instance
app = create_app()

@app.route('/')
def home():
    return "Sisa Rasa API is running!"

@app.route('/api/health')
def health():
    recommender = getattr(app, 'recommender', None)
    if recommender and hasattr(recommender, 'recipes'):
        # Get ingredient count safely
        ingredient_count = 0
        if hasattr(recommender, 'knn_recommender') and hasattr(recommender.knn_recommender, 'ingredient_names'):
            ingredient_count = len(recommender.knn_recommender.ingredient_names)
        elif hasattr(recommender, '_ingredient_names'):
            ingredient_count = len(recommender._ingredient_names)

        return {
            'status': 'ok',
            'message': 'App is running',
            'recipes_loaded': len(recommender.recipes),
            'ingredients_loaded': ingredient_count
        }
    else:
        return {'status': 'ok', 'message': 'App is running (no recommender)'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Sisa Rasa API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


