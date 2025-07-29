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

# Initialize database with proper error handling
try:
    # Import database initialization
    from api.models.user import init_db
    
    # Initialize database
    init_db(app)
    print("✅ Database initialization completed")
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    print("⚠️ App will continue without database")

# Initialize the recommender
recommender = None
_last_data_update = None

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

    print(f"🔍 DEBUG: Base directory: {base_dir}")
    print(f"🔍 DEBUG: Looking for recipes at: {clean_recipes_path}")
    print(f"🔍 DEBUG: Current working directory: {os.getcwd()}")
    print(f"🔍 DEBUG: File exists: {os.path.exists(clean_recipes_path)}")

    # Check if clean recipes file exists
    if not os.path.exists(clean_recipes_path):
        print(f"❌ Error: Clean recipes dataset not found at {clean_recipes_path}")

        # Try alternative paths for Railway deployment
        alternative_paths = [
            os.path.join(os.getcwd(), 'data', 'clean_recipes.json'),
            os.path.join(os.path.dirname(os.getcwd()), 'data', 'clean_recipes.json'),
            './data/clean_recipes.json',
            '../data/clean_recipes.json'
        ]

        for alt_path in alternative_paths:
            print(f"🔍 Trying alternative path: {alt_path}")
            if os.path.exists(alt_path):
                print(f"✅ Found recipes at alternative path: {alt_path}")
                clean_recipes_path = alt_path
                break
        else:
            print("❌ Could not find clean_recipes.json in any expected location")
            print("⚠️ Available files in current directory:")
            try:
                for item in os.listdir('.'):
                    print(f"  - {item}")
            except:
                pass
            return False

    try:
        # Load recipes
        print("Loading clean recipes...")
        recommender.load_recipes(clean_recipes_path, max_rows=max_recipes)

        # Load user interaction data from MongoDB - PRODUCTION VERSION
        with app.app_context():
            try:
                from api.models.user import mongo
                if mongo is not None and mongo.db is not None:
                    recommender.load_user_interaction_data(mongo.db)
                    print("✅ User interaction data loaded successfully!")
                else:
                    print("⚠️ MongoDB not available, using default popularity scores")
            except Exception as e:
                print(f"⚠️ Warning: Could not load user interaction data: {e}")
                print("Continuing with default popularity scores...")

        # Store recommender in app context
        app.recommender = recommender

        # Print some stats about loaded recipes
        print(f"✅ Loaded {len(recommender.recipes)} recipes")
        print(f"✅ Found {len(recommender.knn_recommender.ingredient_names)} unique ingredients")

        # Update the last data update timestamp
        global _last_data_update
        from datetime import datetime
        _last_data_update = datetime.utcnow()

        return True

    except Exception as e:
        print(f"❌ Error initializing recommender: {e}")
        return False

def refresh_recommender_data():
    """
    Refresh the recommender system's user interaction data without full reinitialization.
    This is called when new reviews or ratings are added.
    """
    global recommender, _last_data_update

    if recommender is None:
        print("⚠️ Recommender not initialized, cannot refresh data")
        return False

    try:
        print("🔄 Refreshing recommender data...")

        # Clear existing caches
        recommender.clear_cache()

        # Reload user interaction data from MongoDB
        with app.app_context():
            try:
                from api.models.user import mongo
                if mongo is not None and mongo.db is not None:
                    recommender.load_user_interaction_data(mongo.db)
                    print("✅ User interaction data refreshed successfully!")

                    # Update timestamp
                    from datetime import datetime
                    _last_data_update = datetime.utcnow()
                    return True
                else:
                    print("⚠️ MongoDB not available for data refresh")
                    return False
            except Exception as e:
                print(f"⚠️ Warning: Could not refresh user interaction data: {e}")
                return False

    except Exception as e:
        print(f"❌ Error refreshing recommender data: {e}")
        return False

def get_recommender():
    """
    Get the current recommender instance, ensuring it's properly initialized.
    """
    global recommender

    if recommender is None:
        print("⚠️ Recommender not initialized, initializing now...")
        initialize_recommender(num_recipes=5, max_recipes=100)

    return recommender

def invalidate_recommender_cache():
    """
    Invalidate all caches in the recommender system.
    This should be called when recipe data changes.
    """
    global recommender

    if recommender is not None:
        recommender.clear_cache()
        print("🗑️ Recommender cache invalidated")

# Import and register blueprints
from api.auth import auth_bp
from api.analytics_routes import analytics_bp
from api.routes import main_bp

