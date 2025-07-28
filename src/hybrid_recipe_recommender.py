"""
Hybrid Recipe Recommendation System

This module implements a hybrid recommendation approach that combines:
1. KNN-based collaborative filtering (primary algorithm)
2. Content-based filtering using recipe attributes
3. Collaborative filtering using user ratings and reviews
4. Popularity-based recommendations

The hybrid system maintains the existing KNN algorithm as the core component
while enhancing it with additional recommendation techniques.
"""

import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Import the existing KNN recommender
from clean_recipe_recommender import EnhancedKNNRecipeRecommender


class HybridRecipeRecommender:
    """
    Hybrid recipe recommendation system that combines multiple recommendation techniques.

    This system uses:
    1. KNN as the primary recommendation engine
    2. Content-based filtering for recipe attributes
    3. Collaborative filtering for user preferences
    4. Popularity-based recommendations for new users
    """

    def __init__(self, knn_weight=0.5, content_weight=0.25, collaborative_weight=0.15,
                 popularity_weight=0.1, k=10, metric='cosine'):
        """
        Initialize the hybrid recommender.

        Parameters:
        -----------
        knn_weight : float
            Weight for KNN recommendations (default: 0.5)
        content_weight : float
            Weight for content-based recommendations (default: 0.25)
        collaborative_weight : float
            Weight for collaborative filtering (default: 0.15)
        popularity_weight : float
            Weight for popularity-based recommendations (default: 0.1)
        k : int
            Number of recommendations to return
        metric : str
            Distance metric for KNN
        """
        # Validate weights sum to 1.0
        total_weight = knn_weight + content_weight + collaborative_weight + popularity_weight
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        self.knn_weight = knn_weight
        self.content_weight = content_weight
        self.collaborative_weight = collaborative_weight
        self.popularity_weight = popularity_weight
        self.k = k

        # Initialize the core KNN recommender
        self.knn_recommender = EnhancedKNNRecipeRecommender(k=k, metric=metric, use_stemming=False)

        # Content-based filtering components
        self.content_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.attribute_scaler = StandardScaler()
        self.cuisine_encoder = LabelEncoder()
        self.difficulty_encoder = LabelEncoder()

        # Data storage
        self.recipes = []
        self.recipe_content_vectors = None
        self.recipe_attribute_vectors = None
        self.user_ratings = defaultdict(dict)  # user_id -> {recipe_id: rating}
        self.recipe_popularity_scores = {}
        self.recipe_avg_ratings = {}

        # Caching
        self.recommendation_cache = {}
        self.max_cache_size = 1000

        print("Hybrid Recipe Recommender initialized successfully!")

    def load_recipes(self, recipes_file, max_rows=None, include_user_recipes=True):
        """
        Load recipes and initialize all recommendation components.

        Parameters:
        -----------
        recipes_file : str
            Path to the recipes JSON file
        max_rows : int, optional
            Maximum number of recipes to load
        include_user_recipes : bool, optional
            Whether to include user-shared recipes from database (default: True)
        """
        print("Loading recipes for hybrid recommendation system...")

        # Load system recipes using the KNN recommender
        self.knn_recommender.load_recipes(recipes_file, max_rows)
        self.recipes = self.knn_recommender.recipes.copy()

        print(f"Loaded {len(self.recipes)} system recipes")

        # Load user-shared recipes from database if requested
        if include_user_recipes:
            user_recipes = self._load_user_shared_recipes()
            if user_recipes:
                print(f"Loading {len(user_recipes)} user-shared recipes...")

                # Add user recipes to the main recipe list
                self.recipes.extend(user_recipes)

                # Update KNN recommender's recipe list and indices
                self.knn_recommender.recipes = self.recipes
                self._update_knn_indices_with_user_recipes(user_recipes)

                print(f"Total recipes after including user-shared: {len(self.recipes)}")

        # Initialize content-based filtering
        self._initialize_content_based_filtering()

        # Initialize popularity scores
        self._initialize_popularity_scores()

        print("Hybrid recommendation system ready!")

    def _load_user_shared_recipes(self):
        """
        Load user-shared recipes from MongoDB database.

        Returns:
        --------
        list
            List of user-shared recipes in the same format as system recipes
        """
        try:
            from api.models.user import mongo
            if mongo is None or mongo.db is None:
                print("Warning: MongoDB not available, skipping user-shared recipes")
                return []

            # Get all user-shared recipes from database (no approval required)
            recipes_cursor = mongo.db.recipes.find({
                'original_id': {'$regex': '^user_'}
            })

            user_recipes = []
            for recipe in recipes_cursor:
                try:
                    # Parse ingredients if they're stored as string
                    ingredients = recipe.get('ingredients', [])
                    if isinstance(ingredients, str):
                        try:
                            import json
                            ingredients = json.loads(ingredients)
                        except:
                            ingredients = [ingredients] if ingredients else []

                    # Parse instructions if they're stored as string
                    instructions = recipe.get('instructions', recipe.get('steps', []))
                    if isinstance(instructions, str):
                        try:
                            import json
                            instructions = json.loads(instructions)
                        except:
                            instructions = [instructions] if instructions else []

                    # Ensure numeric fields are properly converted
                    def safe_int(value, default):
                        try:
                            return int(value) if value is not None else default
                        except (ValueError, TypeError):
                            return default

                    # Create recipe data in the same format as system recipes
                    recipe_data = {
                        'id': str(recipe['_id']),  # Use MongoDB ObjectId as string
                        'name': recipe.get('name', 'Untitled Recipe'),
                        'ingredients': ingredients,
                        'instructions': instructions,
                        'prep_time': safe_int(recipe.get('prep_time'), 30),
                        'cook_time': safe_int(recipe.get('cook_time'), 45),
                        'servings': safe_int(recipe.get('servings'), 4),
                        'cuisine': recipe.get('cuisine', 'International'),
                        'difficulty': recipe.get('difficulty', 'Medium'),
                        'is_user_recipe': True,  # Mark as user recipe
                        'submitted_by': recipe.get('submitted_by', ''),
                        'created_at': recipe.get('created_at')
                    }

                    user_recipes.append(recipe_data)

                except Exception as e:
                    print(f"Warning: Error processing user recipe {recipe.get('_id', 'unknown')}: {e}")
                    continue

            return user_recipes

        except Exception as e:
            print(f"Warning: Error loading user-shared recipes: {e}")
            return []

    def _update_knn_indices_with_user_recipes(self, user_recipes):
        """
        Update KNN recommender's ingredient indices with user recipes.

        Parameters:
        -----------
        user_recipes : list
            List of user-shared recipes to add to indices
        """
        try:
            # Get the starting index for new recipes
            start_index = len(self.knn_recommender.recipes) - len(user_recipes)

            # Add ingredients from user recipes to the KNN recommender's indices
            for i, recipe in enumerate(user_recipes):
                recipe_index = start_index + i

                for ingredient in recipe.get('ingredients', []):
                    ingredient_clean = ingredient.lower().strip()
                    self.knn_recommender.ingredient_names.add(ingredient_clean)
                    self.knn_recommender.ingredient_to_recipes[ingredient_clean].append(recipe_index)

            # Recalculate ingredient importance scores with new recipes
            self.knn_recommender._calculate_ingredient_importance()

            # Recreate enhanced vectors and KNN model with all recipes
            self.knn_recommender._create_enhanced_vectors()

            print(f"Updated KNN indices with {len(user_recipes)} user recipes")
            print(f"Total unique ingredients: {len(self.knn_recommender.ingredient_names)}")

        except Exception as e:
            print(f"Warning: Error updating KNN indices with user recipes: {e}")

    def _initialize_content_based_filtering(self):
        """Initialize content-based filtering components."""
        print("Initializing content-based filtering...")

        try:
            # Prepare text content for TF-IDF
            recipe_texts = []
            cuisines = []
            difficulties = []
            prep_times = []
            cook_times = []
            servings = []

            for recipe in self.recipes:
                # Combine ingredients and instructions for text analysis
                ingredients_text = ' '.join(recipe.get('ingredients', []))
                instructions_text = ' '.join(recipe.get('instructions', []))
                combined_text = f"{ingredients_text} {instructions_text}"
                recipe_texts.append(combined_text)

                # Extract attributes
                cuisines.append(recipe.get('cuisine', 'International'))
                difficulties.append(recipe.get('difficulty', 'Medium'))
                prep_times.append(recipe.get('prep_time', 30))
                cook_times.append(recipe.get('cook_time', 45))
                servings.append(recipe.get('servings', 4))

            # Create TF-IDF vectors for recipe content
            self.recipe_content_vectors = self.content_vectorizer.fit_transform(recipe_texts)

            # Encode categorical attributes
            cuisines_encoded = self.cuisine_encoder.fit_transform(cuisines)
            difficulties_encoded = self.difficulty_encoder.fit_transform(difficulties)

            # Combine numerical and categorical attributes
            attribute_matrix = np.column_stack([
                prep_times,
                cook_times,
                servings,
                cuisines_encoded,
                difficulties_encoded
            ])

            # Scale attributes
            self.recipe_attribute_vectors = self.attribute_scaler.fit_transform(attribute_matrix)

            print("Content-based filtering initialized successfully!")

        except Exception as e:
            print(f"Error initializing content-based filtering: {e}")
            # Fallback: create empty vectors
            self.recipe_content_vectors = np.zeros((len(self.recipes), 1))
            self.recipe_attribute_vectors = np.zeros((len(self.recipes), 5))

    def _initialize_popularity_scores(self):
        """Initialize popularity scores for recipes."""
        print("Initializing popularity scores...")

        # For now, initialize with default scores
        # This will be updated when we load user interaction data
        for recipe in self.recipes:
            recipe_id = recipe['id']
            self.recipe_popularity_scores[recipe_id] = 0.5  # Default popularity
            self.recipe_avg_ratings[recipe_id] = 3.0  # Default rating

        print("Popularity scores initialized!")

    def load_user_interaction_data(self, mongo_db):
        """
        Load user interaction data from MongoDB to enhance collaborative filtering.

        Parameters:
        -----------
        mongo_db : pymongo.database.Database
            MongoDB database instance
        """
        print("Loading user interaction data...")

        try:
            # Load user ratings and reviews
            reviews_collection = mongo_db.recipe_reviews
            reviews = list(reviews_collection.find({}))

            # Process ratings for collaborative filtering
            for review in reviews:
                user_id = review.get('user_id')
                recipe_id = review.get('recipe_id')
                rating = review.get('rating')

                if user_id and recipe_id and rating:
                    self.user_ratings[user_id][recipe_id] = rating

            # Calculate recipe popularity and average ratings
            recipe_stats = defaultdict(lambda: {'ratings': [], 'review_count': 0})

            for review in reviews:
                recipe_id = review.get('recipe_id')
                rating = review.get('rating')

                if recipe_id and rating:
                    recipe_stats[recipe_id]['ratings'].append(rating)
                    recipe_stats[recipe_id]['review_count'] += 1

            # Update popularity scores and average ratings
            for recipe_id, stats in recipe_stats.items():
                if stats['ratings']:
                    avg_rating = np.mean(stats['ratings'])
                    review_count = stats['review_count']

                    # Popularity score combines rating and review count
                    # Higher ratings and more reviews = higher popularity
                    popularity = (avg_rating / 5.0) * min(1.0, review_count / 10.0)

                    self.recipe_avg_ratings[recipe_id] = avg_rating
                    self.recipe_popularity_scores[recipe_id] = popularity

            print(f"Loaded interaction data for {len(self.user_ratings)} users")
            print(f"Updated popularity scores for {len(recipe_stats)} recipes")

        except Exception as e:
            print(f"Error loading user interaction data: {e}")

    def get_knn_recommendations(self, user_input, num_recommendations=None, **kwargs):
        """Get recommendations from the KNN algorithm."""
        if num_recommendations is None:
            num_recommendations = self.k

        return self.knn_recommender.recommend_recipes(
            user_input,
            num_recommendations=num_recommendations * 2,  # Get more for filtering
            **kwargs
        )

    def get_content_based_recommendations(self, user_input, user_preferences=None, num_recommendations=None):
        """
        Get content-based recommendations using recipe attributes and content similarity.

        Parameters:
        -----------
        user_input : str or list
            User input ingredients
        user_preferences : dict, optional
            User preferences for cuisine, difficulty, etc.
        num_recommendations : int, optional
            Number of recommendations to return
        """
        if num_recommendations is None:
            num_recommendations = self.k

        try:
            # Create query vector from user input
            if isinstance(user_input, str):
                query_text = user_input
            else:
                query_text = ' '.join(user_input)

            # Transform query text using TF-IDF
            query_content_vector = self.content_vectorizer.transform([query_text])

            # Calculate content similarity
            content_similarities = cosine_similarity(query_content_vector, self.recipe_content_vectors)[0]

            # Apply user preferences if provided
            preference_scores = np.ones(len(self.recipes))
            if user_preferences:
                for i, recipe in enumerate(self.recipes):
                    # Boost recipes matching user preferences
                    if 'cuisine' in user_preferences:
                        if recipe.get('cuisine', '').lower() == user_preferences['cuisine'].lower():
                            preference_scores[i] *= 1.5

                    if 'difficulty' in user_preferences:
                        if recipe.get('difficulty', '').lower() == user_preferences['difficulty'].lower():
                            preference_scores[i] *= 1.3

                    if 'max_prep_time' in user_preferences:
                        if recipe.get('prep_time', 0) <= user_preferences['max_prep_time']:
                            preference_scores[i] *= 1.2

            # Combine content similarity with preferences
            final_scores = content_similarities * preference_scores

            # Get top recommendations
            top_indices = np.argsort(final_scores)[::-1][:num_recommendations]

            recommendations = []
            for idx in top_indices:
                recipe = self.recipes[idx].copy()
                recipe['content_score'] = float(final_scores[idx])
                recommendations.append(recipe)

            return recommendations

        except Exception as e:
            print(f"Error in content-based recommendations: {e}")
            return []

    def get_collaborative_recommendations(self, user_id, num_recommendations=None):
        """
        Get collaborative filtering recommendations based on user ratings.

        Parameters:
        -----------
        user_id : str
            User ID for personalized recommendations
        num_recommendations : int, optional
            Number of recommendations to return
        """
        if num_recommendations is None:
            num_recommendations = self.k

        try:
            if user_id not in self.user_ratings or not self.user_ratings[user_id]:
                # New user - return popular recipes
                return self.get_popularity_based_recommendations(num_recommendations)

            user_ratings = self.user_ratings[user_id]

            # Find similar users based on rating patterns
            similar_users = []
            for other_user_id, other_ratings in self.user_ratings.items():
                if other_user_id == user_id:
                    continue

                # Find common recipes
                common_recipes = set(user_ratings.keys()) & set(other_ratings.keys())
                if len(common_recipes) < 2:  # Need at least 2 common ratings
                    continue

                # Calculate similarity (Pearson correlation)
                user_common_ratings = [user_ratings[recipe_id] for recipe_id in common_recipes]
                other_common_ratings = [other_ratings[recipe_id] for recipe_id in common_recipes]

                if len(set(user_common_ratings)) == 1 or len(set(other_common_ratings)) == 1:
                    continue  # Skip if all ratings are the same

                correlation = np.corrcoef(user_common_ratings, other_common_ratings)[0, 1]
                if not np.isnan(correlation) and correlation > 0.3:  # Minimum similarity threshold
                    similar_users.append((other_user_id, correlation))

            # Sort by similarity
            similar_users.sort(key=lambda x: x[1], reverse=True)

            # Get recommendations from similar users
            recipe_scores = defaultdict(float)
            recipe_count = defaultdict(int)

            for similar_user_id, similarity in similar_users[:10]:  # Top 10 similar users
                for recipe_id, rating in self.user_ratings[similar_user_id].items():
                    if recipe_id not in user_ratings:  # Only recommend unrated recipes
                        recipe_scores[recipe_id] += rating * similarity
                        recipe_count[recipe_id] += 1

            # Calculate average scores
            for recipe_id in recipe_scores:
                if recipe_count[recipe_id] > 0:
                    recipe_scores[recipe_id] /= recipe_count[recipe_id]

            # Get top recommendations
            sorted_recipes = sorted(recipe_scores.items(), key=lambda x: x[1], reverse=True)

            recommendations = []
            for recipe_id, score in sorted_recipes[:num_recommendations]:
                # Find recipe in our dataset
                recipe = None
                for r in self.recipes:
                    if str(r['id']) == str(recipe_id):
                        recipe = r.copy()
                        break

                if recipe:
                    recipe['collaborative_score'] = float(score)
                    recommendations.append(recipe)

            return recommendations

        except Exception as e:
            print(f"Error in collaborative recommendations: {e}")
            return []

    def get_popularity_based_recommendations(self, num_recommendations=None):
        """
        Get popularity-based recommendations.

        Parameters:
        -----------
        num_recommendations : int, optional
            Number of recommendations to return
        """
        if num_recommendations is None:
            num_recommendations = self.k

        try:
            # Sort recipes by popularity score
            recipe_popularity = []
            for recipe in self.recipes:
                recipe_id = recipe['id']
                popularity = self.recipe_popularity_scores.get(recipe_id, 0.5)
                avg_rating = self.recipe_avg_ratings.get(recipe_id, 3.0)

                # Combine popularity and rating for final score
                final_score = (popularity * 0.6) + (avg_rating / 5.0 * 0.4)

                recipe_copy = recipe.copy()
                recipe_copy['popularity_score'] = float(final_score)
                recipe_popularity.append((recipe_copy, final_score))

            # Sort by popularity score
            recipe_popularity.sort(key=lambda x: x[1], reverse=True)

            # Return top recommendations
            recommendations = [recipe for recipe, _ in recipe_popularity[:num_recommendations]]
            return recommendations

        except Exception as e:
            print(f"Error in popularity-based recommendations: {e}")
            return []

    def recommend_recipes(self, user_input, user_id=None, user_preferences=None,
                         num_recommendations=None, explanation=False, **kwargs):
        """
        Main hybrid recommendation method that combines all approaches.

        Parameters:
        -----------
        user_input : str or list
            User input ingredients
        user_id : str, optional
            User ID for personalized recommendations
        user_preferences : dict, optional
            User preferences for content-based filtering
        num_recommendations : int, optional
            Number of recommendations to return
        explanation : bool
            Whether to include explanation of recommendation sources
        **kwargs : dict
            Additional arguments for KNN recommender

        Returns:
        --------
        list
            List of recommended recipes with hybrid scores
        """
        if num_recommendations is None:
            num_recommendations = self.k

        # Create cache key
        cache_key = f"{user_input}_{user_id}_{user_preferences}_{num_recommendations}"
        if cache_key in self.recommendation_cache:
            return self.recommendation_cache[cache_key]

        print(f"Generating hybrid recommendations for: {user_input}")

        try:
            # Get recommendations from each approach
            knn_recs = self.get_knn_recommendations(user_input, num_recommendations * 2, **kwargs)
            content_recs = self.get_content_based_recommendations(user_input, user_preferences, num_recommendations * 2)

            collaborative_recs = []
            if user_id:
                collaborative_recs = self.get_collaborative_recommendations(user_id, num_recommendations * 2)

            popularity_recs = self.get_popularity_based_recommendations(num_recommendations * 2)

            # Create a unified scoring system
            recipe_scores = defaultdict(lambda: {
                'recipe': None,
                'knn_score': 0.0,
                'content_score': 0.0,
                'collaborative_score': 0.0,
                'popularity_score': 0.0,
                'final_score': 0.0,
                'sources': []
            })

            # Process KNN recommendations
            for i, recipe in enumerate(knn_recs):
                recipe_id = recipe['id']
                # Normalize score based on position (higher position = lower score)
                normalized_score = max(0, 1.0 - (i / len(knn_recs)))
                recipe_scores[recipe_id]['recipe'] = recipe
                recipe_scores[recipe_id]['knn_score'] = normalized_score
                recipe_scores[recipe_id]['sources'].append('KNN')

            # Process content-based recommendations
            for i, recipe in enumerate(content_recs):
                recipe_id = recipe['id']
                normalized_score = max(0, 1.0 - (i / len(content_recs)))
                if recipe_scores[recipe_id]['recipe'] is None:
                    recipe_scores[recipe_id]['recipe'] = recipe
                recipe_scores[recipe_id]['content_score'] = normalized_score
                if 'Content-Based' not in recipe_scores[recipe_id]['sources']:
                    recipe_scores[recipe_id]['sources'].append('Content-Based')

            # Process collaborative recommendations
            for i, recipe in enumerate(collaborative_recs):
                recipe_id = recipe['id']
                normalized_score = max(0, 1.0 - (i / len(collaborative_recs)))
                if recipe_scores[recipe_id]['recipe'] is None:
                    recipe_scores[recipe_id]['recipe'] = recipe
                recipe_scores[recipe_id]['collaborative_score'] = normalized_score
                if 'Collaborative' not in recipe_scores[recipe_id]['sources']:
                    recipe_scores[recipe_id]['sources'].append('Collaborative')

            # Process popularity recommendations
            for i, recipe in enumerate(popularity_recs):
                recipe_id = recipe['id']
                normalized_score = max(0, 1.0 - (i / len(popularity_recs)))
                if recipe_scores[recipe_id]['recipe'] is None:
                    recipe_scores[recipe_id]['recipe'] = recipe
                recipe_scores[recipe_id]['popularity_score'] = normalized_score
                if 'Popularity' not in recipe_scores[recipe_id]['sources']:
                    recipe_scores[recipe_id]['sources'].append('Popularity')

            # Calculate final hybrid scores
            for recipe_id, scores in recipe_scores.items():
                final_score = (
                    scores['knn_score'] * self.knn_weight +
                    scores['content_score'] * self.content_weight +
                    scores['collaborative_score'] * self.collaborative_weight +
                    scores['popularity_score'] * self.popularity_weight
                )
                scores['final_score'] = final_score

            # Sort by final score and get top recommendations
            sorted_recipes = sorted(
                recipe_scores.items(),
                key=lambda x: x[1]['final_score'],
                reverse=True
            )

            # Prepare final recommendations
            final_recommendations = []
            for recipe_id, scores in sorted_recipes[:num_recommendations]:
                if scores['recipe'] is None:
                    continue

                recipe = scores['recipe'].copy()
                recipe['hybrid_score'] = scores['final_score']

                if explanation:
                    recipe['recommendation_explanation'] = {
                        'sources': scores['sources'],
                        'knn_score': scores['knn_score'],
                        'content_score': scores['content_score'],
                        'collaborative_score': scores['collaborative_score'],
                        'popularity_score': scores['popularity_score'],
                        'weights': {
                            'knn': self.knn_weight,
                            'content': self.content_weight,
                            'collaborative': self.collaborative_weight,
                            'popularity': self.popularity_weight
                        }
                    }

                final_recommendations.append(recipe)

            # Cache results
            if len(self.recommendation_cache) < self.max_cache_size:
                self.recommendation_cache[cache_key] = final_recommendations

            print(f"Generated {len(final_recommendations)} hybrid recommendations")
            return final_recommendations

        except Exception as e:
            print(f"Error in hybrid recommendations: {e}")
            # Fallback to KNN only
            return self.get_knn_recommendations(user_input, num_recommendations, **kwargs)

    def update_user_preference(self, user_id, recipe_id, rating):
        """
        Update user preferences based on new rating.

        Parameters:
        -----------
        user_id : str
            User ID
        recipe_id : str
            Recipe ID
        rating : int
            User rating (1-5)
        """
        self.user_ratings[user_id][recipe_id] = rating

        # Update recipe popularity and average rating
        recipe_ratings = []
        for user_ratings in self.user_ratings.values():
            if recipe_id in user_ratings:
                recipe_ratings.append(user_ratings[recipe_id])

        if recipe_ratings:
            avg_rating = np.mean(recipe_ratings)
            review_count = len(recipe_ratings)
            popularity = (avg_rating / 5.0) * min(1.0, review_count / 10.0)

            self.recipe_avg_ratings[recipe_id] = avg_rating
            self.recipe_popularity_scores[recipe_id] = popularity

        # Clear cache to ensure fresh recommendations
        self.recommendation_cache.clear()

    def get_recipe_by_id(self, recipe_id):
        """Get a recipe by its ID."""
        for recipe in self.recipes:
            if str(recipe['id']) == str(recipe_id):
                return recipe
        return None

    @property
    def ingredient_names(self):
        """Get all available ingredient names."""
        return self.knn_recommender.ingredient_names
