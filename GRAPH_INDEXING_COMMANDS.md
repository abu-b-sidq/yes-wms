# Graph Indexing Commands - GraphRAG

Complete guide to indexing existing data and knowledge into Neo4j knowledge graph.

---

## 📋 Overview

There are 4 management commands for populating the graph:

| Command | Purpose | Data Source | Best For |
|---------|---------|-------------|----------|
| `backfill_graph` | Index existing transactions, SKUs, locations, facilities | PostgreSQL | Initial setup, bulk import |
| `index_knowledge_graph` | Index knowledge base files into graph | Markdown files | Knowledge base indexing |
| `index_knowledge` | ⚠️ Legacy - embeds knowledge to pgvector | Markdown files | Old vector system (deprecated) |
| `index_existing_data` | ⚠️ Legacy - embeds SKUs/transactions to pgvector | PostgreSQL | Old vector system (deprecated) |

---

## 1️⃣ Backfill Existing Transactions & Data

### Command: `backfill_graph`

Reads all SKUs, Transactions, Locations, and Facilities from PostgreSQL and creates nodes in Neo4j.

### Usage

#### Backfill everything (all data types):
```bash
python manage.py backfill_graph --org org-1
```

**Output:**
```
Backfilling Facilities...
  ✓ Created 5 Facility nodes
Backfilling Locations...
  ✓ Created 24 Location nodes
Backfilling SKUs...
  ✓ Created 150 SKU nodes
Backfilling Transactions...
  ✓ Created 3,847 Transaction nodes
✓ Backfill completed for org org-1
```

#### Backfill specific data type only:
```bash
# Only SKUs
python manage.py backfill_graph --org org-1 --type sku

# Only Transactions
python manage.py backfill_graph --org org-1 --type transaction

# Only Locations
python manage.py backfill_graph --org org-1 --type location

# Only Facilities
python manage.py backfill_graph --org org-1 --type facility
```

#### Limit number of records (for testing):
```bash
# Backfill only first 100 SKUs
python manage.py backfill_graph --org org-1 --type sku --limit 100

# Backfill only first 500 transactions
python manage.py backfill_graph --org org-1 --type transaction --limit 500
```

#### Backfill specific data types in sequence:
```bash
# Step 1: Backfill infrastructure (faster)
python manage.py backfill_graph --org org-1 --type facility
python manage.py backfill_graph --org org-1 --type location

# Step 2: Backfill master data
python manage.py backfill_graph --org org-1 --type sku

# Step 3: Backfill transactions (slowest, most data)
python manage.py backfill_graph --org org-1 --type transaction
```

### Performance Tips

**For large datasets (100k+ transactions):**
```bash
# Process in batches to avoid memory issues
python manage.py backfill_graph --org org-1 --type transaction --limit 10000
python manage.py backfill_graph --org org-1 --type transaction --limit 10000 --offset 10000
# (repeat with different --offset values)
```

**Verify progress:**
```bash
# Check how many nodes were created in Neo4j
python manage.py shell
>>> from app.ai.graph_service import GraphService
>>> service = GraphService.get_instance()
>>> result = service._execute_query(
...   "MATCH (s:SKU {org_id: 'org-1'}) RETURN count(s) as count",
...   {"org_id": "org-1"}
... )
>>> print(result[0]['count'])
150
```

---

## 2️⃣ Index Knowledge Base Files

### Command: `index_knowledge_graph`

Reads markdown files from knowledge directory and creates KnowledgeItem nodes in Neo4j.

### Prerequisites

Create a knowledge directory:
```bash
mkdir -p knowledge/
```

Add markdown files:
```bash
# Example knowledge files
cat > knowledge/sku-handling.md << 'EOF'
# SKU Handling Procedures

## High-Value Item Protocol
For SKUs with value > $1000 (like ABC123, XYZ789):
- Require warehouse manager approval
- Store in secure location SHELF-A or SHELF-B
- Document all movements

## Standard Handling
SKU DEF456 uses standard procedures...
EOF

cat > knowledge/warehouse-safety.md << 'EOF'
# Warehouse Safety Guidelines

## WH-CENTRAL Warehouse
Location: Main facility in Los Angeles
- Keep aisles clear
- Use proper lifting equipment
...
EOF
```

### Usage

#### Index all knowledge files:
```bash
python manage.py index_knowledge_graph --org org-1
```

