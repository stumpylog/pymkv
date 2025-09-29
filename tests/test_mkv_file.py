import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from iso639 import Lang
from pytest_mock import MockerFixture

from pymkv.attachment import MKVAttachment
from pymkv.errors import InputFileNotFoundError
from pymkv.errors import UnsupportedContainerError
from pymkv.file import MKVFile
from pymkv.timestamp import FrameRange
from pymkv.timestamp import TimeRange
from pymkv.timestamp import Timestamp
from pymkv.track import MKVTrack

if TYPE_CHECKING:
    from pymkv.models import MkvmergeIdentificationOutput


class TestMKVFileInit:
    """Test MKVFile initialization."""

    def test_init_with_no_args(self):
        mkv = MKVFile()
        assert mkv.title is None
        assert mkv._chapters_file is None
        assert mkv.chapter_language is None
        assert mkv._global_tags_file is None
        assert mkv._link_to_previous_file is None
        assert mkv._link_to_next_file is None
        assert mkv.tracks == []
        assert mkv.attachments == []
        assert mkv._split_options == []

    def test_init_with_title(self):
        mkv = MKVFile(title="Test Movie")
        assert mkv.title == "Test Movie"
        assert mkv.tracks == []
        assert mkv.attachments == []


class TestMKVFileFromFile:
    """Test MKVFile.from_file() static method."""

    def test_from_file_nonexistent(self, tmp_path: Path):
        nonexistent = tmp_path / "doesnotexist.mkv"
        with pytest.raises(InputFileNotFoundError):
            MKVFile.from_file(nonexistent)

    def test_from_file_success(self, sample_x264_mkv_file: Path, mocker: MockerFixture):
        mock_run = mocker.patch("pymkv.file.run_mkvmerge")
        mock_from_json = mocker.patch("pymkv.file.MKVFile.from_json")
        mock_mkv = MagicMock()
        mock_from_json.return_value = mock_mkv

        mock_data = {"container": {"supported": True}}
        mock_run.return_value = json.dumps(mock_data)

        result = MKVFile.from_file(sample_x264_mkv_file)

        assert result == mock_mkv
        mock_run.assert_called_once()
        mock_from_json.assert_called_once()

    def test_from_file_unsupported_container(self, sample_x264_mkv_file: Path, mocker: MockerFixture):
        mock_run = mocker.patch("pymkv.file.run_mkvmerge")
        mock_data = {"container": {"supported": False}, "tracks": [], "attachments": []}
        mock_run.return_value = json.dumps(mock_data)

        with pytest.raises(UnsupportedContainerError):
            MKVFile.from_file(sample_x264_mkv_file)


class TestMKVFileFromJson:
    """Test MKVFile.from_json() static method."""

    def test_from_json_minimal(self, sample_x264_mkv_file: Path):
        data: MkvmergeIdentificationOutput = {
            "container": {"supported": True, "recognized": True, "properties": {}},
            "tracks": [],
            "attachments": [],
        }
        mkv = MKVFile.from_json(sample_x264_mkv_file, data)
        assert mkv.title is None
        assert len(mkv.tracks) == 0
        assert len(mkv.attachments) == 0

    def test_from_json_with_title(self, sample_x264_mkv_file: Path):
        data: MkvmergeIdentificationOutput = {
            "container": {"supported": True, "recognized": True, "properties": {"title": "Test Title"}},
            "tracks": [],
            "attachments": [],
        }
        mkv = MKVFile.from_json(sample_x264_mkv_file, data)
        assert mkv.title == "Test Title"

    def test_from_json_unsupported(self, sample_x264_mkv_file: Path):
        data: MkvmergeIdentificationOutput = {
            "container": {"supported": False, "recognized": True},
            "tracks": [],
            "attachments": [],
        }
        with pytest.raises(UnsupportedContainerError):
            MKVFile.from_json(sample_x264_mkv_file, data)


