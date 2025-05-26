# Hybrid Recipe Recommendation System

## Overview

The hybrid recipe recommendation system combines multiple recommendation techniques to provide more accurate and diverse recipe suggestions while maintaining the KNN algorithm as the core component. This system addresses the limitations of using KNN alone and provides personalized recommendations based on user preferences and behavior.

## System Architecture

### 1. Core Components

#### **KNN Algorithm (Primary - 50% weight)**
- Enhanced KNN with ingredient importance scoring
- Prioritizes unique ingredients over common ones
- Handles plural forms automatically
- Returns recipe names with decoded ingredients and cooking steps

#### **Content-Based Filtering (25% weight)**
- Uses TF-IDF vectorization of recipe content (ingredients + instructions)
- Considers recipe attributes: cuisine, difficulty, prep time, cook time, servings
- Applies user preferences for filtering and boosting relevant recipes
- Scales numerical attributes for consistent comparison

#### **Collaborative Filtering (15% weight)**
- Analyzes user rating patterns to find similar users
- Recommends recipes liked by users with similar tastes
- Uses Pearson correlation for user similarity calculation
- Falls back to popularity-based recommendations for new users

#### **Popularity-Based Recommendations (10% weight)**
- Combines average ratings with review count
- Provides fallback recommendations for new users
- Ensures popular, well-rated recipes are considered
- Updates dynamically as new ratings are added

### 2. Data Integration

#### **MongoDB Integration**
- Loads user ratings and reviews from the crowd-sourcing system
- Updates recipe popularity scores based on user interactions
- Maintains real-time synchronization with user preferences
- Stores aggregated rating data for efficient retrieval

#### **Recipe Dataset**
- Uses the existing clean_recipes.json dataset
- Processes 10,000+ recipes with 36,000+ unique ingredients
- Maintains compatibility with existing ingredient mapping
- Preserves all recipe attributes and instructions

## Implementation Details

### 3. Hybrid Scoring Algorithm

The final recommendation score is calculated as:

```
Final Score = (KNN Score × 0.5) + 
              (Content Score × 0.25) + 
              (Collaborative Score × 0.15) + 
              (Popularity Score × 0.1)
```

### 4. Key Features

#### **Personalization**
- User-specific recommendations based on rating history
- Content preferences (cuisine, difficulty, cooking time)
- Adaptive learning from user interactions

#### **Diversity**
- Multiple recommendation sources prevent filter bubbles
- Balances popular recipes with personalized suggestions
- Ensures variety in cuisine types and cooking styles

#### **Real-time Updates**
- Immediately incorporates new user ratings
- Updates popularity scores dynamically
- Clears recommendation cache for fresh results

#### **Fallback Mechanisms**
- KNN-only fallback if hybrid system fails
- Popularity-based recommendations for new users
- Graceful degradation when components are unavailable

### 5. API Integration

#### **Enhanced Recommendation Endpoint**
- `/api/recommend` now uses hybrid approach
- Supports both authenticated and anonymous users
- Returns hybrid scores and recommendation explanations
- Maintains backward compatibility with existing UI

#### **User Preference Updates**
- Automatic updates when users rate recipes
- Real-time synchronization with recommendation engine
- Improved recommendations with each user interaction

#### **Performance Optimizations**
- Recommendation caching for frequently requested queries
- Efficient vector operations using scikit-learn
- Optimized MongoDB queries for user data

## Benefits Over KNN-Only Approach

### 6. Improved Accuracy
- **Multiple Signals**: Combines ingredient matching with user preferences and popularity
- **Personalization**: Adapts to individual user tastes over time
- **Context Awareness**: Considers recipe attributes beyond just ingredients

### 7. Better User Experience
- **Diverse Results**: Prevents repetitive recommendations
- **Explanation**: Users can understand why recipes were recommended
- **Adaptive**: Learns from user behavior to improve suggestions

### 8. Scalability
- **Efficient Processing**: Handles large datasets with optimized algorithms
- **Real-time Updates**: Incorporates new data without system restart
- **Modular Design**: Easy to adjust weights and add new components

## Configuration

### 9. Recommendation Weights
The system allows fine-tuning of component weights:

```python
HybridRecipeRecommender(
    knn_weight=0.5,        # Primary algorithm
    content_weight=0.25,   # Recipe attributes
    collaborative_weight=0.15,  # User similarity
    popularity_weight=0.1  # Popular recipes
)
```

### 10. User Preferences
Supports various user preference types:
- **Cuisine**: Filter by cuisine type
- **Difficulty**: Match cooking skill level
- **Time Constraints**: Maximum prep/cook time
- **Dietary Restrictions**: Future enhancement capability

## Testing and Validation

### 11. Comprehensive Testing
- Unit tests for each recommendation component
- Integration tests with MongoDB and API
- Performance tests with large datasets
- User experience validation

### 12. Monitoring
- Recommendation quality metrics
- User engagement tracking
- System performance monitoring
- Error handling and logging

## Future Enhancements

### 13. Planned Improvements
- **Dietary Restrictions**: Support for allergies and dietary preferences
- **Seasonal Recommendations**: Consider ingredient availability
- **Social Features**: Friend-based recommendations
- **Advanced ML**: Deep learning models for better accuracy

### 14. Maintenance
- Regular model retraining with new data
- Performance optimization based on usage patterns
- User feedback integration for continuous improvement
- A/B testing for recommendation algorithm improvements

## Conclusion

The hybrid recommendation system significantly improves upon the KNN-only approach by:
- Providing more accurate and personalized recommendations
- Ensuring diversity in recipe suggestions
- Learning from user behavior and preferences
- Maintaining high performance and scalability

This system preserves the strengths of the original KNN algorithm while addressing its limitations through intelligent combination with other recommendation techniques.
