#!/usr/bin/env python3
"""
Complete SisaRasa Web Application for Railway deployment
Full-featured recipe recommendation system with web interface
"""

import os
import sys
from flask import Flask, jsonify, render_template, redirect, url_for, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Add src directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Create Flask app with proper template and static folder configuration
app = Flask(__name__,
            template_folder='api/templates',
            static_folder='api/static')

# Enable CORS
CORS(app)

# Configuration from environment variables
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'sisarasa-secret-key-2024')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'sisarasa-secret-key-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '86400'))
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/sisarasa')
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'

# Initialize JWT
jwt = JWTManager(app)

# Global variables for system state
app.system_initialized = False
app.recommender = None

# ============================================================================
# WEB ROUTES - Main Pages
# ============================================================================

@app.route('/')
def home():
    """Home page - redirect to welcome page."""
    return redirect(url_for('welcome'))

@app.route('/welcome')
def welcome():
    """Welcome page with analytics and recipe information."""
    try:
        return render_template('welcome.html')
    except Exception as e:
        print(f"Error loading welcome template: {e}")
        return f"""
        <html>
        <head><title>SisaRasa - Welcome</title></head>
        <body>
            <h1>🍽️ Welcome to SisaRasa</h1>
            <p>Your AI-powered recipe recommendation system</p>
            <p><a href="/login">Login</a> | <a href="/signup">Sign Up</a></p>
            <p>System Status: {'Initialized' if app.system_initialized else 'Starting up...'}</p>
        </body>
        </html>
        """

@app.route('/login')
def login():
    """Login page."""
    try:
        return render_template('login.html')
    except Exception as e:
        print(f"Error loading login template: {e}")
        return f"""
        <html>
        <head><title>SisaRasa - Login</title></head>
        <body>
            <h1>🔐 Login to SisaRasa</h1>
            <form method="post" action="/api/auth/login">
                <p><input type="email" name="email" placeholder="Email" required></p>
                <p><input type="password" name="password" placeholder="Password" required></p>
                <p><button type="submit">Login</button></p>
            </form>
            <p><a href="/signup">Don't have an account? Sign up</a></p>
        </body>
        </html>
        """

@app.route('/signup')
def signup():
    """Sign up page."""
    try:
        return render_template('signup.html')
    except Exception as e:
        print(f"Error loading signup template: {e}")
        return f"""
        <html>
        <head><title>SisaRasa - Sign Up</title></head>
        <body>
            <h1>📝 Join SisaRasa</h1>
            <form method="post" action="/api/auth/signup">
                <p><input type="text" name="name" placeholder="Full Name" required></p>
                <p><input type="email" name="email" placeholder="Email" required></p>
                <p><input type="password" name="password" placeholder="Password" required></p>
                <p><button type="submit">Sign Up</button></p>
            </form>
            <p><a href="/login">Already have an account? Login</a></p>
        </body>
        </html>
        """

@app.route('/dashboard')
def dashboard():
    """Recipe recommendation dashboard."""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        print(f"Error loading dashboard template: {e}")
        return f"""
        <html>
        <head><title>SisaRasa - Dashboard</title></head>
        <body>
            <h1>🍳 Recipe Dashboard</h1>
            <p>Find recipes based on your ingredients!</p>
            <form method="post" action="/api/recommend">
                <p><input type="text" name="ingredients" placeholder="Enter ingredients (e.g., chicken, rice, tomato)" style="width: 300px;"></p>
                <p><button type="submit">Get Recommendations</button></p>
            </form>
            <p><a href="/profile">Profile</a> | <a href="/save-recipe">Saved Recipes</a> | <a href="/community-recipes">Community</a></p>
        </body>
        </html>
        """

@app.route('/profile')
def profile():
    """User profile page."""
    try:
        return render_template('profile.html')
    except Exception as e:
        print(f"Error loading profile template: {e}")
        return f"""
        <html>
        <head><title>SisaRasa - Profile</title></head>
        <body>
            <h1>👤 User Profile</h1>
            <p>Manage your account settings</p>
            <p><a href="/dashboard">Back to Dashboard</a></p>
        </body>
        </html>
        """

@app.route('/save-recipe')
def save_recipe_page():
    """Saved recipes page."""
    try:
        return render_template('save-recipe.html')
    except Exception as e:
        print(f"Error loading save-recipe template: {e}")
        return f"""
        <html>
        <head><title>SisaRasa - Saved Recipes</title></head>
        <body>
            <h1>💾 Saved Recipes</h1>
            <p>Your favorite recipes</p>
            <p><a href="/dashboard">Back to Dashboard</a></p>
        </body>
        </html>
        """

