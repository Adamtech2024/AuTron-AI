"""Unit tests for AIBuilder and Trainer classes."""
from pathlib import Path
from unittest.mock import patch

import pytest


class TestAIBuilder:
    """Tests for the AIBuilder class."""

    def _get_module(self, tmp_path, module_name="ultra_builder"):
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
        mod.DOWNLOAD_DIR = tmp_path / "downloads"
        return mod

    def test_build_creates_file(self, tmp_path):
        """AIBuilder.build() should create a Python file."""
        mod = self._get_module(tmp_path, "builder1")
        k = mod.Knowledge()
        builder = mod.AIBuilder(k)
        result = builder.build("test_ai")

        assert "Built" in result
        output_file = tmp_path / "downloads" / "test_ai.py"
        assert output_file.exists()

    def test_build_default_name(self, tmp_path):
        """AIBuilder.build() should use default name when none given."""
        mod = self._get_module(tmp_path, "builder2")
        k = mod.Knowledge()
        builder = mod.AIBuilder(k)
        result = builder.build()

        assert "Built" in result
        output_file = tmp_path / "downloads" / "autron_built.py"
        assert output_file.exists()

    def test_build_includes_source_code(self, tmp_path):
        """Built file should contain Python code."""
        mod = self._get_module(tmp_path, "builder3")
        k = mod.Knowledge()
        builder = mod.AIBuilder(k)
        builder.build("check_content")

        output_file = tmp_path / "downloads" / "check_content.py"
        content = output_file.read_text(encoding="utf-8")
        assert "#!/usr/bin/env python3" in content

    def test_build_creates_download_dir(self, tmp_path):
        """AIBuilder.build() should create download directory if needed."""
        mod = self._get_module(tmp_path, "builder4")
        download_dir = tmp_path / "downloads"
        mod.DOWNLOAD_DIR = download_dir
        assert not download_dir.exists()

        k = mod.Knowledge()
        builder = mod.AIBuilder(k)
        builder.build("test")

        assert download_dir.exists()


class TestTrainer:
    """Tests for the Trainer class."""

    def _get_module(self, tmp_path, module_name="ultra_trainer"):
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

    def test_trainer_train(self, tmp_path):
        """Trainer.train() should return success message."""
        mod = self._get_module(tmp_path, "trainer1")
        k = mod.Knowledge()
        trainer = mod.Trainer(k)
        result = trainer.train("0s")
        assert "optimized" in result

    def test_trainer_train_default_duration(self, tmp_path):
        """Trainer.train() should work with default duration."""
        mod = self._get_module(tmp_path, "trainer2")
        k = mod.Knowledge()
        trainer = mod.Trainer(k)
        result = trainer.train()
        assert "optimized" in result


class TestAutoLearner:
    """Tests for the AutoLearner class."""

    def _get_module(self, tmp_path, module_name="ultra_learner"):
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

    def test_learner_returns_error_when_offline(self, tmp_path):
        """AutoLearner.learn() should return error when offline."""
        mod = self._get_module(tmp_path, "learner1")
        k = mod.Knowledge()
        search = mod.TurboSearch(k)
        learner = mod.AutoLearner(search, k)

        with patch.object(mod, "is_online", return_value=False):
            result = learner.learn("test topic")

        assert "Need internet" in result
