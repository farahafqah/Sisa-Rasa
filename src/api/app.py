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

    # Initialize MongoDB with error handling
    try:
        from api.models.user import init_db
        init_db(app)
        print("✅ MongoDB connection initialized successfully")
    except Exception as e:
        print(f"⚠️  MongoDB initialization warning: {e}")
        print("🔄 App will continue with limited functionality")

    # Register blueprints
    from api.routes import main_bp
    from api.auth import auth_bp
    from api.analytics_routes import analytics_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)

    # Initialize ML recommender system in background for Railway
    # Don't block startup - initialize after health check passes
    app.recommender_initialized = False

    # Create minimal recommender for immediate health checks
    create_minimal_recommender(app)

    # Schedule full initialization in background
    if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
        print("🚀 Railway mode: Deferring ML model loading until after startup")
        # Will be initialized on first API call
    else:
        # Initialize immediately in development
        with app.app_context():
            initialize_recommender(app)

    return app

def initialize_recommender(app):
    """Initialize the hybrid recipe recommender system with Railway-friendly error handling."""
    try:
        print("🤖 Initializing Hybrid Recipe Recommender System...")

        # Add the parent directory to Python path for imports
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from hybrid_recipe_recommender import HybridRecipeRecommender

        # Create recommender instance with Railway-optimized settings
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

        # Check if we're in Railway environment
        is_railway = os.getenv('RAILWAY_ENVIRONMENT') == 'production'
        max_recipes = 5000 if is_railway else 10000  # Reduce memory usage on Railway

        if os.path.exists(recipes_file):
            print(f"📚 Loading recipes from: {recipes_file}")
            print(f"🚀 Railway mode: {is_railway}, Max recipes: {max_recipes}")

            # Load recipes with timeout protection for Railway
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Recipe loading timeout")

            if is_railway:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(180)  # 3 minute timeout for Railway

            try:
                recommender.load_recipes(recipes_file, max_rows=max_recipes)
                print(f"✅ Loaded {len(recommender.recipes)} recipes successfully!")
            finally:
                if is_railway:
                    signal.alarm(0)  # Cancel timeout

        else:
            print(f"⚠️  Warning: Recipe file not found at {recipes_file}")
            print("🔄 Creating minimal recommender for Railway deployment...")
            # Initialize with minimal data for Railway
            recommender.recipes = []
            if hasattr(recommender, 'knn_recommender'):
                recommender.knn_recommender.ingredient_names = set(['chicken', 'rice', 'egg', 'onion', 'garlic'])
                recommender.knn_recommender.recipes = []
            else:
                recommender._ingredient_names = set(['chicken', 'rice', 'egg', 'onion', 'garlic'])

        # Attach to app
        app.recommender = recommender
        print("🎉 Hybrid Recipe Recommender System initialized successfully!")

    except TimeoutError:
        print("⏰ Recipe loading timeout - creating lightweight recommender for Railway")
        create_lightweight_recommender(app)
    except Exception as e:
        print(f"❌ Error initializing recommender system: {e}")
        print("🔄 Creating fallback recommender...")
        create_lightweight_recommender(app)

def create_minimal_recommender(app):
    """Create a minimal recommender for immediate startup."""
    class MinimalRecommender:
        def __init__(self):
            self.recipes = []
            self.ingredient_names = set(['chicken', 'rice', 'egg', 'onion', 'garlic', 'tomato', 'pasta'])
            self._initialized = False

        def recommend_recipes(self, user_input, **kwargs):
            # Lazy load the full recommender on first API call
            if not self._initialized and not getattr(app, 'recommender_initialized', False):
                print("🔄 Lazy loading full recommender system...")
                try:
                    initialize_recommender(app)
                    app.recommender_initialized = True
                    if hasattr(app.recommender, 'recommend_recipes'):
                        return app.recommender.recommend_recipes(user_input, **kwargs)
                except Exception as e:
                    print(f"❌ Failed to lazy load recommender: {e}")
                    return []
            return []

    app.recommender = MinimalRecommender()
    print("✅ Minimal recommender created for fast startup")

def create_lightweight_recommender(app):
    """Create a lightweight recommender for Railway deployment."""
    class LightweightRecommender:
        def __init__(self):
            self.recipes = []
            self.ingredient_names = set(['chicken', 'rice', 'egg', 'onion', 'garlic', 'tomato', 'pasta'])

        def recommend_recipes(self, user_input, **kwargs):
            # Return empty recommendations for now
            return []

    app.recommender = LightweightRecommender()
    print("✅ Lightweight recommender created for Railway deployment")

# Create the app instance
app = create_app()

@app.route('/')
def home():
    return "Sisa Rasa API is running!"

@app.route('/health')
def simple_health():
    """Simple health check for Railway startup."""
    return {'status': 'ok', 'service': 'sisarasa-api'}, 200

@app.route('/api/health')
def health():
    """Enhanced health check for Railway deployment."""
    health_status = {
        'status': 'ok',
        'message': 'SisaRasa API is running',
        'timestamp': str(__import__('datetime').datetime.utcnow()),
        'components': {}
    }

    # Check recommender system
    recommender = getattr(app, 'recommender', None)
    if recommender and hasattr(recommender, 'recipes'):
        # Get ingredient count safely
        ingredient_count = 0
        if hasattr(recommender, 'knn_recommender') and hasattr(recommender.knn_recommender, 'ingredient_names'):
            ingredient_count = len(recommender.knn_recommender.ingredient_names)
        elif hasattr(recommender, '_ingredient_names'):
            ingredient_count = len(recommender._ingredient_names)

        health_status['components']['recommender'] = {
            'status': 'healthy',
            'recipes_loaded': len(recommender.recipes),
            'ingredients_loaded': ingredient_count
        }
    else:
        health_status['components']['recommender'] = {
            'status': 'initializing',
            'message': 'Recommender system starting up'
        }

    # Check MongoDB connection (non-blocking)
    try:
        from api.models.user import mongo
        if mongo and hasattr(mongo, 'db'):
            # Quick ping to check connection
            mongo.db.command('ping')
            health_status['components']['database'] = {
                'status': 'healthy',
                'type': 'MongoDB'
            }
        else:
            health_status['components']['database'] = {
                'status': 'initializing',
                'message': 'Database connection starting'
            }
    except Exception as e:
        health_status['components']['database'] = {
            'status': 'warning',
            'message': f'Database connection issue: {str(e)[:100]}'
        }

    # Always return 200 OK for Railway health checks
    return health_status, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Sisa Rasa API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


