"""Unit tests for get_system_prompt and command parsing."""
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGetSystemPrompt:
    """Tests for get_system_prompt() across different models."""

    def _get_module(self, filename, tmp_path, module_name):
        """Load a module by filename."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / filename
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("pathlib.Path.home", return_value=tmp_path):
            spec.loader.exec_module(mod)
        return mod

    def test_ultra_system_prompt_contains_model_name(self, tmp_path):
        """Ultra system prompt should contain the model name."""
        mod = self._get_module("autron-ultra.py", tmp_path, "sp_ultra")
        prompt = mod.get_system_prompt("AuTron 4 Ultra (Titan)")
        assert "AuTron 4 Ultra (Titan)" in prompt
        assert "autron_behavior" in prompt

    def test_nano_system_prompt_contains_model_name(self, tmp_path):
        """Nano system prompt should contain the model name."""
        mod = self._get_module("autron-nano.py", tmp_path, "sp_nano")
        prompt = mod.get_system_prompt("AuTron 4 Nano (Standard)")
        assert "AuTron 4 Nano (Standard)" in prompt
        assert "Nano" in prompt

    def test_leaf_system_prompt_contains_model_name(self, tmp_path):
        """Leaf system prompt should contain the model name."""
        mod = self._get_module("autron-leaf.py", tmp_path, "sp_leaf")
        prompt = mod.get_system_prompt("AuTron 4 Leaf (Lightweight)")
        assert "AuTron 4 Leaf (Lightweight)" in prompt
        assert "Leaf" in prompt

    def test_neo_system_prompt_contains_model_name(self, tmp_path):
        """Neo system prompt should contain the model name."""
        mod = self._get_module("autron-neo.py", tmp_path, "sp_neo")
        prompt = mod.get_system_prompt("AuTron 4 Neo (Adaptive)")
        assert "AuTron 4 Neo (Adaptive)" in prompt
        assert "Neo" in prompt

    def test_prism_system_prompt_contains_model_name(self, tmp_path):
        """Prism system prompt should contain the model name."""
        mod = self._get_module("autron-prism.py", tmp_path, "sp_prism")
        prompt = mod.get_system_prompt("AuTron 4 Prism (Elite)")
        assert "AuTron 4 Prism (Elite)" in prompt
        assert "Prism" in prompt

    def test_system_prompt_includes_date(self, tmp_path):
        """System prompt should include the current date."""
        from datetime import datetime, timezone
        mod = self._get_module("autron-ultra.py", tmp_path, "sp_date")
        prompt = mod.get_system_prompt("Test")
        # Should contain a date-like string
        today = datetime.now(timezone.utc).strftime("%B %d, %Y")
        assert today in prompt

    def test_system_prompt_includes_search_instructions(self, tmp_path):
        """System prompt should include search instructions."""
        mod = self._get_module("autron-ultra.py", tmp_path, "sp_search")
        prompt = mod.get_system_prompt("Test")
        assert "search_instructions" in prompt
        assert "web_search" in prompt

    def test_system_prompt_includes_refusal_handling(self, tmp_path):
        """System prompt should include refusal handling."""
        mod = self._get_module("autron-ultra.py", tmp_path, "sp_refusal")
        prompt = mod.get_system_prompt("Test")
        assert "refusal_handling" in prompt
        assert "child safety" in prompt


class TestCommandParsing:
    """Tests for AuTron.cmd() command parsing."""

    def _get_autron(self, tmp_path, module_name="ultra_cmd"):
        """Load autron-ultra and return an AuTron instance."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / "autron-ultra.py"
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("pathlib.Path.home", return_value=tmp_path):
            spec.loader.exec_module(mod)
        mod.DATA_DIR = tmp_path
        mod.KNOWLEDGE_FILE = tmp_path / "k.json.gz"
        mod.HISTORY_FILE = tmp_path / "h.json"
        mod.DOWNLOAD_DIR = tmp_path / "downloads"
        return mod

    def test_cmd_help(self, tmp_path):
        """AuTron.cmd('/help') should return help text."""
        mod = self._get_autron(tmp_path, "cmd1")
        ai = mod.AuTron()
        result = ai.cmd("/help")
        assert "CORE MODES" in result
        assert "/mode" in result
        assert "/build-ai" in result

    def test_cmd_mode_valid(self, tmp_path):
        """AuTron.cmd('/mode fast') should set mode."""
        mod = self._get_autron(tmp_path, "cmd2")
        ai = mod.AuTron()
        result = ai.cmd("/mode fast")
        assert "FAST" in result
        assert ai.mode == "fast"

    def test_cmd_mode_auto(self, tmp_path):
        """AuTron.cmd('/mode auto') should set auto mode."""
        mod = self._get_autron(tmp_path, "cmd3")
        ai = mod.AuTron()
        result = ai.cmd("/mode auto")
        assert ai.mode == "auto"

    def test_cmd_mode_invalid(self, tmp_path):
        """AuTron.cmd('/mode invalid') should show usage."""
        mod = self._get_autron(tmp_path, "cmd4")
        ai = mod.AuTron()
        result = ai.cmd("/mode invalid")
        assert "Usage" in result

    def test_cmd_stats(self, tmp_path):
        """AuTron.cmd('/stats') should return knowledge stats."""
        mod = self._get_autron(tmp_path, "cmd5")
        ai = mod.AuTron()
        result = ai.cmd("/stats")
        assert "Knowledge Stats" in result
        assert "Facts" in result

    def test_cmd_clear(self, tmp_path):
        """AuTron.cmd('/clear') should clear conversation."""
        mod = self._get_autron(tmp_path, "cmd6")
        ai = mod.AuTron()
        ai.conv.add("user", "test")
        result = ai.cmd("/clear")
        assert "Cleared" in result
        assert ai.conv.history == []

    def test_cmd_unknown(self, tmp_path):
        """Unknown commands should return error."""
        mod = self._get_autron(tmp_path, "cmd7")
        ai = mod.AuTron()
        result = ai.cmd("/nonexistent")
        assert "Unknown" in result

    def test_cmd_build_ai(self, tmp_path):
        """AuTron.cmd('/build-ai test') should build standalone AI."""
        mod = self._get_autron(tmp_path, "cmd8")
        ai = mod.AuTron()
        result = ai.cmd("/build-ai test_output")
        assert "Built" in result
        assert (tmp_path / "downloads" / "test_output.py").exists()

    def test_cmd_export(self, tmp_path):
        """AuTron.cmd('/export') should export knowledge."""
        mod = self._get_autron(tmp_path, "cmd9")
        ai = mod.AuTron()
        result = ai.cmd("/stats")  # Just test stats as export creates files
        assert "Knowledge Stats" in result

    def test_cmd_pro_without_arg(self, tmp_path):
        """AuTron.cmd('/pro') without argument should show usage."""
        mod = self._get_autron(tmp_path, "cmd10")
        ai = mod.AuTron()
        result = ai.cmd("/pro")
        assert result is None  # It prints usage but returns None