class TestMKVFileCommand:
    """Test MKVFile.command() method."""

    def test_command_basic(self, tmp_path: Path, mocker: MockerFixture):
        mocker.patch("pymkv.file.get_mkvmerge_path", return_value="/usr/bin/mkvmerge")
        mkv = MKVFile()
        output = tmp_path / "output.mkv"

        cmd = mkv.command(output)

        assert cmd[0] == "/usr/bin/mkvmerge"
        assert "-o" in cmd
        assert str(output) in cmd

    def test_command_with_title(self, tmp_path: Path, mocker: MockerFixture):
        mocker.patch("pymkv.file.get_mkvmerge_path", return_value="/usr/bin/mkvmerge")
        mkv = MKVFile(title="Test Movie")
        output = tmp_path / "output.mkv"

        cmd = mkv.command(output)

        assert "--title" in cmd
        assert "Test Movie" in cmd

    def test_command_with_tracks(self, tmp_path: Path, mocker: MockerFixture):
        mocker.patch("pymkv.file.get_mkvmerge_path", return_value="/usr/bin/mkvmerge")
        mkv = MKVFile()
        mock_track = MagicMock(spec=MKVTrack)
        mock_track.command.return_value = ["--track-name", "0:Video"]
        mkv.tracks.append(mock_track)
        output = tmp_path / "output.mkv"

        cmd = mkv.command(output)

        assert "--track-name" in cmd
        assert "0:Video" in cmd
        mock_track.command.assert_called_once()

    def test_command_with_chapters(self, tmp_path: Path, mocker: MockerFixture):
        mocker.patch("pymkv.file.get_mkvmerge_path", return_value="/usr/bin/mkvmerge")
        mkv = MKVFile()
        chapters_file = tmp_path / "chapters.xml"
        chapters_file.write_text("<Chapters></Chapters>")
        mkv.chapters(chapters_file, language=Lang("eng"))
        output = tmp_path / "output.mkv"

        cmd = mkv.command(output)

        assert "--chapter-language" in cmd
        assert "eng" in cmd
        assert "--chapters" in cmd
        assert str(chapters_file) in cmd

    def test_command_with_global_tags(self, tmp_path: Path, mocker: MockerFixture):
        mocker.patch("pymkv.file.get_mkvmerge_path", return_value="/usr/bin/mkvmerge")
        mkv = MKVFile()
        tags_file = tmp_path / "tags.xml"
        tags_file.write_text("<Tags></Tags>")
        mkv.global_tags(tags_file)
        output = tmp_path / "output.mkv"

        cmd = mkv.command(output)

        assert "--global-tags" in cmd
        assert str(tags_file) in cmd

    def test_command_with_linking(self, tmp_path: Path, mocker: MockerFixture):
        mocker.patch("pymkv.file.get_mkvmerge_path", return_value="/usr/bin/mkvmerge")
        mkv = MKVFile()
        prev_file = tmp_path / "prev.mkv"
        next_file = tmp_path / "next.mkv"
        mkv.link_to_previous(prev_file)
        mkv.link_to_next(next_file)
        output = tmp_path / "output.mkv"

        cmd = mkv.command(output)

        assert "--link-to-previous" in cmd
        assert "--link-to-next" in cmd


class TestMKVFileMux:
    """Test MKVFile.mux() method."""

    def test_mux_success(self, tmp_path: Path, mocker: MockerFixture):
        mock_run = mocker.patch("pymkv.file.run_mkvmerge")
        mock_run.return_value = "Muxing completed successfully"
        mocker.patch("pymkv.file.get_mkvmerge_path", return_value="/usr/bin/mkvmerge")

        mkv = MKVFile()
        output = tmp_path / "output.mkv"

        result = mkv.mux(output)

        assert result == "Muxing completed successfully"
        mock_run.assert_called_once()