**Output:**
```
Indexing knowledge from 2 file(s) into Neo4j
Organization: org-1
Category: procedure
Auto-relate: False
Dry run: False

📄 sku-handling
  ✓ Created: sku-handling-chunk-0
  ✓ Created: sku-handling-chunk-1
📄 warehouse-safety
  ✓ Created: warehouse-safety-chunk-0

================================================================
✓ Completed: Indexed 3 chunk(s) from 2 file(s)
```

#### Specify knowledge directory:
```bash
python manage.py index_knowledge_graph --org org-1 --dir /path/to/knowledge/
```

#### Categorize knowledge items:
```bash
# Index as procedures (default)
python manage.py index_knowledge_graph --org org-1 --category procedure

# Index as guides
python manage.py index_knowledge_graph --org org-1 --category guide

# Index as policies
python manage.py index_knowledge_graph --org org-1 --category policy

# Index as FAQs
python manage.py index_knowledge_graph --org org-1 --category faq

# Index as other
python manage.py index_knowledge_graph --org org-1 --category other
```

#### Auto-create relationships to entities:
Creates automatic `[:RELATES_TO]` connections based on mentioned SKU codes, locations, and facilities:

```bash
python manage.py index_knowledge_graph --org org-1 --auto-relate
```

**What it does:**
- Scans knowledge content for SKU codes (ABC123, SKU-001, etc.)
- Scans for location codes ("LOCATION: SHELF-A", etc.)
- Scans for facility codes ("WAREHOUSE: WH-CENTRAL", etc.)
- Creates `RELATES_TO` relationships if mentioned entities exist in database

**Output example:**
```
📄 sku-handling
  ✓ Created: sku-handling-chunk-0
    → Linked to SKU: ABC123
    → Linked to SKU: XYZ789
    → Linked to Location: SHELF-A
    → Linked to Location: SHELF-B
  ✓ Created: sku-handling-chunk-1
    → Linked to SKU: DEF456
```

#### Dry-run mode (preview without creating):
```bash
python manage.py index_knowledge_graph --org org-1 --dry-run
```

**Output:**
```
Indexing knowledge from 2 file(s) into Neo4j
...
Dry run: True

📄 sku-handling
  [DRY RUN] Would create: sku-handling-chunk-0
           Title: sku-handling (Part 1 of 2)
           Content: 523 chars

  [DRY RUN] Would create: sku-handling-chunk-1
           Title: sku-handling (Part 2 of 2)
           Content: 410 chars

================================================================
✓ Completed: Indexed 2 chunk(s) from 1 file(s)
(This was a DRY RUN - no data was created)
```

#### Full example with all options:
```bash
python manage.py index_knowledge_graph \
  --org org-1 \
  --dir /app/knowledge/ \
  --category procedure \
  --auto-relate
```

---

## 📊 Complete Workflow: Initial Setup

### Full initialization of a new organization:

```bash
# Step 1: Make sure Neo4j is running
docker-compose up neo4j -d
sleep 5

# Step 2: Verify Neo4j connection
python manage.py shell -c "
from app.ai.graph_service import GraphService
service = GraphService.get_instance()
print('✓ Neo4j connection successful')
"

# Step 3: Backfill core infrastructure (fast)
python manage.py backfill_graph --org org-1 --type facility
python manage.py backfill_graph --org org-1 --type location

# Step 4: Backfill master data
python manage.py backfill_graph --org org-1 --type sku

# Step 5: Backfill transactions (may take a while for large datasets)
echo "Starting transaction backfill..."
python manage.py backfill_graph --org org-1 --type transaction

# Step 6: Index knowledge base
python manage.py index_knowledge_graph --org org-1 --auto-relate

# Step 7: Verify
echo "Verifying graph..."
python manage.py shell -c "
from app.ai.graph_service import GraphService
service = GraphService.get_instance()
result = service._execute_query(
  'MATCH (n {org_id: \$org_id}) RETURN labels(n)[0] as type, count(*) as count',
  {'org_id': 'org-1'}
)
for record in result:
  print(f\"{record['type']}: {record['count']} nodes\")
"

echo "✓ Setup complete!"
```

---

## 🔍 Verification Queries

### Check what was indexed:

#### Count nodes by type:
```bash
python manage.py shell << 'EOF'
from app.ai.graph_service import GraphService
service = GraphService.get_instance()

org_id = "org-1"

# Count each type
for node_type in ["SKU", "Transaction", "Location", "Facility", "KnowledgeItem", "Message"]:
    result = service._execute_query(
        f"MATCH (n:{node_type} {{org_id: $org_id}}) RETURN count(n) as count",
        {"org_id": org_id}
    )
    count = result[0]['count'] if result else 0
    print(f"{node_type}: {count}")

# Count relationships
result = service._execute_query(
    "MATCH (a {org_id: $org_id})-[r]-(b) RETURN type(r) as rel_type, count(r) as count",
    {"org_id": org_id}
)
print("\nRelationships:")
for record in result:
    print(f"  {record['rel_type']}: {record['count']}")
EOF
```

