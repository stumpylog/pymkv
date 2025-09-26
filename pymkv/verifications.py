# sheldon woodward
# 3/24/18

"""Verification functions for mkvmerge and associated files."""

import json
import logging
import os
import subprocess as sp
from os.path import expanduser
from os.path import isfile
from re import match

from pymkv.errors import InputFileNotFoundError
from pymkv.errors import MkvMergeNotFoundError
from pymkv.errors import MkvMergeSubprocessError

logger = logging.getLogger(__name__)


def verify_mkvmerge(mkvmerge_path="mkvmerge"):
    """Verify mkvmerge is working.

    mkvmerge_path (str):
        Alternate path to mkvmerge if it is not already in the $PATH variable.
    """
    try:
        output = sp.check_output([mkvmerge_path, "-V"]).decode()
    except (sp.CalledProcessError, FileNotFoundError):
        return False
    if match("mkvmerge.*", output):
        return True
    return False


def verify_matroska(file_path, mkvmerge_path="mkvmerge") -> bool:
    """Verify if a file is a Matroska file.

    file_path (str):
        Path of the file to be verified.
    mkvmerge_path (str):
        Alternate path to mkvmerge if it is not already in the $PATH variable.
    """
    if not verify_mkvmerge(mkvmerge_path=mkvmerge_path):
        msg = "mkvmerge is not at the specified path, add it there or change the mkvmerge_path property"
        logger.error(msg)
        raise MkvMergeNotFoundError(msg)
    if isinstance(file_path, os.PathLike):
        file_path = str(file_path)
    elif not isinstance(file_path, str):
        raise TypeError(f'"{file_path}" is not of type str')
    file_path = expanduser(file_path)
    if not isfile(file_path):
        raise InputFileNotFoundError(f'"{file_path}" does not exist')
    try:
        info_json = json.loads(sp.check_output([mkvmerge_path, "-J", file_path]).decode())
    except sp.CalledProcessError:
        raise MkvMergeSubprocessError(f'"{file_path}" could not be opened')
    return info_json["container"]["type"] == "Matroska"


def verify_recognized(file_path, mkvmerge_path="mkvmerge") -> bool:
    """Verify a file is recognized by mkvmerge.

    file_path (str):
        Path to the file to be verified.
    mkvmerge_path (str):
        Alternate path to mkvmerge if it is not already in the $PATH variable.
    """
    if not verify_mkvmerge(mkvmerge_path=mkvmerge_path):
        msg = "mkvmerge is not at the specified path, add it there or change the mkvmerge_path property"
        logger.error(msg)
        raise MkvMergeNotFoundError(msg)
    if not isinstance(file_path, str):
        raise TypeError(f'"{file_path}" is not of type str')
    file_path = expanduser(file_path)
    if not isfile(file_path):
        raise InputFileNotFoundError(f'"{file_path}" does not exist')
    try:
        info_json = json.loads(sp.check_output([mkvmerge_path, "-J", file_path]).decode())
    except sp.CalledProcessError:
        raise MkvMergeSubprocessError(f'"{file_path}" could not be opened')
    return info_json["container"]["recognized"]


def verify_supported(file_path, mkvmerge_path="mkvmerge") -> bool:
    """Verify a file is supported by mkvmerge.

    file_path (str):
        Path to the file to be verified.
    mkvmerge_path (str):
        Alternate path to mkvmerge if it is not already in the $PATH variable.
    """
    if not verify_mkvmerge(mkvmerge_path=mkvmerge_path):
        msg = "mkvmerge is not at the specified path, add it there or change the mkvmerge_path property"
        logger.error(msg)
        raise MkvMergeNotFoundError(msg)
    if not isinstance(file_path, str):
        raise TypeError(f'"{file_path}" is not of type str')
    file_path = expanduser(file_path)
    if not isfile(file_path):
        raise InputFileNotFoundError(f'"{file_path}" does not exist')
    try:
        info_json = json.loads(sp.check_output([mkvmerge_path, "-J", file_path]).decode())
    except sp.CalledProcessError:
        raise MkvMergeSubprocessError(f'"{file_path}" could not be opened')
    return info_json["container"]["supported"]
