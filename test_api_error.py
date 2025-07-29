#!/usr/bin/env python3
"""
Test script to get detailed error information from the API.
"""

import requests
import json

def test_prescriptive_api():
    """Test the prescriptive analytics API and get detailed error info."""
    
    print("🧪 Testing Prescriptive Analytics API")
    print("=" * 50)
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/analytics/prescriptive', timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('status', 'unknown')}")
            popular_recipes = data.get('data', {}).get('popular_recipes', [])
            print(f"📊 Popular recipes found: {len(popular_recipes)}")
        else:
            try:
                data = response.json()
                print(f"❌ Error: {data.get('message', 'No message')}")
                
                if 'traceback' in data:
                    print("\n🔍 Full Traceback:")
                    print("=" * 50)
                    print(data['traceback'])
                    
            except json.JSONDecodeError:
                print(f"❌ Response is not valid JSON")
                print(f"📄 Response text: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    test_prescriptive_api()
