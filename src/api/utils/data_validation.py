"""
Data Validation Utilities for Recipe System

This module provides validation functions to ensure data integrity
and consistency across the recipe recommendation system.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class RecipeDataValidator:
    """Validates recipe data integrity and consistency."""
    
    def __init__(self, mongo_db=None, recommender=None):
        """
        Initialize the validator with database and recommender instances.
        
        Args:
            mongo_db: MongoDB database instance
            recommender: Recipe recommender instance
        """
        self.mongo_db = mongo_db
        self.recommender = recommender
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_recipe_data_integrity(self) -> Dict[str, Any]:
        """
        Comprehensive validation of recipe data integrity.
        
        Returns:
            Dict containing validation results and statistics
        """
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'errors': [],
            'warnings': [],
            'statistics': {},
            'recommendations': []
        }
        
        try:
            # Validate recipe ID consistency
            id_validation = self._validate_recipe_ids()
            results['statistics']['id_validation'] = id_validation
            
            # Validate review data consistency
            review_validation = self._validate_review_data()
            results['statistics']['review_validation'] = review_validation
            
            # Validate verification data consistency
            verification_validation = self._validate_verification_data()
            results['statistics']['verification_validation'] = verification_validation
            
            # Validate recommender system consistency
            recommender_validation = self._validate_recommender_consistency()
            results['statistics']['recommender_validation'] = recommender_validation
            
            # Compile all errors and warnings
            results['errors'] = self.validation_errors
            results['warnings'] = self.validation_warnings
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations()
            
        except Exception as e:
            logger.error(f"Error during data validation: {e}")
            results['errors'].append(f"Validation process failed: {str(e)}")
        
        return results
    
    def _validate_recipe_ids(self) -> Dict[str, Any]:
        """Validate recipe ID consistency across systems."""
        stats = {
            'total_recipes_in_recommender': 0,
            'total_reviews_in_db': 0,
            'total_verifications_in_db': 0,
            'orphaned_reviews': 0,
            'orphaned_verifications': 0,
            'id_format_issues': []
        }
        
        try:
            # Get recipe IDs from recommender
            recommender_ids = set()
            if self.recommender and hasattr(self.recommender, 'recipes'):
                stats['total_recipes_in_recommender'] = len(self.recommender.recipes)
                for recipe in self.recommender.recipes:
                    recipe_id = str(recipe.get('id', ''))
                    if recipe_id:
                        recommender_ids.add(recipe_id)
            
            # Check reviews for orphaned recipe IDs
            if self.mongo_db:
                try:
                    reviews = list(self.mongo_db.recipe_reviews.find({}, {'recipe_id': 1}))
                    stats['total_reviews_in_db'] = len(reviews)
                    
                    for review in reviews:
                        recipe_id = str(review.get('recipe_id', ''))
                        if recipe_id and recipe_id not in recommender_ids:
                            stats['orphaned_reviews'] += 1
                            if stats['orphaned_reviews'] <= 5:  # Log first 5 examples
                                self.validation_warnings.append(f"Review found for non-existent recipe: {recipe_id}")
                
                except Exception as e:
                    self.validation_errors.append(f"Error validating review IDs: {str(e)}")
                
                # Check verifications for orphaned recipe IDs
                try:
                    verifications = list(self.mongo_db.recipe_verifications.find({}, {'recipe_id': 1}))
                    stats['total_verifications_in_db'] = len(verifications)
                    
                    for verification in verifications:
                        recipe_id = str(verification.get('recipe_id', ''))
                        if recipe_id and recipe_id not in recommender_ids:
                            stats['orphaned_verifications'] += 1
                            if stats['orphaned_verifications'] <= 5:  # Log first 5 examples
                                self.validation_warnings.append(f"Verification found for non-existent recipe: {recipe_id}")
                
                except Exception as e:
                    self.validation_errors.append(f"Error validating verification IDs: {str(e)}")
        
        except Exception as e:
            self.validation_errors.append(f"Error in recipe ID validation: {str(e)}")
        
        return stats
    
    def _validate_review_data(self) -> Dict[str, Any]:
        """Validate review data consistency."""
        stats = {
            'total_reviews': 0,
            'invalid_ratings': 0,
            'missing_user_ids': 0,
            'missing_recipe_ids': 0,
            'duplicate_reviews': 0
        }
        
        if not self.mongo_db:
            return stats
        
        try:
            reviews = list(self.mongo_db.recipe_reviews.find())
            stats['total_reviews'] = len(reviews)
            
            seen_combinations = set()
            
            for review in reviews:
                # Check rating validity
                rating = review.get('rating')
                if rating is None or not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
                    stats['invalid_ratings'] += 1
                    if stats['invalid_ratings'] <= 3:
                        self.validation_errors.append(f"Invalid rating found: {rating} in review {review.get('_id')}")
                
                # Check for missing user IDs
                user_id = review.get('user_id')
                if not user_id:
                    stats['missing_user_ids'] += 1
                
                # Check for missing recipe IDs
                recipe_id = review.get('recipe_id')
                if not recipe_id:
                    stats['missing_recipe_ids'] += 1
                
                # Check for duplicate reviews (same user, same recipe)
                if user_id and recipe_id:
                    combination = (str(user_id), str(recipe_id))
                    if combination in seen_combinations:
                        stats['duplicate_reviews'] += 1
                        if stats['duplicate_reviews'] <= 3:
                            self.validation_warnings.append(f"Duplicate review found: user {user_id}, recipe {recipe_id}")
                    else:
                        seen_combinations.add(combination)
        
        except Exception as e:
            self.validation_errors.append(f"Error validating review data: {str(e)}")
        
        return stats
    
    def _validate_verification_data(self) -> Dict[str, Any]:
        """Validate verification data consistency."""
        stats = {
            'total_verifications': 0,
            'missing_user_ids': 0,
            'missing_recipe_ids': 0,
            'duplicate_verifications': 0
        }
        
        if not self.mongo_db:
            return stats
        
        try:
            verifications = list(self.mongo_db.recipe_verifications.find())
            stats['total_verifications'] = len(verifications)
            
            seen_combinations = set()
            
            for verification in verifications:
                # Check for missing user IDs
                user_id = verification.get('user_id')
                if not user_id:
                    stats['missing_user_ids'] += 1
                
                # Check for missing recipe IDs
                recipe_id = verification.get('recipe_id')
                if not recipe_id:
                    stats['missing_recipe_ids'] += 1
                
                # Check for duplicate verifications (same user, same recipe)
                if user_id and recipe_id:
                    combination = (str(user_id), str(recipe_id))
                    if combination in seen_combinations:
                        stats['duplicate_verifications'] += 1
                        if stats['duplicate_verifications'] <= 3:
                            self.validation_warnings.append(f"Duplicate verification found: user {user_id}, recipe {recipe_id}")
                    else:
                        seen_combinations.add(combination)
        
        except Exception as e:
            self.validation_errors.append(f"Error validating verification data: {str(e)}")
        
        return stats
    
    def _validate_recommender_consistency(self) -> Dict[str, Any]:
        """Validate recommender system consistency."""
        stats = {
            'recommender_loaded': False,
            'total_recipes': 0,
            'recipes_with_ingredients': 0,
            'recipes_with_names': 0,
            'cache_status': 'unknown'
        }
        
        try:
            if self.recommender:
                stats['recommender_loaded'] = True
                
                if hasattr(self.recommender, 'recipes') and self.recommender.recipes:
                    stats['total_recipes'] = len(self.recommender.recipes)
                    
                    for recipe in self.recommender.recipes:
                        if recipe.get('name'):
                            stats['recipes_with_names'] += 1
                        if recipe.get('ingredients'):
                            stats['recipes_with_ingredients'] += 1
                
                # Check cache status
                if hasattr(self.recommender, 'knn_recommender'):
                    if hasattr(self.recommender.knn_recommender, 'ingredient_names'):
                        stats['cache_status'] = 'loaded'
                    else:
                        stats['cache_status'] = 'not_loaded'
            else:
                self.validation_errors.append("Recommender system not loaded")
        
        except Exception as e:
            self.validation_errors.append(f"Error validating recommender consistency: {str(e)}")
        
        return stats
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if len(self.validation_errors) > 0:
            recommendations.append("Critical errors found - immediate attention required")
        
        if len(self.validation_warnings) > 10:
            recommendations.append("High number of warnings - consider data cleanup")
        
        if not self.recommender:
            recommendations.append("Recommender system not loaded - initialize recommender")
        
        return recommendations

def create_debug_report(mongo_db=None, recommender=None) -> Dict[str, Any]:
    """
    Create a comprehensive debug report for the recipe system.
    
    Args:
        mongo_db: MongoDB database instance
        recommender: Recipe recommender instance
    
    Returns:
        Dict containing debug information
    """
    validator = RecipeDataValidator(mongo_db, recommender)
    return validator.validate_recipe_data_integrity()
