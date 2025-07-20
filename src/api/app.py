"""
Recipe Recommender API

This module provides a Flask-based API for the recipe recommendation system.
"""

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Import routes
from api.routes import main_bp
app.register_blueprint(main_bp)

# Simple health check
@app.route('/api/health')
def health():
    return {'status': 'ok', 'message': 'App is running'}

@app.route('/')
def home():
    return "Sisa Rasa API is running!"

