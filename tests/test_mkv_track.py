# tests/test_MKVTrack.py
from __future__ import annotations

from pathlib import Path

from pymkv.track import MKVTrack


class TestTrackInit:
    def test_basic_init(self, sample_x264_mkv_file: Path) -> None:
        track = MKVTrack(str(sample_x264_mkv_file))

        assert track.file_path
        assert track.track_id == 0
        assert track.track_codec == "AVC/H.264/MPEG-4p10"
        assert track.track_type == "video"
