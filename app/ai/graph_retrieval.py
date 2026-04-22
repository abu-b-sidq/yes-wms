import json
import logging
import re
from typing import Optional, Dict, List, Any, Tuple

from app.ai.graph_service import GraphService

logger = logging.getLogger(__name__)


class GraphRetrieval:
    """Handles graph-based RAG retrieval using Neo4j and LLM-generated Cypher queries."""

    def __init__(self):
        self.graph_service = GraphService.get_instance()

    # ============== CYPHER GENERATION & VALIDATION ==============

    def validate_cypher_safety(self, cypher_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Cypher query for safety.
        Returns: (is_valid, error_message)
        """
        # Destructive keywords to block
        destructive_patterns = [
            r"\bDELETE\b",
            r"\bCREATE\b(?!.*MERGE)",
            r"\bDROP\b",
            r"\bALTER\b",
            r"\bREMOVE\b",
            r"\bFOREACH\b",
            r"\bCALL\b",
        ]

        upper_query = cypher_query.upper()

        for pattern in destructive_patterns:
            if re.search(pattern, upper_query):
                return False, f"Query contains destructive operation: {pattern}"

        # Ensure it's a read-only query
        has_match = "MATCH" in upper_query or "WITH" in upper_query
        if not has_match:
            return False, "Query must contain MATCH or WITH clause"

        return True, None

    def extract_entity_references(self, cypher_result: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract and categorize entities from Cypher result.
        Returns dict with keys: skus, transactions, locations, facilities, knowledge_items, messages
        """
        extracted = {
            "skus": [],
            "transactions": [],
            "locations": [],
            "facilities": [],
            "knowledge_items": [],
            "messages": [],
        }

        for record in cypher_result:
            for key, value in record.items():
                if value is None:
                    continue

                # Handle single node
                if isinstance(value, dict) and "labels" in str(value):
                    extracted = self._categorize_node(value, extracted)

                # Handle lists of nodes
                elif isinstance(value, list):
                    for item in value:
                        if item:
                            extracted = self._categorize_node(item, extracted)

        return extracted

    def _categorize_node(self, node: Dict, extracted: Dict) -> Dict:
        """Helper to categorize a single node."""
        try:
            node_str = str(node)

            if "SKU" in node_str:
                extracted["skus"].append(node)
            elif "Transaction" in node_str:
                extracted["transactions"].append(node)
            elif "Location" in node_str:
                extracted["locations"].append(node)
            elif "Facility" in node_str:
                extracted["facilities"].append(node)
            elif "KnowledgeItem" in node_str:
                extracted["knowledge_items"].append(node)
            elif "Message" in node_str:
                extracted["messages"].append(node)
        except Exception as e:
            logger.debug(f"Error categorizing node: {e}")

        return extracted

    # ============== RESULT FORMATTING ==============

    def format_cypher_results_as_context(self, cypher_result: List[Dict]) -> str:
        """
        Convert raw Cypher results into natural language context for LLM.
        """
        if not cypher_result:
            return "No results found in graph."

        extracted = self.extract_entity_references(cypher_result)
        context_parts = []

        # Format SKUs
        if extracted["skus"]:
            context_parts.append(self._format_skus(extracted["skus"]))

        # Format Locations
        if extracted["locations"]:
            context_parts.append(self._format_locations(extracted["locations"]))

        # Format Facilities
        if extracted["facilities"]:
            context_parts.append(self._format_facilities(extracted["facilities"]))

        # Format Transactions
        if extracted["transactions"]:
            context_parts.append(self._format_transactions(extracted["transactions"]))

        # Format Knowledge Items
        if extracted["knowledge_items"]:
            context_parts.append(self._format_knowledge_items(extracted["knowledge_items"]))

        # Format Messages
        if extracted["messages"]:
            context_parts.append(self._format_messages(extracted["messages"]))

        return "\n\n".join(context_parts)

    def _format_skus(self, skus: List[Dict]) -> str:
        """Format SKU nodes."""
        lines = ["**SKUs:**"]
        for sku in skus:
            try:
                properties = sku.get("properties", sku)
                code = properties.get("code", "Unknown")
                name = properties.get("name", "")
                uom = properties.get("uom", "EA")
                lines.append(f"  - {code}: {name} (UOM: {uom})")
            except Exception as e:
                logger.debug(f"Error formatting SKU: {e}")

        return "\n".join(lines)

    def _format_locations(self, locations: List[Dict]) -> str:
        """Format Location nodes."""
        lines = ["**Locations:**"]
        for location in locations:
            try:
                properties = location.get("properties", location)
                code = properties.get("code", "Unknown")
                name = properties.get("name", "")
                capacity = properties.get("capacity", "N/A")
                lines.append(f"  - {code}: {name} (Capacity: {capacity})")
            except Exception as e:
                logger.debug(f"Error formatting Location: {e}")

        return "\n".join(lines)

    def _format_facilities(self, facilities: List[Dict]) -> str:
        """Format Facility nodes."""
        lines = ["**Facilities/Warehouses:**"]
        for facility in facilities:
            try:
                properties = facility.get("properties", facility)
                code = properties.get("code", "Unknown")
                name = properties.get("name", "")
                address = properties.get("address", "")
                lines.append(f"  - {code}: {name} ({address})" if address else f"  - {code}: {name}")
            except Exception as e:
                logger.debug(f"Error formatting Facility: {e}")

        return "\n".join(lines)

    def _format_transactions(self, transactions: List[Dict]) -> str:
        """Format Transaction nodes."""
        lines = ["**Transactions:**"]
        for transaction in transactions:
            try:
                properties = transaction.get("properties", transaction)
                trans_id = properties.get("id", "Unknown")
                trans_type = properties.get("type", "")
                status = properties.get("status", "")
                ref_num = properties.get("reference_number", "")
                notes = properties.get("notes", "")

                detail = f"{trans_type} ({status})"
                if ref_num:
                    detail += f" - Ref: {ref_num}"
                if notes:
                    detail += f" - Notes: {notes[:100]}"  # Truncate long notes

                lines.append(f"  - {trans_id}: {detail}")
            except Exception as e:
                logger.debug(f"Error formatting Transaction: {e}")

        return "\n".join(lines)

    def _format_knowledge_items(self, knowledge_items: List[Dict]) -> str:
        """Format KnowledgeItem nodes."""
        lines = ["**Related Procedures/Knowledge:**"]
        for item in knowledge_items:
            try:
                properties = item.get("properties", item)
                title = properties.get("title", "Unknown")
                category = properties.get("category", "procedure")
                lines.append(f"  - [{category}] {title}")
            except Exception as e:
                logger.debug(f"Error formatting KnowledgeItem: {e}")

        return "\n".join(lines)

    def _format_messages(self, messages: List[Dict]) -> str:
        """Format Message nodes."""
        lines = ["**Related Chat Messages:**"]
        for message in messages:
            try:
                properties = message.get("properties", message)
                text = properties.get("text", "")[:150]  # Truncate
                lines.append(f"  - {text}..." if len(properties.get("text", "")) > 150 else f"  - {text}")
            except Exception as e:
                logger.debug(f"Error formatting Message: {e}")

        return "\n".join(lines)

    # ============== MAIN RETRIEVAL FUNCTION ==============

    def graph_search(self, org_id: str, query: str, max_results: int = 50) -> Dict[str, Any]:
        """
        Main entry point for graph-based RAG retrieval.

        Args:
            org_id: Organization ID for isolation
            query: User query (will be processed to understand intent)
            max_results: Max results to return

        Returns:
            {
                "success": bool,
                "context": str,  # Formatted context for LLM
                "raw_results": List[Dict],  # Raw Cypher results
                "error": Optional[str],
            }
        """
        try:
            # Generate Cypher query based on user query intent
            cypher_query = self._generate_cypher_for_query(query, org_id)

            if not cypher_query:
                return {
                    "success": False,
                    "context": "Could not parse query intent for graph search.",
                    "raw_results": [],
                    "error": "Query generation failed",
                }

            # Validate safety
            is_safe, error_msg = self.validate_cypher_safety(cypher_query)
            if not is_safe:
                logger.warning(f"Unsafe Cypher query blocked: {error_msg}")
                return {
                    "success": False,
                    "context": "Invalid query for graph retrieval.",
                    "raw_results": [],
                    "error": error_msg,
                }

            # Execute query
            results = self.graph_service.execute_graph_search(org_id, cypher_query)

            if results is None:
                return {
                    "success": False,
                    "context": "Error executing graph search.",
                    "raw_results": [],
                    "error": "Cypher execution failed",
                }

            # Format results
            context = self.format_cypher_results_as_context(results)

            return {
                "success": True,
                "context": context,
                "raw_results": results,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Graph search error: {e}")
            return {
                "success": False,
                "context": "Error during graph search.",
                "raw_results": [],
                "error": str(e),
            }

    def _generate_cypher_for_query(self, query: str, org_id: str) -> Optional[str]:
        """
        Generate a Cypher query from a user query.
        This is a starting point with common patterns; can be enhanced with LLM.
        """
        query_lower = query.lower()

        # Pattern 1: "Show me SKU <code>"
        sku_match = re.search(r"(?:sku|product|item)[\s:]*([A-Z0-9\-]+)", query_lower, re.IGNORECASE)
        if sku_match:
            sku_code = sku_match.group(1)
            return f"""
            MATCH (s:SKU {{org_id: $org_id, code: '{sku_code}'}})
            OPTIONAL MATCH (s)-[:STORED_AT]->(l:Location)-[:IN_FACILITY]->(f:Facility)
            OPTIONAL MATCH (s)-[:INVOLVED_IN]->(t:Transaction)
            OPTIONAL MATCH (k:KnowledgeItem)-[:RELATES_TO]->(s)
            RETURN s, l, f, t, k
            LIMIT 50
            """

        # Pattern 2: "What's in warehouse <name>"
        warehouse_match = re.search(r"warehouse[\s:]*([\w\-]+)", query_lower, re.IGNORECASE)
        if warehouse_match:
            warehouse_name = warehouse_match.group(1)
            return f"""
            MATCH (f:Facility {{org_id: $org_id, name: '{warehouse_name}'}})
            OPTIONAL MATCH (l:Location)-[:IN_FACILITY]->(f)
            OPTIONAL MATCH (s:SKU)-[:STORED_AT]->(l)
            RETURN f, l, s
            LIMIT 50
            """

        # Pattern 3: "Show transactions" - most recent
        if "transaction" in query_lower:
            return f"""
            MATCH (t:Transaction {{org_id: $org_id}})
            RETURN t
            ORDER BY t.updated_at DESC
            LIMIT 20
            """

        # Pattern 4: "What procedures apply to <location>"
        location_match = re.search(r"(?:location|zone)[\s:]*([\w\-]+)", query_lower, re.IGNORECASE)
        if location_match:
            location_code = location_match.group(1)
            return f"""
            MATCH (l:Location {{org_id: $org_id, code: '{location_code}'}})
            OPTIONAL MATCH (k:KnowledgeItem)-[:RELATES_TO]->(l)
            RETURN l, k
            LIMIT 50
            """

        # Fallback: Generic search across all entities
        return f"""
        MATCH (n {{org_id: $org_id}})
        WHERE n:SKU OR n:Transaction OR n:Location OR n:Facility OR n:KnowledgeItem
        RETURN n
        LIMIT 20
        """


# Singleton instance
_retrieval_instance: Optional[GraphRetrieval] = None


def get_graph_retrieval() -> GraphRetrieval:
    """Get singleton instance of GraphRetrieval."""
    global _retrieval_instance
    if _retrieval_instance is None:
        _retrieval_instance = GraphRetrieval()
    return _retrieval_instance
