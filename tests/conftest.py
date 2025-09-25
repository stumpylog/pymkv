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

@pytest.fixture
def mock_mkvmerge_verification(mocker: MockerFixture):
    """
    Automatically patches pymkv.Verifications.verify_mkvmerge
    to return True.
    """
    # The patch is applied when the fixture starts and removed when the class finishes.
    mocker.patch('pymkv.Verifications.verify_mkvmerge', return_value=True)

    # Use a yield statement if you need the fixture to return a value or
    # execute cleanup code after the test class runs.
    # Since we don't need the patch object itself, we just use yield.
    yield