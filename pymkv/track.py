import json
import logging
from functools import total_ordering
from os import PathLike
from pathlib import Path

from pymkv.errors import InvalidLanguageError
from pymkv.errors import NoTracksError
from pymkv.errors import UnsupportedContainerError
from pymkv.models import MkvmergeIdentificationOutput
from pymkv.models import Track
from pymkv.utils import is_iso_639_2_language_code
from pymkv.utils import run_mkvmerge

logger = logging.getLogger(__name__)


@total_ordering
class MKVTrack:
    def __init__(
        self,
        file_path: Path,
        track_id: int,
        track_codec: str,
        track_type: str,
        track_name: str | None = None,
        language: str | None = None,
        *,
        default_track: bool = False,
        forced_track: bool = False,
    ):
        # immutable once set
        self._file_path = file_path.expanduser().resolve()
        self._track_id = track_id
        self._track_codec = track_codec
        self._track_type = track_type

        # Can be changed
        self.language = language
        self.track_name = track_name
        self.tags_file: Path | None = None
        self.default_track = default_track
        self.forced_track = forced_track

        # output control options
        self.no_chapters = False
        self.no_global_tags = False
        self.no_track_tags = False
        self.no_attachments = False

    @staticmethod
    def from_json(file_path: Path | PathLike | str, data: Track) -> "MKVTrack":
        file_path = Path(file_path).expanduser().resolve()
        return MKVTrack(
            file_path,
            track_id=data["id"],
            track_codec=data["codec"],
            track_type=data["type"],
            track_name=data.get("properties", {}).get("track_name"),
            language=data.get("properties", {}).get("language"),
            default_track=data.get("properties", {}).get("default_track", False),
            forced_track=data.get("properties", {}).get("forced_track", False),
        )

    @staticmethod
    def from_file(file_path: Path | PathLike | str) -> "MKVTrack":
        file_path = Path(file_path).expanduser().resolve()
        info_json: MkvmergeIdentificationOutput = json.loads(
            run_mkvmerge(["--identify", "--identification-format", "json", str(file_path)]),
        )

        if not info_json.get("container", {}).get("supported", False):
            raise UnsupportedContainerError

        if "tracks" not in info_json or len(info_json["tracks"]) == 0:
            raise NoTracksError
        elif len(info_json["tracks"]) > 1:
            logger.warning(f"Multiple tracks detected in {file_path}, selected the first")

        return MKVTrack.from_json(file_path, info_json["tracks"][0])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MKVTrack):
            raise NotImplementedError
        return self._track_id == other._track_id

    def __lt__(self, other: "MKVTrack") -> bool:
        return self._track_id < other._track_id

    def __hash__(self) -> int:
        return hash((self._track_id,))

    @property
    def language(self):
        """str: The language of the track.

        Setting this property will verify that the passed in language is an ISO-639 language code and use it as the
        language for the track.

        Raises
        ------
        ValueError
            Raised if the passed in language is not an ISO 639-2 language code.
        """
        return self._language

    @language.setter
    def language(self, language):
        if language is None or language.lower() == "und" or is_iso_639_2_language_code(language):
            self._language = language
        else:
            msg = f"'{language}' is not a valid ISO639-2 language code"
            logger.error(msg)
            raise InvalidLanguageError(msg)

    @property
    def track_codec(self):
        """str: The codec of the track such as h264 or AAC."""
        return self._track_codec

    @property
    def track_type(self):
        """str: The type of track such as video or audio."""
        return self._track_type

    def command(self) -> list[str]:
        """
        Generate mkvmerge command arguments for this track.

        Builds a list of command-line arguments for mkvmerge based on the track's
        configuration, including track metadata, type-specific options, and exclusions.

        Returns:
            list[str]: Complete list of mkvmerge command arguments for this track,
                    ending with the file path.
        """
        command = []
        self_id_str = str(self._track_id)

        # Track-specific options with None checks
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.track_name
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.language
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.tags
        track_options = [
            (self.track_name, "--track-name", self.track_name),
            (self.language, "--language", self.language),
            (self.tags_file, "--tags", str(self.tags_file)),
        ]

        for condition, flag, value in track_options:
            if condition is not None:
                command.extend([flag, f"{self_id_str}:{value}"])

        # Boolean flags - always set (no conditionals needed for extend calls)
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.default_track_flag
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.forced_display_flag
        command.extend(
            [
                "--default-track-flag",
                f"{self_id_str}:{'1' if self.default_track else '0'}",
                "--forced-display-flag",
                f"{self_id_str}:{'1' if self.forced_track else '0'}",
            ],
        )

        # Track type handling with lookup table
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.no_video
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.video_tracks
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.no_audio
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.audio_tracks
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.no_subtitles
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.subtitle_tracks
        track_type_config = {
            "video": (["--video-tracks", self_id_str], ["--no-audio", "--no-subtitles"]),
            "audio": (["--audio-tracks", self_id_str], ["--no-video", "--no-subtitles"]),
            "subtitles": (["--subtitle-tracks", self_id_str], ["--no-video", "--no-audio"]),
        }

        if self.track_type in track_type_config:
            include_flags, exclude_flags = track_type_config[self.track_type]
            command.extend(include_flags)
            command.extend(exclude_flags)

        # Exclusion flags - batch process
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.no_chapters
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.no_global_tags
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.no_track_tags
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.no_attachments
        exclusions = [
            (self.no_chapters, "--no-chapters"),
            (self.no_global_tags, "--no-global-tags"),
            (self.no_track_tags, "--no-track-tags"),
            (self.no_attachments, "--no-attachments"),
        ]

        command.extend(flag for condition, flag in exclusions if condition)

        # Add file path
        command.append(str(self._file_path))
        return command