class TestMKVFileAddMethods:
    """Test add_file, add_track, and add_attachment methods."""

    def test_add_file_mkvfile_object(self):
        mkv1 = MKVFile()
        mkv2 = MKVFile()
        mock_track = MagicMock(spec=MKVTrack)
        mkv2.tracks.append(mock_track)

        mkv1.add_file(mkv2)

        assert len(mkv1.tracks) == 1
        assert mkv1.tracks[0] == mock_track

    def test_add_file_path(self, sample_x264_mkv_file: Path, mocker: MockerFixture):
        mock_from_file = mocker.patch("pymkv.file.MKVFile.from_file")
        mock_mkv = MagicMock()
        mock_track = MagicMock(spec=MKVTrack)
        mock_mkv.tracks = [mock_track]
        mock_from_file.return_value = mock_mkv

        mkv = MKVFile()
        mkv.add_file(sample_x264_mkv_file)

        assert len(mkv.tracks) == 1
        mock_from_file.assert_called_once_with(sample_x264_mkv_file)

    def test_add_track_object(self):
        mkv = MKVFile()
        mock_track = MagicMock(spec=MKVTrack)

        mkv.add_track(mock_track)

        assert len(mkv.tracks) == 1
        assert mkv.tracks[0] == mock_track

    def test_add_track_path(self, sample_x264_mkv_file: Path, mocker: MockerFixture):
        mock_from_file = mocker.patch("pymkv.file.MKVTrack.from_file")
        mock_track = MagicMock(spec=MKVTrack)
        mock_from_file.return_value = mock_track

        mkv = MKVFile()
        mkv.add_track(sample_x264_mkv_file)

        assert len(mkv.tracks) == 1
        mock_from_file.assert_called_once_with(sample_x264_mkv_file)

    def test_add_attachment_object(self):
        mkv = MKVFile()
        mock_attachment = MagicMock(spec=MKVAttachment)

        mkv.add_attachment(mock_attachment)

        assert len(mkv.attachments) == 1
        assert mkv.attachments[0] == mock_attachment

    def test_add_attachment_path(self, dummy_attachment_file: Path, mocker: MockerFixture):
        mock_from_file = mocker.patch("pymkv.file.MKVAttachment.from_file")
        mock_attachment = MagicMock(spec=MKVAttachment)
        mock_from_file.return_value = mock_attachment

        mkv = MKVFile()
        mkv.add_attachment(dummy_attachment_file)

        assert len(mkv.attachments) == 1
        mock_from_file.assert_called_once_with(dummy_attachment_file)


