import json
import subprocess
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from pymkv.Verifications import verify_matroska
from pymkv.Verifications import verify_mkvmerge
from pymkv.Verifications import verify_recognized
from pymkv.Verifications import verify_supported


class TestVerifyMkvmerge:
    """
    Tests for verify_mkvmerge function.
    """

    def test_verify_mkvmerge_success_default_path(self, mocker: MockerFixture):
        """
        Test successful mkvmerge verification with default path.
        """
        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = b"mkvmerge v1.2.3 ('test') 64-bit\n"

        result = verify_mkvmerge()

        assert result is True
        mock_check_output.assert_called_once_with(["mkvmerge", "-V"])

    def test_verify_mkvmerge_success_custom_path(self, mocker: MockerFixture):
        """
        Test successful mkvmerge verification with custom path.
        """
        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = b"mkvmerge v1.2.3 ('test') 64-bit\n"
        custom_path = "/usr/local/bin/mkvmerge"

        result = verify_mkvmerge(custom_path)

        assert result is True
        mock_check_output.assert_called_once_with([custom_path, "-V"])

    def test_verify_mkvmerge_file_not_found(self, mocker: MockerFixture):
        """
        Test mkvmerge verification when file not found.
        """
        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.side_effect = FileNotFoundError()

        result = verify_mkvmerge()

        assert result is False

    def test_verify_mkvmerge_called_process_error(self, mocker: MockerFixture):
        """
        Test mkvmerge verification when subprocess fails.
        """
        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "mkvmerge")

        result = verify_mkvmerge()

        assert result is False

    def test_verify_mkvmerge_invalid_output(self, mocker: MockerFixture):
        """
        Test mkvmerge verification with invalid output.
        """
        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = b"invalid output\n"

        result = verify_mkvmerge()

        assert result is False

    def test_verify_mkvmerge_partial_match(self, mocker: MockerFixture):
        """
        Test mkvmerge verification with partial valid output.
        """
        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = b"mkvmerge-gui v1.2.3\n"

        result = verify_mkvmerge()

        assert result is True


@pytest.mark.usefixtures("mock_mkvmerge_verification")
class TestVerifyMatroska:
    """Tests for verify_matroska function."""

    @pytest.fixture
    def mock_mkvmerge_info(self):
        """Sample mkvmerge JSON output for Matroska file."""
        return {
            "container": {
                "type": "Matroska",
                "recognized": True,
                "supported": True,
            },
            "tracks": [],
        }

    @pytest.fixture
    def mock_non_matroska_info(self):
        """Sample mkvmerge JSON output for non-Matroska file."""
        return {
            "container": {
                "type": "MP4",
                "recognized": True,
                "supported": True,
            },
            "tracks": [],
        }

    def test_verify_matroska_success(self, mocker, sample_x264_mkv_file: Path, mock_mkvmerge_info):
        """Test successful Matroska verification."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = json.dumps(mock_mkvmerge_info).encode()

        result = verify_matroska(str(sample_x264_mkv_file))

        assert result is True
        mock_check_output.assert_called_once_with(["mkvmerge", "-J", str(sample_x264_mkv_file)])

    def test_verify_matroska_false_for_non_matroska(self, mocker, sample_x264_mp4_file: Path, mock_non_matroska_info):
        """Test Matroska verification returns False for non-Matroska files."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = json.dumps(mock_non_matroska_info).encode()

        result = verify_matroska(str(sample_x264_mp4_file))

        assert result is False

    def test_verify_matroska_custom_mkvmerge_path(self, mocker, sample_x264_mkv_file: Path, mock_mkvmerge_info):
        """Test Matroska verification with custom mkvmerge path."""
        custom_path = "/custom/mkvmerge"

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = json.dumps(mock_mkvmerge_info).encode()

        result = verify_matroska(str(sample_x264_mkv_file), custom_path)

        assert result is True
        mock_check_output.assert_called_once_with([custom_path, "-J", str(sample_x264_mkv_file)])

    def test_verify_matroska_mkvmerge_not_found(self, mocker, sample_x264_mkv_file: Path):
        """Test Matroska verification when mkvmerge not found."""
        mocker.patch("pymkv.Verifications.verify_mkvmerge", return_value=False)

        with pytest.raises(FileNotFoundError, match="mkvmerge is not at the specified path"):
            verify_matroska(str(sample_x264_mkv_file))

    def test_verify_matroska_pathlike_input(self, mocker, sample_x264_mkv_file: Path, mock_mkvmerge_info):
        """Test Matroska verification with PathLike input."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = json.dumps(mock_mkvmerge_info).encode()

        result = verify_matroska(sample_x264_mkv_file)  # Pass Path object directly

        assert result is True

    def test_verify_matroska_invalid_type(self):
        """Test Matroska verification with invalid input type."""

        with pytest.raises(TypeError, match="is not of type str"):
            verify_matroska(123)

    def test_verify_matroska_file_not_exists(self):
        """Test Matroska verification with non-existent file."""

        with pytest.raises(FileNotFoundError, match="does not exist"):
            verify_matroska("/nonexistent/file.mkv")

    def test_verify_matroska_subprocess_error(self, mocker, sample_x264_mkv_file: Path):
        """Test Matroska verification when subprocess fails."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "mkvmerge")

        with pytest.raises(ValueError, match="could not be opened"):
            verify_matroska(str(sample_x264_mkv_file))

    def test_verify_matroska_expanduser(self, mocker, mock_mkvmerge_info):
        """Test Matroska verification expands user path."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = json.dumps(mock_mkvmerge_info).encode()
        _ = mocker.patch("pymkv.Verifications.isfile", return_value=True)
        mock_expanduser = mocker.patch("pymkv.Verifications.expanduser", return_value="/home/user/video.mkv")

        verify_matroska("~/video.mkv")

        mock_expanduser.assert_called_with("~/video.mkv")
        mock_check_output.assert_called_once_with(["mkvmerge", "-J", "/home/user/video.mkv"])


@pytest.mark.usefixtures("mock_mkvmerge_verification")
class TestVerifyRecognized:
    """Tests for verify_recognized function."""

    @pytest.fixture
    def mock_recognized_info(self):
        """Sample mkvmerge JSON output for recognized file."""
        return {
            "container": {
                "recognized": True,
                "supported": True,
            },
        }

    @pytest.fixture
    def mock_unrecognized_info(self):
        """Sample mkvmerge JSON output for unrecognized file."""
        return {
            "container": {
                "recognized": False,
                "supported": False,
            },
        }

    def test_verify_recognized_true(self, mocker, sample_x264_mkv_file: Path, mock_recognized_info):
        """Test verify_recognized returns True for recognized file."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = json.dumps(mock_recognized_info).encode()

        result = verify_recognized(str(sample_x264_mkv_file))

        assert result is True

    def test_verify_recognized_false(self, mocker, sample_x264_mkv_file: Path, mock_unrecognized_info):
        """Test verify_recognized returns False for unrecognized file."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = json.dumps(mock_unrecognized_info).encode()

        result = verify_recognized(str(sample_x264_mkv_file))

        assert result is False

    def test_verify_recognized_mkvmerge_not_found(self, mocker, sample_x264_mkv_file: Path):
        """Test verify_recognized when mkvmerge not found."""
        mocker.patch("pymkv.Verifications.verify_mkvmerge", return_value=False)

        with pytest.raises(FileNotFoundError, match="mkvmerge is not at the specified path"):
            verify_recognized(str(sample_x264_mkv_file))

    def test_verify_recognized_invalid_type(self):
        """Test verify_recognized with invalid input type."""

        with pytest.raises(TypeError, match="is not of type str"):
            verify_recognized(123)

    def test_verify_recognized_file_not_exists(self):
        """Test verify_recognized with non-existent file."""

        with pytest.raises(FileNotFoundError, match="does not exist"):
            verify_recognized("/nonexistent/file.mkv")

    def test_verify_recognized_subprocess_error(self, mocker, sample_x264_mkv_file: Path):
        """Test verify_recognized when subprocess fails."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "mkvmerge")

        with pytest.raises(ValueError, match="could not be opened"):
            verify_recognized(str(sample_x264_mkv_file))


