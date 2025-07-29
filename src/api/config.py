"""
Configuration module for the API.

This module loads configuration from environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (only if not in Railway)
# Railway provides environment variables directly, so we only load .env for local development
if not os.getenv('RAILWAY_ENVIRONMENT'):
    # Get the absolute path to the .env file
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

    # Load the .env file from the specified path
    load_dotenv(dotenv_path=dotenv_path)
    print(f"📁 Loaded .env file from: {dotenv_path}")
else:
    print("🚂 Railway environment detected - using Railway environment variables")

# MongoDB Configuration
# Railway might use different environment variable names, so check multiple options
MONGO_URI = (
    os.getenv('MONGO_URI') or
    os.getenv('MONGODB_URI') or
    os.getenv('DATABASE_URL') or
    os.getenv('MONGODB_URL') or
    'mongodb://localhost:27017/sisarasa'
)

# Validate MongoDB URI
if not MONGO_URI or MONGO_URI == 'mongodb://localhost:27017/sisarasa':
    print("❌ WARNING: Using default MongoDB URI - check environment variables!")
    print(f"🔍 Available env vars: MONGO_URI={bool(os.getenv('MONGO_URI'))}, MONGODB_URI={bool(os.getenv('MONGODB_URI'))}, DATABASE_URL={bool(os.getenv('DATABASE_URL'))}")
else:
    print(f"✅ MongoDB URI loaded: {MONGO_URI[:20]}...")

# Additional Railway debugging
if os.getenv('RAILWAY_ENVIRONMENT'):
    print(f"🚂 Railway environment detected: {os.getenv('RAILWAY_ENVIRONMENT')}")
    print(f"🔍 Railway MongoDB env vars check:")
    print(f"  - MONGO_URI: {'✅' if os.getenv('MONGO_URI') else '❌'}")
    print(f"  - MONGODB_URI: {'✅' if os.getenv('MONGODB_URI') else '❌'}")
    print(f"  - DATABASE_URL: {'✅' if os.getenv('DATABASE_URL') else '❌'}")
    print(f"  - MONGODB_URL: {'✅' if os.getenv('MONGODB_URL') else '❌'}")

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
# Get JWT_ACCESS_TOKEN_EXPIRES and handle potential comment in the value
jwt_expires_env = os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '86400')
# Extract only the numeric part if there's a comment
jwt_expires_value = jwt_expires_env.split('#')[0].strip()
JWT_ACCESS_TOKEN_EXPIRES = int(jwt_expires_value)  # 24 hours

# API Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))

# Email Configuration (for password reset emails)
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

