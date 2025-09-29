import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pymkv.errors import InvalidLanguageError
from pymkv.errors import NoTracksError
from pymkv.errors import UnsupportedContainerError
from pymkv.track import MKVTrack

if TYPE_CHECKING:
    from pymkv.models import Track


class TestMKVTrackInit:
    """Tests for MKVTrack initialization."""

    def test_init_minimal(self, tmp_path: Path):
        """Test initialization with minimal required parameters."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(
            file_path=file_path,
            track_id=0,
            track_codec="h264",
            track_type="video",
        )

        assert track._file_path == file_path.resolve()
        assert track._track_id == 0
        assert track._track_codec == "h264"
        assert track._track_type == "video"
        assert track.track_name is None
        assert track.language is None
        assert track.default_track is False
        assert track.forced_track is False

    def test_init_full(self, tmp_path: Path):
        """Test initialization with all parameters."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(
            file_path=file_path,
            track_id=1,
            track_codec="aac",
            track_type="audio",
            track_name="English Audio",
            language="eng",
            default_track=True,
            forced_track=True,
        )

        assert track._file_path == file_path.resolve()
        assert track._track_id == 1
        assert track._track_codec == "aac"
        assert track._track_type == "audio"
        assert track.track_name == "English Audio"
        assert track.language == "eng"
        assert track.default_track is True
        assert track.forced_track is True

    def test_init_default_control_options(self, tmp_path: Path):
        """Test that output control options are initialized to False."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")

        assert track.no_chapters is False
        assert track.no_global_tags is False
        assert track.no_track_tags is False
        assert track.no_attachments is False
        assert track.tags_file is None


class TestMKVTrackFromJson:
    """Tests for creating MKVTrack from JSON data."""

    def test_from_json_minimal(self, tmp_path: Path):
        """Test creating track from minimal JSON data (no properties field)."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        data: Track = {
            "id": 0,
            "codec": "h264",
            "type": "video",
        }

        track = MKVTrack.from_json(file_path, data)

        assert track._track_id == 0
        assert track._track_codec == "h264"
        assert track._track_type == "video"
        assert track.track_name is None
        assert track.language is None
        assert track.default_track is False
        assert track.forced_track is False

    def test_from_json_with_properties(self, tmp_path: Path):
        """Test creating track from JSON with all relevant properties."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        data: Track = {
            "id": 1,
            "codec": "aac",
            "type": "audio",
            "properties": {
                "track_name": "English",
                "language": "eng",
                "default_track": True,
                "forced_track": True,
            },
        }

        track = MKVTrack.from_json(file_path, data)

        assert track._track_id == 1
        assert track._track_codec == "aac"
        assert track._track_type == "audio"
        assert track.track_name == "English"
        assert track.language == "eng"
        assert track.default_track is True
        assert track.forced_track is True

    def test_from_json_with_partial_properties(self, tmp_path: Path):
        """Test creating track from JSON with some properties missing."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        data: Track = {
            "id": 2,
            "codec": "subrip",
            "type": "subtitles",
            "properties": {
                "language": "fra",
            },
        }

        track = MKVTrack.from_json(file_path, data)

        assert track._track_id == 2
        assert track.language == "fra"
        assert track.track_name is None
        assert track.default_track is False


