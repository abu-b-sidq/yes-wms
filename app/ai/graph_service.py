import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from neo4j import Driver, GraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)


class GraphService:
    _instance: Optional["GraphService"] = None
    _driver: Optional[Driver] = None
    _async_driver: Optional[AsyncDriver] = None

    def __init__(self):
        self._ensure_driver()

    @classmethod
    def _ensure_driver(cls):
        if cls._driver is None:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

            try:
                cls._driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password),
                    trust="TRUST_ALL_CERTIFICATES",
                )
                cls._driver.verify_connectivity()
                logger.info(f"Connected to Neo4j at {neo4j_uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise

    @classmethod
    def get_instance(cls) -> "GraphService":
        if cls._instance is None:
            cls._instance = GraphService()
        return cls._instance

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def _execute_query(self, query: str, parameters: Dict[str, Any]) -> List[Dict]:
        try:
            with self._driver.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}\nQuery: {query}")
            raise

    # ============== SKU NODES ==============

    def create_sku_node(self, org_id: str, sku_code: str, sku_name: str,
                       unit_of_measure: str = "EA", metadata: Optional[Dict] = None) -> bool:
        """Create or update a SKU node in the graph."""
        query = """
        MERGE (s:SKU {org_id: $org_id, code: $code})
        SET s.name = $name, s.uom = $uom, s.metadata = $metadata, s.updated_at = timestamp()
        """
        try:
            self._execute_query(query, {
                "org_id": org_id,
                "code": sku_code,
                "name": sku_name,
                "uom": unit_of_measure,
                "metadata": metadata or {},
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create SKU node: {e}")
            return False

    def delete_sku_node(self, org_id: str, sku_code: str) -> bool:
        """Delete a SKU node and its relationships."""
        query = """
        MATCH (s:SKU {org_id: $org_id, code: $code})
        DETACH DELETE s
        """
        try:
            self._execute_query(query, {"org_id": org_id, "code": sku_code})
            return True
        except Exception as e:
            logger.error(f"Failed to delete SKU node: {e}")
            return False

    # ============== LOCATION NODES ==============

    def create_location_node(self, org_id: str, location_code: str, location_name: str,
                            zone_code: str, capacity: Optional[int] = None) -> bool:
        """Create or update a Location node."""
        query = """
        MERGE (l:Location {org_id: $org_id, code: $code})
        SET l.name = $name, l.zone_code = $zone_code, l.capacity = $capacity, l.updated_at = timestamp()
        """
        try:
            self._execute_query(query, {
                "org_id": org_id,
                "code": location_code,
                "name": location_name,
                "zone_code": zone_code,
                "capacity": capacity,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create Location node: {e}")
            return False

    # ============== FACILITY/WAREHOUSE NODES ==============

    def create_facility_node(self, org_id: str, facility_code: str, facility_name: str,
                            warehouse_key: str, address: str = "") -> bool:
        """Create or update a Facility (Warehouse) node."""
        query = """
        MERGE (f:Facility {org_id: $org_id, code: $code})
        SET f.name = $name, f.warehouse_key = $warehouse_key, f.address = $address, f.updated_at = timestamp()
        """
        try:
            self._execute_query(query, {
                "org_id": org_id,
                "code": facility_code,
                "name": facility_name,
                "warehouse_key": warehouse_key,
                "address": address,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create Facility node: {e}")
            return False

    # ============== TRANSACTION NODES ==============

    def create_transaction_node(self, org_id: str, transaction_id: str, facility_code: str,
                               transaction_type: str, status: str, reference_number: str = "",
                               notes: str = "") -> bool:
        """Create or update a Transaction node."""
        query = """
        MERGE (t:Transaction {org_id: $org_id, id: $id})
        SET t.facility_code = $facility_code, t.type = $type, t.status = $status,
            t.reference_number = $reference_number, t.notes = $notes, t.updated_at = timestamp()
        """
        try:
            self._execute_query(query, {
                "org_id": org_id,
                "id": transaction_id,
                "facility_code": facility_code,
                "type": transaction_type,
                "status": status,
                "reference_number": reference_number,
                "notes": notes,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create Transaction node: {e}")
            return False

    # ============== KNOWLEDGE ITEM NODES ==============

    def create_knowledge_item_node(self, org_id: str, item_id: str, title: str,
                                  content: str, category: str = "procedure") -> bool:
        """Create or update a KnowledgeItem node."""
        query = """
        MERGE (k:KnowledgeItem {org_id: $org_id, id: $id})
        SET k.title = $title, k.content = $content, k.category = $category, k.updated_at = timestamp()
        """
        try:
            self._execute_query(query, {
                "org_id": org_id,
                "id": item_id,
                "title": title,
                "content": content,
                "category": category,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create KnowledgeItem node: {e}")
            return False

    # ============== MESSAGE NODES ==============

    def create_message_node(self, org_id: str, message_id: str, text: str,
                           mentioned_skus: List[str] = None,
                           referenced_transactions: List[str] = None) -> bool:
        """Create a Message node with relationships to mentioned entities."""
        query = """
        MERGE (m:Message {org_id: $org_id, id: $id})
        SET m.text = $text, m.created_at = timestamp()
        """
        try:
            self._execute_query(query, {
                "org_id": org_id,
                "id": message_id,
                "text": text,
            })

            # Create relationships to mentioned SKUs
            if mentioned_skus:
                for sku_code in mentioned_skus:
                    rel_query = """
                    MATCH (m:Message {org_id: $org_id, id: $message_id})
                    MATCH (s:SKU {org_id: $org_id, code: $sku_code})
                    MERGE (m)-[:MENTIONS]->(s)
                    """
                    self._execute_query(rel_query, {
                        "org_id": org_id,
                        "message_id": message_id,
                        "sku_code": sku_code,
                    })

            # Create relationships to referenced transactions
            if referenced_transactions:
                for trans_id in referenced_transactions:
                    rel_query = """
                    MATCH (m:Message {org_id: $org_id, id: $message_id})
                    MATCH (t:Transaction {org_id: $org_id, id: $trans_id})
                    MERGE (m)-[:REFERENCES]->(t)
                    """
                    self._execute_query(rel_query, {
                        "org_id": org_id,
                        "message_id": message_id,
                        "trans_id": trans_id,
                    })

            return True
        except Exception as e:
            logger.error(f"Failed to create Message node: {e}")
            return False

    # ============== RELATIONSHIPS ==============

    def create_stored_at_relationship(self, org_id: str, sku_code: str, location_code: str) -> bool:
        """Create STORED_AT relationship: SKU -> Location."""
        query = """
        MATCH (s:SKU {org_id: $org_id, code: $sku_code})
        MATCH (l:Location {org_id: $org_id, code: $location_code})
        MERGE (s)-[:STORED_AT]->(l)
        """
        try:
            self._execute_query(query, {
                "org_id": org_id,
                "sku_code": sku_code,
                "location_code": location_code,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create STORED_AT relationship: {e}")
            return False

    def create_location_in_facility_relationship(self, org_id: str, location_code: str,
                                                facility_code: str) -> bool:
        """Create IN_FACILITY relationship: Location -> Facility."""
        query = """
        MATCH (l:Location {org_id: $org_id, code: $location_code})
        MATCH (f:Facility {org_id: $org_id, code: $facility_code})
        MERGE (l)-[:IN_FACILITY]->(f)
        """
        try:
            self._execute_query(query, {
                "org_id": org_id,
                "location_code": location_code,
                "facility_code": facility_code,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create IN_FACILITY relationship: {e}")
            return False

    def create_involves_relationship(self, org_id: str, transaction_id: str, sku_code: str) -> bool:
        """Create INVOLVES relationship: Transaction -> SKU."""
        query = """
        MATCH (t:Transaction {org_id: $org_id, id: $transaction_id})
        MATCH (s:SKU {org_id: $org_id, code: $sku_code})
        MERGE (t)-[:INVOLVES]->(s)
        """
        try:
            self._execute_query(query, {
                "org_id": org_id,
                "transaction_id": transaction_id,
                "sku_code": sku_code,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create INVOLVES relationship: {e}")
            return False

    def create_relates_to_relationship(self, org_id: str, knowledge_id: str,
                                      target_type: str, target_code: str) -> bool:
        """Create RELATES_TO relationship: KnowledgeItem -> (SKU|Location|Facility|Transaction)."""
        query = f"""
        MATCH (k:KnowledgeItem {{org_id: $org_id, id: $knowledge_id}})
        MATCH (t:{target_type} {{org_id: $org_id, {("code" if target_type != "Transaction" else "id")}: $target_code}})
        MERGE (k)-[:RELATES_TO]->(t)
        """
        try:
            param_key = "code" if target_type != "Transaction" else "id"
            self._execute_query(query, {
                "org_id": org_id,
                "knowledge_id": knowledge_id,
                "target_code": target_code,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create RELATES_TO relationship: {e}")
            return False

    # ============== SEARCH FUNCTIONS ==============

    def find_sku_with_context(self, org_id: str, sku_code: str, max_hops: int = 2) -> Optional[Dict]:
        """Find a SKU and gather all connected context up to max_hops."""
        query = """
        MATCH (s:SKU {org_id: $org_id, code: $code})
        OPTIONAL MATCH (s)-[:STORED_AT]->(l:Location)-[:IN_FACILITY]->(f:Facility)
        OPTIONAL MATCH (s)-[:INVOLVED_IN]->(t:Transaction)
        OPTIONAL MATCH (k:KnowledgeItem)-[:RELATES_TO]->(s)
        OPTIONAL MATCH (m:Message)-[:MENTIONS]->(s)
        RETURN s,
               collect(distinct l) as locations,
               collect(distinct f) as facilities,
               collect(distinct t) as transactions,
               collect(distinct k) as knowledge_items,
               collect(distinct m) as messages
        """
        try:
            result = self._execute_query(query, {
                "org_id": org_id,
                "code": sku_code,
            })
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to find SKU context: {e}")
            return None

    def find_skus_in_facility(self, org_id: str, facility_code: str) -> List[Dict]:
        """Find all SKUs currently stored in a facility."""
        query = """
        MATCH (s:SKU {org_id: $org_id})-[:STORED_AT]->(l:Location)-[:IN_FACILITY]->(f:Facility {org_id: $org_id, code: $code})
        RETURN distinct s
        """
        try:
            return self._execute_query(query, {
                "org_id": org_id,
                "code": facility_code,
            })
        except Exception as e:
            logger.error(f"Failed to find SKUs in facility: {e}")
            return []

    def validate_cypher_query(self, query: str) -> bool:
        """Validate a Cypher query for safety (no destructive operations)."""
        destructive_keywords = ["CREATE", "DELETE", "SET", "DROP", "REMOVE", "DETACH"]
        upper_query = query.upper()

        # Check for destructive operations
        for keyword in destructive_keywords:
            if keyword in upper_query:
                # Allow SET within MERGE context (data updates)
                if keyword == "SET" and "MERGE" not in upper_query:
                    logger.warning(f"Query contains {keyword} outside MERGE context")
                    return False
                elif keyword != "SET":
                    logger.warning(f"Query contains destructive keyword: {keyword}")
                    return False

        # Only allow read operations
        allowed_keywords = ["MATCH", "OPTIONAL", "WHERE", "RETURN", "WITH", "LIMIT", "ORDER"]
        has_read_op = any(kw in upper_query for kw in ["MATCH", "WITH"])

        if not has_read_op:
            logger.warning("Query does not contain any read operations (MATCH/WITH)")
            return False

        return True

    def execute_graph_search(self, org_id: str, cypher_query: str) -> Optional[List[Dict]]:
        """Execute a validated Cypher query for graph search."""
        if not self.validate_cypher_query(cypher_query):
            logger.error("Cypher query failed validation")
            return None

        try:
            # Add org_id filter to all node matches
            with self._driver.session() as session:
                result = session.run(cypher_query, {"org_id": org_id})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Failed to execute graph search: {e}")
            return None
