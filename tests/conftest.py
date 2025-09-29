from pathlib import Path
from typing import Any

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
def dummy_attachment_file(tmp_path: Path) -> Path:
    """Create a dummy file to be used as an attachment."""
    file_path = tmp_path / "attachment.txt"
    file_path.write_text("This is a test attachment.")
    return file_path


@pytest.fixture
def mock_dependencies(mocker: MockerFixture) -> dict[str, Any]:
    """Central fixture to mock all external dependencies."""
    mock_run = mocker.patch("pymkv.utils.subprocess.run")
    mocker.patch(
        "pymkv.utils.get_mkvmerge_path",
        return_value=Path("/fake/path/to/mkvmerge"),
    )
    mock_logger = mocker.patch("pymkv.utils.logging.getLogger").return_value
    return {"run": mock_run, "logger": mock_logger}
