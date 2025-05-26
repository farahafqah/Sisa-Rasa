#!/usr/bin/env python3
"""
Test script for the Enhanced KNN Recipe Recommendation System

This script demonstrates the capabilities of the enhanced KNN system
and compares it with different configurations.
"""

import os
import sys
import time
from clean_recipe_recommender import EnhancedKNNRecipeRecommender

def test_basic_recommendations():
    """Test basic recommendation functionality."""
    print("=" * 60)
    print("TESTING BASIC RECOMMENDATIONS")
    print("=" * 60)
    
    # Create recommender
    recommender = EnhancedKNNRecipeRecommender(k=5, metric='cosine')
    
    # Load recipes
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    recipes_file = os.path.join(base_dir, 'data', 'clean_recipes.json')
    
    print("Loading recipes...")
    start_time = time.time()
    recommender.load_recipes(recipes_file, max_rows=1000)  # Smaller dataset for testing
    load_time = time.time() - start_time
    print(f"Loaded {len(recommender.recipes)} recipes in {load_time:.2f} seconds")
    
    # Test different ingredient combinations
    test_cases = [
        "chicken, rice, soy sauce",
        "beef, tomato, onion, garlic",
        "pasta, cheese, basil",
        "salmon, lemon, dill",
        "chocolate, flour, eggs, sugar"
    ]
    
    for ingredients in test_cases:
        print(f"\n--- Testing: {ingredients} ---")
        start_time = time.time()
        recommendations = recommender.recommend_recipes(ingredients, num_recommendations=3)
        query_time = time.time() - start_time
        
        print(f"Query time: {query_time:.3f} seconds")
        print(f"Found {len(recommendations)} recommendations:")
        
        for i, recipe in enumerate(recommendations, 1):
            print(f"{i}. {recipe['name']} (Score: {recipe['score']:.3f})")
            print(f"   Matched: {', '.join(recipe['matched_ingredients'][:3])}...")
            print(f"   Cuisine: {recipe['cuisine']} | Prep: {recipe['prep_time']}min")

def test_advanced_features():
    """Test advanced features like filtering and diversity."""
    print("\n" + "=" * 60)
    print("TESTING ADVANCED FEATURES")
    print("=" * 60)
    
    # Create recommender
    recommender = EnhancedKNNRecipeRecommender(k=10, metric='cosine')
    
    # Load recipes
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    recipes_file = os.path.join(base_dir, 'data', 'clean_recipes.json')
    recommender.load_recipes(recipes_file, max_rows=2000)
    
    ingredients = "chicken, garlic, herbs"
    
    # Test without diversity
    print("\n--- Without Diversity Control ---")
    recommendations = recommender.recommend_recipes(
        ingredients, 
        num_recommendations=5, 
        diversity_factor=0.0
    )
    
    for i, recipe in enumerate(recommendations, 1):
        print(f"{i}. {recipe['name']} (Score: {recipe['score']:.3f})")
    
    # Test with diversity
    print("\n--- With Diversity Control ---")
    recommendations = recommender.recommend_recipes(
        ingredients, 
        num_recommendations=5, 
        diversity_factor=0.5
    )
    
    for i, recipe in enumerate(recommendations, 1):
        print(f"{i}. {recipe['name']} (Score: {recipe['score']:.3f})")
    
    # Test with time filter
    print("\n--- With Time Filter (max 30 min prep) ---")
    recommendations = recommender.recommend_recipes(
        ingredients, 
        num_recommendations=5, 
        max_prep_time=30
    )
    
    for i, recipe in enumerate(recommendations, 1):
        print(f"{i}. {recipe['name']} (Prep: {recipe['prep_time']}min)")

def test_ingredient_matching():
    """Test intelligent ingredient matching capabilities."""
    print("\n" + "=" * 60)
    print("TESTING INGREDIENT MATCHING")
    print("=" * 60)
    
    # Create recommender
    recommender = EnhancedKNNRecipeRecommender(k=5, metric='cosine')
    
    # Load recipes
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    recipes_file = os.path.join(base_dir, 'data', 'clean_recipes.json')
    recommender.load_recipes(recipes_file, max_rows=1000)
    
    # Test plural/singular matching
    test_cases = [
        ("tomato", "Testing singular form"),
        ("tomatoes", "Testing plural form"),
        ("beef", "Testing protein (high importance)"),
        ("salt", "Testing common ingredient (low importance)"),
        ("quinoa", "Testing special grain"),
        ("truffle", "Testing luxury ingredient")
    ]
    
    for ingredient, description in test_cases:
        print(f"\n--- {description}: '{ingredient}' ---")
        matched, important, common = recommender.find_matching_ingredients(ingredient)
        print(f"Matched: {matched}")
        print(f"Important: {important}")
        print(f"Common: {common}")

def test_performance():
    """Test performance with different configurations."""
    print("\n" + "=" * 60)
    print("TESTING PERFORMANCE")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    recipes_file = os.path.join(base_dir, 'data', 'clean_recipes.json')
    
    # Test different metrics
    metrics = ['cosine', 'euclidean', 'manhattan']
    ingredients = "chicken, rice, vegetables"
    
    for metric in metrics:
        print(f"\n--- Testing {metric} metric ---")
        recommender = EnhancedKNNRecipeRecommender(k=5, metric=metric)
        
        # Load time
        start_time = time.time()
        recommender.load_recipes(recipes_file, max_rows=1000)
        load_time = time.time() - start_time
        
        # Query time
        start_time = time.time()
        recommendations = recommender.recommend_recipes(ingredients)
        query_time = time.time() - start_time
        
        print(f"Load time: {load_time:.2f}s, Query time: {query_time:.3f}s")
        print(f"Top recipe: {recommendations[0]['name'] if recommendations else 'None'}")

def main():
    """Run all tests."""
    print("Enhanced KNN Recipe Recommendation System - Test Suite")
    print("=" * 60)
    
    try:
        test_basic_recommendations()
        test_advanced_features()
        test_ingredient_matching()
        test_performance()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
