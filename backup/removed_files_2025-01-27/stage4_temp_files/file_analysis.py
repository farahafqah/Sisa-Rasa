#!/usr/bin/env python3
"""
File Usage Analysis for Sisa Rasa Project Cleanup
"""

import os
import re
import json
from pathlib import Path

def analyze_file_usage():
    """Analyze which files are actually used in the project."""
    
    # Define the project structure
    project_files = {
        'core_app_files': [
            'src/api/app.py',
            'src/api/routes.py', 
            'src/api/auth.py',
            'src/api/config.py',
            'src/api/decorators.py',
            'src/run_api.py'
        ],
        'model_files': [
            'src/api/models/__init__.py',
            'src/api/models/user.py',
            'src/api/models/community.py',
            'src/api/models/recipe.py'
        ],
        'recommender_files': [
            'src/hybrid_recipe_recommender.py',
            'src/clean_recipe_recommender.py'
        ],
        'template_files': [
            'src/api/templates/welcome.html',
            'src/api/templates/login.html',
            'src/api/templates/signup.html',
            'src/api/templates/dashboard.html',
            'src/api/templates/profile.html',
            'src/api/templates/search-results.html',
            'src/api/templates/save-recipe.html'
        ],
        'static_files': [
            'src/api/static/main.js',
            'src/api/static/css/',
            'src/api/static/images/'
        ],
        'data_files': [
            'data/clean_recipes.json',
            'data/clean_recipes.csv',
            'ingr_map.pkl'
        ],
        'config_files': [
            '.env',
            'requirements.txt'
        ],
        'test_files': [
            'test_community_features.py',
            'diagnose_rating_issue.py',
            'src/test_enhanced_knn.py',
            'src/test_hybrid_recommender.py'
        ],
        'standalone_scripts': [
            'src/main_clean.py',
            'src/download_clean_dataset.py',
            'src/download_epicurious_dataset.py'
        ],
        'potentially_unused_templates': [
            'src/api/templates/api_docs.html',
            'src/api/templates/check_auth.html',
            'src/api/templates/test-api.html',
            'src/api/templates/test-redirect.html',
            'src/api/templates/test.html'
        ]
    }
    
    # Files that are definitely used (core functionality)
    essential_files = (
        project_files['core_app_files'] + 
        project_files['model_files'] + 
        project_files['recommender_files'] + 
        project_files['template_files'] + 
        project_files['static_files'] + 
        project_files['data_files'] + 
        project_files['config_files']
    )
    
    # Files that might be unused or redundant
    potentially_unused = (
        project_files['potentially_unused_templates'] +
        project_files['standalone_scripts'] +
        project_files['test_files']
    )
    
    return {
        'essential': essential_files,
        'potentially_unused': potentially_unused,
        'all_categories': project_files
    }

if __name__ == "__main__":
    analysis = analyze_file_usage()
    
    print("=== SISA RASA PROJECT FILE ANALYSIS ===")
    print()
    
    print("ESSENTIAL FILES (KEEP):")
    for file in analysis['essential']:
        print(f"  ✓ {file}")
    
    print()
    print("POTENTIALLY UNUSED FILES (REVIEW):")
    for file in analysis['potentially_unused']:
        print(f"  ? {file}")
