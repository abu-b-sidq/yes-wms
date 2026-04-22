# GraphRAG Indexing - Quick Reference

## 🚀 Most Common Commands

### Start Neo4j
```bash
docker-compose up neo4j -d
sleep 5
```

### Backfill All Existing Data
```bash
# Everything at once
python manage.py backfill_graph --org org-1

# Or step by step (faster)
python manage.py backfill_graph --org org-1 --type facility
python manage.py backfill_graph --org org-1 --type location
python manage.py backfill_graph --org org-1 --type sku
python manage.py backfill_graph --org org-1 --type transaction
```

### Index Knowledge Base
```bash
# Basic
python manage.py index_knowledge_graph --org org-1

# With automatic relationships
python manage.py index_knowledge_graph --org org-1 --auto-relate

# Preview without creating (dry-run)
python manage.py index_knowledge_graph --org org-1 --dry-run
```

---

## 📋 Command Reference

### `backfill_graph` - Index Existing Data from PostgreSQL

```bash
python manage.py backfill_graph --org ORG_ID [OPTIONS]
```

**Options:**
- `--org ORG_ID` *(required)* - Organization ID
- `--type {all|sku|facility|location|transaction}` - Data type (default: all)
- `--limit N` - Limit records (for testing)

**Examples:**
```bash
# Backfill everything
python manage.py backfill_graph --org org-1

# Only transactions
python manage.py backfill_graph --org org-1 --type transaction

# Test with 100 records
python manage.py backfill_graph --org org-1 --type sku --limit 100
```

---

### `index_knowledge_graph` - Index Knowledge Files

```bash
python manage.py index_knowledge_graph --org ORG_ID [OPTIONS]
```

**Options:**
- `--org ORG_ID` *(required)* - Organization ID
- `--dir PATH` - Knowledge directory (default: ./knowledge)
- `--category {procedure|guide|policy|faq|other}` - Category (default: procedure)
- `--auto-relate` - Auto-create relationships to SKUs/Locations/Facilities
- `--dry-run` - Preview without creating

**Examples:**
```bash
# Index all knowledge as procedures
python manage.py index_knowledge_graph --org org-1

# Index with auto-relationships
python manage.py index_knowledge_graph --org org-1 --auto-relate

# Preview what would be indexed
python manage.py index_knowledge_graph --org org-1 --dry-run

# Index from custom directory as guides
python manage.py index_knowledge_graph --org org-1 --dir /path/to/docs --category guide
```

---

## 🔄 Complete Setup Workflow

```bash
# 1. Start Neo4j
docker-compose up neo4j -d
sleep 5

# 2. Backfill existing data (fastest to slowest)
python manage.py backfill_graph --org org-1 --type facility
python manage.py backfill_graph --org org-1 --type location
python manage.py backfill_graph --org org-1 --type sku
python manage.py backfill_graph --org org-1 --type transaction

# 3. Index knowledge base
python manage.py index_knowledge_graph --org org-1 --auto-relate

# 4. Verify (optional)
python manage.py shell -c "
from app.ai.graph_service import GraphService
service = GraphService.get_instance()
result = service._execute_query(
  'MATCH (n {org_id: \$org_id}) RETURN count(n)',
  {'org_id': 'org-1'}
)
print(f'Total nodes: {result[0][\"count(n)\"]}')
"
```

---

## 🧪 Testing

### Verify in Neo4j Browser
Visit `http://localhost:7474` and run:

```cypher
# Count nodes
MATCH (n {org_id: "org-1"}) RETURN labels(n)[0] as type, count(*) as count

# Find a SKU
MATCH (s:SKU {org_id: "org-1"}) RETURN s LIMIT 5

# Find relationships
MATCH (s:SKU)-[:STORED_AT]->(l:Location) RETURN s.code, l.code LIMIT 10
```

### Test in Chat
Send: `"Show me SKU ABC123"`
Should see: Prefetched graph context with relationships

---

## 🐛 Troubleshooting

### "Neo4j connection failed"
```bash
docker-compose restart neo4j
sleep 5
```

### "No data created"
```bash
# Check org exists
python manage.py shell -c "
from app.masters.models import Organization
print(Organization.objects.filter(id='org-1').exists())
"
```

### "Out of memory"
```bash
# Process in smaller batches
python manage.py backfill_graph --org org-1 --type transaction --limit 5000
```

---

## 🎯 Data Flow

```
PostgreSQL                Neo4j Graph
    ↓                          ↓
   SKU    ──backfill──→   SKU node
   Trans  ──backfill──→   Transaction node
   Loc    ──backfill──→   Location node
   Facility──backfill──→  Facility node
    ↓                          ↓
Knowledge Files ──index──→ KnowledgeItem node
    ↓                          ↓
   (new data synced automatically via Django signals)
```

---

## 📊 Expected Performance

| Operation | Time | Size |
|-----------|------|------|
| Backfill 100 SKUs | < 1 sec | < 100 KB |
| Backfill 1,000 Transactions | 5-30 sec | 1-5 MB |
| Index 10 Knowledge files | < 5 sec | < 1 MB |
| Full setup (100k txns) | 5-15 min | 50-200 MB |

---

## 💡 Pro Tips

1. **Do facilities first** - they're fastest and required by locations
2. **Then locations** - needed for SKUs
3. **Then SKUs** - small dataset
4. **Finally transactions** - largest dataset, can take a while
5. **Use `--limit` for testing** - verify before full backfill
6. **Use `--dry-run` for knowledge** - preview relationships

---

## 🔗 Related Files

- Detailed guide: `GRAPH_INDEXING_COMMANDS.md`
- Implementation guide: `GRAPHRAG_IMPLEMENTATION.md`
- Environment variables: `.env.example.graphrag`
