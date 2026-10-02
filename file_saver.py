"""File save utility with chunked writing.

Properly handles UTF-8 multibyte characters by sizing write buffers
using byte length rather than character count.
"""

CHUNK_SIZE = 65536  # 64KB


def save_file(content: str, path: str) -> None:
    """Save content to a file using chunked writes.

    Writes the file in chunks of CHUNK_SIZE bytes to manage memory
    usage for large files. Uses byte length (not character count)
    to determine chunk boundaries, and avoids splitting multibyte
    UTF-8 characters across chunk boundaries.

    Args:
        content: The text content to save.
        path: The file path to write to.
    """
    encoded = content.encode("utf-8")
    with open(path, "wb") as f:
        offset = 0
        while offset < len(encoded):
            end = offset + CHUNK_SIZE
            # Avoid splitting a multibyte UTF-8 sequence at the
            # chunk boundary. If 'end' lands in the middle of a
            # multibyte character, back up to the start of that
            # character.
            if end < len(encoded):
                while end > offset and (encoded[end] & 0xC0) == 0x80:
                    end -= 1
            chunk = encoded[offset:end]
            f.write(chunk)
            offset += len(chunk)
