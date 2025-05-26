"""
Download and process a clean recipe dataset from GitHub.

This script downloads a high-quality recipe dataset with proper ingredient names
and converts it to a format compatible with your recommendation system.
"""

import requests
import pandas as pd
import json
import os
import re
import ast
from collections import Counter

def download_recipe_dataset():
    """Download the clean recipe dataset from GitHub."""
    url = "https://raw.githubusercontent.com/josephrmartinez/recipe-dataset/main/13k-recipes.csv"
    filename = os.path.join('data', 'raw_recipes.csv')
    
    try:
        print("Downloading recipe dataset...")
        response = requests.get(url)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Successfully downloaded dataset to {filename}")
        return filename
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        return None

def clean_ingredient_list(ingredients_str):
    """Clean and parse ingredient list from string format."""
    try:
        # The ingredients are stored as string representation of a list
        # Convert string to actual list
        ingredients_list = ast.literal_eval(ingredients_str)
        
        cleaned_ingredients = []
        for ingredient in ingredients_list:
            # Clean each ingredient
            cleaned = clean_ingredient_name(ingredient)
            if cleaned and len(cleaned) > 2:
                cleaned_ingredients.append(cleaned)
        
        return cleaned_ingredients
    except:
        # If parsing fails, try to split by common delimiters
        if isinstance(ingredients_str, str):
            # Remove brackets and quotes
            cleaned_str = re.sub(r'[\[\]\'"]', '', ingredients_str)
            ingredients = [ing.strip() for ing in cleaned_str.split(',')]
            
            cleaned_ingredients = []
            for ingredient in ingredients:
                cleaned = clean_ingredient_name(ingredient)
                if cleaned and len(cleaned) > 2:
                    cleaned_ingredients.append(cleaned)
            
            return cleaned_ingredients
        
        return []

def clean_ingredient_name(ingredient):
    """Clean and standardize ingredient names."""
    if not ingredient or not isinstance(ingredient, str):
        return None
    
    # Convert to lowercase
    ingredient = ingredient.lower().strip()
    
    # Remove quantities and measurements
    # Remove patterns like "1 cup", "2 tablespoons", etc.
    ingredient = re.sub(r'^\d+(\.\d+)?\s*(cups?|tablespoons?|teaspoons?|pounds?|ounces?|lbs?|oz|tsp|tbsp|cloves?|pieces?|slices?|cans?|packages?|jars?)\s+', '', ingredient)
    
    # Remove fractions like "1/2", "3/4"
    ingredient = re.sub(r'^\d+/\d+\s+', '', ingredient)
    
    # Remove parenthetical information
    ingredient = re.sub(r'\([^)]*\)', '', ingredient)
    
    # Remove extra descriptors but keep the main ingredient
    descriptors = ['fresh', 'dried', 'chopped', 'minced', 'diced', 'sliced', 'grated', 'ground', 
                   'whole', 'large', 'small', 'medium', 'fine', 'coarse', 'extra', 'virgin',
                   'unsalted', 'salted', 'raw', 'cooked', 'frozen', 'canned', 'organic',
                   'finely', 'coarsely', 'thinly', 'thickly', 'roughly']
    
    words = ingredient.split()
    cleaned_words = []
    for word in words:
        # Remove commas and other punctuation
        word = re.sub(r'[,;.]', '', word)
        if word not in descriptors and word and len(word) > 1:
            cleaned_words.append(word)
    
    if cleaned_words:
        result = ' '.join(cleaned_words)
        # Remove any remaining numbers at the start
        result = re.sub(r'^\d+\s*', '', result)
        return result.strip()
    else:
        return ingredient.strip()

def process_instructions(instructions_str):
    """Process and clean instructions."""
    if not instructions_str or not isinstance(instructions_str, str):
        return []
    
    # Split instructions by common delimiters
    instructions = re.split(r'\n|\r\n|\. (?=[A-Z])', instructions_str)
    
    cleaned_instructions = []
    for instruction in instructions:
        instruction = instruction.strip()
        if instruction and len(instruction) > 10:  # Skip very short instructions
            # Remove extra whitespace
            instruction = re.sub(r'\s+', ' ', instruction)
            cleaned_instructions.append(instruction)
    
    return cleaned_instructions

