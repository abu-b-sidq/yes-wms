# GraphRAG Implementation Guide for YES WMS

## Overview

This document explains how GraphRAG has been implemented in the YES WMS system as a replacement for pgvector-based semantic search.

## What Changed (Executive Summary)

| Aspect | Before (pgvector) | After (GraphRAG) |
|--------|-------------------|------------------|
| **Data Model** | 768-dimensional vectors in PostgreSQL | Knowledge graph with entities and relationships in Neo4j |
| **Retrieval** | Vector similarity search | Cypher queries + relationship traversal |
| **Context** | Isolated text chunks | Connected entity context (multi-hop) |
| **Explainability** | Just scores (0-1 similarity) | Clear path of relationships |
| **Query Type** | "Find similar text" | "Find SKU, follow its transactions, get applicable procedures" |

---

## Architecture

### Components

1. **Neo4j Graph Database** (Docker container `wms-neo4j`)
   - Stores knowledge graph: entities (SKU, Transaction, Location, Facility, etc.) and relationships
   - Exposes Cypher query language for flexible traversal
   - Browser UI at `http://localhost:7474` for exploration

2. **GraphService** (`app/ai/graph_service.py`)
   - Manages node and relationship creation in Neo4j
   - Functions for creating/updating: SKU, Location, Facility, Transaction, KnowledgeItem, Message nodes
   - Reads-only graph search with validation
   - **Used by**: Django signals (auto-triggers on data save)

3. **GraphRetrieval** (`app/ai/graph_retrieval.py`)
   - Converts user queries into Cypher queries
   - Validates Cypher for safety (blocks destructive operations)
   - Formats Cypher results into natural language context for LLM
   - **Used by**: Chat service, MCP tool

4. **Chat Integration** (`app/ai/chat_service.py`)
   - Calls `graph_search()` to prefetch context before LLM
   - Injects formatted context as system message
   - LLM can call `wms_graph_search()` tool for follow-up queries

5. **MCP Tool** (`app/mcp/tools.py` - `wms_graph_search`)
   - Exposes graph search as a tool callable by LLM
   - Returns structured context dict with success status and formatted text

---

## Data Model

### Nodes

Each node has these properties:
- `org_id` - Organization for multi-tenancy (all queries filtered by org)
- `created_at` / `updated_at` - Timestamps

**Node types:**

```
SKU {org_id, code, name, uom, metadata}
Transaction {org_id, id, facility_code, type, status, reference_number, notes}
Location {org_id, code, name, zone_code, capacity}
Facility {org_id, code, name, warehouse_key, address}
KnowledgeItem {org_id, id, title, content, category}
Message {org_id, id, text}
```

### Relationships

```
(SKU)-[:STORED_AT]->(Location)      # Where is this SKU?
(Location)-[:IN_FACILITY]->(Facility)  # Which warehouse?
(Transaction)-[:INVOLVES]->(SKU)    # What does this transaction affect?
(Message)-[:MENTIONS]->(SKU)        # Did we discuss this SKU?
(Message)-[:REFERENCES]->(Transaction)  # Did we discuss this transaction?
(KnowledgeItem)-[:RELATES_TO]->(SKU|Location|Facility|Transaction)  # What procedures apply?
```

---

## How It Works: Step by Step

### Example Query: "Show me what's happening with SKU ABC123"

**Step 1: Prefetch (Chat Service)**
```python
# User sends message
result = graph_search(org_id="org-1", query="Show me what's happening with SKU ABC123")
# Returns: {"success": True, "context": "SKU ABC123: stored at...", "raw_results": [...]}
```

**Step 2: Context Injection**
```
System message: "Graph-based context has been prefetched...

Prefetched graph context:
SKUs:
  - ABC123: Widget (UOM: EA)

Locations:
  - SHELF-A: Main Shelf (Capacity: 100)

Facilities/Warehouses:
  - WH-CENTRAL: Central Warehouse

Transactions:
  - TXN-001: INBOUND (COMPLETED) - Ref: PO-123

Related Procedures/Knowledge:
  - [procedure] Warehouse WH-CENTRAL High-Value SKU Handling
"
```

**Step 3: LLM Response**
```
Claude: "SKU ABC123 is currently on SHELF-A in warehouse WH-CENTRAL. 
It has 2 recent transactions (inbound and outbound). Since it's in WH-CENTRAL, 
the 'High-Value SKU Handling' procedure applies..."
```

