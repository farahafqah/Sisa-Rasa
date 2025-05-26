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
# Get the MongoDB URI from the environment with a default value
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/sisarasa')

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
