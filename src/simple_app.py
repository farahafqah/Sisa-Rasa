#!/usr/bin/env python3
"""
Ultra-simple Flask app for Railway deployment
No complex imports, no ML models, just basic health checks
"""

import os
from flask import Flask, jsonify

# Create Flask app
app = Flask(__name__)

# Basic configuration from environment
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'simple-secret-key')

@app.route('/')
def home():
    return {
        'status': 'ok',
        'message': 'SisaRasa API - Simple Mode',
        'version': '1.0.0',
        'environment': os.getenv('RAILWAY_ENVIRONMENT', 'development')
    }

@app.route('/health')
def health():
    """Ultra-simple health check for Railway."""
    return {
        'status': 'ok',
        'service': 'sisarasa-api',
        'mode': 'simple',
        'port': os.getenv('PORT', '5000')
    }, 200

@app.route('/api/health')
def api_health():
    """Detailed health check."""
    return {
        'status': 'ok',
        'message': 'SisaRasa API running in simple mode',
        'timestamp': str(__import__('datetime').datetime.utcnow()),
        'components': {
            'app': 'healthy',
            'database': 'not_connected',
            'recommender': 'not_loaded'
        }
    }, 200

@app.route('/api/status')
def status():
    """System status endpoint."""
    return {
        'status': 'running',
        'mode': 'simple',
        'features': {
            'health_check': True,
            'basic_api': True,
            'ml_system': False,
            'database': False,
            'authentication': False
        },
        'next_steps': [
            'Deploy successfully',
            'Initialize full system',
            'Load ML models',
            'Connect database'
        ]
    }

@app.route('/api/test')
def test():
    """Test endpoint to verify API is working."""
    return {
        'test': 'success',
        'message': 'API is responding correctly',
        'environment_vars': {
            'PORT': os.getenv('PORT', 'not_set'),
            'RAILWAY_ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT', 'not_set'),
            'MONGO_URI': 'configured' if os.getenv('MONGO_URI') else 'not_set'
        }
    }

if __name__ == '__main__':
    # Get port from Railway environment
    port = int(os.getenv('PORT', 5000))
    
    print("=" * 50)
    print("🚀 SisaRasa Simple API Starting")
    print("=" * 50)
    print(f"📍 Port: {port}")
    print(f"🌍 Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'development')}")
    print(f"🔗 MongoDB: {'Configured' if os.getenv('MONGO_URI') else 'Not configured'}")
    print("=" * 50)
    
    # Start Flask development server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )
