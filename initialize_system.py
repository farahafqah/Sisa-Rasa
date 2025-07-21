#!/usr/bin/env python3
"""
System Initialization Script for SisaRasa

This script initializes the full ML system after Railway deployment is healthy.
Run this after your Railway app is deployed and health checks are passing.
"""

import requests
import time
import sys

def initialize_deployed_system(app_url):
    """Initialize the full system on the deployed Railway app."""
    
    print(f"🚀 Initializing SisaRasa system at {app_url}")
    
    # First, check if the app is healthy
    try:
        health_response = requests.get(f"{app_url}/health", timeout=10)
        if health_response.status_code != 200:
            print(f"❌ App not healthy: {health_response.status_code}")
            return False
        print("✅ App is healthy, proceeding with initialization...")
    except Exception as e:
        print(f"❌ Failed to check app health: {e}")
        return False
    
    # Initialize the full system
    try:
        print("🔄 Initializing full ML system...")
        init_response = requests.post(f"{app_url}/api/initialize", timeout=300)
        
        if init_response.status_code == 200:
            result = init_response.json()
            print(f"✅ System initialized: {result.get('message', 'Success')}")
            return True
        else:
            print(f"❌ Initialization failed: {init_response.status_code}")
            print(f"Response: {init_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python initialize_system.py <your-railway-app-url>")
        print("Example: python initialize_system.py https://sisa-rasa-production.up.railway.app")
        sys.exit(1)

    app_url = sys.argv[1].rstrip('/')

    print("🎯 SisaRasa Full System Initialization")
    print("=" * 60)

    success = initialize_deployed_system(app_url)

    if success:
        print("\n🎉 Full system initialization completed successfully!")
        print(f"🌐 Your SisaRasa web app is now fully functional!")
        print("=" * 60)
        print("📱 Available Pages:")
        print(f"   • {app_url}/welcome - Welcome page")
        print(f"   • {app_url}/login - User login")
        print(f"   • {app_url}/signup - User registration")
        print(f"   • {app_url}/dashboard - Recipe recommendations")
        print(f"   • {app_url}/profile - User profile")
        print(f"   • {app_url}/community-recipes - Community features")
        print(f"   • {app_url}/share-recipe - Share recipes")
        print("=" * 60)
        print("🔧 API Endpoints:")
        print(f"   • {app_url}/api/health - System health")
        print(f"   • {app_url}/api/status - System status")
        print("=" * 60)
        print("✅ Your complete recipe recommendation system is ready!")
    else:
        print("\n❌ System initialization failed!")
        print("The web interface is still available, but some features may be limited.")
        print("Please check the Railway logs for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
