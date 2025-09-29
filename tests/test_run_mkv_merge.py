import subprocess
from typing import Any

import pytest

from pymkv.errors import MkvMergeSubprocessError
from pymkv.utils import run_mkvmerge


class TestRunMkvmerge:
    """Groups tests for the run_mkvmerge function."""

    def test_success(self, mock_dependencies: dict[str, Any]) -> None:
        """Tests the happy path: command executes successfully (exit code 0)."""
        # Arrange
        mock_run = mock_dependencies["run"]
        mock_logger = mock_dependencies["logger"]
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Success output",
            stderr="",
        )
        command = ["--identify", "file.mkv"]

        # Act
        result = run_mkvmerge(command)

        # Assert
        assert result == "Success output"
        mock_run.assert_called_once()
        mock_logger.debug.assert_any_call("Command completed successfully")
        mock_logger.warning.assert_not_called()

    def test_with_warnings(self, mock_dependencies: dict[str, Any]) -> None:
        """Tests the warning path: command completes with warnings (exit code 1)."""
        # Arrange
        mock_run = mock_dependencies["run"]
        mock_logger = mock_dependencies["logger"]
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="Processed with warnings.",
            stderr="Warning: Track 1 was not copied.",
        )
        command = ["-o", "out.mkv", "in.mkv"]

        # Act
        result = run_mkvmerge(command)

        # Assert
        assert result == "Processed with warnings."
        mock_logger.warning.assert_any_call("Command completed with warnings (exit code 1)")
        mock_logger.warning.assert_any_call("Command stderr: Warning: Track 1 was not copied.")

    def test_with_error(self, mock_dependencies: dict[str, Any]) -> None:
        """Tests the error path: command fails with an error (exit code > 1)."""
        # Arrange
        mock_run = mock_dependencies["run"]
        mock_logger = mock_dependencies["logger"]
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout="",
            stderr="Error: Could not open source file.",
        )
        command = ["--identify", "nonexistent.mkv"]

        # Act & Assert
        with pytest.raises(MkvMergeSubprocessError) as exc_info:
            run_mkvmerge(command)

        assert exc_info.value.returncode == 2
        assert exc_info.value.stderr == "Error: Could not open source file."
        mock_logger.error.assert_any_call("Command stderr: Error: Could not open source file.")

    def test_timeout(self, mock_dependencies: dict[str, Any]) -> None:
        """Tests the timeout path: subprocess.run raises TimeoutExpired."""
        # Arrange
        mock_run = mock_dependencies["run"]
        command = ["-o", "out.mkv", "huge_file.mkv"]
        timeout_exc = subprocess.TimeoutExpired(
            cmd=command,
            timeout=5,
            output=b"Partial output...",
            stderr=b"Still working...",
        )
        mock_run.side_effect = timeout_exc

        # Act & Assert
        with pytest.raises(MkvMergeSubprocessError) as exc_info:
            run_mkvmerge(command, timeout=5)

        assert exc_info.value.returncode == -1
        assert exc_info.value.stdout == "Partial output..."
        assert "Command timed out after 5 seconds" in exc_info.value.message

    def test_unexpected_exception(self, mock_dependencies: dict[str, Any]) -> None:
        """Tests a generic exception during subprocess.run."""
        # Arrange
        mock_run = mock_dependencies["run"]
        command = ["--identify", "file.mkv"]
        mock_run.side_effect = FileNotFoundError("mkvmerge not found")

        # Act & Assert
        with pytest.raises(MkvMergeSubprocessError) as exc_info:
            run_mkvmerge(command)

        assert exc_info.value.returncode == -1
        assert "Unexpected error running command" in exc_info.value.message
        assert "mkvmerge not found" in exc_info.value.message
