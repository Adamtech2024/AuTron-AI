"""Unit tests for TurboSearch and SearchEngine classes."""
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestTurboSearchFormat:
    """Tests for TurboSearch.format() method."""

    def _get_module(self, tmp_path, module_name="ultra_search"):
        """Load autron-ultra with patched paths."""
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
        return mod

    def test_format_empty_results(self, tmp_path):
        """format() should return empty string for empty results."""
        mod = self._get_module(tmp_path, "search1")
        k = mod.Knowledge()
        ts = mod.TurboSearch(k)
        assert ts.format([]) == ""

    def test_format_single_result(self, tmp_path):
        """format() should format a single result correctly."""
        mod = self._get_module(tmp_path, "search2")
        k = mod.Knowledge()
        ts = mod.TurboSearch(k)
        results = [{"t": "Test Title", "b": "Test body text"}]
        output = ts.format(results)
        assert "Test Title" in output
        assert "Test body text" in output
        assert output.startswith("•")

    def test_format_multiple_results(self, tmp_path):
        """format() should format multiple results."""
        mod = self._get_module(tmp_path, "search3")
        k = mod.Knowledge()
        ts = mod.TurboSearch(k)
        results = [
            {"t": "Title 1", "b": "Body 1"},
            {"t": "Title 2", "b": "Body 2"},
            {"t": "Title 3", "b": "Body 3"},
        ]
        output = ts.format(results)
        assert "Title 1" in output
        assert "Title 2" in output
        assert "Title 3" in output

    def test_format_limits_to_5_results(self, tmp_path):
        """format() should only show first 5 results."""
        mod = self._get_module(tmp_path, "search4")
        k = mod.Knowledge()
        ts = mod.TurboSearch(k)
        results = [{"t": f"Title {i}", "b": f"Body {i}"} for i in range(10)]
        output = ts.format(results)
        assert "Title 4" in output
        assert "Title 5" not in output


class TestTurboSearchSearch:
    """Tests for TurboSearch.search() method."""

    def _get_module(self, tmp_path, module_name="ultra_search_s"):
        """Load autron-ultra with patched paths."""
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
        return mod

    def test_search_returns_empty_when_offline(self, tmp_path):
        """search() should return empty list when offline."""
        mod = self._get_module(tmp_path, "search5")
        k = mod.Knowledge()
        ts = mod.TurboSearch(k)

        with patch.object(mod, "is_online", return_value=False):
            results = ts.search("test query")
        assert results == []

    def test_search_returns_empty_when_search_unavailable(self, tmp_path):
        """search() should return empty when SEARCH_AVAILABLE is False."""
        mod = self._get_module(tmp_path, "search6")
        mod.SEARCH_AVAILABLE = False
        k = mod.Knowledge()
        ts = mod.TurboSearch(k)

        results = ts.search("test query")
        assert results == []


class TestSearchEngineQueryExpansion:
    """Tests for SearchEngine query expansion logic in autron-omni."""

    def _get_omni_module(self, module_name="omni_search"):
        """Load autron-omni module."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / "autron-omni.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_search_engine_instantiation(self):
        """SearchEngine should instantiate without errors."""
        mod = self._get_omni_module("omni_se1")
        se = mod.SearchEngine()
        assert se is not None

    def test_search_engine_get_context_with_question(self):
        """get_context should expand question-type queries."""
        mod = self._get_omni_module("omni_se2")
        se = mod.SearchEngine()

        # Mock DDGS to avoid real network calls
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text = MagicMock(return_value=[
            {"title": "Result 1", "body": "Body 1", "href": "http://example.com/1"}
        ])

        with patch.object(mod, "DDGS", return_value=mock_ddgs):
            results = asyncio.run(se.get_context("what is Python programming"))

        assert isinstance(results, list)

    def test_search_engine_get_context_with_news_query(self):
        """get_context should expand news-type queries."""
        mod = self._get_omni_module("omni_se3")
        se = mod.SearchEngine()

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text = MagicMock(return_value=[
            {"title": "News 1", "body": "Latest news body", "href": "http://news.com/1"}
        ])

        with patch.object(mod, "DDGS", return_value=mock_ddgs):
            results = asyncio.run(se.get_context("latest AI news developments"))

        assert isinstance(results, list)

    def test_search_engine_handles_empty_results(self):
        """get_context should handle no results gracefully."""
        mod = self._get_omni_module("omni_se4")
        se = mod.SearchEngine()

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text = MagicMock(return_value=[])

        with patch.object(mod, "DDGS", return_value=mock_ddgs):
            results = asyncio.run(se.get_context("obscure query no results"))

        assert results == []

    def test_search_engine_deduplicates_urls(self):
        """get_context should deduplicate results by URL."""
        mod = self._get_omni_module("omni_se5")
        se = mod.SearchEngine()

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        # Return duplicate URLs
        mock_ddgs.text = MagicMock(return_value=[
            {"title": "Same Page", "body": "Body 1", "href": "http://example.com/same"},
            {"title": "Same Page Again", "body": "Body 2", "href": "http://example.com/same"},
            {"title": "Different Page", "body": "Body 3", "href": "http://example.com/other"},
        ])

        with patch.object(mod, "DDGS", return_value=mock_ddgs):
            results = asyncio.run(se.get_context("test dedup"))

        urls = [r["u"] for r in results]
        assert len(urls) == len(set(urls))
