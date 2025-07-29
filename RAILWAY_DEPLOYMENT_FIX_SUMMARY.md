# Railway Deployment Fix Summary

## Problem
The Railway deployment was failing during the healthcheck phase with "service unavailable" errors. The build was successful, but the application wasn't starting properly.

## Root Cause Analysis
The main issues identified were:

1. **Incorrect Procfile Configuration**: The Procfile was trying to run `gunicorn run_api:app`, but the `app` object wasn't directly exposed in `run_api.py`.

2. **Missing Recommender Initialization**: When using gunicorn, the `initialize_recommender()` function from `run_api.py` was never called because gunicorn imports the module directly.

3. **Lack of Railway-Specific Health Checks**: No proper health check endpoints for Railway's deployment verification.

4. **Missing Environment Variable Debugging**: Limited visibility into Railway environment configuration.

## Fixes Implemented

### 1. Fixed Procfile Configuration
**File**: `Procfile`
```bash
# Before
web: cd src && gunicorn run_api:app --host 0.0.0.0 --port $PORT

# After  
web: cd src && gunicorn api.app:app --host 0.0.0.0 --port $PORT
```

### 2. Added Railway-Specific Recommender Initialization
**File**: `src/api/app.py`
```python
# Initialize recommender for production deployment (Railway/gunicorn)
# This ensures the recommender is initialized when the module is imported
if not recommender and os.environ.get('PORT'):  # Railway sets PORT environment variable
    print("🚂 Railway deployment detected - initializing recommender...")
    try:
        max_recipes = int(os.environ.get('MAX_RECIPES', 5000))
        num_recipes = int(os.environ.get('NUM_RECIPES', 10))
        
        print(f"Initializing with {max_recipes} max recipes, {num_recipes} recommendations")
        success = initialize_recommender(num_recipes=num_recipes, max_recipes=max_recipes)
        
        if not success:
            print("❌ Failed to initialize recommender for Railway deployment")
            print("⚠️ App will continue without recommender - some features may be limited")
        else:
            print("✅ Recommender initialized successfully for Railway deployment")
    except Exception as e:
        print(f"❌ Error during Railway recommender initialization: {e}")
        print("⚠️ App will continue without recommender - some features may be limited")
```

### 3. Enhanced Health Check Endpoints
**File**: `src/api/app.py`
```python
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify app and database status."""
    # ... existing health check code ...
    
    # Check environment variables for Railway debugging
    env_info = {
        'PORT': os.environ.get('PORT', 'Not set'),
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'Not set'),
        'MONGO_URI_SET': '✅' if os.environ.get('MONGO_URI') else '❌',
        'MAX_RECIPES': os.environ.get('MAX_RECIPES', 'Not set'),
        'NUM_RECIPES': os.environ.get('NUM_RECIPES', 'Not set')
    }
    
    return jsonify({
        'status': 'success',
        'app': '✅ running',
        'database': db_status,
        'recommender': '✅ loaded' if recommender else '❌ not loaded',
        'environment': env_info,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/', methods=['GET'])
def root_health_check():
    """Root endpoint for Railway health checks."""
    return jsonify({
        'status': 'success',
        'message': 'Sisa Rasa API is running',
        'health_endpoint': '/api/health'
    })
```

### 4. Improved Data File Path Resolution
**File**: `src/api/app.py`
```python
# Define paths
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
clean_recipes_path = os.path.join(base_dir, 'data', 'clean_recipes.json')

print(f"🔍 DEBUG: Base directory: {base_dir}")
print(f"🔍 DEBUG: Looking for recipes at: {clean_recipes_path}")
print(f"🔍 DEBUG: Current working directory: {os.getcwd()}")
print(f"🔍 DEBUG: File exists: {os.path.exists(clean_recipes_path)}")

# Check if clean recipes file exists
if not os.path.exists(clean_recipes_path):
    print(f"❌ Error: Clean recipes dataset not found at {clean_recipes_path}")
    
    # Try alternative paths for Railway deployment
    alternative_paths = [
        os.path.join(os.getcwd(), 'data', 'clean_recipes.json'),
        os.path.join(os.path.dirname(os.getcwd()), 'data', 'clean_recipes.json'),
        './data/clean_recipes.json',
        '../data/clean_recipes.json'
    ]
    
    for alt_path in alternative_paths:
        print(f"🔍 Trying alternative path: {alt_path}")
        if os.path.exists(alt_path):
            print(f"✅ Found recipes at alternative path: {alt_path}")
            clean_recipes_path = alt_path
            break
    else:
        print("❌ Could not find clean_recipes.json in any expected location")
        return False
```

### 5. Created Railway Deployment Test Script
**File**: `test_railway_deployment.py`
- Comprehensive test that simulates Railway environment
- Verifies all required files exist
- Tests app initialization with Railway environment variables
- Validates health endpoints
- Checks requirements.txt completeness

## Test Results

### Railway Deployment Readiness Test: ✅ PASSED
```
🚂 Railway Deployment Readiness Test
==================================================

1. Checking required files...
✅ Procfile
✅ requirements.txt  
✅ src/api/app.py
✅ src/run_api.py
✅ data/clean_recipes.json

2. Checking Procfile...
✅ Procfile correct: web: cd src && gunicorn api.app:app --host 0.0.0.0 --port $PORT

3. Checking data file...
✅ Recipes data loaded: 13487 recipes

4. Testing app import with Railway environment...
✅ App imported successfully
✅ Recommender initialized
✅ Health endpoint working: success
✅ App component healthy
✅ Database component healthy
✅ Recommender component healthy
✅ Root endpoint working

5. Checking requirements.txt...
✅ All required packages present

🎉 Railway deployment readiness test PASSED!
```

## Key Improvements

1. **Proper Gunicorn Integration**: Fixed Procfile to correctly reference the Flask app object
2. **Automatic Railway Detection**: App automatically detects Railway environment and initializes appropriately
3. **Robust Error Handling**: Graceful degradation if components fail to initialize
4. **Enhanced Debugging**: Comprehensive logging and environment variable reporting
5. **Multiple Health Endpoints**: Both root (`/`) and detailed (`/api/health`) health checks
6. **Path Resolution**: Flexible data file path resolution for different deployment environments

## Deployment Instructions

1. **Set Environment Variables in Railway**:
   - `MONGO_URI`: Your MongoDB connection string
   - `MAX_RECIPES`: Maximum recipes to load (optional, default: 5000)
   - `NUM_RECIPES`: Number of recommendations (optional, default: 10)

2. **Deploy to Railway**: The app will automatically detect Railway environment and initialize properly

3. **Verify Deployment**: 
   - Check Railway logs for initialization messages
   - Test health endpoints: `https://your-app.railway.app/` and `https://your-app.railway.app/api/health`
   - Verify analytics endpoint: `https://your-app.railway.app/api/analytics/leftover-ingredients`

## Expected Railway Behavior

With these fixes, the Railway deployment should:
- ✅ Start successfully without healthcheck failures
- ✅ Initialize the recommender system automatically
- ✅ Connect to MongoDB properly
- ✅ Serve all API endpoints correctly
- ✅ Provide detailed health status information
- ✅ Handle errors gracefully with meaningful messages

The analytics functionality that was previously failing should now work correctly in the Railway environment.
