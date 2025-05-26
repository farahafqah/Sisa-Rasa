"""
Run the Recipe Recommender API

This script runs the Flask API for the recipe recommendation system.
"""

import argparse
from api.app import app, initialize_recommender

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Recipe Recommender API')
    
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to run the API on (default: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to run the API on (default: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true',
                        help='Run the API in debug mode')
    parser.add_argument('--num-recipes', type=int, default=10,
                        help='Number of recipes to recommend (default: 10)')
    parser.add_argument('--max-recipes', type=int, default=10000,
                        help='Maximum number of recipes to load (default: 10000)')
    
    return parser.parse_args()

def main():
    """Main function to run the API."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize the recommender
    print("Initializing recommender...")
    success = initialize_recommender(
        num_recipes=args.num_recipes,
        max_recipes=args.max_recipes
    )
    
    if not success:
        print("Failed to initialize recommender. Exiting.")
        return
    
    # Run the app
    print(f"Starting API on {args.host}:{args.port}...")
    app.run(
        debug=args.debug,
        host=args.host,
        port=args.port
    )

if __name__ == '__main__':
    main()