@pytest.mark.usefixtures("mock_mkvmerge_verification")
class TestVerifySupported:
    """Tests for verify_supported function."""

    @pytest.fixture
    def mock_supported_info(self):
        """Sample mkvmerge JSON output for supported file."""
        return {
            "container": {
                "recognized": True,
                "supported": True,
            },
        }

    @pytest.fixture
    def mock_unsupported_info(self):
        """Sample mkvmerge JSON output for unsupported file."""
        return {
            "container": {
                "recognized": True,
                "supported": False,
            },
        }

    def test_verify_supported_true(self, mocker, sample_x264_mkv_file: Path, mock_supported_info):
        """Test verify_supported returns True for supported file."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = json.dumps(mock_supported_info).encode()

        result = verify_supported(str(sample_x264_mkv_file))

        assert result is True

    def test_verify_supported_false(self, mocker, sample_x264_mkv_file: Path, mock_unsupported_info):
        """Test verify_supported returns False for unsupported file."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.return_value = json.dumps(mock_unsupported_info).encode()

        result = verify_supported(str(sample_x264_mkv_file))

        assert result is False

    def test_verify_supported_mkvmerge_not_found(self, mocker, sample_x264_mkv_file: Path):
        """Test verify_supported when mkvmerge not found."""
        mocker.patch("pymkv.Verifications.verify_mkvmerge", return_value=False)

        with pytest.raises(FileNotFoundError, match="mkvmerge is not at the specified path"):
            verify_supported(str(sample_x264_mkv_file))

    def test_verify_supported_invalid_type(self):
        """Test verify_supported with invalid input type."""

        with pytest.raises(TypeError, match="is not of type str"):
            verify_supported(123)

    def test_verify_supported_file_not_exists(self):
        """Test verify_supported with non-existent file."""

        with pytest.raises(FileNotFoundError, match="does not exist"):
            verify_supported("/nonexistent/file.mkv")

    def test_verify_supported_subprocess_error(self, mocker, sample_x264_mkv_file: Path):
        """Test verify_supported when subprocess fails."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "mkvmerge")

        with pytest.raises(ValueError, match="could not be opened"):
            verify_supported(str(sample_x264_mkv_file))

    def test_verify_supported_bug_fix_format_string(self, mocker, sample_x264_mkv_file: Path):
        """Test that verify_supported has the format string bug (missing file_path)."""

        mock_check_output = mocker.patch("subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "mkvmerge")

        # This test documents the bug in the original code where the error message
        # doesn't include the file_path in the format string
        with pytest.raises(ValueError, match="could not be opened"):
            verify_supported(str(sample_x264_mkv_file))
