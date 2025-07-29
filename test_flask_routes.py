#!/usr/bin/env python3
"""
Test script to check Flask routes registration.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_flask_routes():
    """Test Flask routes registration."""
    
    print("🧪 Testing Flask Routes Registration")
    print("=" * 50)
    
    try:
        # Import Flask app
        from api.app import app
        
        with app.app_context():
            print("✅ Flask app context created")
            
            # List all registered routes
            print("\n📋 Registered Routes:")
            print("-" * 30)
            
            routes_found = []
            for rule in app.url_map.iter_rules():
                route_info = f"{rule.rule} [{', '.join(rule.methods)}]"
                routes_found.append(route_info)
                print(f"  {route_info}")
            
            print(f"\n📊 Total routes found: {len(routes_found)}")
            
            # Check for specific routes we're interested in
            target_routes = [
                '/api/analytics/prescriptive',
                '/api/analytics/prescriptive-test',
                '/api/health'
            ]
            
            print("\n🔍 Checking Target Routes:")
            print("-" * 30)
            
            for target in target_routes:
                found = any(target in route for route in routes_found)
                status = "✅ Found" if found else "❌ Missing"
                print(f"  {target}: {status}")
            
            # Check if the functions exist in the module
            print("\n🔍 Checking Function Definitions:")
            print("-" * 30)
            
            try:
                from api.routes import get_prescriptive_analytics, get_prescriptive_analytics_test
                print("  ✅ get_prescriptive_analytics function found")
                print("  ✅ get_prescriptive_analytics_test function found")
            except ImportError as e:
                print(f"  ❌ Function import error: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    
    print("🧪 FLASK ROUTES DEBUG")
    print("=" * 60)
    
    success = test_flask_routes()
    
    print("\n" + "=" * 60)
    print("📋 DEBUG SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ Flask routes test completed")
        print("💡 Check the route listings above for issues")
    else:
        print("❌ Flask routes test failed")
        print("💡 Check the error messages above")

if __name__ == "__main__":
    main()
