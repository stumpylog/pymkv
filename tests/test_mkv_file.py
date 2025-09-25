from pathlib import Path

from pymkv.MKVFile import MKVFile


class TestFileInit:
    def test_basic_init(self, sample_x264_mkv_file: Path) -> None:
        mkv_file = MKVFile(str(sample_x264_mkv_file))

        assert len(mkv_file.tracks) == 1

    def test_basic_init_2_tracks(self, sample_with_audio_file: Path) -> None:
        mkv_file = MKVFile(str(sample_with_audio_file))

        assert len(mkv_file.tracks) == 2
