import json
import logging
from collections.abc import Iterable
from os import PathLike
from pathlib import Path

from iso639 import Lang

from pymkv.attachment import MKVAttachment
from pymkv.errors import InputFileNotFoundError
from pymkv.errors import UnsupportedContainerError
from pymkv.models import MkvmergeIdentificationOutput
from pymkv.timestamp import FrameRange
from pymkv.timestamp import TimeRange
from pymkv.timestamp import Timestamp
from pymkv.track import MKVTrack
from pymkv.utils import get_mkvmerge_path
from pymkv.utils import run_mkvmerge

logger = logging.getLogger(__name__)


class MKVFile:
    def __init__(
        self,
        title: str | None = None,
    ):
        self.title: str | None = title
        self._chapters_file: Path | None = None
        self.chapter_language: Lang | None = None
        self._global_tags_file: Path | None = None
        self._link_to_previous_file: Path | None = None
        self._link_to_next_file: Path | None = None
        self.tracks: list[MKVTrack] = []
        self.attachments: list[MKVAttachment] = []
        # split options
        self._split_options: list[str] = []

    @staticmethod
    def from_file(file_path: Path | PathLike | str) -> "MKVFile":
        file_path = Path(file_path).expanduser().resolve()

        if not file_path.exists() or not file_path.is_file():
            raise InputFileNotFoundError

        info_json: MkvmergeIdentificationOutput = json.loads(
            run_mkvmerge(["--identify", "--identification-format", "json", str(file_path)]),
        )

        return MKVFile.from_json(file_path, info_json)

    @staticmethod
    def from_json(file_path: Path | PathLike | str, data: MkvmergeIdentificationOutput) -> "MKVFile":
        file_path = Path(file_path).expanduser().resolve()

        if not data.get("container", {}).get("supported", False):
            raise UnsupportedContainerError

        file = MKVFile(title=data.get("container", {}).get("properties", {}).get("title"))

        for track in data.get("tracks", []):
            file.add_track(MKVTrack.from_json(file_path, track))

        for attachment in data.get("attachments", []):
            file.add_attachment(MKVAttachment.from_json(file_path, attachment))

        # TODO(stumpylog): Investigate chapters, tags, etc

        return file

    def command(self, output_path: Path | PathLike | str) -> list[str]:
        output_path = Path(output_path).expanduser().resolve()
        command = ["-o", str(output_path)]
        if self.title is not None:
            command.extend(["--title", self.title])
        # add tracks
        for track in self.tracks:
            command.extend(track.command())

        # add attachments
        for attachment in self.attachments:
            command.extend(attachment.command())

        # chapters
        if self.chapter_language is not None:
            command.extend(["--chapter-language", self.chapter_language.pt2t])
        if self._chapters_file is not None:
            command.extend(["--chapters", str(self._chapters_file)])

        # global tags
        if self._global_tags_file is not None:
            command.extend(["--global-tags", str(self._global_tags_file)])

        # linking
        if self._link_to_previous_file is not None:
            command.extend(["--link-to-previous", "=" + str(self._link_to_previous_file)])
        if self._link_to_next_file is not None:
            command.extend(["--link-to-next", "=" + str(self._link_to_next_file)])

        # split options
        command.extend(self._split_options)

        return [str(get_mkvmerge_path()), *command]

    def mux(self, output_path: Path | PathLike | str) -> str:
        output_path = Path(output_path).expanduser().resolve()
        command = self.command(output_path)
        return run_mkvmerge(command[1:])

    def add_file(self, file: "MKVFile | Path | PathLike | str"):
        if isinstance(file, MKVFile):
            self.tracks.extend(file.tracks)
        else:
            self.tracks.extend(MKVFile.from_file(file).tracks)

    def add_track(self, track: "MKVTrack | Path | PathLike | str"):
        if isinstance(track, MKVTrack):
            self.tracks.append(track)
        else:
            self.tracks.append(MKVTrack.from_file(track))

    def add_attachment(self, attachment: "MKVAttachment | Path | PathLike | str"):
        if isinstance(attachment, MKVAttachment):
            self.attachments.append(attachment)
        else:
            self.attachments.append(MKVAttachment.from_file(attachment))

    def split_none(self):
        self._split_options = []

    def split_size(self, size: int, *, link: bool = False):
        self._split_options = ["--split", f"size:{size}"]
        if link:
            self._split_options.append("--link")

    def split_duration(self, duration: int, *, link: bool = False):
        self._split_options = ["--split", "duration:" + str(Timestamp.from_seconds(duration))]
        if link:
            self._split_options.append("--link")

    def split_timestamps(self, timestamps: Iterable[Timestamp], *, link=False):
        ts_string = "timestamps:" + ",".join(str(ts) for ts in sorted(timestamps))

        # Build options list directly
        self._split_options = ["--split", ts_string]
        if link:
            self._split_options.append("--link")

    def split_frames(self, frames: Iterable[int], *, link: bool = False):
        # Build frames_string using join() - more efficient than string concatenation
        frames_string = "frames:" + ",".join(str(frame) for frame in sorted(frames))

        # Build options list directly
        self._split_options = ["--split", frames_string]
        if link:
            self._split_options.append("--link")

    def split_by_parts(self, ranges: list[TimeRange], *, link: bool = False) -> None:
        if not ranges:
            msg = "At least one time range must be specified"
            raise ValueError(msg)

        # Validation
        prev_end = None
        for i, range_obj in enumerate(ranges):
            # First range can have None start, last range can have None end
            if i == 0 and range_obj.start is None:
                pass  # Valid - starts from beginning
            elif i == len(ranges) - 1 and range_obj.end is None:
                pass  # Valid - goes to end
            elif range_obj.start is None or range_obj.end is None:
                msg = f"Range {i}: Only first range can have None start, only last range can have None end"
                raise ValueError(msg)

            # Check ordering within range
            if range_obj.start is not None and range_obj.end is not None and range_obj.start >= range_obj.end:
                msg = f"Range {i}: start timestamp must be before end timestamp"
                raise ValueError(msg)

            # Check ordering between ranges
            if prev_end is not None and range_obj.start is not None and prev_end > range_obj.start:
                msg = f"Range {i}: start timestamp must be after previous range's end"
                raise ValueError(msg)

            prev_end = range_obj.end

        # Build parts string
        parts = ["parts:"]
        for i, range_obj in enumerate(ranges):
            if i > 0:
                parts.append(",")

            # Add '+' prefix if appending to previous file
            if range_obj.append_to_previous and i > 0:
                parts.append("+")

            # Add start timestamp (or empty for None)
            if range_obj.start is not None:
                parts.append(str(range_obj.start))

            parts.append("-")

            # Add end timestamp (or empty for None)
            if range_obj.end is not None:
                parts.append(str(range_obj.end))

        ts_string = "".join(parts)

        self._split_options = ["--split", ts_string]
        if link:
            self._split_options.append("--link")

    def split_by_parts_frames(self, ranges: list[FrameRange], *, link: bool = False) -> None:
        if not ranges:
            msg = "At least one frame range must be specified"
            raise ValueError(msg)

        # Validation
        prev_end = None
        for i, range_obj in enumerate(ranges):
            # First range can have None start, last range can have None end
            if i == 0 and range_obj.start is None:
                pass  # Valid - starts from beginning
            elif i == len(ranges) - 1 and range_obj.end is None:
                pass  # Valid - goes to end
            elif range_obj.start is None or range_obj.end is None:
                msg = f"Range {i}: Only first range can have None start, only last range can have None end"
                raise ValueError(msg)

            # Check for invalid frame numbers (must be >= 1)
            if range_obj.start is not None and range_obj.start < 1:
                msg = f"Range {i}: start frame must be >= 1 (frame numbering starts at 1)"
                raise ValueError(msg)
            if range_obj.end is not None and range_obj.end < 1:
                msg = f"Range {i}: end frame must be >= 1 (frame numbering starts at 1)"
                raise ValueError(msg)

            # Check ordering within range
            if range_obj.start is not None and range_obj.end is not None and range_obj.start >= range_obj.end:
                msg = f"Range {i}: start frame must be before end frame"
                raise ValueError(msg)

            # Check ordering between ranges
            if prev_end is not None and range_obj.start is not None and prev_end > range_obj.start:
                msg = f"Range {i}: start frame must be after previous range's end"
                raise ValueError(msg)

            prev_end = range_obj.end

        # Build parts-frames string
        parts = ["parts-frames:"]
        for i, range_obj in enumerate(ranges):
            if i > 0:
                parts.append(",")

            # Add '+' prefix if appending to previous file
            if range_obj.append_to_previous and i > 0:
                parts.append("+")

            # Add start frame (or empty for None)
            if range_obj.start is not None:
                parts.append(str(range_obj.start))

            parts.append("-")

            # Add end frame (or empty for None)
            if range_obj.end is not None:
                parts.append(str(range_obj.end))

        ts_string = "".join(parts)

        self._split_options = ["--split", ts_string]
        if link:
            self._split_options.append("--link")

    def split_by_chapters(self, chapters: str | list[int], *, link: bool = False) -> None:
        if isinstance(chapters, str):
            if chapters != "all":
                msg = "String value must be 'all'"
                raise ValueError(msg)
            chapters_str = "all"
        else:
            chapters = list(chapters)
            if not chapters:
                msg = "At least one chapter number must be specified"
                raise ValueError(msg)

            for chapter in chapters:
                if not isinstance(chapter, int) or chapter < 1:
                    msg = "Chapter numbers must be positive integers >= 1"
                    raise ValueError(msg)

            chapters_str = ",".join(str(ch) for ch in chapters)

        self._split_options = ["--split", f"chapters:{chapters_str}"]
        if link:
            self._split_options.append("--link")

    def link_to_previous(self, file_path: Path | PathLike | str):
        self._link_to_previous_file = Path(file_path).expanduser().resolve()

    def link_to_next(self, file_path: Path | PathLike | str):
        self._link_to_next_file = Path(file_path).expanduser().resolve()

    def link_to_none(self):
        self._link_to_previous_file = None
        self._link_to_next_file = None

    def chapters(self, file_path: Path | PathLike | str, language: Lang | None = None):
        self._chapters_file = Path(file_path).expanduser().resolve()
        self.chapter_language = language

    def global_tags(self, file_path: Path | PathLike | str):
        self._global_tags_file = Path(file_path).expanduser().resolve()

    def no_chapters(self):
        for track in self.tracks:
            track.no_chapters = True

    def no_global_tags(self):
        for track in self.tracks:
            track.no_global_tags = True

    def no_track_tags(self):
        for track in self.tracks:
            track.no_track_tags = True

    def no_attachments(self):
        for track in self.tracks:
            track.no_attachments = True
