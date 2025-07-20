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
        print("Example: python initialize_system.py https://sisarasa-production.up.railway.app")
        sys.exit(1)
    
    app_url = sys.argv[1].rstrip('/')
    
    print("🎯 SisaRasa System Initialization")
    print("=" * 50)
    
    success = initialize_deployed_system(app_url)
    
    if success:
        print("\n🎉 System initialization completed successfully!")
        print(f"Your SisaRasa app is now fully functional at: {app_url}")
        print("\nYou can now test:")
        print(f"- Home page: {app_url}/")
        print(f"- Login page: {app_url}/login")
        print(f"- API health: {app_url}/api/health")
    else:
        print("\n❌ System initialization failed!")
        print("Please check the Railway logs for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
