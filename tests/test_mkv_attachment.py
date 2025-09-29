"""Unit tests for MKVAttachment class."""

import json
from typing import TYPE_CHECKING

import pytest

from pymkv import MKVAttachment
from pymkv.errors import NoTracksError
from pymkv.errors import UnsupportedContainerError

if TYPE_CHECKING:
    from pymkv.models import Attachment


class TestMKVAttachmentInit:
    """Tests for MKVAttachment initialization."""

    def test_init_with_required_params(self, dummy_attachment_file):
        """Test initialization with only required parameters."""
        attachment = MKVAttachment(
            file_path=dummy_attachment_file,
            id_=1,
            size=1024,
        )

        assert attachment._id == 1
        assert attachment._size == 1024
        assert attachment._uid is None
        assert attachment.name is None
        assert attachment.description is None
        assert attachment._content_type is None
        assert attachment.attach_once is False
        assert attachment._file_path == dummy_attachment_file.expanduser().resolve()

    def test_init_with_all_params(self, dummy_attachment_file):
        """Test initialization with all parameters."""
        attachment = MKVAttachment(
            file_path=dummy_attachment_file,
            id_=2,
            size=2048,
            uid=12345,
            name="test_name",
            description="test_description",
            content_type="image/jpeg",
            attach_once=True,
        )

        assert attachment._id == 2
        assert attachment._size == 2048
        assert attachment._uid == 12345
        assert attachment.name == "test_name"
        assert attachment.description == "test_description"
        assert attachment._content_type == "image/jpeg"
        assert attachment.attach_once is True

    def test_file_path_expansion(self, tmp_path):
        """Test that file path is expanded and resolved."""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        attachment = MKVAttachment(
            file_path=test_file,
            id_=1,
            size=100,
        )

        assert attachment._file_path.is_absolute()
        assert attachment._file_path == test_file.resolve()


class TestMKVAttachmentFromJson:
    """Tests for MKVAttachment.from_json static method."""

    def test_from_json_minimal(self, dummy_attachment_file):
        """Test creating attachment from minimal JSON data."""
        data: Attachment = {
            "id": 1,
            "size": 1024,
            "file_name": "attachment.bin",
            "properties": {},
        }

        attachment = MKVAttachment.from_json(dummy_attachment_file, data)

        assert attachment._id == 1
        assert attachment._size == 1024
        assert attachment._uid is None
        assert attachment.name == "attachment.bin"
        assert attachment.description is None
        assert attachment._content_type is None

    def test_from_json_complete(self, dummy_attachment_file):
        """Test creating attachment from complete JSON data."""
        data: Attachment = {
            "id": 2,
            "size": 2048,
            "properties": {"uid": 67890},
            "file_name": "cover.jpg",
            "description": "Album cover",
            "content_type": "image/jpeg",
        }

        attachment = MKVAttachment.from_json(dummy_attachment_file, data)

        assert attachment._id == 2
        assert attachment._size == 2048
        assert attachment._uid == 67890
        assert attachment.name == "cover.jpg"
        assert attachment.description == "Album cover"
        assert attachment._content_type == "image/jpeg"


