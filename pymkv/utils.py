import logging
import shutil
import subprocess
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from iso639 import is_language

from pymkv.errors import MkvMergeSubprocessError


def is_iso_639_2_language_code(language: str) -> bool:
    return is_language(language, "pt2t")


@cache
def get_mkvmerge_path() -> Path:
    _path = shutil.which("mkvmerge")
    if TYPE_CHECKING:
        assert _path is not None
    return Path(_path).expanduser().resolve()


def run_mkvmerge(command: list[str], timeout: int | None = None) -> str:
    """
    Run a subprocess command and return decoded stdout.

    Args:
        command: List of command arguments (e.g., ['mkvmerge', '--identify', 'file.mkv'])
        timeout: Optional timeout in seconds (default: None)

    Returns:
        str: Decoded stdout from the subprocess

    Raises:
        MkvMergeSubprocessError: If the subprocess fails or returns non-zero exit code
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"Executing command: {' '.join(command)}")

    try:
        # Run the subprocess
        result = subprocess.run(  # noqa: S603
            [str(get_mkvmerge_path()), *command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,  # We'll handle the return code ourselves
        )
    except subprocess.TimeoutExpired as e:
        error_msg = f"Command timed out after {timeout} seconds: {' '.join(command)}"
        logger.error(error_msg)  # noqa: TRY400
        # Try to get partial output if available
        stdout = e.stdout.decode("utf-8", errors="replace") if e.stdout else ""
        stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
        raise MkvMergeSubprocessError(
            message=error_msg,
            returncode=-1,
            stdout=stdout,
            stderr=stderr,
        ) from e
    except Exception as e:
        error_msg = f"Unexpected error running command: {' '.join(command)}. Error: {e!s}"
        logger.error(error_msg)  # noqa: TRY400
        raise MkvMergeSubprocessError(
            message=error_msg,
            returncode=-1,
        ) from e

    # Process results outside the try block
    stdout = result.stdout or ""
    stderr = result.stderr or ""

    # Handle mkvmerge exit codes according to documentation
    if result.returncode == 0:
        # Success - no logging of output needed
        logger.debug("Command completed successfully")
        return stdout
    elif result.returncode == 1:
        # Warning - log stdout/stderr but don't raise exception
        logger.warning("Command completed with warnings (exit code 1)")
        if stdout:
            logger.warning(f"Command stdout: {stdout.strip()}")
        if stderr:
            logger.warning(f"Command stderr: {stderr.strip()}")
        return stdout
    else:
        # Error (exit code 2 or any other non-zero value) - log and raise exception
        error_msg = f"Command failed with return code {result.returncode}: {' '.join(command)}"
        logger.error(error_msg)

        # Log output on error
        if stdout:
            logger.error(f"Command stdout: {stdout.strip()}")
        if stderr:
            logger.error(f"Command stderr: {stderr.strip()}")

        raise MkvMergeSubprocessError(
            message=error_msg,
            returncode=result.returncode,
            stdout=stdout,
            stderr=stderr,
        )