class TestMKVFileSplitMethods:
    """Test all split methods."""

    def test_split_none(self):
        mkv = MKVFile()
        mkv._split_options = ["--split", "size:100M"]

        mkv.split_none()

        assert mkv._split_options == []

    def test_split_size_without_link(self):
        mkv = MKVFile()

        mkv.split_size(1024)

        assert mkv._split_options == ["--split", "size:1024"]

    def test_split_size_with_link(self):
        mkv = MKVFile()

        mkv.split_size(2048, link=True)

        assert mkv._split_options == ["--split", "size:2048", "--link"]

    def test_split_duration_without_link(self, mocker: MockerFixture):
        mocker.patch("pymkv.file.Timestamp.from_seconds", return_value="00:01:30.000")
        mkv = MKVFile()

        mkv.split_duration(90)

        assert mkv._split_options == ["--split", "duration:00:01:30.000"]

    def test_split_duration_with_link(self, mocker: MockerFixture):
        mocker.patch("pymkv.file.Timestamp.from_seconds", return_value="00:02:00.000")
        mkv = MKVFile()

        mkv.split_duration(120, link=True)

        assert mkv._split_options == ["--split", "duration:00:02:00.000", "--link"]

    def test_split_timestamps_without_link(self):
        mkv = MKVFile()
        ts1 = Timestamp(60)  # 1 minute
        ts2 = Timestamp(120)  # 2 minutes

        mkv.split_timestamps([ts1, ts2])

        assert "--split" in mkv._split_options
        assert "timestamps:" in mkv._split_options[1]
        assert "--link" not in mkv._split_options

    def test_split_timestamps_with_link(self):
        mkv = MKVFile()
        ts1 = Timestamp(60)  # 1 minute

        mkv.split_timestamps([ts1], link=True)

        assert "--split" in mkv._split_options
        assert "--link" in mkv._split_options

    def test_split_frames_without_link(self):
        mkv = MKVFile()

        mkv.split_frames([100, 200, 300])

        assert mkv._split_options == ["--split", "frames:100,200,300"]

    def test_split_frames_with_link(self):
        mkv = MKVFile()

        mkv.split_frames([150, 250], link=True)

        assert mkv._split_options == ["--split", "frames:150,250", "--link"]

    def test_split_by_parts_single_range(self):
        mkv = MKVFile()
        ts1 = Timestamp(60)  # 1 minute
        ts2 = Timestamp(120)  # 2 minutes
        range1 = TimeRange(ts1, ts2)

        mkv.split_by_parts([range1])

        assert "--split" in mkv._split_options
        assert "parts:" in mkv._split_options[1]

    def test_split_by_parts_multiple_ranges(self):
        mkv = MKVFile()
        ts1 = Timestamp(60)  # 1 minute
        ts2 = Timestamp(120)  # 2 minutes
        ts3 = Timestamp(180)  # 3 minutes
        range1 = TimeRange(ts1, ts2)
        range2 = TimeRange(ts2, ts3)

        mkv.split_by_parts([range1, range2])

        assert "--split" in mkv._split_options
        assert "parts:" in mkv._split_options[1]

    def test_split_by_parts_with_none_start(self):
        mkv = MKVFile()
        ts1 = Timestamp(60)  # 1 minute
        range1 = TimeRange(None, ts1)

        mkv.split_by_parts([range1])

        assert "--split" in mkv._split_options

    def test_split_by_parts_with_none_end(self):
        mkv = MKVFile()
        ts1 = Timestamp(60)  # 1 minute
        ts2 = Timestamp(120)  # 2 minutes
        range1 = TimeRange(ts1, ts2)
        range2 = TimeRange(ts2, None)

        mkv.split_by_parts([range1, range2])

        assert "--split" in mkv._split_options

    def test_split_by_parts_empty_list(self):
        mkv = MKVFile()

        with pytest.raises(ValueError, match="At least one time range must be specified"):
            mkv.split_by_parts([])

    def test_split_by_parts_invalid_ordering_within_range(self):
        mkv = MKVFile()
        ts1 = Timestamp(120)  # 2 minutes
        ts2 = Timestamp(60)  # 1 minute
        range1 = TimeRange(ts1, ts2)

        with pytest.raises(ValueError, match="start timestamp must be before end timestamp"):
            mkv.split_by_parts([range1])

    def test_split_by_parts_invalid_ordering_between_ranges(self):
        mkv = MKVFile()
        ts1 = Timestamp(60)  # 1 minute
        ts2 = Timestamp(180)  # 3 minutes
        ts3 = Timestamp(120)  # 2 minutes
        ts4 = Timestamp(240)  # 4 minutes
        range1 = TimeRange(ts1, ts2)
        range2 = TimeRange(ts3, ts4)

        with pytest.raises(ValueError, match="start timestamp must be after previous range's end"):
            mkv.split_by_parts([range1, range2])

    def test_split_by_parts_with_link(self):
        mkv = MKVFile()
        ts1 = Timestamp(60)  # 1 minute
        ts2 = Timestamp(120)  # 2 minutes
        range1 = TimeRange(ts1, ts2)

        mkv.split_by_parts([range1], link=True)

        assert "--link" in mkv._split_options

    def test_split_by_parts_frames_single_range(self):
        mkv = MKVFile()
        range1 = FrameRange(1, 100)

        mkv.split_by_parts_frames([range1])

        assert "--split" in mkv._split_options
        assert "parts-frames:" in mkv._split_options[1]

    def test_split_by_parts_frames_multiple_ranges(self):
        mkv = MKVFile()
        range1 = FrameRange(1, 100)
        range2 = FrameRange(100, 200)

        mkv.split_by_parts_frames([range1, range2])

        assert "--split" in mkv._split_options

    def test_split_by_parts_frames_empty_list(self):
        mkv = MKVFile()

        with pytest.raises(ValueError, match="At least one frame range must be specified"):
            mkv.split_by_parts_frames([])

    def test_split_by_parts_frames_invalid_frame_numbers(self):
        mkv = MKVFile()
        range1 = FrameRange(0, 100)

        with pytest.raises(ValueError, match="start frame must be >= 1"):
            mkv.split_by_parts_frames([range1])

    def test_split_by_parts_frames_invalid_ordering(self):
        mkv = MKVFile()
        range1 = FrameRange(100, 50)

        with pytest.raises(ValueError, match="start frame must be before end frame"):
            mkv.split_by_parts_frames([range1])

    def test_split_by_parts_frames_with_link(self):
        mkv = MKVFile()
        range1 = FrameRange(1, 100)

        mkv.split_by_parts_frames([range1], link=True)

        assert "--link" in mkv._split_options

    def test_split_by_chapters_all(self):
        mkv = MKVFile()

        mkv.split_by_chapters("all")

        assert mkv._split_options == ["--split", "chapters:all"]

    def test_split_by_chapters_list(self):
        mkv = MKVFile()

        mkv.split_by_chapters([1, 3, 5])

        assert mkv._split_options == ["--split", "chapters:1,3,5"]

    def test_split_by_chapters_invalid_string(self):
        mkv = MKVFile()

        with pytest.raises(ValueError, match="String value must be 'all'"):
            mkv.split_by_chapters("invalid")

    def test_split_by_chapters_empty_list(self):
        mkv = MKVFile()

        with pytest.raises(ValueError, match="At least one chapter number must be specified"):
            mkv.split_by_chapters([])

    def test_split_by_chapters_invalid_chapter_number(self):
        mkv = MKVFile()

        with pytest.raises(ValueError, match="Chapter numbers must be positive integers"):
            mkv.split_by_chapters([1, 0, 3])

    def test_split_by_chapters_with_link(self):
        mkv = MKVFile()

        mkv.split_by_chapters("all", link=True)

        assert mkv._split_options == ["--split", "chapters:all", "--link"]


