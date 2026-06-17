"""Shared fixtures for AuTron AI tests."""
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Mock external dependencies before importing modules
@pytest.fixture(autouse=True)
def mock_external_deps(monkeypatch):
    """Mock ollama, duckduckgo_search, and rich so modules can import cleanly."""
    # Create mock modules for optional deps that might not be installed
    mock_ollama = MagicMock()
    mock_ddgs = MagicMock()
    mock_rich_console = MagicMock()
    mock_rich_panel = MagicMock()
    mock_rich_live = MagicMock()
    mock_rich_markdown = MagicMock()

    monkeypatch.setitem(sys.modules, "ollama", mock_ollama)
    monkeypatch.setitem(sys.modules, "duckduckgo_search", mock_ddgs)
    monkeypatch.setitem(sys.modules, "rich", MagicMock())
    monkeypatch.setitem(sys.modules, "rich.console", mock_rich_console)
    monkeypatch.setitem(sys.modules, "rich.panel", mock_rich_panel)
    monkeypatch.setitem(sys.modules, "rich.live", mock_rich_live)
    monkeypatch.setitem(sys.modules, "rich.markdown", mock_rich_markdown)


def load_module(name: str):
    """Load a module from a hyphenated filename."""
    repo_root = Path(__file__).parent.parent
    filepath = repo_root / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """Provide a temporary data directory for Knowledge tests."""
    return tmp_path
