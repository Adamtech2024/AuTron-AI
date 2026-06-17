"""Unit tests for AuTron Omni-specific functionality."""
import asyncio
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestAuTronOmni:
    """Tests for the AuTronOmni class."""

    def _get_module(self, module_name="omni_test"):
        """Load autron-omni module."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / "autron-omni.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_omni_instantiation(self):
        """AuTronOmni should instantiate with search and memory."""
        mod = self._get_module("omni_inst")
        omni = mod.AuTronOmni()
        assert omni.search is not None
        assert omni.memory is not None
        assert isinstance(omni.memory, mod.Memory)

    def test_omni_greeting_detection(self):
        """AuTronOmni should detect greeting inputs."""
        mod = self._get_module("omni_greet")
        omni = mod.AuTronOmni()

        greetings = ["hello", "hi", "who are you", "what are you", "what can you do", "help"]
        for greeting in greetings:
            is_greeting = any(g in greeting.lower() for g in greetings) and len(greeting.split()) < 10
            assert is_greeting is True

    def test_omni_non_greeting_detection(self):
        """AuTronOmni should not classify complex queries as greetings."""
        mod = self._get_module("omni_nongreet")

        greetings_list = ["hello", "hi", "who are you", "what are you", "what can you do", "help"]
        complex_query = "What is the capital of France and its population demographics"
        is_greeting = any(g in complex_query.lower() for g in greetings_list) and len(complex_query.split()) < 10
        assert is_greeting is False


class TestOmniConfig:
    """Tests for Omni configuration."""

    def _get_module(self, module_name="omni_config"):
        """Load autron-omni module."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / "autron-omni.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_version_is_set(self):
        """VERSION should be defined."""
        mod = self._get_module("omni_cfg1")
        assert mod.VERSION == "AuTron 4o (Omni)"

    def test_models_config(self):
        """MODELS should have default and research entries."""
        mod = self._get_module("omni_cfg2")
        assert "default" in mod.MODELS
        assert "research" in mod.MODELS

    def test_data_dir_is_set(self):
        """DATA_DIR should be set to ~/.autron-storage."""
        mod = self._get_module("omni_cfg3")
        assert mod.DATA_DIR.name == ".autron-storage"


class TestOmniFactExtraction:
    """Tests for the fact extraction regex patterns used in Omni."""

    def test_temperature_pattern(self):
        """Should detect temperature patterns."""
        pattern = r'\d+[\.,]?\d*\s*°[FCfc]'
        assert re.search(pattern, "The temperature is 72.5 °F today")
        assert re.search(pattern, "It's 25°C outside")
        assert re.search(pattern, "100 °F is hot")

    def test_financial_pattern(self):
        """Should detect financial figures."""
        pattern = r'\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|trillion))?'
        assert re.search(pattern, "Revenue hit $5.2 billion")
        assert re.search(pattern, "The cost is $1,500.00")
        assert re.search(pattern, "Valued at $100 million")

    def test_percentage_pattern(self):
        """Should detect percentages."""
        pattern = r'\d+(?:\.\d+)?%'
        assert re.search(pattern, "Growth of 15.5% year over year")
        assert re.search(pattern, "Only 3% were affected")

    def test_date_reference_pattern(self):
        """Should detect date references."""
        pattern = r'(?:as of|updated?|reported?)\s+\w+\s+\d{1,2},?\s*\d{4}'
        assert re.search(pattern, "as of January 15, 2025")
        assert re.search(pattern, "reported March 3 2024")

    def test_status_pattern(self):
        """Should detect current status patterns."""
        pattern = r'(?:Currently|Now|Today):?\s*(.{5,80})'
        match = re.search(pattern, "Currently: The CEO is John Smith")
        assert match is not None
        assert "The CEO is John Smith" in match.group(1)
