from pathlib import Path

import pytest
from pytest_mock import MockerFixture


@pytest.fixture(scope="session")
def sample_dir() -> Path:
    return Path(__file__).parent / "samples"


@pytest.fixture(scope="session")
def sample_x264_mkv_file(sample_dir: Path) -> Path:
    # ffmpeg -f lavfi -i testsrc2=duration=5:size=320x240:rate=1 -c:v libx264 -preset ultrafast -crf 30 test_sample.mkv
    return sample_dir / "test_sample_x264.mkv"


@pytest.fixture(scope="session")
def sample_x264_mp4_file(sample_dir: Path) -> Path:
    # ffmpeg -f lavfi -i testsrc2=duration=5:size=320x240:rate=1 -c:v libx264 -preset ultrafast -crf 30 test_sample.mp4
    return sample_dir / "test_sample_x264.mp4"


@pytest.fixture(scope="session")
def sample_with_audio_file(sample_dir: Path) -> Path:
    # ffmpeg -f lavfi -i testsrc2=duration=5:size=320x240:rate=1 \
    #        -f lavfi -i "sine=frequency=440:duration=5" \
    #        -c:v libx264 -preset ultrafast -crf 30 \
    #        -c:a aac test_with_audio.mkv
    #
    # Produces a 5s MKV with one video track and one synthetic audio track (440Hz sine).
    return sample_dir / "test_with_audio.mkv"


@pytest.fixture(scope="session")
def sample_with_chapters_file(sample_dir: Path) -> Path:
    # mkvmerge -o test_with_chapters.mkv test_sample_x264.mkv --chapters chapters.xml
    #
    # Produces an MKV with two chapters: "Intro" and "Main Part".
    return sample_dir / "test_with_chapters.mkv"


@pytest.fixture(scope="session")
def sample_with_tags_file(sample_dir: Path) -> Path:
    # mkvmerge -o test_with_tags.mkv test_sample_x264.mkv --global-tags tags.xml
    #
    # Produces an MKV with a global TITLE tag.
    return sample_dir / "test_with_tags.mkv"


@pytest.fixture(scope="session")
def sample_with_subs_file(sample_dir: Path) -> Path:
    # mkvmerge -o test_with_subs.mkv test_sample_x264.mkv --language 0:eng subs.srt
    #
    # Produces an MKV with one video track and one English subtitle track.
    return sample_dir / "test_with_subs.mkv"


@pytest.fixture
def mock_mkvmerge_verification(mocker: MockerFixture):
    """
    Automatically patches pymkv.verifications.verify_mkvmerge
    to return True.
    """
    # The patch is applied when the fixture starts and removed when the class finishes.
    mocker.patch("pymkv.verifications.verify_mkvmerge", return_value=True)
