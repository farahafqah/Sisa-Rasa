"""
Recipe Recommender API

This module provides a Flask-based API for the recipe recommendation system.
"""

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Sisa Rasa API is running!"

@app.route('/api/health')
def health():
    return {'status': 'ok', 'message': 'App is running'}

# Don't load heavy ML models on startup
# from api.routes import main_bp
# app.register_blueprint(main_bp)


