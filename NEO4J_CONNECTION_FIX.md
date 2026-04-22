# Neo4j Connection Error - FIXED ✅

## The Issue

You got this error:
```
neo4j.exceptions.ConfigurationError: The config settings "encrypted", "trust", 
"trusted_certificates", and "ssl_context" can only be used with the URI schemes 
['bolt', 'neo4j']. Use the other URI schemes ['bolt+ssc', 'bolt+s', 'neo4j+ssc', 
'neo4j+s'] for setting encryption settings.
```

## What Was Wrong

The code was trying to use SSL settings (`trust="TRUST_ALL_CERTIFICATES"`) with an unencrypted URI scheme (`bolt://neo4j:7687`).

**Before (broken):**
```python
cls._driver = GraphDatabase.driver(
    "bolt://neo4j:7687",  # ← Unencrypted scheme
    auth=(user, password),
    trust="TRUST_ALL_CERTIFICATES",  # ← SSL setting on unencrypted scheme ❌
)
```

## The Fix ✅

Updated `app/ai/graph_service.py` to automatically detect the URI scheme and only apply SSL settings when appropriate:

```python
# Now it's smart!
driver_kwargs = {"auth": (neo4j_user, neo4j_password)}

# Only use SSL settings for encrypted schemes
if neo4j_uri.startswith(("bolt+s", "bolt+ssc", "neo4j+s", "neo4j+ssc")):
    driver_kwargs["trust"] = "TRUST_ALL_CERTIFICATES"

cls._driver = GraphDatabase.driver(neo4j_uri, **driver_kwargs)
```

## What to Do Now

### 1. Update your code
The fix is already applied in `app/ai/graph_service.py`. Just make sure you have the latest version.

### 2. Use the correct URI for your environment

**Development (Docker):**
```bash
NEO4J_URI=bolt://neo4j:7687
```

**Production (Secure):**
```bash
NEO4J_URI=bolt+s://neo4j.yourdomain.com:7687
```

**Self-signed certs:**
```bash
NEO4J_URI=bolt+ssc://internal-db.com:7687
```

**Neo4j Aura:**
```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
```

### 3. Test the connection

```bash
python manage.py shell << 'EOF'
from app.ai.graph_service import GraphService
try:
    service = GraphService.get_instance()
    print("✓ Connection successful!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
EOF
```

## URI Scheme Reference

| Scheme | Encryption | Cert Validation | Use Case |
|--------|-----------|-----------------|----------|
| `bolt://` | ❌ No | N/A | Local Docker development |
| `bolt+s://` | ✅ Yes | ✅ Yes | Production with valid SSL |
| `bolt+ssc://` | ✅ Yes | ❌ No | Self-signed certificates |
| `neo4j+s://` | ✅ Yes | ✅ Yes | Neo4j Aura (managed) |

## Example Configurations

### Local Development
```bash
# .env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Production on AWS
```bash
# .env.production
NEO4J_URI=bolt+s://neo4j-prod.ec2.amazonaws.com:7687
NEO4J_USER=neo4j_prod
NEO4J_PASSWORD=your-secret-password
```

### Neo4j Aura
```bash
# .env.aura
NEO4J_URI=neo4j+s://abc12345.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password
```

## That's It! 🎉

The error should now be fixed. Just:
1. Keep `bolt://` for local development
2. Use `bolt+s://` for production
3. Use `bolt+ssc://` for self-signed certs
4. Use `neo4j+s://` for Aura

The Python driver will automatically handle SSL settings correctly!

See `NEO4J_URI_SCHEMES.md` for more detailed information about each scheme.
