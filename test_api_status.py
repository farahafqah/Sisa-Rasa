#!/usr/bin/env python3
"""
Test script to check the status of the Flask API and recommender system.
"""

import requests
import json

def test_api_endpoints():
    """Test various API endpoints to identify issues."""
    
    print("🧪 Testing API Endpoints")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    endpoints_to_test = [
        ("/api/health", "Health Check"),
        ("/api/analytics/prescriptive", "Prescriptive Analytics"),
        ("/api/recipes/popular", "Popular Recipes"),
        ("/api/ingredients", "Ingredients List")
    ]
    
    for endpoint, description in endpoints_to_test:
        print(f"\n📡 Testing {description}: {endpoint}")
        
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Success: {data.get('status', 'unknown')}")
                    
                    # Show specific data for prescriptive analytics
                    if endpoint == "/api/analytics/prescriptive" and data.get('status') == 'success':
                        popular_recipes = data.get('data', {}).get('popular_recipes', [])
                        print(f"   📊 Popular recipes found: {len(popular_recipes)}")
                        if popular_recipes:
                            print(f"   📝 First recipe: {popular_recipes[0].get('name', 'Unknown')}")
                    
                    # Show specific data for popular recipes
                    elif endpoint == "/api/recipes/popular" and data.get('status') == 'success':
                        recipes = data.get('recipes', [])
                        print(f"   📊 Popular recipes found: {len(recipes)}")
                        if recipes:
                            print(f"   📝 First recipe: {recipes[0].get('name', 'Unknown')}")
                            
                except json.JSONDecodeError:
                    print(f"   ⚠️ Response is not valid JSON")
                    print(f"   📄 Response text: {response.text[:200]}...")
                    
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   💬 Error message: {error_data.get('message', 'No message')}")
                except:
                    print(f"   📄 Response text: {response.text[:200]}...")
                    
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error: Flask server may not be running")
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout: Request took too long")
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
    
    return True

def test_flask_server_running():
    """Check if Flask server is running."""
    
    print("\n🔍 Checking Flask Server Status")
    print("=" * 50)
    
    try:
        response = requests.get("http://127.0.0.1:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is running")
            return True
        else:
            print(f"⚠️ Flask server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Flask server is not running or not accessible")
        print("💡 To start the server, run: python src/api/app.py")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {str(e)}")
        return False

def main():
    """Main test function."""
    
    print("🧪 API STATUS DIAGNOSTIC")
    print("=" * 60)
    
    # Check if server is running
    server_running = test_flask_server_running()
    
    if server_running:
        # Test API endpoints
        test_api_endpoints()
        
        print("\n" + "=" * 60)
        print("📋 DIAGNOSIS SUMMARY")
        print("=" * 60)
        print("✅ Flask server is accessible")
        print("🔍 Check the individual endpoint results above")
        print("💡 If prescriptive analytics is failing, the recommender may not be initialized")
        print("💡 Try restarting the Flask server: python src/api/app.py")
        
    else:
        print("\n" + "=" * 60)
        print("📋 DIAGNOSIS SUMMARY")
        print("=" * 60)
        print("❌ Flask server is not running")
        print("💡 Start the server with: python src/api/app.py")
        print("💡 Make sure you're in the correct directory")
        print("💡 Check if port 5000 is available")

if __name__ == "__main__":
    main()