class TestMKVTrackFromFile:
    """Tests for creating MKVTrack from file."""

    def test_from_file_success(self, mocker, tmp_path: Path):
        """Test successfully creating track from file."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        mock_output = {
            "container": {"supported": True},
            "tracks": [
                {
                    "id": 0,
                    "codec": "h264",
                    "type": "video",
                    "properties": {
                        "language": "eng",
                    },
                },
            ],
        }

        mocker.patch("pymkv.track.run_mkvmerge", return_value=json.dumps(mock_output))

        track = MKVTrack.from_file(file_path)

        assert track._track_id == 0
        assert track._track_codec == "h264"
        assert track._track_type == "video"
        assert track.language == "eng"

    def test_from_file_unsupported_container(self, mocker, tmp_path: Path):
        """Test that UnsupportedContainerError is raised for unsupported containers."""
        file_path = tmp_path / "test.avi"
        file_path.touch()

        mock_output = {
            "container": {"supported": False},
        }

        mocker.patch("pymkv.track.run_mkvmerge", return_value=json.dumps(mock_output))

        with pytest.raises(UnsupportedContainerError):
            MKVTrack.from_file(file_path)

    def test_from_file_no_tracks(self, mocker, tmp_path: Path):
        """Test that NoTracksError is raised when file has no tracks."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        mock_output = {
            "container": {"supported": True},
            "tracks": [],
        }

        mocker.patch("pymkv.track.run_mkvmerge", return_value=json.dumps(mock_output))

        with pytest.raises(NoTracksError):
            MKVTrack.from_file(file_path)

    def test_from_file_multiple_tracks_warning(self, mocker, tmp_path: Path):
        """Test that warning is logged when file has multiple tracks."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        mock_output = {
            "container": {"supported": True},
            "tracks": [
                {"id": 0, "codec": "h264", "type": "video"},
                {"id": 1, "codec": "aac", "type": "audio"},
            ],
        }

        mock_logger = mocker.patch("pymkv.track.logger")
        mocker.patch("pymkv.track.run_mkvmerge", return_value=json.dumps(mock_output))

        track = MKVTrack.from_file(file_path)

        assert track._track_id == 0
        mock_logger.warning.assert_called_once()
        assert "Multiple tracks detected" in mock_logger.warning.call_args[0][0]


class TestMKVTrackComparison:
    """Tests for MKVTrack comparison methods."""

    def test_equality_same_id(self, tmp_path: Path):
        """Test that tracks with same ID are equal."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track1 = MKVTrack(file_path, 0, "h264", "video")
        track2 = MKVTrack(file_path, 0, "aac", "audio")

        assert track1 == track2

    def test_equality_different_id(self, tmp_path: Path):
        """Test that tracks with different IDs are not equal."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track1 = MKVTrack(file_path, 0, "h264", "video")
        track2 = MKVTrack(file_path, 1, "h264", "video")

        assert track1 != track2

    def test_equality_not_implemented(self, tmp_path: Path):
        """Test that comparing with non-MKVTrack raises NotImplementedError."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")

        with pytest.raises(NotImplementedError):
            track == "not a track"  # noqa: B015

    def test_less_than(self, tmp_path: Path):
        """Test less than comparison."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track1 = MKVTrack(file_path, 0, "h264", "video")
        track2 = MKVTrack(file_path, 1, "aac", "audio")

        assert track1 < track2
        assert not track2 < track1

    def test_greater_than(self, tmp_path: Path):
        """Test greater than comparison (via total_ordering)."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track1 = MKVTrack(file_path, 0, "h264", "video")
        track2 = MKVTrack(file_path, 1, "aac", "audio")

        assert track2 > track1
        assert not track1 > track2

    def test_hash(self, tmp_path: Path):
        """Test that tracks can be hashed and used in sets."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track1 = MKVTrack(file_path, 0, "h264", "video")
        track2 = MKVTrack(file_path, 0, "h264", "video")
        track3 = MKVTrack(file_path, 1, "aac", "audio")

        assert hash(track1) == hash(track2)
        assert hash(track1) != hash(track3)

        track_set = {track1, track2, track3}
        assert len(track_set) == 2


class TestMKVTrackLanguageProperty:
    """Tests for language property setter and getter."""

    def test_language_valid_code(self, tmp_path: Path):
        """Test setting valid ISO 639-2 language code."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        track.language = "eng"

        assert track.language == "eng"

    def test_language_none(self, tmp_path: Path):
        """Test setting language to None."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video", language="eng")
        track.language = None

        assert track.language is None

    def test_language_und(self, tmp_path: Path):
        """Test setting language to 'und' (undetermined)."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        track.language = "und"

        assert track.language == "und"

    def test_language_und_case_insensitive(self, tmp_path: Path):
        """Test that 'und' is case insensitive."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        track.language = "UND"

        assert track.language == "UND"

    def test_language_invalid_code(self, mocker, tmp_path: Path):
        """Test that invalid language code raises InvalidLanguageError."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        mocker.patch("pymkv.track.is_iso_639_2_language_code", return_value=False)
        mock_logger = mocker.patch("pymkv.track.logger")

        track = MKVTrack(file_path, 0, "h264", "video")

        with pytest.raises(InvalidLanguageError, match="'invalid' is not a valid ISO639-2 language code"):
            track.language = "invalid"

        mock_logger.error.assert_called_once()


class TestMKVTrackProperties:
    """Tests for read-only properties."""

    def test_track_codec_property(self, tmp_path: Path):
        """Test track_codec property returns correct value."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")

        assert track.track_codec == "h264"

    def test_track_type_property(self, tmp_path: Path):
        """Test track_type property returns correct value."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")

        assert track.track_type == "video"