**Optional Step 4: Follow-up Retrieval**
If Claude needs more details, it calls `wms_graph_search` tool to explore further:
```
LLM: Call wms_graph_search with query "Tell me about all transactions in WH-CENTRAL"
Result: Returns all transactions stored in that warehouse
```

---

## Implementation Details

### Neo4j Connection

Set environment variables in `.env`:
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

The `GraphService` singleton automatically connects on first use:
```python
service = GraphService.get_instance()  # Connects if needed
service.create_sku_node(...)
```

### Signal-Driven Data Sync

When a SKU is created, Django signal triggers Neo4j node creation:
```python
# In masters/signals.py
@receiver(post_save, sender=SKU)
def create_sku_graph_node(sender, instance, **kwargs):
    service = GraphService.get_instance()
    service.create_sku_node(...)
```

**Data flows automatically:**
- Save SKU to PostgreSQL → Signal fires → Node created in Neo4j
- Save Transaction → Graph node created
- Save Location/Facility → Graph nodes created

### Cypher Query Generation

The `GraphRetrieval` class has pattern-based query generation:

```python
retrieval = get_graph_retrieval()
result = retrieval.graph_search(org_id="org-1", query="what's in warehouse X?")
```

Pattern matching extracts intent:
- "SKU <code>" → Returns SKU + all its relationships
- "warehouse <name>" → Returns facility + stored SKUs + locations
- "procedures" → Returns relevant KnowledgeItems

### Safety & Validation

All Cypher queries are validated before execution:
```python
is_safe, error = retrieval.validate_cypher_safety(cypher_query)
# Blocks: DELETE, CREATE (outside MERGE), DROP, ALTER, REMOVE, FOREACH, CALL
# Allows: MATCH, WHERE, OPTIONAL MATCH, RETURN, WITH, LIMIT, ORDER
```

Execution happens in read-only mode:
```python
result = service.execute_graph_search(org_id, validated_query)
```

---

## Usage: For Developers

### Add New Node Type

1. Add node creation function to `GraphService`:
```python
def create_supplier_node(self, org_id, supplier_id, name):
    query = """
    MERGE (s:Supplier {org_id: $org_id, id: $id})
    SET s.name = $name, s.updated_at = timestamp()
    """
    self._execute_query(query, {
        "org_id": org_id,
        "id": supplier_id,
        "name": name,
    })
```

2. Add signal in appropriate `models.py`:
```python
@receiver(post_save, sender=Supplier)
def create_supplier_graph_node(sender, instance, **kwargs):
    def _run():
        service = GraphService.get_instance()
        service.create_supplier_node(str(instance.org_id), str(instance.id), instance.name)
    threading.Thread(target=_run, daemon=True).start()
```

3. Data syncs automatically from then on.

### Add New Relationship Type

Add function to `GraphService`:
```python
def create_supplied_by_relationship(self, org_id, sku_code, supplier_id):
    query = """
    MATCH (s:SKU {org_id: $org_id, code: $sku_code})
    MATCH (supplier:Supplier {org_id: $org_id, id: $supplier_id})
    MERGE (s)-[:SUPPLIED_BY]->(supplier)
    """
    self._execute_query(query, {
        "org_id": org_id,
        "sku_code": sku_code,
        "supplier_id": supplier_id,
    })
```

Call when creating the relationship (e.g., after inventory receipt):
```python
service.create_supplied_by_relationship(org_id, sku_code, supplier_id)
```

### Add Custom Cypher Pattern

Edit `GraphRetrieval._generate_cypher_for_query()`:
```python
# Pattern: "supplied by <supplier>"
supplier_match = re.search(r"supplied by\s+([\w\-]+)", query_lower)
if supplier_match:
    supplier_name = supplier_match.group(1)
    return f"""
    MATCH (s:SKU {{org_id: $org_id}})-[:SUPPLIED_BY]->(sup:Supplier {{name: '{supplier_name}'}})
    RETURN s, sup
    LIMIT 50
    """
```

---

## Migration & Backfilling

### Bootstrap Existing Data

When you first set up Neo4j, backfill existing data:

