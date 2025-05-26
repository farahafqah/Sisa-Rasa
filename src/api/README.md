# Recipe Recommender API - ✅ PRODUCTION READY

This API provides a complete backend solution for the Sisa Rasa Recipe Recommendation System. The backend is **fully functional** and ready for frontend integration with 10,000 recipes, 36,915 ingredients, and advanced KNN-based recommendations.

## Getting Started

### Prerequisites

Make sure you have the following Python packages installed:

```
numpy
pandas
scikit-learn
matplotlib
seaborn
flask
flask-cors
gunicorn
```

You can install them using pip:

```
pip install -r requirements.txt
```

### Running the API

Navigate to the `src/` directory and run the `run_api.py` script:

```
cd src
python run_api.py
```

#### Command Line Arguments

- `--port`: Port to run the API on (default: 5000)
- `--host`: Host to run the API on (default: 0.0.0.0)
- `--debug`: Run the API in debug mode (flag)
- `--num-recipes`: Number of recipes to recommend (default: 10)
- `--max-recipes`: Maximum number of recipes to load (default: 10000)

Example:

```
python run_api.py --port 8000 --debug --num-recipes 20
```

## API Endpoints

### Health Check

```
GET /api/health
```

Returns the status of the API and information about the loaded recipes and ingredients.

### Get Ingredients

```
GET /api/ingredients?search=egg&limit=10
```

Returns a list of ingredients that match the search term.

#### Query Parameters

- `search`: Search term to filter ingredients by name (optional)
- `limit`: Maximum number of ingredients to return (default: 100)

### Recommend Recipes

```
POST /api/recommend
```

Returns a list of recommended recipes based on the provided ingredients.

#### Request Body

```json
{
    "ingredients": ["egg", "chicken", "rice"],
    "limit": 10,
    "min_score": 0.05,
    "strict": false
}
```

- `ingredients`: List of ingredient names or IDs
- `limit`: Maximum number of recipes to return (default: 10)
- `min_score`: Minimum score threshold for recommendations (default: 0.05)
- `strict`: If true, only return recipes that contain ALL user ingredients (default: false)

### Get Recipe Details

```
GET /api/recipe/{recipe_id}
```

Returns details for a specific recipe.

#### Path Parameters

- `recipe_id`: ID of the recipe to get

## Example Usage

### Get Ingredients

```
GET /api/ingredients?search=egg
```

Response:

```json
{
    "status": "ok",
    "count": 5,
    "ingredients": [
        {
            "id": "1355",
            "name": "egg"
        },
        {
            "id": "1356",
            "name": "egg white"
        },
        {
            "id": "1357",
            "name": "egg yolk"
        },
        {
            "id": "1358",
            "name": "eggplant"
        },
        {
            "id": "1359",
            "name": "egg noodles"
        }
    ]
}
```

### Recommend Recipes

```
POST /api/recommend
```

Request Body:

```json
{
    "ingredients": ["egg", "chicken", "rice"],
    "limit": 2
}
```

Response:

```json
{
    "status": "ok",
    "count": 2,
    "recipes": [
        {
            "id": "123",
            "name": "Chicken Fried Rice",
            "ingredients": [
                {"id": "1355", "name": "egg"},
                {"id": "389", "name": "chicken"},
                {"id": "840", "name": "rice"},
                {"id": "1527", "name": "garlic"},
                {"id": "652", "name": "onion"}
            ],
            "steps": ["Cook rice according to package instructions.", "Heat oil in a large skillet over medium heat.", "Add chicken and cook until no longer pink.", "Add garlic and onion and cook until fragrant.", "Push everything to one side of the skillet and add egg to the other side.", "Scramble the egg and then mix everything together.", "Add rice and stir to combine."],
            "techniques": ["frying", "boiling"],
            "calorie_level": 1,
            "score": 0.85,
            "ingredient_match_percentage": 75.0
        },
        {
            "id": "456",
            "name": "Chicken and Egg Bowl",
            "ingredients": [
                {"id": "1355", "name": "egg"},
                {"id": "389", "name": "chicken"},
                {"id": "1527", "name": "garlic"},
                {"id": "652", "name": "onion"}
            ],
            "steps": ["Cook chicken in a skillet until no longer pink.", "Add garlic and onion and cook until fragrant.", "In a separate pan, fry an egg.", "Serve chicken mixture with the fried egg on top."],
            "techniques": ["frying"],
            "calorie_level": 1,
            "score": 0.75,
            "ingredient_match_percentage": 50.0
        }
    ]
}
```