class TestMKVTrackCommand:
    """Tests for command generation."""

    def test_command_minimal(self, tmp_path: Path):
        """Test command generation with minimal track configuration."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        command = track.command()

        assert "--default-track-flag" in command
        assert "0:0" in command
        assert "--forced-display-flag" in command
        assert "--video-tracks" in command
        assert "0" in command
        assert "--no-audio" in command
        assert "--no-subtitles" in command
        assert str(file_path) in command

    def test_command_with_track_name(self, tmp_path: Path):
        """Test command generation with track name."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video", track_name="Main Video")
        command = track.command()

        assert "--track-name" in command
        assert "0:Main Video" in command

    def test_command_with_language(self, tmp_path: Path):
        """Test command generation with language."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video", language="eng")
        command = track.command()

        assert "--language" in command
        assert "0:eng" in command

    def test_command_with_tags_file(self, tmp_path: Path):
        """Test command generation with tags file."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()
        tags_file = tmp_path / "tags.xml"
        tags_file.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        track.tags_file = tags_file
        command = track.command()

        assert "--tags" in command
        assert f"0:{tags_file}" in command

    def test_command_default_track_true(self, tmp_path: Path):
        """Test command generation with default_track=True."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video", default_track=True)
        command = track.command()

        assert "--default-track-flag" in command
        assert "0:1" in command

    def test_command_forced_track_true(self, tmp_path: Path):
        """Test command generation with forced_track=True."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video", forced_track=True)
        command = track.command()

        assert "--forced-display-flag" in command
        assert "0:1" in command

    def test_command_audio_track(self, tmp_path: Path):
        """Test command generation for audio track."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 1, "aac", "audio")
        command = track.command()

        assert "--audio-tracks" in command
        assert "1" in command
        assert "--no-video" in command
        assert "--no-subtitles" in command

    def test_command_subtitle_track(self, tmp_path: Path):
        """Test command generation for subtitle track."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 2, "subrip", "subtitles")
        command = track.command()

        assert "--subtitle-tracks" in command
        assert "2" in command
        assert "--no-video" in command
        assert "--no-audio" in command

    def test_command_no_chapters(self, tmp_path: Path):
        """Test command generation with no_chapters=True."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        track.no_chapters = True
        command = track.command()

        assert "--no-chapters" in command

    def test_command_no_global_tags(self, tmp_path: Path):
        """Test command generation with no_global_tags=True."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        track.no_global_tags = True
        command = track.command()

        assert "--no-global-tags" in command

    def test_command_no_track_tags(self, tmp_path: Path):
        """Test command generation with no_track_tags=True."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        track.no_track_tags = True
        command = track.command()

        assert "--no-track-tags" in command

    def test_command_no_attachments(self, tmp_path: Path):
        """Test command generation with no_attachments=True."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        track.no_attachments = True
        command = track.command()

        assert "--no-attachments" in command

    def test_command_all_exclusions(self, tmp_path: Path):
        """Test command generation with all exclusion flags."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "h264", "video")
        track.no_chapters = True
        track.no_global_tags = True
        track.no_track_tags = True
        track.no_attachments = True
        command = track.command()

        assert "--no-chapters" in command
        assert "--no-global-tags" in command
        assert "--no-track-tags" in command
        assert "--no-attachments" in command

    def test_command_full_configuration(self, tmp_path: Path):
        """Test command generation with full track configuration."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()
        tags_file = tmp_path / "tags.xml"
        tags_file.touch()

        track = MKVTrack(
            file_path,
            1,
            "aac",
            "audio",
            track_name="English Audio",
            language="eng",
            default_track=True,
            forced_track=True,
        )
        track.tags_file = tags_file
        track.no_chapters = True
        track.no_global_tags = True

        command = track.command()

        assert "--track-name" in command
        assert "1:English Audio" in command
        assert "--language" in command
        assert "1:eng" in command
        assert "--tags" in command
        assert "--default-track-flag" in command
        assert "1:1" in command
        assert "--forced-display-flag" in command
        assert "--audio-tracks" in command
        assert "--no-video" in command
        assert "--no-subtitles" in command
        assert "--no-chapters" in command
        assert "--no-global-tags" in command
        assert str(file_path) == command[-1]

    def test_command_unknown_track_type(self, tmp_path: Path):
        """Test command generation with unknown track type."""
        file_path = tmp_path / "test.mkv"
        file_path.touch()

        track = MKVTrack(file_path, 0, "unknown", "unknown")
        command = track.command()

        # Should still generate basic command without track type specific flags
        assert "--default-track-flag" in command
        assert "--forced-display-flag" in command
        assert str(file_path) in command
        # Should not have track type specific flags
        assert "--video-tracks" not in command
        assert "--audio-tracks" not in command
        assert "--subtitle-tracks" not in command