#### Find all knowledge items for a SKU:
```cypher
MATCH (k:KnowledgeItem {org_id: "org-1"})-[:RELATES_TO]->(s:SKU {code: "ABC123"})
RETURN k.title, k.category
```

#### Find all SKUs in a warehouse that have procedures:
```cypher
MATCH (k:KnowledgeItem {org_id: "org-1"})-[:RELATES_TO]->(f:Facility {code: "WH-CENTRAL"})
OPTIONAL MATCH (f)<-[:IN_FACILITY]-(l:Location)<-[:STORED_AT]-(s:SKU)
RETURN s.code, s.name, k.title
```

---

## ⚠️ Old Commands (Deprecated)

These commands are for the old pgvector system. Use `backfill_graph` and `index_knowledge_graph` instead:

### `index_existing_data` (pgvector, deprecated)
```bash
# ⚠️ DO NOT USE - pgvector is being phased out
python manage.py index_existing_data --org org-1 --type all|sku|transaction
```

### `index_knowledge` (pgvector, deprecated)
```bash
# ⚠️ DO NOT USE - pgvector is being phased out
python manage.py index_knowledge --org org-1 --dir /path/to/knowledge/
```

---

## 🐛 Troubleshooting

### "Neo4j connection failed"
```bash
# Check Neo4j is running
docker-compose ps neo4j

# Check logs
docker-compose logs neo4j

# Restart if needed
docker-compose restart neo4j
sleep 5
```

### "No data was indexed"
```bash
# Verify directory/files exist
ls -la knowledge/
ls -la knowledge/*.md

# Check org_id is correct
python manage.py shell -c "
from app.masters.models import Organization
print(Organization.objects.all().values_list('id', flat=True))
"
```

### "Relationship creation failed"
Make sure the target entity exists:
```bash
python manage.py shell -c "
from app.masters.models import SKU
print(SKU.objects.filter(org_id='org-1', code='ABC123').exists())  # Should be True
"
```

### "Out of memory during backfill"
Use `--limit` to process in smaller batches:
```bash
python manage.py backfill_graph --org org-1 --type transaction --limit 5000
```

---

## 📈 Performance Expectations

| Data Type | Typical Count | Time to Index | Neo4j Storage |
|-----------|---------------|---------------|---------------|
| SKUs | 100-1,000 | < 5 seconds | < 1 MB |
| Locations | 20-500 | < 5 seconds | < 1 MB |
| Facilities | 2-50 | < 2 seconds | < 100 KB |
| Transactions | 1,000-100,000+ | 10 sec - 10 min | 10-500 MB |
| Knowledge Items | 10-500 | < 5 seconds | 1-10 MB |

---

## 🚀 Continuous Syncing

After initial backfill, new data automatically syncs to Neo4j via Django signals:

```python
# When you create a new SKU:
sku = SKU.objects.create(org_id="org-1", code="NEW001", name="New Product")
# ✓ Neo4j node created automatically in background

# When you create a transaction:
transaction = Transaction.objects.create(...)
# ✓ Neo4j node created automatically in background
```

To verify continuous sync is working:
```bash
# Create a test SKU
python manage.py shell -c "
from app.masters.models import SKU, Organization
org = Organization.objects.get(id='org-1')
SKU.objects.create(org=org, code='TEST999', name='Sync Test')
print('Created test SKU')
"

# Wait 2 seconds for background thread
sleep 2

# Check if it appeared in Neo4j
python manage.py shell << 'EOF'
from app.ai.graph_service import GraphService
service = GraphService.get_instance()
result = service._execute_query(
    "MATCH (s:SKU {code: 'TEST999'}) RETURN s.name",
    {}
)
if result:
    print(f"✓ Found in Neo4j: {result[0]['s.name']}")
else:
    print("✗ Not found in Neo4j yet")
EOF
```

---

## 📝 Troubleshooting Checklist

- [ ] Neo4j is running: `docker-compose ps neo4j`
- [ ] Organization ID exists: `python manage.py shell`
- [ ] Knowledge files exist: `ls knowledge/*.md`
- [ ] Correct file permissions: `chmod 644 knowledge/*.md`
- [ ] Enough disk space: `df -h`
- [ ] Neo4j connection works: Manual test in Neo4j Browser
- [ ] Environment variables set: `echo $NEO4J_URI`