# Initialize the recommender with smaller dataset for faster startup
initialize_recommender(num_recipes=5, max_recipes=100)

# Add a simple home route
@app.route('/', methods=['GET'])
def home():
    """Home page for the recipe recommendation system."""
    from flask import render_template
    return render_template('home.html')

@app.route('/welcome', methods=['GET'])
def welcome():
    """Welcome page with analytics and recipe information."""
    from flask import render_template
    return render_template('welcome.html')

@app.route('/login', methods=['GET'])
def login():
    """Login page for the recipe recommendation system."""
    from flask import render_template
    return render_template('login.html')

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test API endpoint."""
    from flask import jsonify
    return jsonify({'status': 'success', 'message': 'API is working!'})

# @app.route('/api/analytics/leftover-ingredients', methods=['GET'])
# def get_leftover_ingredients_analytics():
#     """
#     Get analytics for most searched leftover-prone ingredients.
#     """
#     from flask import jsonify
#     from datetime import datetime

#     # Return fallback data for now
#     most_searched_leftovers = [
#         {'name': 'Chicken', 'count': 245, 'percentage': 22.1},
#         {'name': 'Rice', 'count': 189, 'percentage': 17.0},
#         {'name': 'Tomatoes', 'count': 167, 'percentage': 15.1},
#         {'name': 'Onions', 'count': 134, 'percentage': 12.1},
#         {'name': 'Carrots', 'count': 112, 'percentage': 10.1}
#     ]
#     total_ingredient_searches = sum(item['count'] for item in most_searched_leftovers)

#     return jsonify({
#         'status': 'success',
#         'data': {
#             'most_searched_leftovers': most_searched_leftovers,
#             'total_searches': total_ingredient_searches,
#             'last_updated': datetime.utcnow().isoformat()
#         }
#     })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify app and database status."""
    from datetime import datetime
    
    try:
        with app.app_context():
            from api.models.user import mongo
            # Test MongoDB connection
            if mongo is not None and mongo.db is not None:  # ← FIXED
                mongo.db.command('ping')
                db_status = "✅ connected"
            else:
                db_status = "⚠️ not initialized"
    except Exception as e:
        db_status = f"❌ disconnected: {str(e)}"
    
    # Check environment variables for Railway debugging
    env_info = {
        'PORT': os.environ.get('PORT', 'Not set'),
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'Not set'),
        'MONGO_URI_SET': '✅' if os.environ.get('MONGO_URI') else '❌',
        'MAX_RECIPES': os.environ.get('MAX_RECIPES', 'Not set'),
        'NUM_RECIPES': os.environ.get('NUM_RECIPES', 'Not set')
    }

    return jsonify({
        'status': 'success',
        'app': '✅ running',
        'database': db_status,
        'recommender': '✅ loaded' if recommender else '❌ not loaded',
        'environment': env_info,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/', methods=['GET'])
def root_health_check():
    """Root endpoint for Railway health checks."""
    return jsonify({
        'status': 'success',
        'message': 'Sisa Rasa API is running',
        'health_endpoint': '/api/health'
    })

# Register blueprints
try:
    app.register_blueprint(analytics_bp)  # This should come first
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    print("✅ All blueprints registered successfully")
except ValueError as e:
    print(f"⚠️ Blueprint registration warning: {e}")
    pass

# Initialize recommender for production deployment (Railway/gunicorn)
# This ensures the recommender is initialized when the module is imported
if not recommender and os.environ.get('PORT'):  # Railway sets PORT environment variable
    print("🚂 Railway deployment detected - initializing recommender...")
    try:
        max_recipes = int(os.environ.get('MAX_RECIPES', 5000))
        num_recipes = int(os.environ.get('NUM_RECIPES', 10))

        print(f"Initializing with {max_recipes} max recipes, {num_recipes} recommendations")
        success = initialize_recommender(num_recipes=num_recipes, max_recipes=max_recipes)

        if not success:
            print("❌ Failed to initialize recommender for Railway deployment")
            print("⚠️ App will continue without recommender - some features may be limited")
        else:
            print("✅ Recommender initialized successfully for Railway deployment")
    except Exception as e:
        print(f"❌ Error during Railway recommender initialization: {e}")
        print("⚠️ App will continue without recommender - some features may be limited")

if __name__ == '__main__':
    # Initialize the recommender with small dataset for testing
    initialize_recommender(num_recipes=5, max_recipes=100)

    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)






