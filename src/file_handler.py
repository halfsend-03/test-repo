"""File handler with correct UTF-8 buffer allocation.

The save path previously allocated buffers based on character count
(len(text)) rather than byte length (len(text.encode('utf-8'))). For
ASCII-only content both values are equal, but multibyte UTF-8 characters
(emoji, CJK, accented letters, etc.) use 2-4 bytes per character. When
the text exceeds 64 KB in *characters* yet fits in a character-count
based buffer, the actual byte payload overflows the buffer and causes a
segmentation fault.

Fix: allocate and chunk based on byte length, not character count.
"""

CHUNK_SIZE = 65536  # 64 KB


def save_file(path: str, content: str) -> None:
    """Write *content* to *path* using chunked byte-level I/O.

    The content is encoded to UTF-8 first, then written in CHUNK_SIZE
    byte chunks.  This avoids the buffer overrun that occurred when
    chunking was based on character count.
    """
    data = content.encode("utf-8")
    with open(path, "wb") as fh:
        for offset in range(0, len(data), CHUNK_SIZE):
            fh.write(data[offset : offset + CHUNK_SIZE])


def read_file(path: str) -> str:
    """Read a UTF-8 encoded file and return its content as a string."""
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")
