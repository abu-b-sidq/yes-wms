"""Tests for Neo4j graph service."""
import pytest
from unittest.mock import patch, MagicMock

from app.ai.graph_service import GraphService
from app.ai.graph_retrieval import GraphRetrieval


@pytest.mark.asyncio
class TestGraphService:
    """Test graph service functionality."""

    def test_create_sku_node(self):
        """Test creating a SKU node."""
        service = GraphService.get_instance()

        # Mock the driver
        with patch.object(service, '_execute_query') as mock_query:
            mock_query.return_value = []

            result = service.create_sku_node(
                org_id="test-org",
                sku_code="ABC123",
                sku_name="Test Product",
                unit_of_measure="EA",
                metadata={"color": "red"},
            )

            assert result is True
            mock_query.assert_called_once()

    def test_create_transaction_node(self):
        """Test creating a Transaction node."""
        service = GraphService.get_instance()

        with patch.object(service, '_execute_query') as mock_query:
            mock_query.return_value = []

            result = service.create_transaction_node(
                org_id="test-org",
                transaction_id="TXN-001",
                facility_code="WH-A",
                transaction_type="INBOUND",
                status="COMPLETED",
                reference_number="PO-123",
                notes="Test transaction",
            )

            assert result is True

    def test_validate_cypher_query(self):
        """Test Cypher query validation."""
        retrieval = GraphRetrieval()

        # Valid read query
        valid_query = "MATCH (s:SKU) RETURN s"
        is_safe, error = retrieval.validate_cypher_safety(valid_query)
        assert is_safe is True
        assert error is None

        # Invalid destructive query
        invalid_query = "MATCH (s:SKU) DELETE s"
        is_safe, error = retrieval.validate_cypher_safety(invalid_query)
        assert is_safe is False
        assert "destructive" in error.lower()

    def test_format_cypher_results(self):
        """Test formatting Cypher results as context."""
        retrieval = GraphRetrieval()

        mock_results = [
            {
                "s": {
                    "properties": {"code": "ABC123", "name": "Test SKU", "uom": "EA"}
                }
            }
        ]

        context = retrieval.format_cypher_results_as_context(mock_results)
        assert "ABC123" in context
        assert "Test SKU" in context