```bash
# Backfill all data types
python manage.py backfill_graph --org org-1

# Backfill specific type (useful for testing)
python manage.py backfill_graph --org org-1 --type sku
python manage.py backfill_graph --org org-1 --type transaction

# Limit records (for testing)
python manage.py backfill_graph --org org-1 --type sku --limit 100
```

This reads from PostgreSQL and creates all nodes + relationships in Neo4j.

### Ongoing Sync

Going forward, signals auto-sync:
- Every new SKU → Neo4j node created
- Every new Transaction → Neo4j node created
- Every new Location/Facility → Neo4j node created

### Verify in Neo4j Browser

1. Open `http://localhost:7474`
2. Login with `neo4j / password`
3. Run queries:
```cypher
// Count SKU nodes
MATCH (s:SKU {org_id: "org-1"}) RETURN count(s)

// Find SKU with all its relationships
MATCH (s:SKU {org_id: "org-1", code: "ABC123"})
OPTIONAL MATCH (s)-[:STORED_AT]->(l:Location)-[:IN_FACILITY]->(f:Facility)
OPTIONAL MATCH (s)-[:INVOLVED_IN]->(t:Transaction)
RETURN s, l, f, t

// Find what's in a warehouse
MATCH (f:Facility {org_id: "org-1", code: "WH-A"})
OPTIONAL MATCH (l:Location)-[:IN_FACILITY]->(f)
OPTIONAL MATCH (s:SKU)-[:STORED_AT]->(l)
RETURN f, l, s
```

---

## Testing

### Run Unit Tests

```bash
pytest app/ai/tests/test_graph_service.py -v
```

### Test in Chat

1. Start the app: `docker-compose up wms-middleware`
2. Open chat interface
3. Send message: "Show me SKU ABC123"
4. Verify prefetched context appears
5. Verify Claude can reference the graph data

### Test MCP Tool

In chat, manually call:
```
Call wms_graph_search with org_id="org-1", query="what's in warehouse X?"
```

---

## Performance Considerations

### Neo4j Server Requirements

**Community Edition** (what we're using):
- Memory: ~1GB heap (default)
- Storage: Varies by data size
- Performance: Fine for thousands of nodes/relationships

**For large deployments:**
- Consider Neo4j Enterprise
- Increase heap: `NEO4J_HEAP_MEMORY=4g` in docker-compose
- Add indexes: Create indexes on frequently searched properties

### Query Optimization

Use proper indexes:
```cypher
CREATE INDEX ON :SKU(org_id, code)
CREATE INDEX ON :Facility(org_id, code)
CREATE INDEX ON :Transaction(org_id, id)
```

Limit result sets:
```cypher
MATCH (...) RETURN ... LIMIT 50  # Always use LIMIT
```

---

## Troubleshooting

### Issue: "Neo4j connection failed"

**Check:**
```bash
docker-compose logs neo4j  # Check Neo4j startup
docker-compose ps          # Verify container is running
curl bolt://localhost:7687  # Test connectivity
```

**Fix:**
```bash
docker-compose up neo4j -d  # Restart Neo4j
```

### Issue: "No results in graph search"

**Check:**
1. Did you run `backfill_graph`?
2. Is org_id correct?
3. Query in browser to debug:
   ```cypher
   MATCH (n {org_id: "your-org-id"}) RETURN count(n)
   ```

### Issue: "Cypher query failed validation"

**Check:**
- Query contains only read operations (MATCH, WHERE, RETURN, WITH)
- No destructive keywords (DELETE, CREATE, DROP, REMOVE)
- Syntax is valid

---

## Next Steps

### Future Enhancements

1. **Full-text search fallback**: If pattern matching fails, do a full-text search
2. **LLM-generated Cypher**: Let Claude generate more complex Cypher queries (with validation)
3. **Relationship templates**: Pre-define common traversals for better performance
4. **Analytics**: Track which queries are run most; optimize those patterns
5. **Knowledge import**: Auto-extract relationships from knowledge base documents

### Monitoring

Track graph performance:
```cypher
PROFILE MATCH (s:SKU {org_id: "org-1"}) RETURN s
```

---

## References

- **Neo4j Docs**: https://neo4j.com/docs/
- **GraphRAG Concept**: https://neo4j.com/blog/genai/what-is-graphrag/
- **Cypher Query Language**: https://neo4j.com/docs/cypher-manual/current/
- **Neo4j Python Driver**: https://neo4j.com/docs/python-manual/current/
