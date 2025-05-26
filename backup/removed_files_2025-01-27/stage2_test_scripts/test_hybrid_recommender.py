"""
Test script for the Hybrid Recipe Recommender

This script tests the hybrid recommendation system to ensure it works correctly
and provides better recommendations than the KNN-only approach.
"""

import os
import sys
import json
from collections import defaultdict

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hybrid_recipe_recommender import HybridRecipeRecommender


def test_basic_functionality():
    """Test basic functionality of the hybrid recommender."""
    print("=" * 60)
    print("TESTING BASIC HYBRID RECOMMENDER FUNCTIONALITY")
    print("=" * 60)
    
    # Create hybrid recommender
    recommender = HybridRecipeRecommender(
        knn_weight=0.5,
        content_weight=0.25,
        collaborative_weight=0.15,
        popularity_weight=0.1,
        k=10
    )
    
    # Load recipes
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    recipes_file = os.path.join(base_dir, 'data', 'clean_recipes.json')
    
    if not os.path.exists(recipes_file):
        print(f"Error: Recipe file not found at {recipes_file}")
        return False
    
    print(f"Loading recipes from: {recipes_file}")
    recommender.load_recipes(recipes_file, max_rows=1000)  # Load subset for testing
    
    print(f"Loaded {len(recommender.recipes)} recipes")
    print(f"Found {len(recommender.ingredient_names)} unique ingredients")
    
    return recommender


def test_knn_recommendations(recommender):
    """Test KNN-only recommendations."""
    print("\n" + "=" * 60)
    print("TESTING KNN-ONLY RECOMMENDATIONS")
    print("=" * 60)
    
    test_ingredients = "chicken, garlic, onion"
    print(f"Getting KNN recommendations for: {test_ingredients}")
    
    knn_recs = recommender.get_knn_recommendations(test_ingredients, num_recommendations=5)
    
    print(f"\nKNN Recommendations ({len(knn_recs)} found):")
    for i, recipe in enumerate(knn_recs[:5], 1):
        print(f"{i}. {recipe['name']}")
        print(f"   Score: {recipe.get('score', 'N/A'):.3f}")
        print(f"   Ingredients: {', '.join(recipe['ingredients'][:3])}...")
        print()
    
    return knn_recs


def test_content_based_recommendations(recommender):
    """Test content-based recommendations."""
    print("\n" + "=" * 60)
    print("TESTING CONTENT-BASED RECOMMENDATIONS")
    print("=" * 60)
    
    test_ingredients = "chicken, garlic, onion"
    user_preferences = {
        'cuisine': 'International',
        'difficulty': 'Medium',
        'max_prep_time': 60
    }
    
    print(f"Getting content-based recommendations for: {test_ingredients}")
    print(f"User preferences: {user_preferences}")
    
    content_recs = recommender.get_content_based_recommendations(
        test_ingredients, 
        user_preferences=user_preferences, 
        num_recommendations=5
    )
    
    print(f"\nContent-Based Recommendations ({len(content_recs)} found):")
    for i, recipe in enumerate(content_recs[:5], 1):
        print(f"{i}. {recipe['name']}")
        print(f"   Content Score: {recipe.get('content_score', 'N/A'):.3f}")
        print(f"   Cuisine: {recipe.get('cuisine', 'N/A')}")
        print(f"   Difficulty: {recipe.get('difficulty', 'N/A')}")
        print(f"   Prep Time: {recipe.get('prep_time', 'N/A')} min")
        print()
    
    return content_recs


def test_popularity_recommendations(recommender):
    """Test popularity-based recommendations."""
    print("\n" + "=" * 60)
    print("TESTING POPULARITY-BASED RECOMMENDATIONS")
    print("=" * 60)
    
    # Add some mock ratings to test popularity
    mock_ratings = {
        'user1': {'1': 5, '2': 4, '3': 3},
        'user2': {'1': 4, '2': 5, '4': 4},
        'user3': {'1': 5, '3': 2, '5': 5}
    }
    
    # Update recommender with mock ratings
    for user_id, ratings in mock_ratings.items():
        for recipe_id, rating in ratings.items():
            recommender.update_user_preference(user_id, recipe_id, rating)
    
    print("Added mock ratings for testing popularity...")
    
    popularity_recs = recommender.get_popularity_based_recommendations(num_recommendations=5)
    
    print(f"\nPopularity-Based Recommendations ({len(popularity_recs)} found):")
    for i, recipe in enumerate(popularity_recs[:5], 1):
        recipe_id = recipe['id']
        avg_rating = recommender.recipe_avg_ratings.get(recipe_id, 3.0)
        popularity = recommender.recipe_popularity_scores.get(recipe_id, 0.5)
        
        print(f"{i}. {recipe['name']}")
        print(f"   Popularity Score: {recipe.get('popularity_score', 'N/A'):.3f}")
        print(f"   Avg Rating: {avg_rating:.1f}")
        print(f"   Popularity: {popularity:.3f}")
        print()
    
    return popularity_recs


