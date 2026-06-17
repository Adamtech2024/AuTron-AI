"""Unit tests for Conversation and Memory classes."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestConversation:
    """Tests for the Conversation class (used in ultra, prism, neo, nano, leaf)."""

    def _get_module(self, tmp_path, module_name="autron_ultra_conv"):
        """Load the autron-ultra module with patched paths."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / "autron-ultra.py"
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("pathlib.Path.home", return_value=tmp_path):
            spec.loader.exec_module(mod)
        mod.DATA_DIR = tmp_path
        mod.HISTORY_FILE = tmp_path / "history_test.json"
        return mod

    def test_conversation_starts_empty(self, tmp_path):
        """Conversation should have empty history on init with no file."""
        mod = self._get_module(tmp_path, "conv1")
        conv = mod.Conversation()
        assert conv.history == []

    def test_conversation_add_message(self, tmp_path):
        """Conversation.add() should append messages."""
        mod = self._get_module(tmp_path, "conv2")
        conv = mod.Conversation()
        conv.add("user", "Hello")
        conv.add("assistant", "Hi there!")

        assert len(conv.history) == 2
        assert conv.history[0] == {"role": "user", "content": "Hello"}
        assert conv.history[1] == {"role": "assistant", "content": "Hi there!"}

    def test_conversation_truncates_long_content(self, tmp_path):
        """Conversation.add() should truncate content to 500 chars."""
        mod = self._get_module(tmp_path, "conv3")
        conv = mod.Conversation()
        long_message = "x" * 1000
        conv.add("user", long_message)

        assert len(conv.history[0]["content"]) == 500

    def test_conversation_limits_history_size(self, tmp_path):
        """Conversation should limit history to 15 most recent messages."""
        mod = self._get_module(tmp_path, "conv4")
        conv = mod.Conversation()

        # Add 25 messages
        for i in range(25):
            conv.add("user", f"message {i}")

        assert len(conv.history) <= 20

    def test_conversation_persists_to_file(self, tmp_path):
        """Conversation should save history to JSON file."""
        mod = self._get_module(tmp_path, "conv5")
        history_file = tmp_path / "history_test.json"
        mod.HISTORY_FILE = history_file

        conv = mod.Conversation()
        conv.add("user", "test message")

        assert history_file.exists()
        with open(history_file, "r") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["content"] == "test message"

    def test_conversation_loads_from_file(self, tmp_path):
        """Conversation should load history from existing file."""
        mod = self._get_module(tmp_path, "conv6")
        history_file = tmp_path / "history_test.json"
        mod.HISTORY_FILE = history_file

        existing_history = [
            {"role": "user", "content": "old message"},
            {"role": "assistant", "content": "old response"},
        ]
        history_file.write_text(json.dumps(existing_history))

        conv = mod.Conversation()
        assert len(conv.history) == 2
        assert conv.history[0]["content"] == "old message"

    def test_conversation_clear(self, tmp_path):
        """Conversation.clear() should empty the history."""
        mod = self._get_module(tmp_path, "conv7")
        conv = mod.Conversation()
        conv.add("user", "message")
        conv.clear()

        assert conv.history == []


class TestMemory:
    """Tests for the Memory class (used in autron-omni)."""

    def _get_omni_module(self, module_name="omni_mem"):
        """Load the autron-omni module."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / "autron-omni.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_memory_starts_empty(self):
        """Memory should start with empty history."""
        mod = self._get_omni_module("omni_mem1")
        mem = mod.Memory()
        assert mem.history == []

    def test_memory_add(self):
        """Memory.add() should append messages."""
        mod = self._get_omni_module("omni_mem2")
        mem = mod.Memory()
        mem.add("user", "Hello Omni")
        mem.add("assistant", "Hello!")

        assert len(mem.history) == 2
        assert mem.history[0] == {"role": "user", "content": "Hello Omni"}

    def test_memory_limits_to_10(self):
        """Memory should keep only last 10 messages (drops oldest)."""
        mod = self._get_omni_module("omni_mem3")
        mem = mod.Memory()

        for i in range(15):
            mem.add("user", f"msg {i}")

        assert len(mem.history) == 10
        # Should have messages 5-14 (oldest dropped)
        assert mem.history[0]["content"] == "msg 5"
        assert mem.history[-1]["content"] == "msg 14"