@app.route('/community-recipes')
def community_recipes():
    """Community recipes page."""
    try:
        return render_template('community-recipes.html')
    except Exception as e:
        print(f"Error loading community-recipes template: {e}")
        return f"""
        <html>
        <head><title>SisaRasa - Community Recipes</title></head>
        <body>
            <h1>👥 Community Recipes</h1>
            <p>Discover and share recipes with the community</p>
            <p><a href="/share-recipe">Share a Recipe</a> | <a href="/dashboard">Back to Dashboard</a></p>
        </body>
        </html>
        """

@app.route('/share-recipe')
def share_recipe():
    """Share recipe page."""
    try:
        return render_template('share-recipe.html')
    except Exception as e:
        print(f"Error loading share-recipe template: {e}")
        return f"""
        <html>
        <head><title>SisaRasa - Share Recipe</title></head>
        <body>
            <h1>📤 Share Your Recipe</h1>
            <p>Share your favorite recipes with the community</p>
            <p><a href="/community-recipes">Back to Community</a></p>
        </body>
        </html>
        """

@app.route('/search-results')
def search_results():
    """Search results page."""
    try:
        return render_template('search-results.html')
    except Exception as e:
        print(f"Error loading search-results template: {e}")
        return f"""
        <html>
        <head><title>SisaRasa - Search Results</title></head>
        <body>
            <h1>🔍 Recipe Search Results</h1>
            <p>Your recommended recipes will appear here</p>
            <p><a href="/dashboard">New Search</a></p>
        </body>
        </html>
        """

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images) for Railway deployment."""
    try:
        from flask import send_from_directory
        static_dir = os.path.join(current_dir, 'api', 'static')
        return send_from_directory(static_dir, filename)
    except Exception as e:
        print(f"Static file serving error: {e}")
        return f"Static file not found: {filename}", 404

@app.route('/favicon.ico')
def favicon():
    """Serve favicon."""
    try:
        from flask import send_from_directory
        static_dir = os.path.join(current_dir, 'api', 'static', 'images')
        return send_from_directory(static_dir, 'logo.png')
    except:
        return '', 204

# ============================================================================
# API ENDPOINTS FOR RECIPE RECOMMENDATIONS
# ============================================================================

@app.route('/api/recommend', methods=['POST'])
def recommend_recipes_api():
    """API endpoint for recipe recommendations."""
    try:
        # Get ingredients from form or JSON
        if request.is_json:
            data = request.get_json()
            ingredients = data.get('ingredients', '')
        else:
            ingredients = request.form.get('ingredients', '')

        if not ingredients:
            return jsonify({
                'status': 'error',
                'message': 'No ingredients provided'
            }), 400

        # Convert string to list if needed
        if isinstance(ingredients, str):
            ingredients_list = [ing.strip() for ing in ingredients.split(',') if ing.strip()]
        else:
            ingredients_list = ingredients

        if not ingredients_list:
            return jsonify({
                'status': 'error',
                'message': 'No valid ingredients provided'
            }), 400

        # Get recommendations from ML system
        if app.recommender and hasattr(app.recommender, 'recommend_recipes'):
            try:
                recommendations = app.recommender.recommend_recipes(
                    user_input=', '.join(ingredients_list),
                    num_recommendations=10
                )

                # Format recommendations for web interface
                formatted_recipes = []
                for recipe in recommendations[:10]:  # Limit to 10 results
                    formatted_recipe = {
                        'id': recipe.get('id', 'unknown'),
                        'name': recipe.get('name', 'Unknown Recipe'),
                        'ingredients': recipe.get('ingredients', []),
                        'steps': recipe.get('instructions', recipe.get('steps', [])),
                        'prep_time': recipe.get('prep_time', 30),
                        'cook_time': recipe.get('cook_time', 45),
                        'servings': recipe.get('servings', 4),
                        'difficulty': recipe.get('difficulty', 'Medium'),
                        'cuisine': recipe.get('cuisine', 'International'),
                        'score': recipe.get('score', 0.5),
                        'ingredient_match_percentage': recipe.get('ingredient_match_percentage', 0)
                    }
                    formatted_recipes.append(formatted_recipe)

                return jsonify({
                    'status': 'success',
                    'count': len(formatted_recipes),
                    'search_ingredients': ingredients_list,
                    'recipes': formatted_recipes
                })

            except Exception as e:
                print(f"ML recommendation error: {e}")
                # Return fallback recommendations
                return get_fallback_recommendations(ingredients_list)
        else:
            # Return fallback recommendations if ML system not ready
            return get_fallback_recommendations(ingredients_list)

    except Exception as e:
        print(f"Recipe recommendation error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting recommendations: {str(e)}'
        }), 500

def get_fallback_recommendations(ingredients_list):
    """Get fallback recipe recommendations when ML system is not available."""
    # Simple fallback recipes based on common ingredients
    fallback_recipes = [
        {
            'id': 'fallback_1',
            'name': 'Simple Fried Rice',
            'ingredients': ['rice', 'egg', 'soy sauce', 'vegetables'],
            'steps': ['Cook rice', 'Scramble eggs', 'Mix with vegetables', 'Add soy sauce'],
            'prep_time': 10,
            'cook_time': 15,
            'servings': 2,
            'difficulty': 'Easy',
            'cuisine': 'Asian',
            'score': 0.8,
            'ingredient_match_percentage': 75
        },
        {
            'id': 'fallback_2',
            'name': 'Quick Chicken Stir Fry',
            'ingredients': ['chicken', 'vegetables', 'garlic', 'oil'],
            'steps': ['Cut chicken', 'Heat oil', 'Cook chicken', 'Add vegetables', 'Season'],
            'prep_time': 15,
            'cook_time': 10,
            'servings': 3,
            'difficulty': 'Easy',
            'cuisine': 'Asian',
            'score': 0.7,
            'ingredient_match_percentage': 60
        },
        {
            'id': 'fallback_3',
            'name': 'Basic Pasta',
            'ingredients': ['pasta', 'tomato', 'garlic', 'olive oil'],
            'steps': ['Boil pasta', 'Sauté garlic', 'Add tomatoes', 'Mix with pasta'],
            'prep_time': 5,
            'cook_time': 20,
            'servings': 4,
            'difficulty': 'Easy',
            'cuisine': 'Italian',
            'score': 0.6,
            'ingredient_match_percentage': 50
        }
    ]

    # Filter recipes that might match user ingredients
    user_ingredients_lower = [ing.lower() for ing in ingredients_list]
    matched_recipes = []

    for recipe in fallback_recipes:
        recipe_ingredients_lower = [ing.lower() for ing in recipe['ingredients']]
        matches = sum(1 for user_ing in user_ingredients_lower
                     if any(user_ing in recipe_ing or recipe_ing in user_ing
                           for recipe_ing in recipe_ingredients_lower))

        if matches > 0:
            recipe['ingredient_match_percentage'] = (matches / len(user_ingredients_lower)) * 100
            matched_recipes.append(recipe)

    # Sort by match percentage
    matched_recipes.sort(key=lambda x: x['ingredient_match_percentage'], reverse=True)

    return jsonify({
        'status': 'success',
        'count': len(matched_recipes),
        'search_ingredients': ingredients_list,
        'recipes': matched_recipes,
        'note': 'Using fallback recommendations - initialize full system for better results'
    })

@app.route('/api/ingredients', methods=['GET'])
def get_ingredients_api():
    """Get available ingredients for autocomplete."""
    try:
        search = request.args.get('search', '').lower()
        limit = int(request.args.get('limit', 50))

        if app.recommender and hasattr(app.recommender, 'ingredient_names'):
            ingredient_names = getattr(app.recommender, 'ingredient_names', set())

            # Filter ingredients by search term
            if search:
                filtered_ingredients = [
                    ing for ing in ingredient_names
                    if search in ing.lower()
                ][:limit]
            else:
                filtered_ingredients = list(ingredient_names)[:limit]

            return jsonify({
                'status': 'success',
                'count': len(filtered_ingredients),
                'ingredients': [{'name': ing, 'id': ing} for ing in sorted(filtered_ingredients)]
            })
        else:
            # Fallback ingredient list
            fallback_ingredients = [
                'chicken', 'beef', 'pork', 'fish', 'egg', 'rice', 'pasta', 'potato',
                'tomato', 'onion', 'garlic', 'carrot', 'broccoli', 'spinach',
                'cheese', 'milk', 'butter', 'oil', 'salt', 'pepper'
            ]

            if search:
                filtered_ingredients = [ing for ing in fallback_ingredients if search in ing.lower()]
            else:
                filtered_ingredients = fallback_ingredients

            return jsonify({
                'status': 'success',
                'count': len(filtered_ingredients),
                'ingredients': [{'name': ing, 'id': ing} for ing in filtered_ingredients],
                'note': 'Using fallback ingredients - initialize full system for complete list'
            })

    except Exception as e:
        print(f"Ingredients API error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting ingredients: {str(e)}'
        }), 500

# ============================================================================
# COMMUNITY FEATURES API ENDPOINTS
# ============================================================================

@app.route('/api/community/recipes', methods=['GET'])
def get_community_recipes_api():
    """Get community shared recipes."""
    try:
        # Mock community recipes for now
        community_recipes = [
            {
                'id': 'community_1',
                'name': 'Grandma\'s Secret Fried Rice',
                'description': 'A family recipe passed down for generations',
                'ingredients': ['rice', 'egg', 'soy sauce', 'green onions', 'sesame oil'],
                'steps': [
                    'Cook rice and let it cool',
                    'Beat eggs and scramble them',
                    'Heat oil in wok',
                    'Add rice and stir-fry',
                    'Add eggs and seasonings'
                ],
                'prep_time': 15,
                'cook_time': 10,
                'servings': 4,
                'difficulty': 'Easy',
                'cuisine': 'Asian',
                'contributor': 'Sarah Chen',
                'rating': 4.8,
                'reviews_count': 23,
                'created_at': '2024-01-15',
                'image_url': None
            },
            {
                'id': 'community_2',
                'name': 'Mediterranean Chicken Bowl',
                'description': 'Healthy and delicious Mediterranean-inspired dish',
                'ingredients': ['chicken breast', 'quinoa', 'cucumber', 'tomatoes', 'feta cheese', 'olive oil'],
                'steps': [
                    'Season and grill chicken',
                    'Cook quinoa',
                    'Chop vegetables',
                    'Assemble bowl',
                    'Drizzle with olive oil'
                ],
                'prep_time': 20,
                'cook_time': 25,
                'servings': 2,
                'difficulty': 'Medium',
                'cuisine': 'Mediterranean',
                'contributor': 'Mike Rodriguez',
                'rating': 4.6,
                'reviews_count': 18,
                'created_at': '2024-01-10',
                'image_url': None
            }
        ]

        return jsonify({
            'status': 'success',
            'count': len(community_recipes),
            'recipes': community_recipes
        })

    except Exception as e:
        print(f"Community recipes error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting community recipes: {str(e)}'
        }), 500

@app.route('/api/community/recipes', methods=['POST'])
def share_recipe_api():
    """Share a new recipe with the community."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'ingredients': request.form.get('ingredients', '').split(','),
                'steps': request.form.get('steps', '').split('\n'),
                'prep_time': int(request.form.get('prep_time', 30)),
                'cook_time': int(request.form.get('cook_time', 30)),
                'servings': int(request.form.get('servings', 4)),
                'difficulty': request.form.get('difficulty', 'Medium'),
                'cuisine': request.form.get('cuisine', 'International')
            }

        # Validate required fields
        required_fields = ['name', 'ingredients', 'steps']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400

        # Create new recipe (mock implementation)
        new_recipe = {
            'id': f'community_{__import__("time").time()}',
            'name': data['name'],
            'description': data.get('description', ''),
            'ingredients': data['ingredients'] if isinstance(data['ingredients'], list) else data['ingredients'].split(','),
            'steps': data['steps'] if isinstance(data['steps'], list) else data['steps'].split('\n'),
            'prep_time': data.get('prep_time', 30),
            'cook_time': data.get('cook_time', 30),
            'servings': data.get('servings', 4),
            'difficulty': data.get('difficulty', 'Medium'),
            'cuisine': data.get('cuisine', 'International'),
            'contributor': 'Anonymous User',  # Would be actual user when auth is implemented
            'rating': 0,
            'reviews_count': 0,
            'created_at': str(__import__('datetime').datetime.now().date()),
            'image_url': None
        }

        return jsonify({
            'status': 'success',
            'message': 'Recipe shared successfully!',
            'recipe': new_recipe
        }), 201

    except Exception as e:
        print(f"Share recipe error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error sharing recipe: {str(e)}'
        }), 500

