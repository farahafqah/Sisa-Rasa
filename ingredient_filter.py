#!/usr/bin/env python3
"""
Ingredient Analytics Filter for SisaRasa

This module provides filtering functionality to focus on main ingredients
relevant to food waste reduction, removing common seasonings and basic ingredients.
"""

# Common seasonings and basic ingredients to filter out
COMMON_SEASONINGS = {
    'salt', 'pepper', 'black pepper', 'white pepper', 'sea salt', 'kosher salt',
    'sugar', 'brown sugar', 'white sugar', 'granulated sugar', 'powdered sugar',
    'honey', 'maple syrup', 'corn syrup', 'agave', 'stevia',
    'vanilla', 'vanilla extract', 'almond extract', 'lemon extract',
    'baking powder', 'baking soda', 'yeast', 'cornstarch', 'flour',
    'all-purpose flour', 'wheat flour', 'bread flour', 'cake flour',
    'water', 'ice', 'ice water', 'cold water', 'warm water', 'hot water',
    'oil', 'olive oil', 'vegetable oil', 'canola oil', 'coconut oil',
    'butter', 'margarine', 'shortening', 'lard', 'cooking spray'
}

HERBS_AND_SPICES = {
    'herbs', 'spices', 'seasoning', 'herb', 'spice',
    'basil', 'oregano', 'thyme', 'rosemary', 'sage', 'parsley', 'cilantro',
    'dill', 'mint', 'chives', 'tarragon', 'bay leaves', 'bay leaf',
    'cinnamon', 'nutmeg', 'cloves', 'allspice', 'cardamom', 'ginger powder',
    'paprika', 'cumin', 'coriander', 'turmeric', 'curry powder', 'chili powder',
    'cayenne', 'red pepper flakes', 'garlic powder', 'onion powder',
    'dried herbs', 'fresh herbs', 'italian seasoning', 'herbs de provence',
    'chinese five spice', 'garam masala', 'taco seasoning', 'ranch seasoning'
}

CONDIMENTS_AND_SAUCES = {
    'vinegar', 'white vinegar', 'apple cider vinegar', 'balsamic vinegar',
    'soy sauce', 'worcestershire sauce', 'hot sauce', 'tabasco',
    'ketchup', 'mustard', 'mayonnaise', 'ranch', 'bbq sauce',
    'teriyaki sauce', 'fish sauce', 'oyster sauce', 'hoisin sauce',
    'sriracha', 'salsa', 'pesto', 'marinara sauce', 'tomato sauce'
}

# Main ingredients that are relevant to food waste reduction
MAIN_INGREDIENTS = {
    # Proteins
    'chicken', 'beef', 'pork', 'lamb', 'turkey', 'duck', 'fish', 'salmon',
    'tuna', 'cod', 'shrimp', 'crab', 'lobster', 'scallops', 'mussels',
    'eggs', 'tofu', 'tempeh', 'seitan', 'beans', 'lentils', 'chickpeas',
    'black beans', 'kidney beans', 'pinto beans', 'navy beans',
    
    # Vegetables
    'onions', 'garlic', 'tomatoes', 'potatoes', 'carrots', 'celery',
    'bell peppers', 'broccoli', 'cauliflower', 'spinach', 'lettuce',
    'cabbage', 'zucchini', 'eggplant', 'mushrooms', 'asparagus',
    'green beans', 'peas', 'corn', 'sweet potatoes', 'beets',
    'radishes', 'turnips', 'leeks', 'fennel', 'artichokes',
    
    # Fruits
    'apples', 'bananas', 'oranges', 'lemons', 'limes', 'berries',
    'strawberries', 'blueberries', 'raspberries', 'blackberries',
    'grapes', 'pears', 'peaches', 'plums', 'cherries', 'pineapple',
    'mango', 'avocado', 'kiwi', 'melon', 'watermelon', 'cantaloupe',
    
    # Grains and Starches
    'rice', 'pasta', 'bread', 'quinoa', 'barley', 'oats', 'wheat',
    'couscous', 'bulgur', 'farro', 'millet', 'buckwheat', 'noodles',
    
    # Dairy
    'milk', 'cheese', 'yogurt', 'cream', 'sour cream', 'cottage cheese',
    'ricotta', 'mozzarella', 'cheddar', 'parmesan', 'feta', 'goat cheese',
    
    # Nuts and Seeds
    'almonds', 'walnuts', 'pecans', 'cashews', 'peanuts', 'pistachios',
    'sunflower seeds', 'pumpkin seeds', 'sesame seeds', 'chia seeds',
    'flax seeds', 'pine nuts'
}

