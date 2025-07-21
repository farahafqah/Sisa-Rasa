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

# Debug path information
print(f"🔧 Current directory: {current_dir}")
print(f"🔧 API directory: {os.path.join(current_dir, 'api')}")
print(f"🔧 API directory exists: {os.path.exists(os.path.join(current_dir, 'api'))}")
print(f"🔧 Auth file exists: {os.path.exists(os.path.join(current_dir, 'api', 'auth.py'))}")

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
    """Home page - serve the actual home.html template."""
    try:
        # Check if template exists
        template_path = os.path.join(current_dir, 'api', 'templates', 'home.html')
        if not os.path.exists(template_path):
            print(f"❌ Home template not found at: {template_path}")
            return create_fallback_home_page()

        return render_template('home.html')
    except Exception as e:
        print(f"❌ Error loading home template: {e}")
        return create_fallback_home_page()

@app.route('/home')
def home_alt():
    """Alternative home route."""
    return home()

def create_fallback_home_page():
    """Create a fallback home page when template fails."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sisa Rasa - Home</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <link href='https://cdn.jsdelivr.net/npm/boxicons@2.0.5/css/boxicons.min.css' rel='stylesheet'>
        <style>
            body {{
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #f1ead1, #e1cc7f);
                min-height: 100vh;
                margin: 0;
            }}
            .navbar {{ background: #f1ead1 !important; }}
            .hero {{ background: rgba(255,255,255,0.95); border-radius: 15px; padding: 3rem; margin: 2rem 0; }}
            .btn-custom {{ background: #e1cc7f; border: none; color: #0b0a0a; font-weight: 600; }}
            .btn-custom:hover {{ background: #f9e59a; color: #0b0a0a; }}
            .feature-card {{ background: rgba(255,255,255,0.9); border-radius: 10px; padding: 1.5rem; margin: 1rem 0; }}
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-light">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/">🍽️ Sisa Rasa</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/welcome">Welcome</a>
                    <a class="nav-link" href="/login">Login</a>
                    <a class="nav-link" href="/signup">Sign Up</a>
                </div>
            </div>
        </nav>

        <!-- Hero Section -->
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-10">
                    <div class="hero text-center">
                        <h1 class="display-3 mb-4">🍽️ Sisa Rasa</h1>
                        <p class="lead mb-4">Transform Your Leftovers Into Delicious Meals</p>
                        <p class="mb-4">AI-powered recipe recommendations that help reduce food waste while creating amazing dishes from ingredients you already have.</p>

                        <div class="row mb-5">
                            <div class="col-md-4 mb-3">
                                <a href="/signup" class="btn btn-custom btn-lg w-100">🚀 Get Started</a>
                            </div>
                            <div class="col-md-4 mb-3">
                                <a href="/login" class="btn btn-outline-secondary btn-lg w-100">🔐 Login</a>
                            </div>
                            <div class="col-md-4 mb-3">
                                <a href="/welcome" class="btn btn-outline-info btn-lg w-100">📊 Learn More</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Features -->
            <div class="row">
                <div class="col-md-4">
                    <div class="feature-card text-center">
                        <i class='bx bx-search-alt-2 bx-lg mb-3' style="color: #e1cc7f;"></i>
                        <h4>Smart Recipe Search</h4>
                        <p>Enter your available ingredients and get personalized recipe recommendations powered by AI.</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="feature-card text-center">
                        <i class='bx bx-group bx-lg mb-3' style="color: #e1cc7f;"></i>
                        <h4>Community Sharing</h4>
                        <p>Share your favorite recipes and discover new ones from our community of food enthusiasts.</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="feature-card text-center">
                        <i class='bx bx-leaf bx-lg mb-3' style="color: #e1cc7f;"></i>
                        <h4>Reduce Food Waste</h4>
                        <p>Make the most of your ingredients and contribute to a more sustainable future.</p>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

@app.route('/welcome')
def welcome():
    """Welcome page with analytics and recipe information."""
    try:
        # Check if template exists
        template_path = os.path.join(current_dir, 'api', 'templates', 'welcome.html')
        if not os.path.exists(template_path):
            print(f"❌ Welcome template not found at: {template_path}")
            return create_fallback_welcome_page()

        return render_template('welcome.html')
    except Exception as e:
        print(f"❌ Error loading welcome template: {e}")
        return create_fallback_welcome_page()

def create_fallback_welcome_page():
    """Create a fallback welcome page when template fails."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SisaRasa - Welcome</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #f1ead1, #e1cc7f); min-height: 100vh; }}
            .hero {{ background: rgba(255,255,255,0.9); border-radius: 15px; padding: 3rem; margin: 2rem 0; }}
            .btn-custom {{ background: #e1cc7f; border: none; color: #0b0a0a; font-weight: 600; }}
            .btn-custom:hover {{ background: #f9e59a; color: #0b0a0a; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="hero text-center">
                        <h1 class="display-4 mb-4">🍽️ Welcome to SisaRasa</h1>
                        <p class="lead mb-4">Your AI-powered recipe recommendation system</p>
                        <p class="mb-4">Reduce food waste and discover amazing recipes with ingredients you already have!</p>

                        <div class="row mb-4">
                            <div class="col-md-6 mb-3">
                                <a href="/login" class="btn btn-custom btn-lg w-100">🔐 Login</a>
                            </div>
                            <div class="col-md-6 mb-3">
                                <a href="/signup" class="btn btn-outline-secondary btn-lg w-100">📝 Sign Up</a>
                            </div>
                        </div>

                        <div class="alert alert-info">
                            <strong>System Status:</strong> {'✅ Fully Initialized' if app.system_initialized else '🔄 Starting up...'}
                        </div>

                        <div class="row text-start">
                            <div class="col-md-4">
                                <h5>🔍 Smart Search</h5>
                                <p>Find recipes based on your available ingredients</p>
                            </div>
                            <div class="col-md-4">
                                <h5>👥 Community</h5>
                                <p>Share and discover recipes from other users</p>
                            </div>
                            <div class="col-md-4">
                                <h5>📊 Analytics</h5>
                                <p>Track your cooking habits and preferences</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - handles both GET (show form) and POST (process form)."""
    if request.method == 'POST':
        # Handle form submission by redirecting to API
        try:
            # Get form data
            email = request.form.get('email')
            password = request.form.get('password')

            if not email or not password:
                return create_fallback_login_page(error="Email and password are required")

            # Try direct API call first, then fallback to internal processing
            try:
                import requests
                api_url = request.url_root.rstrip('/') + '/api/auth/login'
                response = requests.post(api_url, json={
                    'email': email,
                    'password': password
                }, timeout=10)

                if response.status_code == 200:
                    # Login successful - redirect to dashboard
                    return redirect(url_for('dashboard'))
                else:
                    # Login failed
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', 'Login failed')
                    except:
                        error_msg = f'Login failed (Status: {response.status_code})'
                    return create_fallback_login_page(error=error_msg)

            except Exception as api_error:
                print(f"API call failed, trying direct authentication: {api_error}")

                # Fallback: Try direct authentication
                try:
                    from api.models.user import get_user_by_email, verify_password
                    user = get_user_by_email(email)

                    if user and verify_password(user, password):
                        # Direct login successful
                        return redirect(url_for('dashboard'))
                    else:
                        return create_fallback_login_page(error="Invalid email or password")

                except Exception as direct_auth_error:
                    print(f"Direct authentication failed: {direct_auth_error}")
                    return create_fallback_login_page(error="Authentication system temporarily unavailable")

        except Exception as e:
            print(f"Login form processing error: {e}")
            return create_fallback_login_page(error="Login system temporarily unavailable")

    # GET request - show login form
    try:
        return render_template('login.html')
    except Exception as e:
        print(f"Error loading login template: {e}")
        return create_fallback_login_page()

def create_fallback_login_page(error=None):
    """Create a fallback login page when template fails."""
    error_html = f'<div class="alert alert-danger">{error}</div>' if error else ''

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SisaRasa - Login</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #f1ead1, #e1cc7f); min-height: 100vh; }}
            .login-form {{ background: rgba(255,255,255,0.95); border-radius: 15px; padding: 2rem; margin: 3rem 0; }}
            .btn-custom {{ background: #e1cc7f; border: none; color: #0b0a0a; font-weight: 600; }}
            .btn-custom:hover {{ background: #f9e59a; color: #0b0a0a; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="login-form">
                        <h2 class="text-center mb-4">🔐 Login to SisaRasa</h2>
                        {error_html}
                        <form method="post" action="/login">
                            <div class="mb-3">
                                <label for="email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" name="email" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-custom w-100 mb-3">Login</button>
                        </form>
                        <div class="text-center">
                            <p><a href="/signup">Don't have an account? Sign up</a></p>
                            <p><a href="/welcome">← Back to Welcome</a></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Sign up page - handles both GET (show form) and POST (process form)."""
    if request.method == 'POST':
        # Handle form submission by redirecting to API
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')

            if not name or not email or not password:
                return create_fallback_signup_page(error="All fields are required")

            # Try direct API call first, then fallback to internal processing
            try:
                import requests
                api_url = request.url_root.rstrip('/') + '/api/auth/signup'
                response = requests.post(api_url, json={
                    'name': name,
                    'email': email,
                    'password': password
                }, timeout=10)

                if response.status_code == 201:
                    # Signup successful - redirect to login
                    return redirect(url_for('login') + '?message=Registration successful! Please login.')
                else:
                    # Signup failed
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', 'Registration failed')
                    except:
                        error_msg = f'Registration failed (Status: {response.status_code})'
                    return create_fallback_signup_page(error=error_msg)

            except Exception as api_error:
                print(f"API call failed, trying direct registration: {api_error}")

                # Fallback: Try direct user creation
                try:
                    from api.models.user import create_user, get_user_by_email

                    # Check if user already exists
                    if get_user_by_email(email):
                        return create_fallback_signup_page(error="Email already registered")

                    # Validate password length
                    if len(password) < 6:
                        return create_fallback_signup_page(error="Password must be at least 6 characters long")

                    # Create user directly
                    user = create_user(name=name, email=email, password=password)

                    if user:
                        return redirect(url_for('login') + '?message=Registration successful! Please login.')
                    else:
                        return create_fallback_signup_page(error="Failed to create user account")

                except Exception as direct_create_error:
                    print(f"Direct user creation failed: {direct_create_error}")
                    return create_fallback_signup_page(error="Registration system temporarily unavailable")

        except Exception as e:
            print(f"Signup form processing error: {e}")
            return create_fallback_signup_page(error="Registration system temporarily unavailable")

    # GET request - show signup form
    try:
        return render_template('signup.html')
    except Exception as e:
        print(f"Error loading signup template: {e}")
        return create_fallback_signup_page()

def create_fallback_signup_page(error=None):
    """Create a fallback signup page when template fails."""
    error_html = f'<div class="alert alert-danger">{error}</div>' if error else ''

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SisaRasa - Sign Up</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #f1ead1, #e1cc7f); min-height: 100vh; }}
            .signup-form {{ background: rgba(255,255,255,0.95); border-radius: 15px; padding: 2rem; margin: 3rem 0; }}
            .btn-custom {{ background: #e1cc7f; border: none; color: #0b0a0a; font-weight: 600; }}
            .btn-custom:hover {{ background: #f9e59a; color: #0b0a0a; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="signup-form">
                        <h2 class="text-center mb-4">📝 Join SisaRasa</h2>
                        {error_html}
                        <form method="post" action="/signup">
                            <div class="mb-3">
                                <label for="name" class="form-label">Full Name</label>
                                <input type="text" class="form-control" id="name" name="name" required>
                            </div>
                            <div class="mb-3">
                                <label for="email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" name="email" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                                <div class="form-text">Password must be at least 6 characters long</div>
                            </div>
                            <button type="submit" class="btn btn-custom w-100 mb-3">Sign Up</button>
                        </form>
                        <div class="text-center">
                            <p><a href="/login">Already have an account? Login</a></p>
                            <p><a href="/welcome">← Back to Welcome</a></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
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

def register_auth_blueprints():
    """Register authentication blueprints - critical for login/signup."""
    try:
        # Import and register authentication blueprint
        api_dir = os.path.join(current_dir, 'api')
        print(f"🔧 Attempting to register auth blueprints from: {api_dir}")
        print(f"🔧 API directory exists: {os.path.exists(api_dir)}")
        print(f"🔧 Auth file exists: {os.path.exists(os.path.join(api_dir, 'auth.py'))}")

        if api_dir not in sys.path:
            sys.path.insert(0, api_dir)
            print(f"🔧 Added {api_dir} to sys.path")

        # Try multiple import paths to ensure compatibility
        auth_bp = None

        # Method 1: Direct import from current directory structure
        try:
            # Since we're in src/ and api/ is in src/api/, we can import directly
            sys.path.insert(0, os.path.join(current_dir, 'api'))
            from auth import auth_bp
            print("✅ Imported auth blueprint from auth module")
        except ImportError as e1:
            print(f"⚠️  Method 1 failed: {e1}")

            # Method 2: Try with api prefix
            try:
                from api.auth import auth_bp
                print("✅ Imported auth blueprint from api.auth")
            except ImportError as e2:
                print(f"⚠️  Method 2 failed: {e2}")

                # Method 3: Manual module loading
                try:
                    import importlib.util
                    auth_file_path = os.path.join(current_dir, 'api', 'auth.py')
                    spec = importlib.util.spec_from_file_location("auth", auth_file_path)
                    auth_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(auth_module)
                    auth_bp = auth_module.auth_bp
                    print("✅ Imported auth blueprint via manual loading")
                except Exception as e3:
                    print(f"❌ All import methods failed. Last error: {e3}")
                    raise e3

        if auth_bp:
            app.register_blueprint(auth_bp)
            print("✅ Authentication blueprint registered successfully")

            # Test the blueprint registration
            try:
                with app.app_context():
                    # Check if auth routes are available
                    auth_routes = [rule.rule for rule in app.url_map.iter_rules() if rule.rule.startswith('/api/auth')]
                    print(f"✅ Registered auth routes: {auth_routes}")
                    if not auth_routes:
                        print("⚠️  No auth routes found after registration")
            except Exception as route_check_error:
                print(f"⚠️  Route check failed: {route_check_error}")
        else:
            raise Exception("auth_bp is None after all import attempts")

    except Exception as e:
        print(f"❌ Authentication blueprint registration failed: {e}")
        print(f"❌ Current working directory: {os.getcwd()}")
        print(f"❌ Current sys.path (first 5): {sys.path[:5]}")
        print(f"❌ Files in api directory: {os.listdir(api_dir) if os.path.exists(api_dir) else 'Directory not found'}")
        raise e  # Re-raise to ensure we know auth failed

def register_other_blueprints():
    """Register other API blueprints for additional functionality."""
    try:
        # Import and register other blueprints
        api_dir = os.path.join(current_dir, 'api')
        if api_dir not in sys.path:
            sys.path.insert(0, api_dir)

        # Try to import main routes blueprint
        try:
            from api.routes import main_bp
            app.register_blueprint(main_bp)
            print("✅ Main routes blueprint registered")
        except ImportError:
            try:
                from routes import main_bp
                app.register_blueprint(main_bp)
                print("✅ Main routes blueprint registered (fallback import)")
            except ImportError as e:
                print(f"⚠️  Main routes blueprint import failed: {e}")

        # Try to import analytics blueprint
        try:
            from api.analytics_routes import analytics_bp
            app.register_blueprint(analytics_bp)
            print("✅ Analytics blueprint registered")
        except ImportError:
            try:
                from analytics_routes import analytics_bp
                app.register_blueprint(analytics_bp)
                print("✅ Analytics blueprint registered (fallback import)")
            except ImportError as e:
                print(f"⚠️  Analytics blueprint import failed: {e}")

        print("✅ Additional API blueprints registration completed")

    except Exception as e:
        print(f"⚠️  Additional blueprint registration failed: {e}")
        # Continue without full API functionality

def register_api_blueprints():
    """Register all API blueprints for full functionality."""
    try:
        register_auth_blueprints()
        register_other_blueprints()

    except Exception as e:
        print(f"⚠️  Full blueprint registration failed: {e}")
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

    # CRITICAL: Always initialize database and authentication first
    print("🔧 Initializing essential systems...")

    # Initialize MongoDB connection
    try:
        api_path = os.path.join(current_dir, 'api')
        if api_path not in sys.path:
            sys.path.append(api_path)

        print(f"🔧 Initializing MongoDB connection...")
        print(f"🔧 API path: {api_path}")
        print(f"🔧 API path exists: {os.path.exists(api_path)}")

        # Set up MongoDB URI in app config
        MONGO_URI = None
        try:
            # Try importing from config first
            sys.path.insert(0, api_path)
            from config import MONGO_URI as CONFIG_MONGO_URI
            MONGO_URI = CONFIG_MONGO_URI
            print("✅ MongoDB URI loaded from config.py")
        except ImportError as config_error:
            print(f"⚠️  Config import failed: {config_error}")
            # Fallback to environment variable
            MONGO_URI = os.getenv('MONGO_URI')
            if MONGO_URI:
                print("✅ MongoDB URI loaded from environment variable")
            else:
                print("❌ No MongoDB URI found in config or environment")
                raise Exception("No MongoDB URI available")

        if MONGO_URI:
            app.config['MONGO_URI'] = MONGO_URI
            # Mask sensitive parts for logging
            masked_uri = MONGO_URI
            if '@' in MONGO_URI and '://' in MONGO_URI:
                try:
                    parts = MONGO_URI.split('://')
                    protocol = parts[0]
                    rest = parts[1]
                    if '@' in rest:
                        credentials, host_part = rest.split('@', 1)
                        masked_uri = f"{protocol}://***:***@{host_part}"
                except:
                    masked_uri = "mongodb://***:***@***"
            print(f"🔗 MongoDB URI configured: {masked_uri}")

        # Initialize database connection
        try:
            # Try multiple import methods for user model
            user_module = None
            try:
                from models.user import init_db, mongo
                user_module = "models.user"
                print("✅ Imported user model from models.user")
            except ImportError:
                try:
                    from api.models.user import init_db, mongo
                    user_module = "api.models.user"
                    print("✅ Imported user model from api.models.user")
                except ImportError as e:
                    print(f"❌ Failed to import user model: {e}")
                    raise e

            init_db(app)
            print("✅ MongoDB connection initialized")

        except Exception as init_error:
            print(f"❌ Database initialization failed: {init_error}")
            raise init_error

        # Test the connection with detailed error handling
        try:
            with app.app_context():
                # Try to ping the database
                result = mongo.db.command('ping')
                print("✅ MongoDB connection verified - database is responsive")

                # Test user collection access
                user_count = mongo.db.users.count_documents({})
                print(f"✅ User collection accessible - {user_count} users in database")

                # Mark database as available
                app.config['DATABASE_AVAILABLE'] = True

        except Exception as db_test_error:
            print(f"❌ MongoDB connection test failed: {db_test_error}")
            print(f"❌ This will cause authentication failures")
            app.config['DATABASE_AVAILABLE'] = False
            raise db_test_error

    except Exception as e:
        print(f"❌ MongoDB initialization failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Error details: {str(e)}")
        print(f"❌ This will cause user registration and login to fail")
        print(f"❌ Environment MONGO_URI set: {'Yes' if os.getenv('MONGO_URI') else 'No'}")
        # Continue without database - some features will be limited
        app.config['DATABASE_AVAILABLE'] = False

    # Register authentication blueprints immediately (critical for login/signup)
    auth_success = False
    try:
        register_auth_blueprints()
        print("✅ Authentication system initialized")
        auth_success = True
    except Exception as e:
        print(f"❌ Authentication initialization failed: {e}")
        print("🚨 CRITICAL: Users will not be able to register or login!")

        # Try alternative authentication setup
        try:
            print("🔄 Attempting alternative authentication setup...")
            alternative_auth_setup()
            auth_success = True
            print("✅ Alternative authentication setup successful")
        except Exception as alt_e:
            print(f"❌ Alternative authentication setup also failed: {alt_e}")

    # Register other API blueprints
    try:
        register_other_blueprints()
        print("✅ Additional API blueprints registered")
    except Exception as e:
        print(f"⚠️  Additional API blueprint registration failed: {e}")

    # Set system initialization status
    if auth_success and app.config.get('DATABASE_AVAILABLE', False):
        app.system_initialized = True
        print("🎉 System fully initialized - all features available")
    elif auth_success:
        app.system_initialized = True
        print("⚠️  System partially initialized - authentication works but database limited")
    else:
        app.system_initialized = False
        print("❌ System initialization incomplete - authentication unavailable")

    # In production (Railway), defer ML system initialization
    if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
        print("🔄 Railway mode: ML system can be initialized via /api/initialize")
    else:
        # In development, initialize ML system if basic systems work
        if app.system_initialized:
            print("🔧 Development mode: Initializing ML system...")
            try:
                initialize_ml_system()
                print("✅ ML system initialized")
            except Exception as ml_e:
                print(f"⚠️  ML system initialization failed: {ml_e}")

def alternative_auth_setup():
    """Alternative authentication setup method."""
    print("🔧 Setting up authentication via alternative method...")

    # Create minimal auth routes directly in the main app
    from flask import request, jsonify

    @app.route('/api/auth/signup', methods=['POST'])
    def alt_signup():
        try:
            data = request.get_json()
            if not data or not all(k in data for k in ['name', 'email', 'password']):
                return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

            # Try direct user creation
            from api.models.user import create_user, get_user_by_email

            if get_user_by_email(data['email']):
                return jsonify({'status': 'error', 'message': 'Email already registered'}), 409

            if len(data['password']) < 6:
                return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters'}), 400

            user = create_user(data['name'], data['email'], data['password'])
            if user:
                return jsonify({
                    'status': 'success',
                    'message': 'User registered successfully',
                    'user': {'id': str(user['_id']), 'name': user['name'], 'email': user['email']}
                }), 201
            else:
                return jsonify({'status': 'error', 'message': 'Failed to create user'}), 500

        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Registration error: {str(e)}'}), 500

    @app.route('/api/auth/login', methods=['POST'])
    def alt_login():
        try:
            data = request.get_json()
            if not data or not all(k in data for k in ['email', 'password']):
                return jsonify({'status': 'error', 'message': 'Missing email or password'}), 400

            from api.models.user import get_user_by_email, verify_password
            from flask_jwt_extended import create_access_token

            user = get_user_by_email(data['email'])
            if not user or not verify_password(user, data['password']):
                return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

            token = create_access_token(identity=str(user['_id']))
            return jsonify({
                'status': 'success',
                'token': token,
                'user': {'id': str(user['_id']), 'name': user['name'], 'email': user['email']}
            }), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Login error: {str(e)}'}), 500

    print("✅ Alternative auth routes created directly in main app")

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
