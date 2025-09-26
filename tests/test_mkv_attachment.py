from pathlib import Path

import pytest

from pymkv.attachment import MKVAttachment
from pymkv.errors import InputFileNotFoundError


@pytest.fixture
def dummy_attachment_file(tmp_path: Path) -> Path:
    """Create a dummy file to be used as an attachment."""
    file_path = tmp_path / "attachment.txt"
    file_path.write_text("This is a test attachment.")
    return file_path


class TestMKVAttachment:
    """Tests for the MKVAttachment class."""

    def test_init_with_valid_file(self, dummy_attachment_file: Path):
        """
        Test that an MKVAttachment can be initialized with a valid file path.
        """
        attachment = MKVAttachment(str(dummy_attachment_file))
        assert attachment.file_path == str(dummy_attachment_file)
        assert attachment.name is None
        assert attachment.description is None
        assert not attachment.attach_once
        assert attachment.mime_type == "text/plain"

    def test_init_with_options(self, dummy_attachment_file: Path):
        """
        Test initializing an MKVAttachment with name, description, and attach_once.
        """
        attachment = MKVAttachment(
            str(dummy_attachment_file),
            name="Test Attachment",
            description="A test file.",
            attach_once=True,
        )
        assert attachment.name == "Test Attachment"
        assert attachment.description == "A test file."
        assert attachment.attach_once is True

    def test_init_with_nonexistent_file(self):
        """
        Test that initializing with a non-existent file path raises FileNotFoundError.
        """
        with pytest.raises(InputFileNotFoundError):
            MKVAttachment("nonexistent/file.txt")

    def test_file_path_setter(self, dummy_attachment_file: Path, tmp_path: Path):
        """
        Test the file_path property setter with a valid new path.
        """
        attachment = MKVAttachment(str(dummy_attachment_file), name="Old Name")

        new_file = tmp_path / "new_attachment.jpg"
        new_file.touch()

        attachment.file_path = str(new_file)
        assert attachment.file_path == str(new_file)
        assert attachment.mime_type == "image/jpeg"
        # Per the class implementation, setting file_path resets the name
        assert attachment.name is None

    def test_file_path_setter_nonexistent(self, dummy_attachment_file: Path):
        """
        Test that setting file_path to a non-existent file raises FileNotFoundError.
        """
        attachment = MKVAttachment(str(dummy_attachment_file))
        with pytest.raises(InputFileNotFoundError):
            attachment.file_path = "nonexistent/new_file.txt"
