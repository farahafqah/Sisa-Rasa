"""
Run the Recipe Recommender API

This script runs the Flask API for the recipe recommendation system.
"""

import os
from api.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