def process_recipe_dataset(csv_file):
    """Process the recipe dataset into a clean format."""
    try:
        print("Processing recipe dataset...")
        
        # Read the CSV file
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} recipes from CSV")
        
        processed_recipes = []
        ingredient_counter = Counter()
        
        for index, row in df.iterrows():
            if index % 1000 == 0:
                print(f"Processed {index} recipes...")
            
            # Extract basic information
            recipe_id = index + 1
            name = row.get('Title', f'Recipe {recipe_id}')
            
            # Process ingredients
            raw_ingredients = row.get('Ingredients', '')
            cleaned_ingredients = clean_ingredient_list(raw_ingredients)
            
            if not cleaned_ingredients:
                continue
            
            # Count ingredients
            for ingredient in cleaned_ingredients:
                ingredient_counter[ingredient] += 1
            
            # Process instructions
            raw_instructions = row.get('Instructions', '')
            instructions = process_instructions(raw_instructions)
            
            if not instructions:
                continue
            
            # Create processed recipe
            processed_recipe = {
                'id': recipe_id,
                'name': name,
                'ingredients': cleaned_ingredients,
                'instructions': instructions,
                'prep_time': 30,  # Default prep time
                'cook_time': 45,  # Default cook time
                'servings': 4,    # Default servings
                'cuisine': 'International',  # Default cuisine
                'difficulty': 'Medium'       # Default difficulty
            }
            
            processed_recipes.append(processed_recipe)
        
        print(f"Successfully processed {len(processed_recipes)} recipes")
        print(f"Found {len(ingredient_counter)} unique ingredients")
        
        # Show most common ingredients
        print("\nMost common ingredients:")
        for ingredient, count in ingredient_counter.most_common(20):
            print(f"  {ingredient}: {count}")
        
        return processed_recipes, ingredient_counter
    
    except Exception as e:
        print(f"Error processing dataset: {e}")
        return None, None

def save_processed_data(recipes, ingredient_counter):
    """Save the processed data in multiple formats."""
    try:
        # Save recipes as JSON
        recipes_file = os.path.join('data', 'clean_recipes.json')
        with open(recipes_file, 'w', encoding='utf-8') as f:
            json.dump(recipes, f, indent=2, ensure_ascii=False)
        print(f"Saved recipes to {recipes_file}")
        
        # Save recipes as CSV
        csv_data = []
        for recipe in recipes:
            csv_data.append({
                'id': recipe['id'],
                'name': recipe['name'],
                'ingredients': '; '.join(recipe['ingredients']),
                'instructions': ' | '.join(recipe['instructions']),
                'prep_time': recipe['prep_time'],
                'cook_time': recipe['cook_time'],
                'servings': recipe['servings'],
                'cuisine': recipe['cuisine'],
                'difficulty': recipe['difficulty']
            })
        
        df = pd.DataFrame(csv_data)
        csv_file = os.path.join('data', 'clean_recipes.csv')
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"Saved recipes to {csv_file}")
        
        # Create ingredient mapping with IDs
        ingredient_mapping = {}
        for i, (ingredient, count) in enumerate(ingredient_counter.most_common()):
            ingredient_mapping[str(i + 1)] = ingredient
        
        mapping_file = os.path.join('data', 'clean_ingredient_mapping.json')
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(ingredient_mapping, f, indent=2, ensure_ascii=False)
        print(f"Saved ingredient mapping to {mapping_file}")
        
        return recipes_file, csv_file, mapping_file
    
    except Exception as e:
        print(f"Error saving data: {e}")
        return None, None, None

def main():
    """Main function to download and process the dataset."""
    print("Clean Recipe Dataset Downloader and Processor")
    print("=" * 50)
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Download the dataset
    raw_file = download_recipe_dataset()
    if not raw_file:
        print("Failed to download dataset")
        return
    
    # Process the data
    recipes, ingredient_counter = process_recipe_dataset(raw_file)
    if not recipes:
        print("Failed to process dataset")
        return
    
    # Save the processed data
    recipes_file, csv_file, mapping_file = save_processed_data(recipes, ingredient_counter)
    
    if recipes_file:
        print("\n" + "=" * 50)
        print("Dataset processing completed successfully!")
        print(f"Total recipes: {len(recipes)}")
        print(f"Total unique ingredients: {len(ingredient_counter)}")
        print("\nFiles created:")
        print(f"  - {recipes_file} (JSON format)")
        print(f"  - {csv_file} (CSV format)")
        print(f"  - {mapping_file} (Ingredient mapping)")
        
        print("\nNext steps:")
        print("1. Update your recommendation system to use the new dataset")
        print("2. Test the system with clean ingredient names")
        print("3. Enjoy your improved recipe recommendations!")

if __name__ == "__main__":
    main()
