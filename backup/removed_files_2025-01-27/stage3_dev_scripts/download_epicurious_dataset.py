"""
Download and process the Epicurious recipe dataset.

This script downloads a clean recipe dataset with proper ingredient names
and converts it to a format compatible with your recommendation system.
"""

import requests
import json
import pandas as pd
import os
import re
from collections import Counter

def download_epicurious_dataset():
    """Download the Epicurious dataset."""
    url = "https://raw.githubusercontent.com/fictivekin/openrecipes/master/epicurious.json"
    filename = os.path.join('data', 'epicurious_raw.json')

    try:
        print("Downloading Epicurious dataset...")
        response = requests.get(url)
        response.raise_for_status()

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)

        print(f"Successfully downloaded dataset to {filename}")
        return filename
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        return None

def extract_time_value(time_str):
    """Extract time value in minutes from various time formats."""
    if not time_str or not isinstance(time_str, str):
        return 0

    time_str = time_str.lower().strip()

    # Look for patterns like "PT30M", "30 minutes", "1 hour 30 minutes", etc.
    # ISO 8601 duration format (PT30M = 30 minutes, PT1H30M = 1 hour 30 minutes)
    if time_str.startswith('pt'):
        total_minutes = 0
        # Extract hours
        hour_match = re.search(r'(\d+)h', time_str)
        if hour_match:
            total_minutes += int(hour_match.group(1)) * 60
        # Extract minutes
        minute_match = re.search(r'(\d+)m', time_str)
        if minute_match:
            total_minutes += int(minute_match.group(1))
        return total_minutes

    # Look for explicit time mentions
    total_minutes = 0

    # Hours
    hour_patterns = [r'(\d+)\s*(?:hours?|hrs?|h)', r'(\d+)\s*(?:hour|hr)']
    for pattern in hour_patterns:
        match = re.search(pattern, time_str)
        if match:
            total_minutes += int(match.group(1)) * 60

    # Minutes
    minute_patterns = [r'(\d+)\s*(?:minutes?|mins?|m)', r'(\d+)\s*(?:minute|min)']
    for pattern in minute_patterns:
        match = re.search(pattern, time_str)
        if match:
            total_minutes += int(match.group(1))

    # If no specific time found, try to extract any number and assume minutes
    if total_minutes == 0:
        number_match = re.search(r'(\d+)', time_str)
        if number_match:
            total_minutes = int(number_match.group(1))
            # If the number is very large, it might be in seconds
            if total_minutes > 300:  # More than 5 hours in minutes
                total_minutes = total_minutes // 60  # Convert from seconds

    # Reasonable bounds for cooking times
    return max(0, min(480, total_minutes))  # 0 to 8 hours max

def extract_cuisine(recipe):
    """Extract cuisine type from recipe data."""
    # Check various fields that might contain cuisine information
    cuisine_fields = ['cuisine', 'category', 'tags', 'keywords']

    for field in cuisine_fields:
        if field in recipe and recipe[field]:
            cuisine_value = recipe[field]
            if isinstance(cuisine_value, list):
                cuisine_value = ', '.join(str(c) for c in cuisine_value)
            cuisine_value = str(cuisine_value).strip()

            if cuisine_value and cuisine_value.lower() not in ['', 'none', 'null']:
                # Clean up the cuisine value
                cuisine_value = cuisine_value.title()
                # Limit length
                if len(cuisine_value) > 50:
                    cuisine_value = cuisine_value[:50].strip()
                return cuisine_value

    # If no cuisine found, return default
    return 'International'