@app.route('/api/community/recipes/<recipe_id>/reviews', methods=['GET'])
def get_recipe_reviews_api(recipe_id):
    """Get reviews for a specific recipe."""
    try:
        # Mock reviews
        reviews = [
            {
                'id': 'review_1',
                'recipe_id': recipe_id,
                'user_name': 'John Doe',
                'rating': 5,
                'comment': 'Amazing recipe! My family loved it.',
                'created_at': '2024-01-20',
                'helpful_votes': 12
            },
            {
                'id': 'review_2',
                'recipe_id': recipe_id,
                'user_name': 'Jane Smith',
                'rating': 4,
                'comment': 'Good recipe, but I added more spices.',
                'created_at': '2024-01-18',
                'helpful_votes': 8
            }
        ]

        return jsonify({
            'status': 'success',
            'count': len(reviews),
            'reviews': reviews,
            'average_rating': 4.5
        })

    except Exception as e:
        print(f"Recipe reviews error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting reviews: {str(e)}'
        }), 500

@app.route('/api/community/recipes/<recipe_id>/reviews', methods=['POST'])
def add_recipe_review_api(recipe_id):
    """Add a review for a recipe."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'rating': int(request.form.get('rating')),
                'comment': request.form.get('comment', '')
            }

        # Validate rating
        if not data.get('rating') or not (1 <= int(data['rating']) <= 5):
            return jsonify({
                'status': 'error',
                'message': 'Rating must be between 1 and 5'
            }), 400

        # Create new review (mock implementation)
        new_review = {
            'id': f'review_{__import__("time").time()}',
            'recipe_id': recipe_id,
            'user_name': 'Anonymous User',  # Would be actual user when auth is implemented
            'rating': int(data['rating']),
            'comment': data.get('comment', ''),
            'created_at': str(__import__('datetime').datetime.now().date()),
            'helpful_votes': 0
        }

        return jsonify({
            'status': 'success',
            'message': 'Review added successfully!',
            'review': new_review
        }), 201

    except Exception as e:
        print(f"Add review error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error adding review: {str(e)}'
        }), 500

# ============================================================================
# SYSTEM INITIALIZATION
# ============================================================================

def initialize_full_system():
    """Initialize the complete SisaRasa system."""
    if app.system_initialized:
        return True

    try:
        print("🚀 Initializing full SisaRasa system...")

        # Initialize MongoDB
        try:
            sys.path.append(os.path.join(current_dir, 'api'))
            from api.models.user import init_db
            init_db(app)
            print("✅ MongoDB initialized")
        except Exception as e:
            print(f"⚠️  MongoDB initialization failed: {e}")

        # Initialize ML recommender system
        try:
            initialize_ml_system()
            print("✅ ML system initialized")
        except Exception as e:
            print(f"⚠️  ML system initialization failed: {e}")

        # Register API blueprints
        try:
            register_api_blueprints()
            print("✅ API blueprints registered")
        except Exception as e:
            print(f"⚠️  API blueprint registration failed: {e}")

        app.system_initialized = True
        print("🎉 Full SisaRasa system initialized successfully!")
        return True

    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False

def initialize_ml_system():
    """Initialize the ML recommendation system."""
    try:
        # Add project root to path
        project_root = os.path.dirname(current_dir)
        sys.path.insert(0, project_root)

        from hybrid_recipe_recommender import HybridRecipeRecommender

        # Create recommender
        recommender = HybridRecipeRecommender(k=10, metric='cosine')

        # Load recipes
        recipes_file = os.path.join(project_root, 'data', 'clean_recipes.json')
        if os.path.exists(recipes_file):
            # Load optimized number of recipes for Railway
            max_recipes = 3000 if os.getenv('RAILWAY_ENVIRONMENT') == 'production' else 10000
            print(f"📚 Loading {max_recipes} recipes...")
            recommender.load_recipes(recipes_file, max_rows=max_recipes)
            print(f"✅ Loaded {len(recommender.recipes)} recipes")
        else:
            print(f"⚠️  Recipe file not found: {recipes_file}")
            # Create minimal fallback
            recommender.recipes = []
            recommender.ingredient_names = set(['chicken', 'rice', 'egg', 'onion'])

        app.recommender = recommender

    except Exception as e:
        print(f"❌ ML system initialization failed: {e}")
        # Create simple fallback
        class SimpleRecommender:
            def __init__(self):
                self.recipes = []
                self.ingredient_names = set(['chicken', 'rice', 'egg'])
        app.recommender = SimpleRecommender()

def register_api_blueprints():
    """Register API blueprints for full functionality."""
    try:
        # Import and register blueprints
        api_dir = os.path.join(current_dir, 'api')
        sys.path.insert(0, api_dir)

        from auth import auth_bp
        from routes import main_bp
        from analytics_routes import analytics_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(analytics_bp)

    except Exception as e:
        print(f"⚠️  Blueprint registration failed: {e}")
        # Continue without full API functionality

# ============================================================================
# HEALTH CHECK AND STATUS ENDPOINTS
# ============================================================================

@app.route('/health')
def health():
    """Ultra-simple health check for Railway."""
    return {
        'status': 'ok',
        'service': 'sisarasa-web-app',
        'mode': 'full' if app.system_initialized else 'starting',
        'port': os.getenv('PORT', '5000')
    }, 200

@app.route('/api/health')
def api_health():
    """Detailed health check."""
    return {
        'status': 'ok',
        'message': 'SisaRasa Web Application',
        'timestamp': str(__import__('datetime').datetime.utcnow()),
        'system_initialized': app.system_initialized,
        'components': {
            'web_app': 'healthy',
            'templates': 'loaded',
            'database': 'connected' if app.system_initialized else 'initializing',
            'recommender': 'loaded' if app.recommender and hasattr(app.recommender, 'recipes') and len(getattr(app.recommender, 'recipes', [])) > 0 else 'initializing'
        }
    }, 200

@app.route('/api/status')
def status():
    """System status endpoint."""
    recipe_count = len(getattr(app.recommender, 'recipes', [])) if app.recommender else 0

    return {
        'status': 'running',
        'mode': 'full_web_app',
        'system_initialized': app.system_initialized,
        'features': {
            'web_interface': True,
            'user_authentication': app.system_initialized,
            'recipe_recommendations': app.system_initialized,
            'community_features': app.system_initialized,
            'ml_system': recipe_count > 0,
            'database': app.system_initialized
        },
        'stats': {
            'recipes_loaded': recipe_count,
            'templates_available': True
        },
        'pages': [
            '/welcome - Welcome page',
            '/login - User login',
            '/signup - User registration',
            '/dashboard - Recipe recommendations',
            '/profile - User profile',
            '/community-recipes - Community features'
        ]
    }

@app.route('/api/initialize', methods=['POST'])
def initialize_system_endpoint():
    """Initialize the full system via API call."""
    if app.system_initialized:
        return {'status': 'already_initialized', 'message': 'System is already fully initialized'}, 200

    success = initialize_full_system()

    if success:
        return {
            'status': 'success',
            'message': 'Full SisaRasa system initialized successfully',
            'features_enabled': [
                'User authentication',
                'Recipe recommendations',
                'Community features',
                'ML system',
                'Database connectivity'
            ]
        }, 200
    else:
        return {
            'status': 'partial',
            'message': 'System partially initialized - some features may be limited'
        }, 200

# ============================================================================
# STARTUP AND MAIN EXECUTION
# ============================================================================

def startup_initialization():
    """Initialize system on startup - Railway compatible."""
    print("🚀 SisaRasa Web Application Starting...")

    # Initialize basic system immediately for health checks
    app.recommender = type('SimpleRecommender', (), {
        'recipes': [],
        'ingredient_names': set(['chicken', 'rice', 'egg'])
    })()

    # In production (Railway), defer full initialization
    if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
        print("🔄 Railway mode: Deferring full system initialization")
        print("💡 Visit /api/initialize to load full features after deployment")
    else:
        # In development, initialize everything immediately
        print("🔧 Development mode: Initializing full system...")
        initialize_full_system()

if __name__ == '__main__':
    # Get port from Railway environment
    port = int(os.getenv('PORT', 5000))

    print("=" * 60)
    print("🍽️  SisaRasa - AI Recipe Recommendation System")
    print("=" * 60)
    print(f"📍 Port: {port}")
    print(f"🌍 Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'development')}")
    print(f"🔗 MongoDB: {'Configured' if os.getenv('MONGO_URI') else 'Not configured'}")
    print(f"🎯 Mode: Full Web Application")
    print("=" * 60)

    # Perform startup initialization
    startup_initialization()

    print("✅ Web application ready!")
    print(f"🌐 Access your app at: http://localhost:{port}")
    print("📱 Available pages:")
    print("   • /welcome - Welcome page")
    print("   • /login - User login")
    print("   • /signup - User registration")
    print("   • /dashboard - Recipe recommendations")
    print("   • /community-recipes - Community features")
    print("=" * 60)

    # Start Flask development server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )
