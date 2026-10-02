"""File save module with correct UTF-8 buffer handling.

Fixes a regression introduced in v2.3.1 where buffer allocation used
character count instead of byte length, causing a segmentation fault
when saving files larger than 64KB containing UTF-8 multibyte characters
(e.g., emoji or CJK characters).
"""

import os
import tempfile

# 64KB buffer threshold
BUFFER_SIZE = 65536


def save_file(path: str, content: str) -> None:
    """Save content to a file using byte-length buffer allocation.

    Uses len(encoded_content) (byte length) instead of len(content)
    (character count) to correctly handle UTF-8 multibyte characters.
    Without this, multibyte characters cause the actual byte length to
    exceed the allocated buffer at the 64KB boundary.

    Args:
        path: Destination file path.
        content: Text content to save.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    byte_length = len(encoded)

    # Write atomically via temp file to prevent data loss on failure
    dir_name = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    try:
        offset = 0
        while offset < byte_length:
            chunk = encoded[offset : offset + BUFFER_SIZE]
            os.write(fd, chunk)
            offset += len(chunk)
        os.close(fd)
        fd = -1
        os.replace(tmp_path, path)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
