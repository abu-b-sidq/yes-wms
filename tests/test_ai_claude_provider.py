import logging

from app.ai.llm_providers import _log_prompt_request, _to_anthropic_messages


def test_to_anthropic_messages_converts_tool_calls_and_results():
    system_text, anthropic_messages = _to_anthropic_messages([
        {"role": "system", "content": "System instructions"},
        {"role": "user", "content": "Show my inventory"},
        {
            "role": "assistant",
            "content": "Let me check that.",
            "tool_calls": [
                {
                    "id": "toolu_123",
                    "type": "function",
                    "function": {
                        "name": "wms_list_inventory",
                        "arguments": '{"limit": 5}',
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "toolu_123",
            "content": '{"rows": []}',
        },
    ])

    assert system_text == "System instructions"
    assert anthropic_messages == [
        {"role": "user", "content": "Show my inventory"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Let me check that."},
                {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "wms_list_inventory",
                    "input": {"limit": 5},
                },
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_123",
                    "content": '{"rows": []}',
                }
            ],
        },
    ]


def test_to_anthropic_messages_groups_consecutive_tool_results():
    _, anthropic_messages = _to_anthropic_messages([
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "toolu_1",
                    "type": "function",
                    "function": {
                        "name": "tool_one",
                        "arguments": "{}",
                    },
                },
                {
                    "id": "toolu_2",
                    "type": "function",
                    "function": {
                        "name": "tool_two",
                        "arguments": "{}",
                    },
                },
            ],
        },
        {"role": "tool", "tool_call_id": "toolu_1", "content": '{"ok": true}'},
        {"role": "tool", "tool_call_id": "toolu_2", "content": '{"ok": true}'},
    ])

    assert anthropic_messages == [
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "toolu_1", "name": "tool_one", "input": {}},
                {"type": "tool_use", "id": "toolu_2", "name": "tool_two", "input": {}},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "toolu_1", "content": '{"ok": true}'},
                {"type": "tool_result", "tool_use_id": "toolu_2", "content": '{"ok": true}'},
            ],
        },
    ]


def test_log_prompt_request_emits_llm_prompt_event(caplog, monkeypatch):
    app_logger = logging.getLogger("app")
    ai_logger = logging.getLogger("app.ai")
    prompt_logger = logging.getLogger("app.ai.llm_prompts")
    monkeypatch.setattr(app_logger, "handlers", [])
    monkeypatch.setattr(app_logger, "propagate", True)
    monkeypatch.setattr(ai_logger, "handlers", [])
    monkeypatch.setattr(ai_logger, "propagate", True)
    monkeypatch.setattr(prompt_logger, "handlers", [])
    monkeypatch.setattr(prompt_logger, "propagate", True)
    caplog.set_level(logging.INFO, logger="app.ai.llm_prompts")

    _log_prompt_request(
        provider_name="openai",
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "System instructions"},
            {"role": "user", "content": "Where is pallet P-100?"},
        ],
        tools=[
            {
                "type": "function",
                "function": {"name": "wms_lookup_pallet"},
            }
        ],
    )

    records = [
        record
        for record in caplog.records
        if record.name == "app.ai.llm_prompts" and getattr(record, "event_name", None) == "ai.prompt"
    ]
    assert records

    event_data = records[-1].event_data
    assert event_data["provider"] == "openai"
    assert event_data["model"] == "gpt-4o-mini"
    assert event_data["message_count"] == 2
    assert event_data["tool_names"] == ["wms_lookup_pallet"]
    assert event_data["messages"][1]["content"] == "Where is pallet P-100?"
