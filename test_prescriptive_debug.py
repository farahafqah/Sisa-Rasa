#!/usr/bin/env python3
"""
Debug script to test the prescriptive analytics function in isolation.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_prescriptive_function():
    """Test the prescriptive analytics function directly."""
    
    print("🧪 Testing Prescriptive Analytics Function")
    print("=" * 50)
    
    try:
        # Import Flask app and create app context
        from api.app import app
        
        with app.app_context():
            print("✅ Flask app context created")
            
            # Check if recommender is available
            from flask import current_app
            recommender = getattr(current_app, 'recommender', None)
            
            if recommender:
                print(f"✅ Recommender found with {len(recommender.recipes) if hasattr(recommender, 'recipes') and recommender.recipes else 0} recipes")
            else:
                print("❌ Recommender not found in current_app")
                return False
            
            # Try to import the function
            try:
                from api.routes import get_prescriptive_analytics
                print("✅ Function imported successfully")
            except ImportError as e:
                print(f"❌ Failed to import function: {e}")
                return False
            
            # Try to call the function
            try:
                result = get_prescriptive_analytics()
                print(f"✅ Function executed successfully")
                print(f"📊 Result type: {type(result)}")
                
                # If it's a Flask response, get the data
                if hasattr(result, 'get_json'):
                    data = result.get_json()
                    print(f"📊 Status: {data.get('status', 'unknown')}")
                    if data.get('status') == 'success':
                        popular_recipes = data.get('data', {}).get('popular_recipes', [])
                        print(f"📊 Popular recipes found: {len(popular_recipes)}")
                    else:
                        print(f"❌ Error in response: {data.get('message', 'No message')}")
                
                return True
                
            except Exception as e:
                print(f"❌ Function execution failed: {str(e)}")
                print(f"❌ Error type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_variable_scope():
    """Test if there are any variable scope issues."""
    
    print("\n🔍 Testing Variable Scope")
    print("=" * 50)
    
    try:
        # Read the routes.py file and check for syntax issues
        with open('src/api/routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to compile the code to check for syntax errors
        try:
            compile(content, 'src/api/routes.py', 'exec')
            print("✅ No syntax errors found in routes.py")
        except SyntaxError as e:
            print(f"❌ Syntax error found: {e}")
            print(f"❌ Line {e.lineno}: {e.text}")
            return False
        
        # Check for 'recommender' variable usage patterns
        lines = content.split('\n')
        recommender_lines = []
        
        for i, line in enumerate(lines, 1):
            if 'recommender' in line and not line.strip().startswith('#'):
                recommender_lines.append((i, line.strip()))
        
        print(f"📊 Found {len(recommender_lines)} lines with 'recommender'")
        
        # Look for the prescriptive analytics function
        in_prescriptive_function = False
        function_start = None
        
        for i, line in enumerate(lines, 1):
            if 'def get_prescriptive_analytics(' in line:
                in_prescriptive_function = True
                function_start = i
                print(f"📍 Function starts at line {i}")
                break
        
        if not in_prescriptive_function:
            print("❌ Could not find get_prescriptive_analytics function")
            return False
        
        # Find where recommender is first defined in the function
        recommender_definition = None
        for i, line in enumerate(lines[function_start:], function_start + 1):
            if 'recommender = getattr(current_app' in line:
                recommender_definition = i
                print(f"📍 Recommender defined at line {i}")
                break
        
        if not recommender_definition:
            print("❌ Could not find recommender definition in function")
            return False
        
        # Check if there are any uses of recommender before its definition
        for line_num, line_content in recommender_lines:
            if function_start < line_num < recommender_definition:
                if 'recommender' in line_content and 'getattr' not in line_content:
                    print(f"⚠️ Potential issue at line {line_num}: {line_content}")
                    print("   This line uses 'recommender' before it's defined")
        
        return True
        
    except Exception as e:
        print(f"❌ Variable scope test failed: {str(e)}")
        return False

def main():
    """Main test function."""
    
    print("🧪 PRESCRIPTIVE ANALYTICS DEBUG")
    print("=" * 60)
    
    # Test variable scope first
    scope_ok = test_variable_scope()
    
    if scope_ok:
        # Test the actual function
        function_ok = test_prescriptive_function()
        
        print("\n" + "=" * 60)
        print("📋 DEBUG SUMMARY")
        print("=" * 60)
        
        if function_ok:
            print("✅ All tests passed!")
            print("✅ The prescriptive analytics function should work")
        else:
            print("❌ Function test failed")
            print("💡 Check the error messages above for details")
    else:
        print("\n" + "=" * 60)
        print("📋 DEBUG SUMMARY")
        print("=" * 60)
        print("❌ Variable scope issues found")
        print("💡 Fix the scope issues before testing the function")

if __name__ == "__main__":
    main()
