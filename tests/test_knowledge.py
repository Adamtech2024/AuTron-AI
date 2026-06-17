"""Unit tests for the Knowledge class shared across AuTron models."""
import gzip
import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestKnowledgeLoad:
    """Tests for Knowledge._load() method."""

    def test_load_returns_default_when_no_file(self, tmp_path):
        """Knowledge should return default structure when no file exists."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"

        with patch("pathlib.Path.home", return_value=tmp_path):
            # Import the module fresh
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)

            # Patch module-level paths before exec
            with patch.dict("os.environ", {}):
                spec.loader.exec_module(mod)

            # Override paths
            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            assert k.data == {"facts": {}, "searches": {}, "learned": [], "training": []}

    def test_load_reads_existing_gzip_file(self, tmp_path):
        """Knowledge should load data from existing gzip file."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"
        test_data = {
            "facts": {"python": ["Python is a language"]},
            "searches": {},
            "learned": ["item1"],
            "training": []
        }
        with gzip.open(knowledge_file, "wt", encoding="utf-8") as f:
            json.dump(test_data, f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra2",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            assert k.data["facts"] == {"python": ["Python is a language"]}
            assert k.data["learned"] == ["item1"]

    def test_load_handles_corrupt_file(self, tmp_path):
        """Knowledge should handle corrupt gzip files gracefully."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"
        knowledge_file.write_bytes(b"not valid gzip data")

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra3",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            assert k.data == {"facts": {}, "searches": {}, "learned": [], "training": []}

    def test_load_fills_missing_keys(self, tmp_path):
        """Knowledge should fill in missing keys from partial data."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"
        # Only has 'facts' key
        partial_data = {"facts": {"ai": ["AI is cool"]}}
        with gzip.open(knowledge_file, "wt", encoding="utf-8") as f:
            json.dump(partial_data, f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra4",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            assert k.data["facts"] == {"ai": ["AI is cool"]}
            assert "searches" in k.data
            assert "learned" in k.data
            assert "training" in k.data


class TestKnowledgeSave:
    """Tests for Knowledge.save() method."""

    def test_save_creates_gzip_file(self, tmp_path):
        """Knowledge.save() should create a gzip JSON file."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra5",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            k.data["facts"]["test"] = ["test fact"]
            k.save()

            assert knowledge_file.exists()
            with gzip.open(knowledge_file, "rt", encoding="utf-8") as f:
                loaded = json.load(f)
            assert loaded["facts"]["test"] == ["test fact"]


class TestKnowledgeExport:
    """Tests for Knowledge.export() method."""

    def test_export_creates_file(self, tmp_path):
        """Knowledge.export() should create an export file."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"
        download_dir = tmp_path / "downloads"

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra6",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file
            mod.DOWNLOAD_DIR = download_dir

            k = mod.Knowledge()
            k.data["facts"]["export_test"] = ["exported"]
            result = k.export()

            assert "Exported" in result
            assert download_dir.exists()
            # Verify an export file was created
            exports = list(download_dir.glob("autron_export_*.json.gz"))
            assert len(exports) == 1


class TestKnowledgeImport:
    """Tests for Knowledge.import_file() method."""

    def test_import_json_file(self, tmp_path):
        """Knowledge.import_file() should import from JSON file."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"
        import_file = tmp_path / "import_data.json"

        import_data = {
            "facts": {"imported": ["data"]},
            "learned": ["imported_item"],
            "training": [{"topic": "test", "info": "info"}]
        }
        import_file.write_text(json.dumps(import_data))

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra7",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            result = k.import_file(str(import_file))

            assert "Imported" in result
            assert k.data["facts"]["imported"] == ["data"]
            assert "imported_item" in k.data["learned"]

    def test_import_gzip_file(self, tmp_path):
        """Knowledge.import_file() should import from gzip file."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"
        import_file = tmp_path / "import_data.json.gz"

        import_data = {
            "facts": {"compressed": ["value"]},
            "learned": [],
            "training": []
        }
        with gzip.open(import_file, "wt", encoding="utf-8") as f:
            json.dump(import_data, f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra8",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            result = k.import_file(str(import_file))

            assert "Imported" in result
            assert k.data["facts"]["compressed"] == ["value"]

    def test_import_invalid_file(self, tmp_path):
        """Knowledge.import_file() should handle invalid files gracefully."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra9",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            result = k.import_file("/nonexistent/path/file.json")

            assert "failed" in result


class TestKnowledgeStats:
    """Tests for Knowledge.stats() method."""

    def test_stats_empty_knowledge(self, tmp_path):
        """Knowledge.stats() should report zeros for empty knowledge."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra10",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            stats = k.stats()
            assert "Facts: 0" in stats
            assert "Learned: 0" in stats
            assert "Training: 0" in stats

    def test_stats_with_data(self, tmp_path):
        """Knowledge.stats() should report correct counts."""
        knowledge_file = tmp_path / "knowledge_test.json.gz"
        test_data = {
            "facts": {"a": ["1", "2"], "b": ["3"]},
            "searches": {},
            "learned": ["x", "y"],
            "training": [{"t": "z"}]
        }
        with gzip.open(knowledge_file, "wt", encoding="utf-8") as f:
            json.dump(test_data, f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "autron_ultra11",
                Path(__file__).parent.parent / "autron-ultra.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            mod.DATA_DIR = tmp_path
            mod.KNOWLEDGE_FILE = knowledge_file

            k = mod.Knowledge()
            stats = k.stats()
            assert "Facts: 3" in stats
            assert "Learned: 2" in stats
            assert "Training: 1" in stats
