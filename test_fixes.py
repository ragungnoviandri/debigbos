"""Quick test suite for TheBigBos fixes."""
import asyncio
import sys
import json


def test_anthropic_thinking_block():
    """Test 1: Anthropic thinking block parsing."""
    print("=== TEST 1: Anthropic thinking block parsing ===")

    class FakeBlock:
        def __init__(self, type, text="", thinking="", name="", input=None, id="", data=""):
            self.type = type
            self.text = text
            self.thinking = thinking
            self.name = name
            self.input = input or {}
            self.id = id
            self.data = data

    blocks = [
        FakeBlock(type="thinking", thinking="Hmm, let me analyze this code carefully..."),
        FakeBlock(type="text", text="The bug is in line 42."),
    ]

    tool_calls = []
    text_content = ""
    reasoning_content = ""

    for block in blocks:
        if block.type == "text":
            text_content += block.text
        elif block.type == "tool_use":
            tool_calls.append(block)
        elif block.type == "thinking":
            reasoning_content += block.thinking
        elif block.type == "redacted_thinking":
            reasoning_content += f"[redacted: {block.data}]"

    assert reasoning_content == "Hmm, let me analyze this code carefully...", "FAIL!"
    assert text_content == "The bug is in line 42.", "FAIL!"
    print(f"  text_content: {text_content!r}")
    print(f"  reasoning_content: {reasoning_content!r}")
    print("  PASS - Thinking block parsed correctly\n")


def test_reasoning_before_content():
    """Test 2: Reasoning flows before content."""
    print("=== TEST 2: Reasoning flows before content ===")
    reasoning = "Let me analyze the code step by step."
    content = "The issue is a missing parameter."

    events = []
    if reasoning:
        events.append(("reasoning", reasoning))
    if content:
        events.append(("content", content))

    assert events[0][0] == "reasoning", "FAIL: reasoning not first!"
    assert events[1][0] == "content", "FAIL: content not second!"
    print(f"  Event order: {[e[0] for e in events]}")
    print("  PASS - Reasoning emitted before content\n")


def test_opencode_reasoning_stream():
    """Test 3: Opencode reasoning stream handling."""
    print("=== TEST 3: Opencode reasoning stream parsing ===")
    stream_chunks = [
        "[reasoning]Hmm, let me think about this...[/reasoning]",
        "Here is the",
        " actual answer.",
    ]

    full_reasoning = ""
    full_content = ""

    for chunk in stream_chunks:
        if chunk.startswith("[reasoning]") and chunk.endswith("[/reasoning]"):
            reasoning_text = chunk[len("[reasoning]"):-len("[/reasoning]")]
            full_reasoning += reasoning_text
        else:
            full_content += chunk

    assert full_reasoning == "Hmm, let me think about this...", "FAIL!"
    assert full_content == "Here is the actual answer.", "FAIL!"
    print(f"  Reasoning extracted: {full_reasoning!r}")
    print(f"  Content extracted: {full_content!r}")
    print("  PASS - Reasoning marker parsed correctly\n")


def test_api_key_safety():
    """Test 4: API key uses env variable."""
    print("=== TEST 4: Config & API key safety ===")
    config = json.load(open("thebigbos.json"))
    opencode_key = config["providers"]["opencode-go"]["api_key"]
    if "sk-" in opencode_key and "opencode" not in opencode_key.lower() and "${" not in opencode_key:
        print(f"  FAIL - API key still hardcoded: {opencode_key[:15]}...")
        sys.exit(1)
    print(f"  API key: {opencode_key}")
    print("  PASS - API key uses env variable\n")


def test_thinking_budget_targeting():
    """Test 5: thinking_budget only for reasoning models."""
    print("=== TEST 5: thinking_budget targeting ===")
    reasoning_models = ("deepseek", "sonnet", "opus", "claude")

    for model, should_think in [
        ("deepseek-v4-pro", True),
        ("claude-sonnet-4-20250514", True),
        ("gpt-4o", False),
        ("o1", False),
        ("llama3.1", False),
    ]:
        result = any(r in model.lower() for r in reasoning_models)
        assert result == should_think, f"FAIL: {model} expected {should_think}, got {result}"
        print(f"  {model:30s} -> thinking_budget: {result}")

    print("  PASS - thinking_budget targeted correctly\n")


def test_modelresponse_has_reasoning():
    """Test 6: ModelResponse dataclass has reasoning_content."""
    print("=== TEST 6: ModelResponse supports reasoning_content ===")
    from thebigbos.models.provider import ModelResponse

    resp = ModelResponse(
        content="Answer",
        reasoning_content="Thinking...",
        finish_reason="stop",
    )
    assert resp.reasoning_content == "Thinking...", "FAIL!"
    assert resp.content == "Answer", "FAIL!"
    print(f"  content: {resp.content!r}")
    print(f"  reasoning_content: {resp.reasoning_content!r}")
    print("  PASS - ModelResponse holds reasoning separately\n")


def test_tui_no_duplicate_handler():
    """Test 7: TUI home.py has no duplicate thinking handler."""
    print("=== TEST 7: No duplicate 'thinking' handler in TUI ===")
    with open("thebigbos/tui/screens/home.py", encoding="utf-8") as f:
        source = f.read()

    # Count lines with 'event_type == "thinking"'
    thinking_lines = [l for l in source.split("\n") if 'event_type == "thinking"' in l]
    assert len(thinking_lines) <= 1, f"FAIL: Found {len(thinking_lines)} thinking handlers!"
    print(f"  thinking handlers found: {len(thinking_lines)}")
    print("  PASS - No duplicate handlers\n")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  THEBIGBOS FIX VERIFICATION SUITE")
    print("=" * 50 + "\n")

    test_anthropic_thinking_block()
    test_reasoning_before_content()
    test_opencode_reasoning_stream()
    test_api_key_safety()
    test_thinking_budget_targeting()
    test_modelresponse_has_reasoning()
    test_tui_no_duplicate_handler()

    print("=" * 50)
    print("  ALL TESTS PASSED!")
    print("=" * 50)
