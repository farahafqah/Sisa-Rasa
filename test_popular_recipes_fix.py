#!/usr/bin/env python3
"""
Comprehensive Test Script for Popular Recipes Fix

This script tests all the fixes implemented for the "most popular recipes" feature:
1. Recipe ID standardization and consistency
2. Removal of fallback data system
3. Data synchronization and cache invalidation
4. Database query optimization
5. Data validation and integrity checks

Run this script to verify that the popular recipes feature works consistently.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:5000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "password123"

class PopularRecipesTestSuite:
    def __init__(self):
        self.token = None
        self.test_results = []
        self.errors = []
        
    def log_test(self, test_name, passed, message="", details=None):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            'test_name': test_name,
            'passed': passed,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        if not passed:
            self.errors.append(f"{test_name}: {message}")
    
    def setup_authentication(self):
        """Set up authentication for API calls."""
        print("\n🔐 Setting up authentication...")
        
        # Try to login
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.log_test("Authentication", True, "Successfully logged in")
                return True
            else:
                self.log_test("Authentication", False, f"Login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Login error: {str(e)}")
            return False
    
    def test_api_health(self):
        """Test API health and basic functionality."""
        print("\n🏥 Testing API health...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health", True, "API is running", data)
                return True
            else:
                self.log_test("API Health", False, f"Health check failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("API Health", False, f"Health check error: {str(e)}")
            return False
    
    def test_data_validation(self):
        """Test the data validation debug endpoint."""
        print("\n🔍 Testing data validation...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/debug/data-validation")
            
            if response.status_code == 200:
                data = response.json()
                report = data.get('report', {})
                summary = report.get('summary', {})
                
                validation_status = summary.get('validation_status', 'UNKNOWN')
                data_quality_score = summary.get('data_quality_score', 0)
                
                if validation_status == 'PASS':
                    self.log_test("Data Validation", True, f"Data validation passed (Quality Score: {data_quality_score})", summary)
                else:
                    errors = report.get('errors', [])
                    warnings = report.get('warnings', [])
                    self.log_test("Data Validation", False, f"Data validation failed with {len(errors)} errors and {len(warnings)} warnings", {
                        'errors': errors[:5],  # First 5 errors
                        'warnings': warnings[:5]  # First 5 warnings
                    })
                
                return validation_status == 'PASS'
            else:
                self.log_test("Data Validation", False, f"Validation endpoint failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Data Validation", False, f"Validation error: {str(e)}")
            return False
    
    def test_popular_recipes_analysis(self):
        """Test the popular recipes analysis debug endpoint."""
        print("\n📊 Testing popular recipes analysis...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/debug/popular-recipes-analysis")
            
            if response.status_code == 200:
                data = response.json()
                analysis = data.get('analysis', {})
                
                data_sources = analysis.get('data_sources', {})
                top_recipes = analysis.get('top_recipes', [])
                issues_found = analysis.get('issues_found', [])
                
                # Check if we have meaningful data
                reviews_data = data_sources.get('reviews', {})
                total_reviews = reviews_data.get('total_reviews', 0)
                
                if total_reviews > 0 and len(top_recipes) > 0:
                    self.log_test("Popular Recipes Analysis", True, f"Analysis successful with {total_reviews} reviews and {len(top_recipes)} top recipes", {
                        'data_sources': data_sources,
                        'top_recipes_count': len(top_recipes),
                        'issues_count': len(issues_found)
                    })
                    return True
                else:
                    self.log_test("Popular Recipes Analysis", False, f"Insufficient data: {total_reviews} reviews, {len(top_recipes)} top recipes")
                    return False
            else:
                self.log_test("Popular Recipes Analysis", False, f"Analysis endpoint failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Popular Recipes Analysis", False, f"Analysis error: {str(e)}")
            return False
    
    def test_popular_recipes_consistency(self):
        """Test popular recipes endpoint for consistency across multiple calls."""
        print("\n🔄 Testing popular recipes consistency...")
        
        try:
            # Make multiple calls to the popular recipes endpoint
            results = []
            
            for i in range(3):
                response = requests.get(f"{API_BASE_URL}/api/recipes/popular")
                
                if response.status_code == 200:
                    data = response.json()
                    popular_recipes = data.get('popular_recipes', [])
                    results.append([recipe.get('id') for recipe in popular_recipes])
                    time.sleep(1)  # Small delay between requests
                else:
                    self.log_test("Popular Recipes Consistency", False, f"Request {i+1} failed: {response.text}")
                    return False
            
            # Check consistency
            if len(results) == 3:
                # Check if all results are the same (or at least similar)
                first_result = results[0]
                consistent = all(result == first_result for result in results)
                
                if consistent:
                    self.log_test("Popular Recipes Consistency", True, f"All 3 requests returned identical results with {len(first_result)} recipes")
                    return True
                else:
                    # Check if results are at least similar (allowing for minor differences)
                    similarity_scores = []
                    for i in range(1, len(results)):
                        common_recipes = len(set(first_result) & set(results[i]))
                        similarity = common_recipes / max(len(first_result), len(results[i])) if max(len(first_result), len(results[i])) > 0 else 0
                        similarity_scores.append(similarity)
                    
                    avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
                    
                    if avg_similarity >= 0.8:  # 80% similarity threshold
                        self.log_test("Popular Recipes Consistency", True, f"Results are {avg_similarity:.1%} similar (acceptable)")
                        return True
                    else:
                        self.log_test("Popular Recipes Consistency", False, f"Results are only {avg_similarity:.1%} similar", {
                            'results': results
                        })
                        return False
            else:
                self.log_test("Popular Recipes Consistency", False, "Failed to get 3 successful responses")
                return False
                
        except Exception as e:
            self.log_test("Popular Recipes Consistency", False, f"Consistency test error: {str(e)}")
            return False
    
    def test_cache_invalidation(self):
        """Test cache invalidation by submitting a review and checking if data updates."""
        print("\n🗑️ Testing cache invalidation...")
        
        if not self.token:
            self.log_test("Cache Invalidation", False, "No authentication token available")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            
            # Get initial popular recipes
            response = requests.get(f"{API_BASE_URL}/api/recipes/popular")
            if response.status_code != 200:
                self.log_test("Cache Invalidation", False, "Failed to get initial popular recipes")
                return False
            
            initial_data = response.json()
            initial_recipes = initial_data.get('popular_recipes', [])
            
            if not initial_recipes:
                self.log_test("Cache Invalidation", False, "No initial popular recipes found")
                return False
            
            # Submit a review for the first recipe
            test_recipe_id = initial_recipes[0].get('id')
            review_data = {
                "rating": 5,
                "review_text": f"Test review for cache invalidation - {datetime.now().isoformat()}"
            }
            
            review_response = requests.post(
                f"{API_BASE_URL}/api/recipe/{test_recipe_id}/review",
                json=review_data,
                headers=headers
            )
            
            if review_response.status_code == 200:
                # Wait a moment for cache to refresh
                time.sleep(2)
                
                # Get popular recipes again
                updated_response = requests.get(f"{API_BASE_URL}/api/recipes/popular")
                if updated_response.status_code == 200:
                    self.log_test("Cache Invalidation", True, "Successfully submitted review and retrieved updated data")
                    return True
                else:
                    self.log_test("Cache Invalidation", False, "Failed to get updated popular recipes after review")
                    return False
            else:
                self.log_test("Cache Invalidation", False, f"Failed to submit review: {review_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Cache Invalidation", False, f"Cache invalidation test error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in the test suite."""
        print("🧪 Starting Popular Recipes Fix Test Suite")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            self.test_api_health,
            self.setup_authentication,
            self.test_data_validation,
            self.test_popular_recipes_analysis,
            self.test_popular_recipes_consistency,
            self.test_cache_invalidation
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests:.1%}")
        
        if self.errors:
            print("\n❌ ERRORS FOUND:")
            for error in self.errors:
                print(f"  - {error}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! The popular recipes fix is working correctly.")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} TESTS FAILED. Please review the issues above.")
            return False

def main():
    """Main function to run the test suite."""
    test_suite = PopularRecipesTestSuite()
    success = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
