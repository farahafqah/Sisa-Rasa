"""
Configuration module for the API.

This module loads configuration from environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
# Get the absolute path to the .env file
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Load the .env file from the specified path
load_dotenv(dotenv_path=dotenv_path)

# MongoDB Configuration
# Get the MongoDB URI from the environment with Railway-friendly defaults
MONGO_URI = os.getenv('MONGO_URI')

# If no MONGO_URI is set, use Railway's internal MongoDB or fallback
if not MONGO_URI:
    # Check for Railway's MongoDB plugin environment variables
    railway_mongo_host = os.getenv('MONGOHOST')
    railway_mongo_port = os.getenv('MONGOPORT', '27017')
    railway_mongo_user = os.getenv('MONGOUSER')
    railway_mongo_password = os.getenv('MONGOPASSWORD')
    railway_mongo_database = os.getenv('MONGODATABASE', 'sisarasa')

    if railway_mongo_host and railway_mongo_user and railway_mongo_password:
        # Use Railway's MongoDB plugin
        MONGO_URI = f"mongodb://{railway_mongo_user}:{railway_mongo_password}@{railway_mongo_host}:{railway_mongo_port}/{railway_mongo_database}"
        print(f"🔗 Using Railway MongoDB plugin: {railway_mongo_host}")
    else:
        # Fallback to localhost for development
        MONGO_URI = 'mongodb://localhost:27017/sisarasa'
        print("⚠️  Using localhost MongoDB - ensure MongoDB is running locally")

print(f"🔗 MongoDB URI configured: {MONGO_URI.replace(MONGO_URI.split('@')[0].split('//')[1] + '@', '***:***@') if '@' in MONGO_URI else MONGO_URI}")

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
# Get JWT_ACCESS_TOKEN_EXPIRES and handle potential comment in the value
jwt_expires_env = os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '86400')
# Extract only the numeric part if there's a comment
jwt_expires_value = jwt_expires_env.split('#')[0].strip()
JWT_ACCESS_TOKEN_EXPIRES = int(jwt_expires_value)  # 24 hours

# API Configuration
DEBUG = os.getenv('RAILWAY_ENVIRONMENT') != 'production'
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