def test_hybrid_recommendations(recommender):
    """Test full hybrid recommendations."""
    print("\n" + "=" * 60)
    print("TESTING FULL HYBRID RECOMMENDATIONS")
    print("=" * 60)
    
    test_ingredients = "chicken, garlic, onion"
    user_id = "test_user"
    user_preferences = {
        'cuisine': 'International',
        'max_prep_time': 45
    }
    
    print(f"Getting hybrid recommendations for: {test_ingredients}")
    print(f"User ID: {user_id}")
    print(f"User preferences: {user_preferences}")
    
    hybrid_recs = recommender.recommend_recipes(
        user_input=test_ingredients,
        user_id=user_id,
        user_preferences=user_preferences,
        num_recommendations=5,
        explanation=True
    )
    
    print(f"\nHybrid Recommendations ({len(hybrid_recs)} found):")
    for i, recipe in enumerate(hybrid_recs[:5], 1):
        print(f"{i}. {recipe['name']}")
        print(f"   Hybrid Score: {recipe.get('hybrid_score', 'N/A'):.3f}")
        
        if 'recommendation_explanation' in recipe:
            exp = recipe['recommendation_explanation']
            print(f"   Sources: {', '.join(exp['sources'])}")
            print(f"   Component Scores:")
            print(f"     - KNN: {exp['knn_score']:.3f} (weight: {exp['weights']['knn']})")
            print(f"     - Content: {exp['content_score']:.3f} (weight: {exp['weights']['content']})")
            print(f"     - Collaborative: {exp['collaborative_score']:.3f} (weight: {exp['weights']['collaborative']})")
            print(f"     - Popularity: {exp['popularity_score']:.3f} (weight: {exp['weights']['popularity']})")
        
        print(f"   Cuisine: {recipe.get('cuisine', 'N/A')}")
        print(f"   Prep Time: {recipe.get('prep_time', 'N/A')} min")
        print()
    
    return hybrid_recs


def test_different_scenarios(recommender):
    """Test different recommendation scenarios."""
    print("\n" + "=" * 60)
    print("TESTING DIFFERENT SCENARIOS")
    print("=" * 60)
    
    scenarios = [
        {
            'name': 'Italian Cuisine Preference',
            'ingredients': 'pasta, tomato, cheese',
            'preferences': {'cuisine': 'Italian', 'max_prep_time': 30}
        },
        {
            'name': 'Quick Breakfast',
            'ingredients': 'egg, bread, butter',
            'preferences': {'max_prep_time': 15, 'difficulty': 'Easy'}
        },
        {
            'name': 'Healthy Dinner',
            'ingredients': 'chicken, vegetables, rice',
            'preferences': {'cuisine': 'Asian', 'max_prep_time': 60}
        }
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        print(f"Ingredients: {scenario['ingredients']}")
        print(f"Preferences: {scenario['preferences']}")
        
        recs = recommender.recommend_recipes(
            user_input=scenario['ingredients'],
            user_preferences=scenario['preferences'],
            num_recommendations=3
        )
        
        print(f"Top 3 recommendations:")
        for i, recipe in enumerate(recs[:3], 1):
            print(f"  {i}. {recipe['name']} (Score: {recipe.get('hybrid_score', 0):.3f})")


def main():
    """Main test function."""
    print("Starting Hybrid Recipe Recommender Tests...")
    
    # Test basic functionality
    recommender = test_basic_functionality()
    if not recommender:
        print("Failed to initialize recommender. Exiting.")
        return
    
    # Test individual components
    test_knn_recommendations(recommender)
    test_content_based_recommendations(recommender)
    test_popularity_recommendations(recommender)
    
    # Test full hybrid system
    test_hybrid_recommendations(recommender)
    
    # Test different scenarios
    test_different_scenarios(recommender)
    
    print("\n" + "=" * 60)
    print("HYBRID RECOMMENDER TESTS COMPLETED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
