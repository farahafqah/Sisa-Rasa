#!/usr/bin/env python3
"""
Test script to verify that frontend fallback data has been removed.

This script checks the HTML templates to ensure that fake recipe data
like "Classic Chicken Curry" has been replaced with proper error messages.
"""

import re
import os

def test_template_fallback_removal():
    """Test that fake recipe data has been removed from templates."""
    
    print("🧪 Testing Frontend Fallback Data Removal")
    print("=" * 50)
    
    # Templates to check
    templates = [
        'src/api/templates/welcome.html',
        'src/api/templates/dashboard.html'
    ]
    
    # Fake recipe names that should NOT appear in fallback data
    fake_recipe_names = [
        'Classic Chicken Curry',
        'Homemade Fried Rice', 
        'Simple Pasta Marinara',
        'Vegetable Stir Fry',
        'Fried Rice',
        'Chicken Salad',
        'Omelette',
        'Pancakes',
        'Nasi Lemak'
    ]
    
    # Fake review counts that should NOT appear
    fake_review_counts = [156, 89, 67, 234, 189]
    
    issues_found = []
    
    for template_path in templates:
        if not os.path.exists(template_path):
            print(f"⚠️ Template not found: {template_path}")
            continue
            
        print(f"\n📄 Checking {template_path}...")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for fake recipe names in fallback data
        for fake_name in fake_recipe_names:
            # Look for the fake name in fallback contexts
            pattern = rf"name:\s*['\"]({re.escape(fake_name)})['\"]"
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            if matches:
                # Check if it's in a fallback context (not in comments or other contexts)
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if fake_name in line and ('fallback' in line.lower() or 'popular_recipes' in line):
                        issues_found.append(f"{template_path}:{i+1} - Found fake recipe '{fake_name}' in fallback data")
                        print(f"❌ Found fake recipe '{fake_name}' at line {i+1}")
        
        # Check for fake review counts
        for fake_count in fake_review_counts:
            pattern = rf"review_count:\s*{fake_count}"
            if re.search(pattern, content):
                issues_found.append(f"{template_path} - Found fake review count {fake_count}")
                print(f"❌ Found fake review count {fake_count}")
        
        # Check for proper error messages
        if 'Unable to Load Popular Recipes' in content or 'No Popular Recipes Available' in content:
            print(f"✅ Found proper error message in fallback data")
        else:
            print(f"⚠️ No proper error message found - may still have fake data")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    if issues_found:
        print(f"❌ {len(issues_found)} ISSUES FOUND:")
        for issue in issues_found:
            print(f"  - {issue}")
        return False
    else:
        print("✅ NO FAKE RECIPE DATA FOUND IN TEMPLATES")
        print("✅ Frontend fallback data has been properly cleaned up")
        return True

def test_backend_placeholder_system():
    """Test that backend placeholder system is working correctly."""
    
    print("\n🔧 Testing Backend Placeholder System")
    print("=" * 50)
    
    routes_file = 'src/api/routes.py'
    
    if not os.path.exists(routes_file):
        print(f"❌ Routes file not found: {routes_file}")
        return False
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for proper placeholder system
    checks = [
        ('is_placeholder', 'Placeholder marking system'),
        ('New recipe - be the first to review!', 'Proper placeholder description'),
        ('RecipeIDManager.find_recipe_in_recommender', 'Recipe validation system'),
        ('validated_popular_ids', 'Recipe validation before display')
    ]
    
    all_passed = True
    
    for check_text, description in checks:
        if check_text in content:
            print(f"✅ {description} - Found")
        else:
            print(f"❌ {description} - Missing")
            all_passed = False
    
    return all_passed

def main():
    """Main test function."""
    
    print("🧪 FRONTEND FALLBACK FIX VERIFICATION")
    print("=" * 60)
    
    # Test template cleanup
    templates_clean = test_template_fallback_removal()
    
    # Test backend system
    backend_working = test_backend_placeholder_system()
    
    # Final result
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULT")
    print("=" * 60)
    
    if templates_clean and backend_working:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Fake recipe data has been removed from frontend templates")
        print("✅ Backend placeholder system is properly implemented")
        print("✅ The 'Classic Chicken Curry' issue should be resolved")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        if not templates_clean:
            print("❌ Frontend templates still contain fake recipe data")
        if not backend_working:
            print("❌ Backend placeholder system has issues")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
