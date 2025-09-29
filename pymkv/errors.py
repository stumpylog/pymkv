class PyMkvBaseError(Exception):
    """
    The base error for all library errors
    """


class MkvMergeNotFoundError(PyMkvBaseError):
    """
    The mkvmerge executable was not found
    """


class InputFileNotFoundError(PyMkvBaseError):
    """
    A given input file was not found to be a file
    """


class MkvMergeSubprocessError(PyMkvBaseError):
    """
    error for problems when calling mkvmerge with subprocess
    """

    def __init__(self, message: str, returncode: int, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.message = message
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TimestampBaseError(PyMkvBaseError):
    """
    Base error for problems constructing Timestamps
    """


class TimestampValueOutOfRangeError(TimestampBaseError):
    """
    A provided or parsed value provided is out of the range mkvmerge allows
    """


class TimestampInvalidStringError(TimestampBaseError):
    """
    The timestamp string is not a valid format
    """


class InvalidLanguageError(PyMkvBaseError):
    """
    The provided language code is not a valid ISO-639 pt2 code
    """


class UnsupportedContainerError(PyMkvBaseError):
    """
    mkvmerge does not support this container
    """


class NoTracksError(PyMkvBaseError):
    """
    There were no tracks in a given file (through it is supported)
    """
