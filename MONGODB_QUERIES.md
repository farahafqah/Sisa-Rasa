# MongoDB Queries for Sisa Rasa User Data Inspection

This document contains useful MongoDB queries for directly inspecting user data in the Sisa Rasa recipe recommendation system.

## Connection

```bash
# Connect to MongoDB (adjust URI as needed)
mongosh "mongodb://localhost:27017/sisarasa"
```

## Basic User Queries

### List All Users
```javascript
// Get all users with basic info
db.users.find({}, {
  name: 1, 
  email: 1, 
  created_at: 1,
  "analytics.total_reviews_given": 1,
  "analytics.total_recipe_saves": 1
}).sort({created_at: -1})

// Count total users
db.users.countDocuments({})
```

### Find Specific User
```javascript
// Find user by email
db.users.findOne({email: "user@example.com"})

// Find user by ID
db.users.findOne({_id: ObjectId("USER_ID_HERE")})

// Find users by name (case insensitive)
db.users.find({name: {$regex: "john", $options: "i"}})
```

### Get Complete User Data
```javascript
// Get user with all fields (including password hash)
db.users.findOne({email: "user@example.com"})

// Get user without password
db.users.findOne(
  {email: "user@example.com"}, 
  {password: 0}
)
```

## User Activity Queries

### User's Saved Recipes
```javascript
// Get all saved recipes for a user
db.saved_recipes.find({user_id: "USER_ID_HERE"}).sort({created_at: -1})

// Count saved recipes per user
db.saved_recipes.aggregate([
  {$group: {_id: "$user_id", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

### User's Reviews and Ratings
```javascript
// Get all reviews by a user
db.recipe_reviews.find({user_id: "USER_ID_HERE"}).sort({created_at: -1})

// Get reviews with rating breakdown
db.recipe_reviews.find(
  {user_id: "USER_ID_HERE"}, 
  {recipe_id: 1, rating: 1, review_text: 1, created_at: 1}
)

// Find all 5-star reviews by user
db.recipe_reviews.find({user_id: "USER_ID_HERE", rating: 5})

// Get average rating given by user
db.recipe_reviews.aggregate([
  {$match: {user_id: "USER_ID_HERE"}},
  {$group: {_id: null, avgRating: {$avg: "$rating"}, totalReviews: {$sum: 1}}}
])
```

### User's Recipe Verifications
```javascript
// Get all verifications by a user
db.recipe_verifications.find({user_id: "USER_ID_HERE"}).sort({created_at: -1})

// Get verifications with photos
db.recipe_verifications.find({
  user_id: "USER_ID_HERE", 
  photo_data: {$exists: true}
})

