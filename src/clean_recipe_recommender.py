"""
Enhanced KNN Recipe Recommender System

This module provides an advanced recipe recommendation system that combines KNN algorithms
with intelligent ingredient matching, importance scoring, and sophisticated similarity metrics.
It works with clean ingredient names and provides highly accurate recipe recommendations.
"""

import json
import os
import re
import pickle
import math
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances, manhattan_distances
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
import numpy as np
from difflib import SequenceMatcher
import warnings
warnings.filterwarnings('ignore')

# Simple stemmer implementation to avoid NLTK dependency
class SimpleStemmer:
    """A simple rule-based stemmer for basic ingredient normalization."""

    def stem(self, word):
        """Apply basic stemming rules."""
        if len(word) <= 3:
            return word

        # Remove common suffixes
        suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'ness', 'ment']
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]

        # Handle plurals
        if word.endswith('ies') and len(word) > 4:
            return word[:-3] + 'y'
        elif word.endswith('es') and len(word) > 3:
            return word[:-2]
        elif word.endswith('s') and len(word) > 3:
            return word[:-1]

        return word

class EnhancedKNNRecipeRecommender:
    """An advanced recipe recommender using KNN algorithms with intelligent ingredient matching."""

    def __init__(self, k=10, algorithm='auto', metric='cosine', use_stemming=False):
        """
        Initialize the enhanced KNN recommender.

        Parameters:
        -----------
        k : int
            Number of recommendations to return
        algorithm : str
            KNN algorithm to use ('auto', 'ball_tree', 'kd_tree', 'brute')
        metric : str
            Distance metric ('cosine', 'euclidean', 'manhattan')
        use_stemming : bool
            Whether to use stemming for ingredient normalization
        """
        self.k = k
        self.algorithm = algorithm
        self.metric = metric
        self.use_stemming = use_stemming

        # Core data structures
        self.recipes = []
        self.ingredient_to_recipes = defaultdict(list)
        self.ingredient_names = set()
        self.ingredient_importance_scores = {}

        # ML models and vectors
        self.vectorizer = None
        self.recipe_vectors = None
        self.knn_model = None
        self.scaler = None
        self.svd_model = None

        # Enhanced features
        self.ingredient_categories = {}
        self.cuisine_vectors = {}
        self.recipe_features = None
        self.stemmer = SimpleStemmer() if use_stemming else None

        # Caching for performance
        self.query_cache = {}
        self.max_cache_size = 1000

        # Define common/basic ingredients that should have lower importance
        self.common_ingredients = {
            # Basic seasonings and spices
            'salt', 'kosher salt', 'sea salt', 'table salt', 'teaspoon salt', 'tablespoon salt',
            'pepper', 'black pepper', 'white pepper', 'freshly black pepper', 'teaspoon black pepper',
            'sugar', 'white sugar', 'brown sugar', 'cup sugar', 'teaspoon sugar', 'tablespoon sugar',
            'water', 'cold water', 'warm water', 'boiling water', 'ice water',

            # Basic oils and fats
            'oil', 'vegetable oil', 'olive oil', 'cooking oil', 'canola oil',
            'butter', 'unsalted butter', 'salted butter',

            # Basic baking ingredients
            'flour', 'all-purpose flour', 'baking powder', 'baking soda', 'vanilla extract',
            'eggs', 'egg', 'egg whites', 'egg yolks',

            # Basic dairy
            'milk', 'whole milk', 'skim milk', '2% milk',

            # Basic aromatics (still important but very common)
            'garlic', 'garlic cloves', 'garlic clove', 'onion', 'onions',

            # Basic herbs (common but not as basic as salt/pepper)
            'parsley', 'fresh parsley', 'dried parsley',

            # Measurements and preparations that got through cleaning
            'cup', 'teaspoon', 'tablespoon', 'pound', 'ounce', 'chopped', 'diced', 'minced'
        }

    def load_recipes(self, recipes_file, max_rows=None):
        """
        Load recipes from JSON file.

        Parameters:
        -----------
        recipes_file : str
            Path to the recipes JSON file
        max_rows : int, optional
            Maximum number of recipes to load
        """
        try:
            print(f"Loading recipes from {recipes_file}...")

            with open(recipes_file, 'r', encoding='utf-8') as f:
                all_recipes = json.load(f)

            # Limit recipes if specified
            if max_rows:
                all_recipes = all_recipes[:max_rows]

            self.recipes = []
            self.ingredient_to_recipes = defaultdict(list)
            self.ingredient_names = set()

            for recipe in all_recipes:
                # Store recipe
                recipe_data = {
                    'id': recipe['id'],
                    'name': recipe['name'],
                    'ingredients': recipe['ingredients'],
                    'instructions': recipe['instructions'],
                    'prep_time': recipe.get('prep_time', 30),
                    'cook_time': recipe.get('cook_time', 45),
                    'servings': recipe.get('servings', 4),
                    'cuisine': recipe.get('cuisine', 'International'),
                    'difficulty': recipe.get('difficulty', 'Medium')
                }

                self.recipes.append(recipe_data)

                # Index ingredients
                for ingredient in recipe['ingredients']:
                    ingredient_clean = ingredient.lower().strip()
                    self.ingredient_names.add(ingredient_clean)
                    self.ingredient_to_recipes[ingredient_clean].append(len(self.recipes) - 1)

            print(f"Successfully loaded {len(self.recipes)} recipes")
            print(f"Found {len(self.ingredient_names)} unique ingredients")

            # Calculate ingredient importance scores
            self._calculate_ingredient_importance()

            # Create enhanced vectors and KNN model
            self._create_enhanced_vectors()

        except Exception as e:
            print(f"Error loading recipes: {e}")
            raise

    def _calculate_ingredient_importance(self):
        """Calculate enhanced importance scores for ingredients based on frequency, category, and uniqueness."""
        print("Calculating enhanced ingredient importance scores...")

        # Count ingredient frequencies
        ingredient_counts = {}
        total_recipes = len(self.recipes)

        for ingredient in self.ingredient_names:
            count = len(self.ingredient_to_recipes[ingredient])
            ingredient_counts[ingredient] = count

        # Calculate importance scores with enhanced logic
        for ingredient in self.ingredient_names:
            count = ingredient_counts[ingredient]

            # Base score: inverse frequency (rarer ingredients are more important)
            # Use log to smooth the curve and add small constant to avoid log(0)
            frequency_score = math.log(total_recipes / max(count, 1)) + 1

            # Enhanced categorization and scoring
            category_multiplier = self._get_ingredient_category_multiplier(ingredient)
            frequency_score *= category_multiplier

            # Penalty for very common ingredients
            if self._is_common_ingredient(ingredient):
                # Very common ingredients get heavily penalized
                if ingredient in ['salt', 'pepper', 'water', 'oil', 'sugar']:
                    penalty = 0.05  # 95% penalty
                elif ingredient in ['garlic', 'onion', 'butter', 'flour', 'eggs']:
                    penalty = 0.2   # 80% penalty
                else:
                    penalty = 0.4   # 60% penalty
                frequency_score *= penalty

            # Boost for special/unique ingredients
            if self._is_special_ingredient(ingredient):
                frequency_score *= 2.0  # 100% boost

            # Additional boost for protein sources (main ingredients)
            if self._is_protein_source(ingredient):
                frequency_score *= 1.8  # 80% boost

            # Boost for unique cooking techniques or special preparations
            if self._has_special_preparation(ingredient):
                frequency_score *= 1.3  # 30% boost

            self.ingredient_importance_scores[ingredient] = max(frequency_score, 0.01)

        # Normalize scores to 0-10 range for better interpretability
        max_score = max(self.ingredient_importance_scores.values())
        for ingredient in self.ingredient_importance_scores:
            self.ingredient_importance_scores[ingredient] = (
                self.ingredient_importance_scores[ingredient] / max_score * 10
            )

        # Show some examples
        sorted_ingredients = sorted(self.ingredient_importance_scores.items(),
                                  key=lambda x: x[1], reverse=True)

        print("Most important ingredients:")
        for ingredient, score in sorted_ingredients[:15]:
            print(f"  {ingredient}: {score:.3f}")

        print("Least important ingredients:")
        for ingredient, score in sorted_ingredients[-10:]:
            print(f"  {ingredient}: {score:.3f}")

    def _is_common_ingredient(self, ingredient):
        """Check if an ingredient is common/basic."""
        ingredient_lower = ingredient.lower().strip()

        # Direct match
        if ingredient_lower in self.common_ingredients:
            return True

        # Partial matches for variations
        common_keywords = ['salt', 'pepper', 'sugar', 'water', 'oil', 'butter', 'flour', 'egg']
        for keyword in common_keywords:
            if keyword in ingredient_lower:
                return True

        return False

    def _get_ingredient_category_multiplier(self, ingredient):
        """Get category-based multiplier for ingredient importance."""
        ingredient_lower = ingredient.lower().strip()

        # Protein sources (highest importance)
        if self._is_protein_source(ingredient_lower):
            return 2.5

        # Unique vegetables and fruits
        unique_produce = ['truffle', 'saffron', 'artichoke', 'asparagus', 'avocado',
                         'eggplant', 'zucchini', 'fennel', 'leek', 'shallot']
        if any(produce in ingredient_lower for produce in unique_produce):
            return 2.0

        # Specialty grains and starches
        grains = ['quinoa', 'barley', 'couscous', 'polenta', 'risotto', 'bulgur']
        if any(grain in ingredient_lower for grain in grains):
            return 1.8

        # Specialty cheeses and dairy
        special_dairy = ['parmesan', 'mozzarella', 'cheddar', 'brie', 'goat cheese',
                        'ricotta', 'feta', 'blue cheese', 'gruyere']
        if any(dairy in ingredient_lower for dairy in special_dairy):
            return 1.6

        # Herbs and spices (moderate importance)
        herbs_spices = ['basil', 'oregano', 'thyme', 'rosemary', 'sage', 'cilantro',
                       'parsley', 'cumin', 'paprika', 'turmeric', 'ginger']
        if any(herb in ingredient_lower for herb in herbs_spices):
            return 1.2

        # Default multiplier
        return 1.0

    def _is_protein_source(self, ingredient):
        """Check if an ingredient is a protein source."""
        ingredient_lower = ingredient.lower().strip()

        proteins = [
            # Meats
            'beef', 'chicken', 'pork', 'lamb', 'veal', 'duck', 'turkey', 'venison',
            # Seafood
            'fish', 'salmon', 'tuna', 'cod', 'halibut', 'trout', 'bass', 'snapper',
            'shrimp', 'crab', 'lobster', 'scallops', 'mussels', 'clams', 'oysters',
            # Plant proteins
            'tofu', 'tempeh', 'seitan', 'beans', 'lentils', 'chickpeas', 'quinoa'
        ]

        return any(protein in ingredient_lower for protein in proteins)

    def _has_special_preparation(self, ingredient):
        """Check if ingredient has special preparation methods."""
        ingredient_lower = ingredient.lower().strip()

        special_preparations = [
            'marinated', 'smoked', 'cured', 'aged', 'fermented', 'pickled',
            'roasted', 'grilled', 'braised', 'confit', 'sous vide'
        ]

        return any(prep in ingredient_lower for prep in special_preparations)

    def _is_special_ingredient(self, ingredient):
        """Check if an ingredient is special/unique."""
        ingredient_lower = ingredient.lower().strip()

        # Proteins (main ingredients)
        proteins = ['beef', 'chicken', 'pork', 'lamb', 'fish', 'salmon', 'tuna', 'shrimp',
                   'crab', 'lobster', 'duck', 'turkey', 'veal']

        # Unique vegetables and fruits
        special_produce = ['truffle', 'saffron', 'caviar', 'foie gras', 'wagyu', 'lobster',
                          'artichoke', 'asparagus', 'avocado', 'eggplant', 'zucchini']

        # Specialty cheeses and dairy
        special_dairy = ['parmesan', 'mozzarella', 'cheddar', 'brie', 'goat cheese',
                        'ricotta', 'feta', 'blue cheese']

        # Grains and starches
        grains = ['rice', 'pasta', 'quinoa', 'barley', 'couscous', 'polenta', 'risotto']

        # Specialty spices and herbs
        special_spices = ['saffron', 'cardamom', 'star anise', 'lemongrass', 'ginger',
                         'turmeric', 'cumin', 'coriander', 'paprika', 'cayenne']

        all_special = proteins + special_produce + special_dairy + grains + special_spices

        for special in all_special:
            if special in ingredient_lower:
                return True

        return False

    def _normalize_ingredient(self, ingredient):
        """Enhanced ingredient normalization with optional stemming."""
        if not ingredient:
            return ""

        # Convert to lowercase and strip whitespace
        normalized = ingredient.lower().strip()

        # Remove common prefixes and suffixes that don't affect meaning
        # Remove measurements and quantities (enhanced patterns)
        normalized = re.sub(r'^\d+(\.\d+)?\s*(cups?|tablespoons?|teaspoons?|pounds?|ounces?|lbs?|oz|tsp|tbsp|cloves?|pieces?|slices?|cans?|packages?|jars?|grams?|kg|ml|liters?)\s+', '', normalized)
        normalized = re.sub(r'^\d+/\d+\s+', '', normalized)
        normalized = re.sub(r'^\d+\s*-\s*\d+\s+', '', normalized)

        # Remove common descriptors (expanded list)
        descriptors_to_remove = [
            'fresh', 'dried', 'chopped', 'minced', 'diced', 'sliced', 'grated', 'ground',
            'whole', 'large', 'small', 'medium', 'fine', 'coarse', 'extra', 'virgin',
            'unsalted', 'salted', 'raw', 'cooked', 'frozen', 'canned', 'organic',
            'finely', 'coarsely', 'thinly', 'thickly', 'roughly', 'plus', 'more', 'for',
            'about', 'approximately', 'room', 'temperature', 'cold', 'warm', 'hot',
            'preferably', 'optional', 'divided', 'separated', 'peeled', 'trimmed',
            'boneless', 'skinless', 'lean', 'fat', 'reduced', 'low', 'free', 'range'
        ]

        words = normalized.split()
        filtered_words = []
        for word in words:
            # Remove punctuation but keep hyphens in compound words
            clean_word = re.sub(r'[^\w\-]', '', word)
            if clean_word and clean_word not in descriptors_to_remove and len(clean_word) > 1:
                # Apply stemming if enabled
                if self.use_stemming and self.stemmer:
                    clean_word = self.stemmer.stem(clean_word)
                filtered_words.append(clean_word)

        result = ' '.join(filtered_words)

        # Additional cleanup for common patterns
        result = re.sub(r'\s+', ' ', result)  # Multiple spaces to single space
        result = result.strip()

        return result

    def _get_ingredient_variations(self, ingredient):
        """Generate variations of an ingredient name for better matching."""
        variations = set()
        normalized = self._normalize_ingredient(ingredient)

        if not normalized:
            return variations

        # Add the normalized version
        variations.add(normalized)

        # Handle plurals and singulars
        words = normalized.split()
        if words:
            # For single word ingredients
            if len(words) == 1:
                word = words[0]
                variations.add(word)

                # Add plural/singular variations
                if word.endswith('s') and len(word) > 3:
                    # Try removing 's' for singular
                    singular = word[:-1]
                    variations.add(singular)

                    # Handle special cases like "tomatoes" -> "tomato"
                    if word.endswith('es') and len(word) > 4:
                        singular_es = word[:-2]
                        variations.add(singular_es)

                    # Handle "ies" -> "y" (like "berries" -> "berry")
                    if word.endswith('ies') and len(word) > 4:
                        singular_ies = word[:-3] + 'y'
                        variations.add(singular_ies)
                else:
                    # Add plural forms
                    variations.add(word + 's')
                    if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
                        variations.add(word + 'es')
                    elif word.endswith('y') and len(word) > 2 and word[-2] not in 'aeiou':
                        variations.add(word[:-1] + 'ies')

            # For multi-word ingredients, try variations of the last word (usually the main ingredient)
            else:
                last_word = words[-1]
                base_phrase = ' '.join(words[:-1])

                # Generate variations of the last word
                last_word_variations = self._get_ingredient_variations(last_word)
                for var in last_word_variations:
                    if var != last_word:  # Don't duplicate the original
                        variations.add(f"{base_phrase} {var}")

        return variations

    def _find_best_ingredient_match(self, user_ingredient, similarity_threshold=0.6):
        """Find the best matching ingredient from the database."""
        user_ingredient = user_ingredient.lower().strip()

        # Generate variations of the user input
        user_variations = self._get_ingredient_variations(user_ingredient)

        best_matches = []

        # First, try exact matches with variations
        for variation in user_variations:
            for db_ingredient in self.ingredient_names:
                db_normalized = self._normalize_ingredient(db_ingredient)

                # Exact match
                if variation == db_normalized:
                    return db_ingredient, 1.0, "exact"

                # Check if variation is contained in database ingredient
                if variation in db_normalized or db_normalized in variation:
                    similarity = len(variation) / max(len(variation), len(db_normalized))
                    best_matches.append((db_ingredient, similarity, "contains"))

        # If no exact matches, try fuzzy matching
        if not best_matches:
            for variation in user_variations:
                for db_ingredient in self.ingredient_names:
                    db_normalized = self._normalize_ingredient(db_ingredient)

                    # Calculate similarity using sequence matching
                    similarity = SequenceMatcher(None, variation, db_normalized).ratio()

                    if similarity >= similarity_threshold:
                        best_matches.append((db_ingredient, similarity, "fuzzy"))

        # Return the best match
        if best_matches:
            best_matches.sort(key=lambda x: x[1], reverse=True)
            return best_matches[0]

        return None, 0.0, "none"

    def _create_enhanced_vectors(self):
        """Create enhanced feature vectors combining TF-IDF with additional features."""
        try:
            print("Creating enhanced feature vectors for KNN similarity calculation...")

            # Create documents from recipe ingredients
            recipe_documents = []
            for recipe in self.recipes:
                # Combine ingredients into a single document with importance weighting
                weighted_ingredients = []
                for ingredient in recipe['ingredients']:
                    normalized_ing = self._normalize_ingredient(ingredient)
                    if normalized_ing:
                        # Weight ingredients by their importance
                        importance = self.ingredient_importance_scores.get(ingredient.lower().strip(), 1.0)
                        # Add ingredient multiple times based on importance (up to 3 times)
                        repeat_count = min(int(importance / 2) + 1, 3)
                        weighted_ingredients.extend([normalized_ing] * repeat_count)

                doc = ' '.join(weighted_ingredients)
                recipe_documents.append(doc)

            # Create enhanced TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words='english',
                ngram_range=(1, 3),  # Use unigrams, bigrams, and trigrams
                max_features=8000,   # Increased features for better representation
                min_df=2,           # Ignore terms that appear in less than 2 documents
                max_df=0.8,         # Ignore terms that appear in more than 80% of documents
                sublinear_tf=True   # Use sublinear term frequency scaling
            )

            # Fit and transform the documents
            tfidf_vectors = self.vectorizer.fit_transform(recipe_documents)

            # Create additional feature vectors
            additional_features = self._create_additional_features()

            # Combine TF-IDF with additional features
            if additional_features is not None:
                from scipy.sparse import hstack
                self.recipe_vectors = hstack([tfidf_vectors, additional_features])
            else:
                self.recipe_vectors = tfidf_vectors

            # Apply dimensionality reduction if vectors are too large
            if self.recipe_vectors.shape[1] > 5000:
                print("Applying dimensionality reduction...")
                self.svd_model = TruncatedSVD(n_components=1000, random_state=42)
                self.recipe_vectors = self.svd_model.fit_transform(self.recipe_vectors)

            # Initialize and fit KNN model
            print(f"Initializing KNN model with {self.k} neighbors...")
            self.knn_model = NearestNeighbors(
                n_neighbors=min(self.k * 3, len(self.recipes)),  # Get more neighbors for filtering
                algorithm=self.algorithm,
                metric=self.metric if self.metric != 'cosine' else 'cosine',
                n_jobs=-1  # Use all available cores
            )

            self.knn_model.fit(self.recipe_vectors)

            print("Enhanced vectors and KNN model created successfully")
            print(f"Feature vector shape: {self.recipe_vectors.shape}")

        except Exception as e:
            print(f"Error creating enhanced vectors: {e}")
            raise

    def _create_additional_features(self):
        """Create additional numerical features for recipes."""
        try:
            features = []

            for recipe in self.recipes:
                recipe_features = []

                # Basic recipe metadata
                recipe_features.append(recipe.get('prep_time', 30) / 100.0)  # Normalized prep time
                recipe_features.append(recipe.get('cook_time', 45) / 100.0)  # Normalized cook time
                recipe_features.append(recipe.get('servings', 4) / 10.0)     # Normalized servings

                # Ingredient count and complexity
                ingredient_count = len(recipe['ingredients'])
                recipe_features.append(ingredient_count / 20.0)  # Normalized ingredient count

                # Instruction complexity (number of steps)
                instruction_count = len(recipe['instructions'])
                recipe_features.append(instruction_count / 20.0)  # Normalized instruction count

                # Cuisine encoding (one-hot for major cuisines)
                cuisine = recipe.get('cuisine', 'International').lower()
                major_cuisines = ['italian', 'chinese', 'mexican', 'indian', 'french', 'american']
                for major_cuisine in major_cuisines:
                    recipe_features.append(1.0 if major_cuisine in cuisine else 0.0)

                # Difficulty encoding
                difficulty = recipe.get('difficulty', 'Medium').lower()
                recipe_features.append(1.0 if difficulty == 'easy' else 0.0)
                recipe_features.append(1.0 if difficulty == 'medium' else 0.0)
                recipe_features.append(1.0 if difficulty == 'hard' else 0.0)

                # Ingredient importance score (average)
                importance_scores = []
                for ingredient in recipe['ingredients']:
                    score = self.ingredient_importance_scores.get(ingredient.lower().strip(), 1.0)
                    importance_scores.append(score)
                avg_importance = sum(importance_scores) / len(importance_scores) if importance_scores else 1.0
                recipe_features.append(avg_importance / 10.0)  # Normalized average importance

                # Protein content indicator
                has_protein = any(self._is_protein_source(ing) for ing in recipe['ingredients'])
                recipe_features.append(1.0 if has_protein else 0.0)

                features.append(recipe_features)

            return np.array(features) if features else None

        except Exception as e:
            print(f"Warning: Could not create additional features: {e}")
            return None

    def find_matching_ingredients(self, user_input):
        """
        Find ingredients that match user input and classify them by importance.
        Uses intelligent matching for plurals, variations, and similar forms.

        Parameters:
        -----------
        user_input : str
            User input string with ingredient names

        Returns:
        --------
        tuple
            (matched_ingredients, important_ingredients, common_ingredients)
        """
        # Split user input by commas and clean
        input_ingredients = [ing.strip() for ing in user_input.split(',') if ing.strip()]

        matched_ingredients = []
        important_ingredients = []
        common_ingredients = []

        for input_ing in input_ingredients:
            if not input_ing:
                continue

            # Use intelligent matching to find the best match
            best_match, similarity, match_type = self._find_best_ingredient_match(input_ing)

            if best_match:
                matched_ingredients.append(best_match)

                # Classify by importance
                if self._is_common_ingredient(best_match):
                    common_ingredients.append(best_match)
                    if match_type == "exact":
                        print(f"  - '{input_ing}' (exact match, common)")
                    else:
                        print(f"  - '{input_ing}' → '{best_match}' (similarity: {similarity:.2f}, common)")
                else:
                    important_ingredients.append(best_match)
                    if match_type == "exact":
                        print(f"  - '{input_ing}' (exact match, important)")
                    else:
                        print(f"  - '{input_ing}' → '{best_match}' (similarity: {similarity:.2f}, important)")
            else:
                print(f"  - '{input_ing}' (no match found)")

        return matched_ingredients, important_ingredients, common_ingredients

    def recommend_recipes(self, user_input, num_recommendations=None, diversity_factor=0.3,
                         cuisine_filter=None, max_prep_time=None):
        """
        Enhanced KNN-based recipe recommendation with diversity and filtering options.

        Parameters:
        -----------
        user_input : str or list
            User input ingredients (string or list of ingredient names)
        num_recommendations : int, optional
            Number of recommendations to return
        diversity_factor : float
            Factor to promote diversity in recommendations (0.0 = no diversity, 1.0 = max diversity)
        cuisine_filter : str, optional
            Filter recipes by cuisine type
        max_prep_time : int, optional
            Maximum preparation time in minutes

        Returns:
        --------
        list
            List of recommended recipes with scores
        """
        if num_recommendations is None:
            num_recommendations = self.k

        # Check cache first
        cache_key = f"{user_input}_{num_recommendations}_{diversity_factor}_{cuisine_filter}_{max_prep_time}"
        if cache_key in self.query_cache:
            print("Using cached results...")
            return self.query_cache[cache_key]

        # Handle input
        if isinstance(user_input, str):
            matched_ingredients, important_ingredients, common_ingredients = self.find_matching_ingredients(user_input)
        else:
            matched_ingredients = [ing.lower().strip() for ing in user_input]
            important_ingredients = [ing for ing in matched_ingredients if not self._is_common_ingredient(ing)]
            common_ingredients = [ing for ing in matched_ingredients if self._is_common_ingredient(ing)]

        if not matched_ingredients:
            return []

        print(f"Important ingredients: {important_ingredients}")
        print(f"Common ingredients: {common_ingredients}")
        print(f"Using enhanced KNN algorithm for recipe matching...")

        # Create enhanced query vector
        query_vector = self._create_query_vector(important_ingredients, common_ingredients)

        # Use KNN to find similar recipes
        distances, indices = self.knn_model.kneighbors(query_vector,
                                                      n_neighbors=min(num_recommendations * 5, len(self.recipes)))

        # Calculate enhanced scores combining KNN distance with ingredient matching
        recipe_scores = []
        for i, (distance, recipe_idx) in enumerate(zip(distances[0], indices[0])):
            recipe = self.recipes[recipe_idx]

            # Apply filters
            if cuisine_filter and cuisine_filter.lower() not in recipe.get('cuisine', '').lower():
                continue
            if max_prep_time and recipe.get('prep_time', 0) > max_prep_time:
                continue

            # Calculate ingredient matching score
            ingredient_score = self._calculate_ingredient_matching_score(
                recipe, important_ingredients, common_ingredients
            )

            # Convert distance to similarity (lower distance = higher similarity)
            knn_similarity = 1.0 / (1.0 + distance)

            # Combine scores
            final_score = (knn_similarity * 0.6) + (ingredient_score * 0.4)

            recipe_scores.append({
                'recipe_idx': recipe_idx,
                'score': final_score,
                'knn_distance': distance,
                'ingredient_score': ingredient_score,
                'diversity_penalty': 0.0  # Will be calculated later
            })

        # Apply diversity penalty to avoid too similar recipes
        if diversity_factor > 0:
            recipe_scores = self._apply_diversity_penalty(recipe_scores, diversity_factor)

        # Sort by final score
        recipe_scores.sort(key=lambda x: x['score'], reverse=True)

        # Build final recommendations
        recommendations = []
        for item in recipe_scores[:num_recommendations]:
            recipe = self.recipes[item['recipe_idx']]

            # Find which ingredients matched
            matched_in_recipe, important_matched, common_matched = self._find_matched_ingredients(
                recipe, important_ingredients, common_ingredients
            )

            recommendation = {
                'id': recipe['id'],
                'name': recipe['name'],
                'score': item['score'],
                'knn_distance': item['knn_distance'],
                'ingredient_score': item['ingredient_score'],
                'ingredients': recipe['ingredients'],
                'matched_ingredients': matched_in_recipe,
                'important_matched': important_matched,
                'common_matched': common_matched,
                'instructions': recipe['instructions'],
                'prep_time': recipe['prep_time'],
                'cook_time': recipe['cook_time'],
                'servings': recipe['servings'],
                'cuisine': recipe['cuisine'],
                'difficulty': recipe['difficulty']
            }

            recommendations.append(recommendation)

        # Cache results
        if len(self.query_cache) < self.max_cache_size:
            self.query_cache[cache_key] = recommendations

        return recommendations

    def _create_query_vector(self, important_ingredients, common_ingredients):
        """Create a query vector from user ingredients."""
        # Create weighted query prioritizing important ingredients
        weighted_query_parts = []

        for ingredient in important_ingredients:
            normalized_ing = self._normalize_ingredient(ingredient)
            if normalized_ing:
                # Add important ingredients multiple times based on their importance
                importance_score = self.ingredient_importance_scores.get(ingredient, 1.0)
                weight = min(int(importance_score / 2) + 2, 4)  # 2-4 repetitions
                weighted_query_parts.extend([normalized_ing] * weight)

        # Add common ingredients with lower weight
        for ingredient in common_ingredients:
            normalized_ing = self._normalize_ingredient(ingredient)
            if normalized_ing:
                weighted_query_parts.append(normalized_ing)

        user_query = ' '.join(weighted_query_parts)

        # Transform using the same vectorizer
        query_tfidf = self.vectorizer.transform([user_query])

        # Create dummy additional features to match training data
        additional_features = self._create_query_additional_features()

        # Combine TF-IDF with additional features
        if additional_features is not None:
            from scipy.sparse import hstack, csr_matrix
            combined_query = hstack([query_tfidf, csr_matrix(additional_features)])
        else:
            combined_query = query_tfidf

        # Apply dimensionality reduction if it was used during training
        if hasattr(self, 'svd_model') and self.svd_model is not None:
            query_vector = self.svd_model.transform(combined_query)
        else:
            query_vector = combined_query

        return query_vector

    def _create_query_additional_features(self):
        """Create dummy additional features for query to match training data dimensions."""
        try:
            # Create default/average features for a query
            query_features = []

            # Default recipe metadata (using averages)
            query_features.append(30 / 100.0)  # Default prep time
            query_features.append(45 / 100.0)  # Default cook time
            query_features.append(4 / 10.0)    # Default servings

            # Default ingredient count (estimated)
            query_features.append(8 / 20.0)    # Estimated ingredient count

            # Default instruction complexity
            query_features.append(10 / 20.0)   # Estimated instruction count

            # Cuisine encoding (all zeros for query - no specific cuisine)
            major_cuisines = ['italian', 'chinese', 'mexican', 'indian', 'french', 'american']
            for _ in major_cuisines:
                query_features.append(0.0)

            # Difficulty encoding (default to medium)
            query_features.append(0.0)  # easy
            query_features.append(1.0)  # medium
            query_features.append(0.0)  # hard

            # Average importance (estimated)
            query_features.append(5.0 / 10.0)  # Average importance

            # Protein content (assume yes for most queries)
            query_features.append(1.0)

            return np.array([query_features])

        except Exception as e:
            print(f"Warning: Could not create query additional features: {e}")
            return None

    def _calculate_ingredient_matching_score(self, recipe, important_ingredients, common_ingredients):
        """Calculate how well a recipe matches the user's ingredients."""
        recipe_ingredients = [ing.lower().strip() for ing in recipe['ingredients']]

        # Score for important ingredient matches
        important_score = 0
        important_matches = 0
        for ing in important_ingredients:
            if any(ing in recipe_ing for recipe_ing in recipe_ingredients):
                importance = self.ingredient_importance_scores.get(ing, 1.0)
                important_score += importance
                important_matches += 1

        # Score for common ingredient matches
        common_score = 0
        common_matches = 0
        for ing in common_ingredients:
            if any(ing in recipe_ing for recipe_ing in recipe_ingredients):
                common_score += 0.3  # Lower weight for common ingredients
                common_matches += 1

        # Bonus for having multiple important ingredients
        if important_matches > 1:
            important_score *= (1 + 0.2 * (important_matches - 1))

        # Penalty for recipes with too many unmatched ingredients
        total_recipe_ingredients = len(recipe_ingredients)
        total_matches = important_matches + common_matches
        if total_recipe_ingredients > 0:
            match_ratio = total_matches / total_recipe_ingredients
            if match_ratio < 0.3:  # Less than 30% match
                penalty = 0.5
            else:
                penalty = 1.0
        else:
            penalty = 1.0

        final_score = (important_score + common_score) * penalty
        return min(final_score / 10.0, 1.0)  # Normalize to 0-1 range

    def _apply_diversity_penalty(self, recipe_scores, diversity_factor):
        """Apply diversity penalty to promote varied recommendations."""
        if len(recipe_scores) <= 1:
            return recipe_scores

        # Calculate similarity between recipes based on ingredients
        for i, score_item in enumerate(recipe_scores):
            recipe_i = self.recipes[score_item['recipe_idx']]
            ingredients_i = set(ing.lower().strip() for ing in recipe_i['ingredients'])

            diversity_penalty = 0
            for j, other_score_item in enumerate(recipe_scores[:i]):  # Only compare with higher-ranked recipes
                recipe_j = self.recipes[other_score_item['recipe_idx']]
                ingredients_j = set(ing.lower().strip() for ing in recipe_j['ingredients'])

                # Calculate Jaccard similarity
                intersection = len(ingredients_i.intersection(ingredients_j))
                union = len(ingredients_i.union(ingredients_j))
                similarity = intersection / union if union > 0 else 0

                # Apply penalty based on similarity and position
                position_weight = 1.0 / (j + 1)  # Higher penalty for similarity to top recipes
                diversity_penalty += similarity * position_weight * diversity_factor

            # Apply the penalty
            score_item['diversity_penalty'] = diversity_penalty
            score_item['score'] = score_item['score'] * (1 - diversity_penalty)

        return recipe_scores

    def _find_matched_ingredients(self, recipe, important_ingredients, common_ingredients):
        """Find which ingredients matched in a recipe."""
        recipe_ingredients = [ing.lower().strip() for ing in recipe['ingredients']]
        matched_in_recipe = []
        important_matched = []
        common_matched = []

        for ing in important_ingredients:
            for recipe_ing in recipe_ingredients:
                if ing in recipe_ing:
                    matched_in_recipe.append(recipe_ing)
                    important_matched.append(recipe_ing)
                    break

        for ing in common_ingredients:
            for recipe_ing in recipe_ingredients:
                if ing in recipe_ing:
                    matched_in_recipe.append(recipe_ing)
                    common_matched.append(recipe_ing)
                    break

        return matched_in_recipe, important_matched, common_matched

