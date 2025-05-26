"""
Main script for the Clean Recipe Recommendation System.

This script provides a command-line interface for the recipe recommendation system
using the new clean dataset with proper ingredient names.
"""

import os
import sys
import argparse

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from clean_recipe_recommender import CleanRecipeRecommender

def main():
    """Main function for the clean recipe recommendation system."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Clean Recipe Recommendation System')
    parser.add_argument('--num-recipes', type=int, default=10,
                       help='Number of recipes to recommend (default: 10)')
    parser.add_argument('--max-recipes', type=int, default=10000,
                       help='Maximum number of recipes to load from dataset (default: 10000)')
    parser.add_argument('--min-score', type=float, default=0.1,
                       help='Minimum similarity score threshold (default: 0.1)')

    args = parser.parse_args()

    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    recipes_file = os.path.join(base_dir, 'data', 'clean_recipes.json')

    # Check if the clean dataset exists
    if not os.path.exists(recipes_file):
        print(f"Error: Clean recipe dataset not found at {recipes_file}")
        print("\nPlease run the dataset download script first:")
        print("  python src/download_clean_dataset.py")
        return

    # Create and initialize the recommender
    print("Initializing Clean Recipe Recommendation System...")
    recommender = CleanRecipeRecommender(k=args.num_recipes)

    # Load recipes
    print("Loading recipes...")
    recommender.load_recipes(recipes_file, max_rows=args.max_recipes)

    # Print some stats
    print(f"Loaded {len(recommender.recipes)} recipes")
    print(f"Found {len(recommender.ingredient_names)} unique ingredients")

    # Show some sample ingredients
    print("\nSample ingredients in the database:")
    sample_ingredients = list(recommender.ingredient_names)[:15]
    for i, ingredient in enumerate(sample_ingredients):
        print(f"  - {ingredient}")

    # Create a simple command-line interface
    print("\n" + "="*70)
    print("Welcome to the Clean Recipe Recommendation System!")
    print("="*70)
    print("\nThis system recommends recipes based on ingredients you have.")
    print("All ingredient names are clean and human-readable!")

    print("\nCommands:")
    print("  - Enter ingredients separated by commas (e.g., 'chicken, garlic, onion')")
    print("  - Type 'limit:X' to show X recipes (e.g., 'limit:15')")
    print("  - Type 'min-score:X' to set minimum score threshold (e.g., 'min-score:0.2')")
    print("  - Type 'help' to see this message again")
    print("  - Type 'quit' to exit")

    # Initialize dynamic settings
    num_recommendations = args.num_recipes
    min_score = args.min_score

    while True:
        user_input = input("\nEnter ingredients or command: ")

        if user_input.lower() == 'quit':
            break

        elif user_input.lower() == 'help':
            print("\nCommands:")
            print("  - Enter ingredients separated by commas (e.g., 'chicken, garlic, onion')")
            print("  - Type 'limit:X' to show X recipes (e.g., 'limit:15')")
            print("  - Type 'min-score:X' to set minimum score threshold (e.g., 'min-score:0.2')")
            print("  - Type 'help' to see this message again")
            print("  - Type 'quit' to exit")
            continue

        elif user_input.lower().startswith('limit:'):
            try:
                limit_value = int(user_input.lower().split(':', 1)[1].strip())
                if limit_value > 0:
                    num_recommendations = limit_value
                    print(f"Will show up to {num_recommendations} recipes.")
                else:
                    print("Limit must be a positive number.")
            except ValueError:
                print("Invalid limit value. Please use a number.")
            continue

        elif user_input.lower().startswith('min-score:'):
            try:
                score_value = float(user_input.lower().split(':', 1)[1].strip())
                if 0 <= score_value <= 1:
                    min_score = score_value
                    print(f"Minimum score threshold set to {min_score:.2f}")
                else:
                    print("Score must be between 0 and 1.")
            except ValueError:
                print("Invalid score value. Please use a number between 0 and 1.")
            continue

        try:
            # Get recommendations
            print("Matched ingredients:")
            recommendations = recommender.recommend_recipes(user_input, num_recommendations)

            # Filter by minimum score
            filtered_recommendations = [r for r in recommendations if r['score'] >= min_score]

            if filtered_recommendations:
                print(f"\nFound {len(filtered_recommendations)} recipes matching your ingredients (min score: {min_score:.2f}):")
                print("-" * 70)

                for i, recipe in enumerate(filtered_recommendations, 1):
                    print(f"{i}. {recipe['name']}")
                    print(f"   Match Score: {recipe['score']:.3f}")
                    print(f"   Cuisine: {recipe['cuisine']} | Difficulty: {recipe['difficulty']}")
                    print(f"   Prep Time: {recipe['prep_time']} min | Cook Time: {recipe['cook_time']} min | Serves: {recipe['servings']}")

                    # Show matched ingredients with importance classification
                    if recipe.get('important_matched'):
                        print(f"   Key Ingredients Matched: {', '.join(recipe['important_matched'])}")
                    if recipe.get('common_matched'):
                        print(f"   Common Ingredients Matched: {', '.join(recipe['common_matched'])}")

                    # Show all ingredients (limit to first 8 for readability)
                    ingredients_display = recipe['ingredients'][:8]
                    if len(recipe['ingredients']) > 8:
                        ingredients_display.append(f"... and {len(recipe['ingredients']) - 8} more")
                    print(f"   All Ingredients: {', '.join(ingredients_display)}")

                    # Show first few instructions
                    if recipe['instructions']:
                        print("   Instructions:")
                        for j, instruction in enumerate(recipe['instructions'][:3], 1):
                            # Truncate long instructions
                            if len(instruction) > 80:
                                instruction = instruction[:77] + "..."
                            print(f"     {j}. {instruction}")
                        if len(recipe['instructions']) > 3:
                            print(f"     ... and {len(recipe['instructions']) - 3} more steps")

                    print("-" * 70)
            else:
                print(f"No recipes found with those ingredients (min score: {min_score:.2f}).")
                print("Try:")
                print("  - Using more common ingredients")
                print("  - Lowering the minimum score threshold with 'min-score:0.05'")
                print("  - Adding more ingredients to your search")

        except Exception as e:
            print(f"Error: {e}")
            print("Please enter valid ingredients.")

if __name__ == "__main__":
    main()
