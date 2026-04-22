# Neo4j URI Schemes - Configuration Guide

## Fixed! ✅

The error has been fixed in `app/ai/graph_service.py`. It now automatically detects the URI scheme and only applies SSL/trust settings when appropriate.

---

## URI Schemes Explained

Neo4j supports different URI schemes depending on your setup:

### **Development / Local Docker** 🐳

**Scheme:** `bolt://` (unencrypted, local only)

```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

**Use for:**
- Local Docker development (service-to-service communication)
- Internal docker networks
- No encryption needed (trusted network)

**Example docker-compose.yml:**
```yaml
neo4j:
  image: neo4j:5-community
  environment:
    NEO4J_AUTH: neo4j/password
  ports:
    - "7687:7687"
```

---

### **Production with SSL (Secure)** 🔒

**Scheme:** `bolt+s://` or `neo4j+s://` (encrypted)

```bash
NEO4J_URI=bolt+s://neo4j.yourdomain.com:7687
NEO4J_USER=neo4j_prod
NEO4J_PASSWORD=your-strong-password
```

**Use for:**
- Production environments
- Remote Neo4j servers
- Internet-exposed Neo4j instances
- When certificate verification is required

**Note:** The Python driver will automatically validate SSL certificates.

---

### **Production with SSL (Skip Certificate Validation)** ⚠️

**Scheme:** `bolt+ssc://` or `neo4j+ssc://` (encrypted, skip cert check)

```bash
NEO4J_URI=bolt+ssc://neo4j.yourdomain.com:7687
NEO4J_USER=neo4j_prod
NEO4J_PASSWORD=your-strong-password
```

**Use for:**
- Self-signed certificates
- Testing SSL without valid certificates
- Internal infrastructure with custom CAs

**Warning:** Use only if you understand the security implications.

---

### **Neo4j Aura (Managed Service)** ☁️

**Scheme:** `neo4j+s://` (Aura default)

```bash
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password
```

**Get your URI from:**
1. Neo4j Aura console
2. Copy the connection URI from your database

**Note:** Aura URIs look like:
```
neo4j+s://a1b2c3d4.databases.neo4j.io
```

---

## Quick Reference

| Environment | URI Scheme | Example | SSL |
|-------------|-----------|---------|-----|
| Local Docker | `bolt://` | `bolt://neo4j:7687` | ❌ No |
| Local Machine | `bolt://` | `bolt://localhost:7687` | ❌ No |
| Production | `bolt+s://` | `bolt+s://prod-neo4j.com:7687` | ✅ Yes |
| Production (self-signed) | `bolt+ssc://` | `bolt+ssc://internal-db.com:7687` | ✅ Yes (insecure) |
| Neo4j Aura | `neo4j+s://` | `neo4j+s://abc123.databases.neo4j.io` | ✅ Yes |

---

## Configuration by Environment

### Development (.env)
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Staging (.env.staging)
```bash
NEO4J_URI=bolt+s://staging-neo4j.internal:7687
NEO4J_USER=neo4j_staging
NEO4J_PASSWORD=your-staging-password
```

### Production (.env.production)
```bash
NEO4J_URI=bolt+s://prod-neo4j.yourdomain.com:7687
NEO4J_USER=neo4j_prod
NEO4J_PASSWORD=your-strong-password-from-secrets-manager
```

### Neo4j Aura
```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password
```

---

## How the Python Driver Works

The Neo4j Python driver now automatically detects your URI scheme:

```python
# Local development - no SSL settings
driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))
✅ Works! No SSL validation

# Production with SSL - enables secure connection
driver = GraphDatabase.driver("bolt+s://prod-neo4j.com:7687", auth=(...))
✅ Works! Validates SSL certificate

# Self-signed cert - skip validation
driver = GraphDatabase.driver("bolt+ssc://internal-db.com:7687", auth=(...))
✅ Works! Skips certificate validation
```

---

## Testing Your Connection

### Test locally:
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

### Test via Neo4j Browser:
1. Visit your Neo4j browser URL:
   - Local: `http://localhost:7474`
   - Aura: Provided in console
2. Login with your credentials
3. Run: `MATCH (n) RETURN count(n) LIMIT 5`

---

## Common Issues & Solutions

### "neo4j.exceptions.ConfigurationError: The config settings..."
**Cause:** Using SSL settings (trust) with unencrypted scheme (bolt://)
**Solution:** ✅ Fixed in latest code! Just update `graph_service.py`

### "Insecure connection to database!"
**Cause:** Using `bolt://` or `bolt+ssc://` from external network
**Solution:** Use `bolt+s://` with valid SSL certificate

### "SSL: CERTIFICATE_VERIFY_FAILED"
**Cause:** SSL certificate invalid or self-signed
**Solution:** Use `bolt+ssc://` for self-signed certificates

### "Connection refused"
**Cause:** Neo4j not running or wrong host/port
**Solution:**
```bash
docker-compose ps neo4j
docker-compose logs neo4j
docker-compose restart neo4j
```

---

## Best Practices

1. **Development:** Use `bolt://` with Docker compose
2. **Production:** Use `bolt+s://` with valid SSL certificates
3. **Secrets:** Never commit passwords to git
   ```bash
   # ✅ Good
   NEO4J_PASSWORD=$(aws secretsmanager get-secret-value --secret-id neo4j-password)
   
   # ❌ Bad
   NEO4J_PASSWORD=my-password-in-git
   ```

4. **Testing:** Use `--dry-run` flag on commands
   ```bash
   python manage.py backfill_graph --org org-1 --type sku --dry-run
   ```

5. **Monitoring:** Check connection health regularly
   ```bash
   python manage.py shell -c "
   from app.ai.graph_service import GraphService
   service = GraphService.get_instance()
   print('✓ Neo4j is healthy')
   "
   ```

---

## Setup Examples

### Example 1: Docker Compose (Local Development)
```yaml
# docker-compose.yml
services:
  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7687:7687"
      - "7474:7474"
    volumes:
      - neo4j_data:/var/lib/neo4j/data

volumes:
  neo4j_data:
```

```bash
# .env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Example 2: AWS EC2 (Production)
```bash
# .env.production (stored in secrets manager)
NEO4J_URI=bolt+s://neo4j-prod.ec2.amazonaws.com:7687
NEO4J_USER=neo4j_prod
NEO4J_PASSWORD=your-aws-secrets-manager-password
```

### Example 3: Neo4j Aura (Managed)
```bash
# .env.aura
NEO4J_URI=neo4j+s://abc12345.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password
```

### Example 4: Kubernetes (Production)
```yaml
# deployment.yaml
containers:
- name: wms-middleware
  env:
  - name: NEO4J_URI
    value: "bolt+s://neo4j-service.neo4j:7687"
  - name: NEO4J_USER
    value: "neo4j_prod"
  - name: NEO4J_PASSWORD
    valueFrom:
      secretKeyRef:
        name: neo4j-credentials
        key: password
```

---

## Summary

✅ **The fix automatically handles URI scheme detection**

- `bolt://` → No SSL (local only)
- `bolt+s://` → SSL with certificate validation (production)
- `bolt+ssc://` → SSL without validation (self-signed certs)
- `neo4j+s://` → Neo4j Aura (SSL with validation)

Just set the correct URI in your `.env` and it will work!
