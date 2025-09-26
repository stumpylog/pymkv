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
    The base error for problems when calling mkvmerge with subprocess
    """


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
