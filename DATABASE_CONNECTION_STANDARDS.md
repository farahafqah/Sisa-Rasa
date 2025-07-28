# SisaRasa Database Connection Standards

## Overview

This document establishes standardized patterns for MongoDB database connections throughout the SisaRasa system to ensure consistency, security, and proper Atlas connectivity.

## Environment Variable Standards

### Primary Connection Variable
- **Variable Name**: `MONGO_URI`
- **Purpose**: Primary MongoDB connection string for Atlas
- **Format**: `mongodb+srv://username:password@cluster.mongodb.net/database?options`
- **Usage**: All production code should use this variable

### Deprecated Variables
- **Variable Name**: `MONGODB_URI` 
- **Status**: ❌ **DEPRECATED** - Do not use
- **Reason**: Causes confusion and defaults to local MongoDB

## Connection Patterns

### 1. Flask-PyMongo Pattern (Recommended for Web App)

**Use Case**: Flask web application components
**Files**: `user.py`, `recipe.py`, `community.py`

```python
from flask_pymongo import PyMongo

# Initialize PyMongo
mongo = PyMongo()

def init_db(app):
    """Initialize the database connection."""
    mongo.init_app(app)  # Automatically uses MONGO_URI from Flask config
```

**Advantages**:
- Automatic connection management
- Integrates with Flask configuration
- Connection pooling handled by Flask-PyMongo
- Consistent with Flask best practices

### 2. Direct MongoClient Pattern (For Standalone Scripts)

**Use Case**: Standalone scripts, utilities, analytics tools
**Files**: All standalone Python scripts

```python
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_database():
    """Connect to MongoDB database."""
    try:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        client = MongoClient(mongo_uri)
        db = client.get_default_database()
        
        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {mongo_uri}")
        return db, client
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None, None
```

**Key Points**:
- Always use `os.getenv('MONGO_URI')`
- Use `client.get_default_database()` instead of hardcoded database names
- Include connection testing with `ping` command
- Provide fallback for development (localhost)
- Always load environment variables with `load_dotenv()`

## Security Standards

### Environment Variable Management
1. **Never hardcode credentials** in source code
2. **Always use environment variables** for connection strings
3. **Load environment variables** using `python-dotenv`
4. **Use .env files** for local development configuration

### Credential Protection
```python
# ❌ WRONG - Hardcoded credentials
atlas_uri = "mongodb+srv://user:pass@cluster.mongodb.net/db"

# ✅ CORRECT - Environment variable
atlas_uri = os.getenv('MONGO_URI')
if not atlas_uri:
    print("❌ MONGO_URI environment variable not found")
    sys.exit(1)
```

## Database Access Patterns

### Database Selection
```python
# ✅ RECOMMENDED - Uses database from connection string
db = client.get_default_database()

# ❌ AVOID - Hardcoded database name
db = client['sisarasa']
```

### Connection Testing
```python
# Always test connections
try:
    client.admin.command('ping')
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    return None
```

## File-Specific Standards

### Flask Application Files
- **Pattern**: Flask-PyMongo
- **Configuration**: Uses `MONGO_URI` from Flask config
- **Files**: `src/api/models/*.py`

### Standalone Scripts
- **Pattern**: Direct MongoClient
- **Environment**: Load with `load_dotenv()`
- **Variable**: `os.getenv('MONGO_URI')`
- **Files**: All root-level `.py` scripts

### Configuration Files
- **File**: `src/api/config.py`
- **Responsibility**: Central configuration management
- **Pattern**: Load and expose `MONGO_URI`

## Migration Checklist

When adding new database connections:

### ✅ Pre-Development Checklist
- [ ] Determine if Flask-PyMongo or Direct MongoClient pattern is appropriate
- [ ] Ensure `.env` file contains `MONGO_URI`
- [ ] Import `load_dotenv()` for standalone scripts

### ✅ Development Checklist
- [ ] Use `os.getenv('MONGO_URI')` (not `MONGODB_URI`)
- [ ] Use `client.get_default_database()` (not hardcoded database names)
- [ ] Include connection testing with `ping` command
- [ ] Handle connection errors gracefully
- [ ] Add appropriate logging

### ✅ Security Checklist
- [ ] No hardcoded connection strings
- [ ] No embedded credentials in source code
- [ ] Environment variables properly loaded
- [ ] Connection strings not logged in plain text

### ✅ Testing Checklist
- [ ] Test connection to Atlas cluster
- [ ] Verify correct database is accessed
- [ ] Test error handling for connection failures
- [ ] Run `test_all_database_connections.py`

## Common Mistakes to Avoid

### ❌ Wrong Environment Variable
```python
# WRONG
mongo_uri = os.getenv('MONGODB_URI')  # Defaults to local
```

### ❌ Hardcoded Database Name
```python
# WRONG
db = client['sisarasa']  # Hardcoded database name
```

### ❌ Missing Environment Loading
```python
# WRONG - Missing load_dotenv()
mongo_uri = os.getenv('MONGO_URI')  # May be None
```

### ❌ No Connection Testing
```python
# WRONG - No connection verification
client = MongoClient(mongo_uri)
db = client.get_default_database()
# Proceed without testing connection
```

## Troubleshooting

### Connection Issues
1. **Check environment variables**: Ensure `MONGO_URI` is set
2. **Verify Atlas URI format**: Should start with `mongodb+srv://`
3. **Test network connectivity**: Ensure Atlas cluster is accessible
4. **Check credentials**: Verify username/password in connection string

### Common Error Messages
- `ServerSelectionTimeoutError`: Network/firewall issues
- `OperationFailure`: Authentication problems
- `ConfigurationError`: Malformed connection string

### Debugging Tools
- Use `test_all_database_connections.py` for comprehensive testing
- Check connection string format and credentials
- Verify environment variable loading with `print(os.getenv('MONGO_URI'))`

## Maintenance

### Regular Audits
- Run `test_all_database_connections.py` monthly
- Review new files for compliance with standards
- Update documentation when patterns change

### Version Control
- Never commit `.env` files with real credentials
- Use `.env.example` for documentation
- Keep connection patterns consistent across updates

## Contact and Support

For questions about database connection standards:
1. Review this documentation
2. Run the test suite: `python test_all_database_connections.py`
3. Check the audit report: `DATABASE_CONNECTION_AUDIT.md`

---

**Last Updated**: 2025-07-29  
**Version**: 1.0  
**Status**: ✅ All connections verified and standardized
