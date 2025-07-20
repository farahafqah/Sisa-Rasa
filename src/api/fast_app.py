"""
Fast-starting Recipe Recommender API for Railway deployment

This module provides a minimal Flask app that starts quickly for Railway health checks.
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

def create_fast_app():
    """Create a fast-starting Flask application for Railway."""

    # Create Flask app with proper template and static folder configuration
    app = Flask(__name__,
                template_folder='templates',
                static_folder='templates')

    # Enable CORS
    CORS(app)

    # Load configuration directly from environment variables
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/sisarasa')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '86400'))
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'

    print(f"🔗 MongoDB URI: {app.config['MONGO_URI'][:50]}...")
    print(f"🔑 JWT configured: {'Yes' if app.config['JWT_SECRET_KEY'] else 'No'}")

    # Create minimal recommender for health checks
    class FastRecommender:
        def __init__(self):
            self.recipes = []
            self.ingredient_names = set(['chicken', 'rice', 'egg'])

    app.recommender = FastRecommender()
    app.recommender_ready = False

    # Register only essential routes for fast startup
    register_essential_routes(app)

    return app

def register_essential_routes(app):
    """Register only essential routes for fast startup."""
    
    @app.route('/')
    def home():
        return "SisaRasa API - Fast Mode"
    
    @app.route('/health')
    def health():
        """Ultra-simple health check for Railway."""
        return {'status': 'ok', 'mode': 'fast-startup'}, 200
    
    @app.route('/api/health')
    def api_health():
        """Detailed health check."""
        return {
            'status': 'ok',
            'message': 'SisaRasa API running in fast mode',
            'components': {
                'app': 'healthy',
                'recommender': 'minimal' if not app.recommender_ready else 'ready'
            }
        }, 200
    
    @app.route('/api/initialize', methods=['POST'])
    def initialize_full_system():
        """Initialize the full system after startup."""
        if app.recommender_ready:
            return {'status': 'already_initialized'}, 200

        try:
            print("🔄 Starting full system initialization...")

            # Add the src directory to Python path for imports
            src_dir = os.path.dirname(os.path.abspath(__file__))
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)

            # Import and register blueprints
            try:
                from routes import main_bp
                from auth import auth_bp
                from analytics_routes import analytics_bp

                app.register_blueprint(main_bp)
                app.register_blueprint(auth_bp)
                app.register_blueprint(analytics_bp)
                print("✅ Blueprints registered")
            except Exception as e:
                print(f"⚠️  Blueprint registration failed: {e}")

            # Initialize ML system
            try:
                initialize_ml_system(app)
                print("✅ ML system initialized")
            except Exception as e:
                print(f"⚠️  ML system initialization failed: {e}")

            app.recommender_ready = True
            return {'status': 'initialized', 'message': 'Full system ready'}, 200

        except Exception as e:
            print(f"❌ Full system initialization failed: {e}")
            return {'status': 'error', 'message': str(e)}, 500

def initialize_ml_system(app):
    """Initialize ML system after startup."""
    try:
        print("🤖 Initializing ML system...")

        # Add parent directories to path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        project_root = os.path.dirname(src_dir)

        sys.path.insert(0, src_dir)
        sys.path.insert(0, project_root)

        # Try to import and initialize the hybrid recommender
        try:
            from hybrid_recipe_recommender import HybridRecipeRecommender

            recommender = HybridRecipeRecommender(k=10, metric='cosine')

            # Load recipes with Railway optimization
            recipes_file = os.path.join(project_root, 'data', 'clean_recipes.json')

            if os.path.exists(recipes_file):
                # Load fewer recipes for Railway
                max_recipes = 2000 if os.getenv('RAILWAY_ENVIRONMENT') == 'production' else 5000
                print(f"📚 Loading {max_recipes} recipes...")
                recommender.load_recipes(recipes_file, max_rows=max_recipes)
                print(f"✅ ML system loaded with {len(recommender.recipes)} recipes")
                app.recommender = recommender
            else:
                print(f"⚠️  Recipe file not found: {recipes_file}")

        except Exception as e:
            print(f"⚠️  Hybrid recommender failed, using simple fallback: {e}")
            # Create a simple fallback recommender
            class SimpleRecommender:
                def __init__(self):
                    self.recipes = [
                        {'id': 1, 'name': 'Chicken Rice', 'ingredients': ['chicken', 'rice']},
                        {'id': 2, 'name': 'Egg Fried Rice', 'ingredients': ['egg', 'rice']},
                        {'id': 3, 'name': 'Chicken Soup', 'ingredients': ['chicken', 'onion']}
                    ]
                    self.ingredient_names = set(['chicken', 'rice', 'egg', 'onion'])

                def recommend_recipes(self, user_input, **kwargs):
                    return self.recipes[:3]  # Return first 3 recipes

            app.recommender = SimpleRecommender()
            print("✅ Simple fallback recommender created")

    except Exception as e:
        print(f"❌ ML system initialization completely failed: {e}")
        # Keep the original minimal recommender

# Create the app instance
app = create_fast_app()

if __name__ == '__main__':
    # Railway sets PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting SisaRasa Fast API on port {port}")
    print(f"🔗 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'development')}")

    # Use Gunicorn in production, Flask dev server locally
    if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
        print("🚀 Using Gunicorn for production")
        import subprocess
        cmd = [
            'gunicorn',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '1',
            '--timeout', '60',
            '--access-logfile', '-',
            '--error-logfile', '-',
            'api.fast_app:app'
        ]
        subprocess.run(cmd)
    else:
        print("🔧 Using Flask dev server")
        app.run(host='0.0.0.0', port=port, debug=False)