def is_main_ingredient(ingredient):
    """
    Check if an ingredient is a main ingredient relevant to food waste reduction.
    
    Args:
        ingredient (str): The ingredient name to check
        
    Returns:
        bool: True if it's a main ingredient, False if it should be filtered out
    """
    if not ingredient or not isinstance(ingredient, str):
        return False
    
    # Clean and normalize the ingredient name
    ingredient_clean = ingredient.lower().strip()
    
    # Remove common prefixes/suffixes
    prefixes_to_remove = ['fresh ', 'dried ', 'frozen ', 'canned ', 'organic ', 'raw ', 'cooked ']
    suffixes_to_remove = [' powder', ' flakes', ' extract', ' sauce', ' oil']
    
    for prefix in prefixes_to_remove:
        if ingredient_clean.startswith(prefix):
            ingredient_clean = ingredient_clean[len(prefix):]
            break
    
    for suffix in suffixes_to_remove:
        if ingredient_clean.endswith(suffix):
            ingredient_clean = ingredient_clean[:-len(suffix)]
            break
    
    # Check if it's a common seasoning/basic ingredient (filter out)
    if ingredient_clean in COMMON_SEASONINGS:
        return False
    
    if ingredient_clean in HERBS_AND_SPICES:
        return False
    
    if ingredient_clean in CONDIMENTS_AND_SAUCES:
        return False
    
    # Check if it's a main ingredient (keep)
    if ingredient_clean in MAIN_INGREDIENTS:
        return True
    
    # For ingredients not in our lists, use some heuristics
    # Keep ingredients that are likely to be main ingredients
    main_keywords = ['meat', 'vegetable', 'fruit', 'grain', 'dairy', 'protein']
    filter_keywords = ['seasoning', 'spice', 'herb', 'sauce', 'dressing', 'extract']
    
    for keyword in filter_keywords:
        if keyword in ingredient_clean:
            return False
    
    for keyword in main_keywords:
        if keyword in ingredient_clean:
            return True
    
    # Default: if it's not obviously a seasoning and has substance, keep it
    # Filter out very short ingredients (likely abbreviations or seasonings)
    if len(ingredient_clean) <= 2:
        return False
    
    return True

def filter_ingredients_list(ingredients):
    """
    Filter a list of ingredients to keep only main ingredients.
    
    Args:
        ingredients (list): List of ingredient names
        
    Returns:
        list: Filtered list containing only main ingredients
    """
    if not ingredients:
        return []
    
    return [ing for ing in ingredients if is_main_ingredient(ing)]

def filter_ingredient_stats(ingredient_stats):
    """
    Filter ingredient statistics dictionary to keep only main ingredients.
    
    Args:
        ingredient_stats (dict): Dictionary with ingredient names as keys
        
    Returns:
        dict: Filtered dictionary containing only main ingredients
    """
    if not ingredient_stats:
        return {}
    
    return {ing: count for ing, count in ingredient_stats.items() if is_main_ingredient(ing)}

def get_main_ingredients_from_recipe(recipe):
    """
    Extract main ingredients from a recipe, filtering out seasonings.
    
    Args:
        recipe (dict): Recipe dictionary with 'ingredients' field
        
    Returns:
        list: List of main ingredients
    """
    if not recipe or 'ingredients' not in recipe:
        return []
    
    return filter_ingredients_list(recipe['ingredients'])

# Test function
def test_ingredient_filter():
    """Test the ingredient filtering functionality."""
    test_ingredients = [
        'chicken breast', 'salt', 'black pepper', 'olive oil', 'garlic',
        'onions', 'tomatoes', 'basil', 'oregano', 'parmesan cheese',
        'pasta', 'water', 'sugar', 'vanilla extract', 'flour'
    ]
    
    print("Testing Ingredient Filter:")
    print("=" * 40)
    
    for ingredient in test_ingredients:
        is_main = is_main_ingredient(ingredient)
        status = "KEEP" if is_main else "FILTER"
        print(f"{ingredient:20} -> {status}")
    
    print("\nFiltered list:")
    filtered = filter_ingredients_list(test_ingredients)
    print(filtered)

if __name__ == "__main__":
    test_ingredient_filter()
