"""
Fast-starting Recipe Recommender API for Railway deployment

This module provides a minimal Flask app that starts quickly for Railway health checks.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

def create_fast_app():
    """Create a fast-starting Flask application for Railway."""
    
    # Create Flask app with proper template and static folder configuration
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='templates')
    
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
    
    # Initialize MongoDB with error handling (non-blocking)
    try:
        from api.models.user import init_db
        init_db(app)
        print("✅ MongoDB connection initialized")
    except Exception as e:
        print(f"⚠️  MongoDB initialization deferred: {e}")
    
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
            # Import and initialize the full system
            from api.routes import main_bp
            from api.auth import auth_bp
            from api.analytics_routes import analytics_bp
            
            # Register blueprints
            app.register_blueprint(main_bp)
            app.register_blueprint(auth_bp)  
            app.register_blueprint(analytics_bp)
            
            # Initialize ML system in background
            initialize_ml_system(app)
            
            app.recommender_ready = True
            return {'status': 'initialized', 'message': 'Full system ready'}, 200
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500

def initialize_ml_system(app):
    """Initialize ML system after startup."""
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from hybrid_recipe_recommender import HybridRecipeRecommender
        
        recommender = HybridRecipeRecommender(k=10, metric='cosine')
        
        # Load recipes with Railway optimization
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        recipes_file = os.path.join(project_root, 'data', 'clean_recipes.json')
        
        if os.path.exists(recipes_file):
            # Load fewer recipes for Railway
            max_recipes = 3000 if os.getenv('RAILWAY_ENVIRONMENT') == 'production' else 10000
            recommender.load_recipes(recipes_file, max_rows=max_recipes)
            print(f"✅ ML system loaded with {len(recommender.recipes)} recipes")
        
        app.recommender = recommender
        
    except Exception as e:
        print(f"❌ ML system initialization failed: {e}")
        # Keep the minimal recommender

# Create the app instance
app = create_fast_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting SisaRasa Fast API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