def main():
    """Test the clean recipe recommender."""
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    recipes_file = os.path.join(base_dir, 'data', 'clean_recipes.json')

    if not os.path.exists(recipes_file):
        print(f"Error: Recipe file not found at {recipes_file}")
        print("Please run the dataset download script first.")
        return

    # Create recommender
    print("Creating Enhanced KNN Recipe Recommender...")
    recommender = EnhancedKNNRecipeRecommender(k=10, metric='cosine', use_stemming=False)

    # Load recipes (limit to 5000 for faster testing)
    recommender.load_recipes(recipes_file, max_rows=5000)

    # Test recommendations
    print("\n" + "="*60)
    print("Testing Recipe Recommendations")
    print("="*60)

    test_ingredients = [
        "chicken, garlic, onion",
        "beef, potato, carrot",
        "pasta, tomato, cheese",
        "egg, flour, sugar"
    ]

    for ingredients in test_ingredients:
        print(f"\nSearching for recipes with: {ingredients}")
        print("Matched ingredients:")

        recommendations = recommender.recommend_recipes(ingredients, 5)

        if recommendations:
            print(f"\nFound {len(recommendations)} recommendations:")
            print("-" * 40)

            for i, recipe in enumerate(recommendations, 1):
                print(f"{i}. {recipe['name']} (Score: {recipe['score']:.3f})")
                print(f"   Matched: {', '.join(recipe['matched_ingredients'])}")
                print(f"   All ingredients: {', '.join(recipe['ingredients'][:5])}...")
                print(f"   Cuisine: {recipe['cuisine']} | Difficulty: {recipe['difficulty']}")
                print()
        else:
            print("No recommendations found.")

        print("-" * 60)

if __name__ == "__main__":
    main()
