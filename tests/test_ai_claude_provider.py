from app.ai.llm_providers import _to_anthropic_messages


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
