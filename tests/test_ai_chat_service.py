from __future__ import annotations

from app.ai.chat_service import _parse_response


def test_parse_response_handles_single_json_payload():
    payload = """
    {
      "text": "There have been a total of 12 completed Goods Received Note (GRN) transactions till now.",
      "components": [
        {
          "type": "stat_card",
          "label": "GRNs Total",
          "value": 12,
          "description": "Completed GRN transactions"
        }
      ]
    }
    """

    parsed = _parse_response(payload)

    assert parsed is not None
    assert parsed["text"] == "There have been a total of 12 completed Goods Received Note (GRN) transactions till now."
    assert parsed["components"] == [
        {
            "type": "stat_card",
            "label": "GRNs Total",
            "value": 12,
            "description": "Completed GRN transactions",
        }
    ]


def test_parse_response_handles_duplicated_json_payloads():
    payload = """
    {
      "text": "There have been a total of 12 completed Goods Received Note (GRN) transactions till now.",
      "components": [
        {
          "type": "stat_card",
          "label": "GRNs Total",
          "value": 12,
          "description": "Completed GRN transactions"
        }
      ]
    }
    {
      "text": "There have been a total of 12 completed Goods Received Note (GRN) transactions till now.",
      "components": [
        {
          "type": "stat_card",
          "label": "GRNs Total",
          "value": 12,
          "description": "Completed GRN transactions"
        }
      ]
    }
    """

    parsed = _parse_response(payload)

    assert parsed is not None
    assert parsed["text"] == "There have been a total of 12 completed Goods Received Note (GRN) transactions till now."
    assert parsed["components"] == [
        {
            "type": "stat_card",
            "label": "GRNs Total",
            "value": 12,
            "description": "Completed GRN transactions",
        }
    ]
