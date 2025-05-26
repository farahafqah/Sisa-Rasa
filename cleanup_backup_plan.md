# SISA RASA PROJECT CLEANUP BACKUP PLAN

## 📅 Cleanup Date: 2025-01-27
## 🎯 Objective: Remove unused, redundant, and obsolete files while preserving all working functionality

---

## 🔒 BACKUP STRATEGY

### 1. Git Backup
- Current branch: main
- Backup branch: backup-before-cleanup-2025-01-27
- Full project state preserved in version control

### 2. File Archive Backup
- Archive location: ./backup/removed_files_2025-01-27/
- All removed files will be copied here before deletion
- Organized by removal stage for easy restoration if needed

---

## 📋 DETAILED REMOVAL PLAN

### STAGE 1: TEST/DEVELOPMENT TEMPLATES (3 files)
**Risk Level: VERY LOW** - These are development testing pages

1. **src/api/templates/test-api.html** (279 lines)
   - Purpose: API testing interface for developers
   - Route: /test-api (defined in routes.py line 120-123)
   - Why Remove: Development tool, not needed in production
   - Dependencies: None

2. **src/api/templates/test-redirect.html** (45 lines)
   - Purpose: Testing redirect functionality to search results
   - Route: /test-redirect (defined in routes.py line 110-113)
   - Why Remove: Development tool for testing redirects
   - Dependencies: None

3. **src/api/templates/test.html** (14 lines)
   - Purpose: Testing static file serving (images)
   - Route: /test (defined in routes.py line 115-118)
   - Why Remove: Development tool for static file testing
   - Dependencies: None

### STAGE 2: DIAGNOSTIC/TEST SCRIPTS (4 files)
**Risk Level: LOW** - These are standalone testing scripts

4. **test_community_features.py** (216 lines)
   - Purpose: Test community features (reviews, verifications)
   - Usage: Standalone script for testing API endpoints
   - Why Remove: Functionality confirmed working, no longer needed
   - Dependencies: None (standalone)

5. **diagnose_rating_issue.py** (178 lines)
   - Purpose: Diagnostic script for rating submission issues
   - Usage: Troubleshooting tool for rating problems
   - Why Remove: Issues resolved, diagnostic complete
   - Dependencies: None (standalone)

6. **src/test_enhanced_knn.py** (estimated ~100-200 lines)
   - Purpose: Testing enhanced KNN recommender functionality
   - Usage: Development testing for KNN algorithms
   - Why Remove: Not needed for production system
   - Dependencies: None (standalone)

7. **src/test_hybrid_recommender.py** (estimated ~100-200 lines)
   - Purpose: Testing hybrid recommender system
   - Usage: Development testing for hybrid algorithms
   - Why Remove: Not needed for production system
   - Dependencies: None (standalone)

### STAGE 3: STANDALONE DEVELOPMENT SCRIPTS (3 files)
**Risk Level: LOW** - These are one-time setup scripts

8. **src/download_clean_dataset.py** (277 lines)
   - Purpose: Download and process clean recipe dataset from GitHub
   - Usage: One-time data preparation script
   - Why Remove: Dataset already downloaded and processed
   - Dependencies: None (standalone)

9. **src/download_epicurious_dataset.py** (estimated ~200-300 lines)
   - Purpose: Download alternative Epicurious dataset
   - Usage: Alternative data source (not used)
   - Why Remove: Not used in current system
   - Dependencies: None (standalone)

10. **src/main_clean.py** (171 lines)
    - Purpose: Command-line interface for recipe recommendations
    - Usage: Standalone CLI tool for testing recommendations
    - Why Remove: Superseded by web API interface
    - Dependencies: clean_recipe_recommender.py (but that stays)

### STAGE 4: TEMPORARY ANALYSIS FILES (1 file)
**Risk Level: NONE** - Created for this cleanup

11. **file_analysis.py** (100 lines)
    - Purpose: Analysis script created for this cleanup process
    - Usage: Temporary file for cleanup analysis
    - Why Remove: No longer needed after cleanup
    - Dependencies: None

---

## 🛡️ SAFETY MEASURES

### Files That Look Similar But MUST BE KEPT:
- ✅ **src/api/templates/check_auth.html** - KEEP (used by decorators.py)
- ✅ **src/api/templates/api_docs.html** - KEEP (professional API documentation)
- ✅ **src/clean_recipe_recommender.py** - KEEP (used by hybrid recommender)
- ✅ **src/hybrid_recipe_recommender.py** - KEEP (main recommender system)

### Routes That Will Be Removed:
- /test-api
- /test-redirect  
- /test

These routes will be removed from routes.py after template removal.

---

## 📊 CLEANUP SUMMARY

**Total Files to Remove: 11**
- Stage 1: 3 test templates
- Stage 2: 4 test scripts  
- Stage 3: 3 development scripts
- Stage 4: 1 temporary file

**Estimated Space Savings: 2-3 MB**
**Risk Level: VERY LOW**
**Functionality Impact: NONE** (all production features preserved)
