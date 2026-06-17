"""Unit tests for Output class and is_online utility."""
import socket
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestIsOnline:
    """Tests for the is_online() utility function."""

    def _get_module(self, tmp_path, module_name="ultra_online"):
        """Load autron-ultra with patched paths."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / "autron-ultra.py"
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("pathlib.Path.home", return_value=tmp_path):
            spec.loader.exec_module(mod)
        return mod

    def test_is_online_returns_true_when_connected(self, tmp_path):
        """is_online() should return True when connection succeeds."""
        mod = self._get_module(tmp_path, "online1")
        mock_conn = MagicMock()
        with patch("socket.create_connection", return_value=mock_conn):
            assert mod.is_online() is True
        mock_conn.close.assert_called_once()

    def test_is_online_returns_false_when_no_connection(self, tmp_path):
        """is_online() should return False when connection fails."""
        mod = self._get_module(tmp_path, "online2")
        with patch("socket.create_connection", side_effect=OSError("No route")):
            assert mod.is_online() is False

    def test_is_online_returns_false_on_timeout(self, tmp_path):
        """is_online() should return False on timeout."""
        mod = self._get_module(tmp_path, "online3")
        with patch("socket.create_connection", side_effect=socket.timeout("timed out")):
            assert mod.is_online() is False


class TestOutput:
    """Tests for the Output class."""

    def _get_module(self, tmp_path, module_name="ultra_output"):
        """Load autron-ultra with patched paths."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / "autron-ultra.py"
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("pathlib.Path.home", return_value=tmp_path):
            spec.loader.exec_module(mod)
        return mod

    def test_output_print_with_rich(self, tmp_path):
        """Output.print() should use rich console when available."""
        mod = self._get_module(tmp_path, "output1")
        mod.RICH_AVAILABLE = True
        output = mod.Output()
        # Should not raise
        output.print("Test message", style="bold")

    def test_output_print_without_rich(self, tmp_path, capsys):
        """Output.print() should fallback to print when rich unavailable."""
        mod = self._get_module(tmp_path, "output2")
        mod.RICH_AVAILABLE = False
        output = mod.Output()
        output.print("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_output_stream_print_without_rich(self, tmp_path, capsys):
        """Output.stream_print() should print without newline."""
        mod = self._get_module(tmp_path, "output3")
        mod.RICH_AVAILABLE = False
        output = mod.Output()
        output.stream_print("chunk1")
        output.stream_print("chunk2")
        captured = capsys.readouterr()
        assert "chunk1" in captured.out
        assert "chunk2" in captured.out

    def test_output_clear(self, tmp_path):
        """Output.clear() should call os.system with clear command."""
        mod = self._get_module(tmp_path, "output4")
        output = mod.Output()
        with patch("os.system") as mock_sys:
            output.clear()
            mock_sys.assert_called_once()
            # On Linux it should use 'clear'
            call_arg = mock_sys.call_args[0][0]
            assert call_arg in ["clear", "cls"]


class TestUI:
    """Tests for the UI class in autron-omni."""

    def _get_omni_module(self, module_name="omni_ui"):
        """Load autron-omni."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent.parent / "autron-omni.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_ui_print(self):
        """UI.print() should not raise."""
        mod = self._get_omni_module("omni_ui1")
        # Should not raise
        mod.UI.print("Test message", style="white")

    def test_ui_stream_print(self):
        """UI.stream_print() should not raise."""
        mod = self._get_omni_module("omni_ui2")
        # Should not raise
        mod.UI.stream_print("streaming text")