def clean_ingredient_name(ingredient):
    """Clean and standardize ingredient names."""
    if not ingredient or not isinstance(ingredient, str):
        return None

    # Convert to lowercase
    ingredient = ingredient.lower().strip()

    # Remove quantities and measurements
    # Remove patterns like "1 cup", "2 tablespoons", etc.
    ingredient = re.sub(r'^\d+(\.\d+)?\s*(cups?|tablespoons?|teaspoons?|pounds?|ounces?|lbs?|oz|tsp|tbsp|cloves?|pieces?|slices?)\s+', '', ingredient)

    # Remove fractions like "1/2", "3/4"
    ingredient = re.sub(r'^\d+/\d+\s+', '', ingredient)

    # Remove parenthetical information
    ingredient = re.sub(r'\([^)]*\)', '', ingredient)

    # Remove extra descriptors but keep the main ingredient
    # Remove words like "fresh", "dried", "chopped", "minced", etc.
    descriptors = ['fresh', 'dried', 'chopped', 'minced', 'diced', 'sliced', 'grated', 'ground',
                   'whole', 'large', 'small', 'medium', 'fine', 'coarse', 'extra', 'virgin',
                   'unsalted', 'salted', 'raw', 'cooked', 'frozen', 'canned', 'organic']

    words = ingredient.split()
    cleaned_words = []
    for word in words:
        # Remove commas and other punctuation
        word = re.sub(r'[,;.]', '', word)
        if word not in descriptors and word:
            cleaned_words.append(word)

    if cleaned_words:
        return ' '.join(cleaned_words)
    else:
        return ingredient.strip()

def process_epicurious_data(raw_file):
    """Process the raw Epicurious data into a clean format."""
    try:
        print("Processing Epicurious data...")

        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        processed_recipes = []
        ingredient_counter = Counter()

        for i, recipe in enumerate(raw_data):
            if i % 1000 == 0:
                print(f"Processed {i} recipes...")

            # Extract basic information
            recipe_id = recipe.get('id', i)
            name = recipe.get('name', f'Recipe {recipe_id}')

            # Process ingredients
            raw_ingredients = recipe.get('ingredients', [])
            if not raw_ingredients:
                continue

            cleaned_ingredients = []
            for ingredient in raw_ingredients:
                cleaned = clean_ingredient_name(ingredient)
                if cleaned and len(cleaned) > 2:  # Skip very short ingredients
                    cleaned_ingredients.append(cleaned)
                    ingredient_counter[cleaned] += 1

            if not cleaned_ingredients:
                continue

            # Process instructions
            instructions = recipe.get('instructions', [])
            if isinstance(instructions, str):
                instructions = [instructions]

            # Extract other metadata with better parsing
            prep_time = extract_time_value(recipe.get('prepTime', ''))
            cook_time = extract_time_value(recipe.get('cookTime', ''))

            # Try to extract servings
            servings = 4  # Default
            if 'yield' in recipe:
                try:
                    yield_str = str(recipe['yield']).lower()
                    # Look for numbers in yield field
                    numbers = re.findall(r'\d+', yield_str)
                    if numbers:
                        servings = int(numbers[0])
                        # Reasonable bounds for servings
                        servings = max(1, min(12, servings))
                except:
                    servings = 4

            # Extract cuisine with better parsing
            cuisine = extract_cuisine(recipe)

            processed_recipe = {
                'id': recipe_id,
                'name': name,
                'ingredients': cleaned_ingredients,
                'instructions': instructions,
                'prep_time': prep_time,
                'cook_time': cook_time,
                'servings': servings,
                'cuisine': cuisine,
                'difficulty': 'Medium'  # Default difficulty
            }

            processed_recipes.append(processed_recipe)

        print(f"Processed {len(processed_recipes)} recipes")
        print(f"Found {len(ingredient_counter)} unique ingredients")

        # Show most common ingredients
        print("\nMost common ingredients:")
        for ingredient, count in ingredient_counter.most_common(20):
            print(f"  {ingredient}: {count}")

        return processed_recipes, ingredient_counter

    except Exception as e:
        print(f"Error processing data: {e}")
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

        # Save ingredient mapping
        ingredient_mapping = {}
        for i, (ingredient, _) in enumerate(ingredient_counter.most_common()):
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
    print("Epicurious Dataset Downloader and Processor")
    print("=" * 50)

    # Create data directory
    os.makedirs('data', exist_ok=True)

    # Download the dataset
    raw_file = download_epicurious_dataset()
    if not raw_file:
        print("Failed to download dataset")
        return

    # Process the data
    recipes, ingredient_counter = process_epicurious_data(raw_file)
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