class TestMKVAttachmentFromFile:
    """Tests for MKVAttachment.from_file static method."""

    def test_from_file_success(self, mocker, dummy_attachment_file):
        """Test successfully loading attachment from file."""
        mock_json = {
            "container": {"supported": True},
            "attachments": [
                {
                    "id": 1,
                    "size": 1024,
                    "properties": {"uid": 123},
                    "file_name": "test.jpg",
                    "description": "Test image",
                    "content_type": "image/jpeg",
                },
            ],
        }
        mock_run = mocker.patch("pymkv.attachment.run_mkvmerge", return_value=json.dumps(mock_json))

        attachment = MKVAttachment.from_file(dummy_attachment_file)

        assert attachment._id == 1
        assert attachment._size == 1024
        assert attachment.name == "test.jpg"
        mock_run.assert_called_once()

    def test_from_file_unsupported_container(self, mocker, dummy_attachment_file):
        """Test error when container is not supported."""
        mock_json = {
            "container": {"supported": False},
        }
        mocker.patch("pymkv.attachment.run_mkvmerge", return_value=json.dumps(mock_json))

        with pytest.raises(UnsupportedContainerError):
            MKVAttachment.from_file(dummy_attachment_file)

    def test_from_file_no_attachments(self, mocker, dummy_attachment_file):
        """Test error when file has no attachments."""
        mock_json = {
            "container": {"supported": True},
            "attachments": [],
        }
        mocker.patch("pymkv.attachment.run_mkvmerge", return_value=json.dumps(mock_json))

        with pytest.raises(NoTracksError):
            MKVAttachment.from_file(dummy_attachment_file)

    def test_from_file_missing_attachments_key(self, mocker, dummy_attachment_file):
        """Test error when attachments key is missing."""
        mock_json = {
            "container": {"supported": True},
        }
        mocker.patch("pymkv.attachment.run_mkvmerge", return_value=json.dumps(mock_json))

        with pytest.raises(NoTracksError):
            MKVAttachment.from_file(dummy_attachment_file)

    def test_from_file_multiple_attachments_warning(self, mocker, dummy_attachment_file, caplog):
        """Test warning logged when multiple attachments found."""
        mock_json = {
            "container": {"supported": True},
            "attachments": [
                {
                    "id": 1,
                    "size": 1024,
                    "file_name": "first.bin",
                    "properties": {},
                },
                {
                    "id": 2,
                    "size": 2048,
                    "file_name": "second.bin",
                    "properties": {},
                },
            ],
        }
        mocker.patch("pymkv.attachment.run_mkvmerge", return_value=json.dumps(mock_json))

        attachment = MKVAttachment.from_file(dummy_attachment_file)

        assert attachment._id == 1  # First attachment selected
        assert "Multiple attachments detected" in caplog.text

    def test_from_file_path_types(self, mocker, dummy_attachment_file):
        """Test from_file accepts different path types."""
        mock_json = {
            "container": {"supported": True},
            "attachments": [
                {
                    "id": 1,
                    "size": 1024,
                    "file_name": "test.bin",
                    "properties": {},
                },
            ],
        }
        mock_run = mocker.patch("pymkv.attachment.run_mkvmerge", return_value=json.dumps(mock_json))

        # Test with string
        MKVAttachment.from_file(str(dummy_attachment_file))

        # Test with Path
        MKVAttachment.from_file(dummy_attachment_file)

        assert mock_run.call_count == 2


class TestMKVAttachmentComparison:
    """Tests for MKVAttachment comparison methods."""

    def test_equality_same_id(self, dummy_attachment_file):
        """Test equality for attachments with same ID."""
        att1 = MKVAttachment(dummy_attachment_file, id_=1, size=100)
        att2 = MKVAttachment(dummy_attachment_file, id_=1, size=200)

        assert att1 == att2

    def test_equality_different_id(self, dummy_attachment_file):
        """Test inequality for attachments with different IDs."""
        att1 = MKVAttachment(dummy_attachment_file, id_=1, size=100)
        att2 = MKVAttachment(dummy_attachment_file, id_=2, size=100)

        assert att1 != att2

    def test_equality_not_implemented(self, dummy_attachment_file):
        """Test equality raises NotImplementedError for non-MKVAttachment objects."""
        att = MKVAttachment(dummy_attachment_file, id_=1, size=100)

        with pytest.raises(NotImplementedError):
            att == "not an attachment"  # noqa: B015

    def test_less_than(self, dummy_attachment_file):
        """Test less than comparison."""
        att1 = MKVAttachment(dummy_attachment_file, id_=1, size=100)
        att2 = MKVAttachment(dummy_attachment_file, id_=2, size=100)

        assert att1 < att2
        assert not att2 < att1

    def test_sorting(self, dummy_attachment_file):
        """Test attachments can be sorted by ID."""
        att3 = MKVAttachment(dummy_attachment_file, id_=3, size=100)
        att1 = MKVAttachment(dummy_attachment_file, id_=1, size=100)
        att2 = MKVAttachment(dummy_attachment_file, id_=2, size=100)

        sorted_atts = sorted([att3, att1, att2])

        assert sorted_atts == [att1, att2, att3]

    def test_hash(self, dummy_attachment_file):
        """Test attachment hashing."""
        att1 = MKVAttachment(dummy_attachment_file, id_=1, size=100)
        att2 = MKVAttachment(dummy_attachment_file, id_=1, size=200)
        att3 = MKVAttachment(dummy_attachment_file, id_=2, size=100)

        assert hash(att1) == hash(att2)
        assert hash(att1) != hash(att3)

    def test_hashable_in_set(self, dummy_attachment_file):
        """Test attachments can be used in sets."""
        att1 = MKVAttachment(dummy_attachment_file, id_=1, size=100)
        att2 = MKVAttachment(dummy_attachment_file, id_=1, size=200)
        att3 = MKVAttachment(dummy_attachment_file, id_=2, size=100)

        attachment_set = {att1, att2, att3}

        assert len(attachment_set) == 2  # att1 and att2 are considered same


