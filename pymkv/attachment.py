""":class:`~pymkv.MKVAttachment` classes are used to represent attachment files within an MKV or to be used in an
MKV.

Examples
--------
Below are some basic examples of how the :class:`~pymkv.MKVAttachment` objects can be used.

Create a new :class:`~pymkv.MKVAttachment` and add it to an :class:`~pymkv.MKVFile`.

>>> from pymkv import MKVAttachment
>>> attachment = MKVAttachment('path/to/attachment.jpg', name='NAME')
>>> attachment.description = 'DESCRIPTION'

Attachments can also be added directly to an :class:`~pymkv.MKVFile`.

>>> from pymkv import MKVFile
>>> mkv = MKVFile('path/to/file.mkv')
>>> mkv.add_attachment('path/to/other/attachment.png')

Now, the MKV can be muxed with both attachments.

>>> mkv.add_attachment(attachment)
>>> mkv.mux('path/to/output.mkv')
"""

import json
import logging
from functools import total_ordering
from os import PathLike
from pathlib import Path

from pymkv.errors import NoTracksError
from pymkv.errors import UnsupportedContainerError
from pymkv.models import Attachment
from pymkv.models import MkvmergeIdentificationOutput
from pymkv.utils import run_mkvmerge

logger = logging.getLogger(__name__)


@total_ordering
class MKVAttachment:
    """A class that represents an MKV attachment for an :class:`~pymkv.MKVFile` object.

    Parameters
    ----------
    file_path : str
        The path to the attachment file.
    name : str, optional
        The name that will be given to the attachment when muxed into a file.
    description : str, optional
        The description that will be given to the attachment when muxed into a file.
    attach_once : bool, optional
        Determines if the attachment should be added to all split files or only the first. Default is False,
        which will attach to all files.

    Attributes
    ----------
    mime_type : str
        The attachment's MIME type. The type will be guessed when :attr:`~pymkv.MKVAttachment.file_path` is set.
    name : str
        The name that will be given to the attachment when muxed into a file.
    description : str
        The description that will be given to the attachment when muxed into a file.
    attach_once : bool
        Determines if the attachment should be added to all split files or only the first. Default is False,
        which will attach to all files.
    """

    def __init__(
        self,
        file_path: Path,
        id_: int,
        size: int,
        uid: int | None = None,
        name: str | None = None,
        description: str | None = None,
        content_type: str | None = None,
        *,
        attach_once: bool = False,
    ):
        # immutable once set
        self._id = id_
        self._size = size
        self._uid = uid
        self._content_type = content_type
        self._file_path = file_path.expanduser().resolve()

        # Can be changed by the user
        self.name = name
        self.description = description
        self.attach_once = attach_once

    @staticmethod
    def from_json(file_path: Path, data: Attachment) -> "MKVAttachment":
        return MKVAttachment(
            file_path,
            data["id"],
            data["size"],
            data["properties"].get("uid"),
            data["file_name"],
            data.get("description"),
            data.get("content_type"),
        )

    @staticmethod
    def from_file(file_path: Path | PathLike | str) -> "MKVAttachment":
        file_path = Path(file_path).expanduser().resolve()
        info_json: MkvmergeIdentificationOutput = json.loads(
            run_mkvmerge(["--identify", "--identification-format", "json", str(file_path)]),
        )

        if not info_json.get("container", {}).get("supported", False):
            raise UnsupportedContainerError

        if "attachments" not in info_json or len(info_json["attachments"]) == 0:
            raise NoTracksError
        elif len(info_json["attachments"]) > 1:
            logger.warning(f"Multiple attachments detected in {file_path}, selected the first")

        return MKVAttachment.from_json(file_path, info_json["attachments"][0])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MKVAttachment):
            raise NotImplementedError
        return self._id == other._id

    def __lt__(self, other: "MKVAttachment") -> bool:
        return self._id < other._id

    def __hash__(self) -> int:
        return hash((self._id,))

    def command(self) -> list[str]:
        """
        Generate mkvmerge command arguments for this attachment.

        Builds a list of command-line arguments for mkvmerge based on the attachment's
        configuration, including optional metadata and the appropriate attach method.

        Returns:
            list[str]: Complete list of mkvmerge command arguments for this attachment,
                    ending with the file attachment directive.
        """
        command = []

        # Attachment metadata options with None checks
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.attachment_name
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.attachment_description
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.attachment_mime_type
        attachment_options = [
            (self.name, "--attachment-name", self.name),
            (self.description, "--attachment-description", self.description),
            (self._content_type, "--attachment-mime-type", self._content_type),
        ]

        for condition, flag, value in attachment_options:
            if condition is not None:
                command.extend([flag, value])

        # Add attachment with appropriate method
        # https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.description.attach_file
        attach_flag = "--attach-file-once" if self.attach_once else "--attach-file"
        command.extend([attach_flag, str(self._file_path)])

        return command