// Count verifications per user
db.recipe_verifications.aggregate([
  {$group: {_id: "$user_id", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

### User's Review Votes
```javascript
// Get all votes by a user
db.review_votes.find({user_id: "USER_ID_HERE"}).sort({created_at: -1})

// Count helpful vs unhelpful votes
db.review_votes.aggregate([
  {$match: {user_id: "USER_ID_HERE"}},
  {$group: {_id: "$vote_type", count: {$sum: 1}}}
])
```

## Analytics and Search History

### User Analytics
```javascript
// Get user analytics data
db.users.findOne(
  {email: "user@example.com"}, 
  {analytics: 1, dashboard_data: 1}
)

// Find users with most recipe views
db.users.find({}, {
  name: 1, 
  email: 1, 
  "analytics.total_recipe_views": 1
}).sort({"analytics.total_recipe_views": -1}).limit(10)

// Find most active users (by total reviews)
db.users.find({}, {
  name: 1, 
  email: 1, 
  "analytics.total_reviews_given": 1
}).sort({"analytics.total_reviews_given": -1}).limit(10)
```

### Search History
```javascript
// Get user's search history
db.users.findOne(
  {email: "user@example.com"}, 
  {"dashboard_data.recent_searches": 1, "dashboard_data.ingredient_history": 1}
)

// Find users who searched for specific ingredient
db.users.find({
  "dashboard_data.ingredient_history": {$in: ["chicken"]}
})
```

## System-Wide Statistics

### Overall Stats
```javascript
// Count documents in each collection
db.users.countDocuments({})
db.recipe_reviews.countDocuments({})
db.recipe_verifications.countDocuments({})
db.saved_recipes.countDocuments({})
db.review_votes.countDocuments({})

// Recent activity (last 7 days)
var sevenDaysAgo = new Date(Date.now() - 7*24*60*60*1000);
db.users.countDocuments({created_at: {$gte: sevenDaysAgo}})
db.recipe_reviews.countDocuments({created_at: {$gte: sevenDaysAgo}})
```

### Top Users and Content
```javascript
// Top reviewers
db.recipe_reviews.aggregate([
  {$group: {_id: "$user_id", count: {$sum: 1}, user_name: {$first: "$user_name"}}},
  {$sort: {count: -1}},
  {$limit: 10}
])

// Rating distribution
db.recipe_reviews.aggregate([
  {$group: {_id: "$rating", count: {$sum: 1}}},
  {$sort: {_id: 1}}
])

// Most saved recipes
db.saved_recipes.aggregate([
  {$group: {_id: "$name", count: {$sum: 1}}},
  {$sort: {count: -1}},
  {$limit: 10}
])
```

## Debugging Specific Issues

### Find Users with Rating Issues
```javascript
// Users who have submitted reviews recently
var yesterday = new Date(Date.now() - 24*60*60*1000);
db.recipe_reviews.find({created_at: {$gte: yesterday}})

// Find duplicate reviews (same user, same recipe)
db.recipe_reviews.aggregate([
  {$group: {
    _id: {user_id: "$user_id", recipe_id: "$recipe_id"}, 
    count: {$sum: 1},
    reviews: {$push: "$$ROOT"}
  }},
  {$match: {count: {$gt: 1}}}
])

// Find reviews without corresponding users
db.recipe_reviews.aggregate([
  {$lookup: {
    from: "users",
    localField: "user_id",
    foreignField: "_id",
    as: "user"
  }},
  {$match: {user: {$size: 0}}}
])
```

### Find Data Inconsistencies
```javascript
// Users with analytics data but no actual reviews
db.users.find({
  "analytics.total_reviews_given": {$gt: 0}
}).forEach(function(user) {
  var actualReviews = db.recipe_reviews.countDocuments({user_id: user._id.toString()});
  if (actualReviews !== user.analytics.total_reviews_given) {
    print("Mismatch for user " + user.email + ": analytics=" + 
          user.analytics.total_reviews_given + ", actual=" + actualReviews);
  }
})

// Find orphaned saved recipes
db.saved_recipes.aggregate([
  {$lookup: {
    from: "users",
    localField: "user_id",
    foreignField: "_id",
    as: "user"
  }},
  {$match: {user: {$size: 0}}}
])
```

## Data Export Queries

### Export User Data
```javascript
// Export complete user data
var userId = "USER_ID_HERE";
var userData = {
  user: db.users.findOne({_id: ObjectId(userId)}),
  saved_recipes: db.saved_recipes.find({user_id: userId}).toArray(),
  reviews: db.recipe_reviews.find({user_id: userId}).toArray(),
  verifications: db.recipe_verifications.find({user_id: userId}).toArray(),
  review_votes: db.review_votes.find({user_id: userId}).toArray()
};
print(JSON.stringify(userData, null, 2));
```

### Backup Specific Collections
```javascript
// Export all users (without passwords)
db.users.find({}, {password: 0}).forEach(function(doc) {
  print(JSON.stringify(doc));
});

// Export all reviews
db.recipe_reviews.find({}).forEach(function(doc) {
  print(JSON.stringify(doc));
});
```

## Useful Indexes for Performance

```javascript
// Create indexes for better query performance
db.users.createIndex({email: 1}, {unique: true})
db.recipe_reviews.createIndex({user_id: 1})
db.recipe_reviews.createIndex({recipe_id: 1})
db.recipe_reviews.createIndex({created_at: -1})
db.saved_recipes.createIndex({user_id: 1})
db.recipe_verifications.createIndex({user_id: 1})
db.review_votes.createIndex({user_id: 1})
db.review_votes.createIndex({review_id: 1})
```

## Quick Commands for Development

```bash
# Connect and run a quick user count
mongosh "mongodb://localhost:27017/sisarasa" --eval "db.users.countDocuments({})"

# Find a specific user quickly
mongosh "mongodb://localhost:27017/sisarasa" --eval "db.users.findOne({email: 'test@example.com'}, {password: 0})"

# Get recent reviews
mongosh "mongodb://localhost:27017/sisarasa" --eval "db.recipe_reviews.find({}).sort({created_at: -1}).limit(5)"
```