class TestMKVFileLinkingMethods:
    """Test linking methods."""

    def test_link_to_previous(self, tmp_path: Path):
        mkv = MKVFile()
        prev_file = tmp_path / "prev.mkv"

        mkv.link_to_previous(prev_file)

        assert mkv._link_to_previous_file == prev_file.resolve()

    def test_link_to_next(self, tmp_path: Path):
        mkv = MKVFile()
        next_file = tmp_path / "next.mkv"

        mkv.link_to_next(next_file)

        assert mkv._link_to_next_file == next_file.resolve()

    def test_link_to_none(self, tmp_path: Path):
        mkv = MKVFile()
        prev_file = tmp_path / "prev.mkv"
        next_file = tmp_path / "next.mkv"
        mkv.link_to_previous(prev_file)
        mkv.link_to_next(next_file)

        mkv.link_to_none()

        assert mkv._link_to_previous_file is None
        assert mkv._link_to_next_file is None


class TestMKVFileChaptersAndTags:
    """Test chapters and tags methods."""

    def test_chapters_without_language(self, tmp_path: Path):
        mkv = MKVFile()
        chapters_file = tmp_path / "chapters.xml"
        chapters_file.write_text("<Chapters></Chapters>")

        mkv.chapters(chapters_file)

        assert mkv._chapters_file == chapters_file.resolve()
        assert mkv.chapter_language is None

    def test_chapters_with_language(self, tmp_path: Path):
        mkv = MKVFile()
        chapters_file = tmp_path / "chapters.xml"
        chapters_file.write_text("<Chapters></Chapters>")
        lang = Lang("eng")

        mkv.chapters(chapters_file, language=lang)

        assert mkv._chapters_file == chapters_file.resolve()
        assert mkv.chapter_language == lang

    def test_global_tags(self, tmp_path: Path):
        mkv = MKVFile()
        tags_file = tmp_path / "tags.xml"
        tags_file.write_text("<Tags></Tags>")

        mkv.global_tags(tags_file)

        assert mkv._global_tags_file == tags_file.resolve()


class TestMKVFileNoMethods:
    """Test no_* methods that affect tracks."""

    def test_no_chapters(self):
        mkv = MKVFile()
        track1 = MagicMock(spec=MKVTrack)
        track2 = MagicMock(spec=MKVTrack)
        track1.no_chapters = False
        track2.no_chapters = False
        mkv.tracks = [track1, track2]

        mkv.no_chapters()

        assert track1.no_chapters is True
        assert track2.no_chapters is True

    def test_no_global_tags(self):
        mkv = MKVFile()
        track1 = MagicMock(spec=MKVTrack)
        track2 = MagicMock(spec=MKVTrack)
        track1.no_global_tags = False
        track2.no_global_tags = False
        mkv.tracks = [track1, track2]

        mkv.no_global_tags()

        assert track1.no_global_tags is True
        assert track2.no_global_tags is True

    def test_no_track_tags(self):
        mkv = MKVFile()
        track1 = MagicMock(spec=MKVTrack)
        track2 = MagicMock(spec=MKVTrack)
        track1.no_track_tags = False
        track2.no_track_tags = False
        mkv.tracks = [track1, track2]

        mkv.no_track_tags()

        assert track1.no_track_tags is True
        assert track2.no_track_tags is True

    def test_no_attachments(self):
        mkv = MKVFile()
        track1 = MagicMock(spec=MKVTrack)
        track2 = MagicMock(spec=MKVTrack)
        track1.no_attachments = False
        track2.no_attachments = False
        mkv.tracks = [track1, track2]

        mkv.no_attachments()

        assert track1.no_attachments is True
        assert track2.no_attachments is True