class TestMKVAttachmentCommand:
    """Tests for MKVAttachment.command method."""

    def test_command_minimal(self, dummy_attachment_file):
        """Test command generation with minimal options."""
        attachment = MKVAttachment(dummy_attachment_file, id_=1, size=100)

        command = attachment.command()

        assert command == ["--attach-file", str(dummy_attachment_file.resolve())]

    def test_command_with_name(self, dummy_attachment_file):
        """Test command generation with name."""
        attachment = MKVAttachment(
            dummy_attachment_file,
            id_=1,
            size=100,
            name="cover.jpg",
        )

        command = attachment.command()

        assert "--attachment-name" in command
        assert "cover.jpg" in command
        assert command[-2:] == ["--attach-file", str(dummy_attachment_file.resolve())]

    def test_command_with_description(self, dummy_attachment_file):
        """Test command generation with description."""
        attachment = MKVAttachment(
            dummy_attachment_file,
            id_=1,
            size=100,
            description="Album cover",
        )

        command = attachment.command()

        assert "--attachment-description" in command
        assert "Album cover" in command

    def test_command_with_mime_type(self, dummy_attachment_file):
        """Test command generation with MIME type."""
        attachment = MKVAttachment(
            dummy_attachment_file,
            id_=1,
            size=100,
            content_type="image/jpeg",
        )

        command = attachment.command()

        assert "--attachment-mime-type" in command
        assert "image/jpeg" in command

    def test_command_attach_once(self, dummy_attachment_file):
        """Test command generation with attach_once flag."""
        attachment = MKVAttachment(
            dummy_attachment_file,
            id_=1,
            size=100,
            attach_once=True,
        )

        command = attachment.command()

        assert "--attach-file-once" in command
        assert "--attach-file" not in command

    def test_command_all_options(self, dummy_attachment_file):
        """Test command generation with all options."""
        attachment = MKVAttachment(
            dummy_attachment_file,
            id_=1,
            size=100,
            name="cover.jpg",
            description="Album cover",
            content_type="image/jpeg",
            attach_once=True,
        )

        command = attachment.command()

        assert "--attachment-name" in command
        assert "cover.jpg" in command
        assert "--attachment-description" in command
        assert "Album cover" in command
        assert "--attachment-mime-type" in command
        assert "image/jpeg" in command
        assert "--attach-file-once" in command
        assert command[-1] == str(dummy_attachment_file.resolve())

    def test_command_order(self, dummy_attachment_file):
        """Test that file path is always last in command."""
        attachment = MKVAttachment(
            dummy_attachment_file,
            id_=1,
            size=100,
            name="test",
            description="desc",
            content_type="text/plain",
        )

        command = attachment.command()

        # The last two elements should be attach flag and file path
        assert command[-2] in ["--attach-file", "--attach-file-once"]
        assert command[-1] == str(dummy_attachment_file.resolve())


class TestMKVAttachmentMutability:
    """Tests for mutable vs immutable attributes."""

    def test_mutable_attributes_can_change(self, dummy_attachment_file):
        """Test that mutable attributes can be changed."""
        attachment = MKVAttachment(dummy_attachment_file, id_=1, size=100)

        attachment.name = "new_name"
        attachment.description = "new_description"
        attachment.attach_once = True

        assert attachment.name == "new_name"
        assert attachment.description == "new_description"
        assert attachment.attach_once is True

    def test_immutable_attributes_set_once(self, dummy_attachment_file):
        """Test that immutable attributes are set during initialization."""
        attachment = MKVAttachment(
            dummy_attachment_file,
            id_=1,
            size=100,
            uid=123,
            content_type="image/jpeg",
        )

        # These should not change
        assert attachment._id == 1
        assert attachment._size == 100
        assert attachment._uid == 123
        assert attachment._content_type == "image/jpeg"
