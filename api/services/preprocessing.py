"""Classical computer-vision preprocessing pipeline for OnMe virtual try-on."""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

MIN_DIM = 256
MAX_DIM = 4096


def validate_image(file_path: str) -> tuple[int, int]:
    """Validate that *file_path* is a readable image within allowed dimensions.

    Opens the file with Pillow, calls ``verify()`` to check integrity,
    then reopens to read actual pixel dimensions.

    Returns:
        (width, height) of the validated image.

    Raises:
        ValueError: If the image is smaller than 256×256 or larger than 4096×4096.
        Exception: Any Pillow error (corrupt file, unsupported format, etc.).
    """
    # First pass – integrity check
    with Image.open(file_path) as img:
        img.verify()

    # Second pass – read dimensions (verify() invalidates the object)
    with Image.open(file_path) as img:
        width, height = img.size

    if width < MIN_DIM or height < MIN_DIM:
        raise ValueError(
            f"Image too small ({width}x{height}); "
            f"minimum is {MIN_DIM}x{MIN_DIM}."
        )
    if width > MAX_DIM or height > MAX_DIM:
        raise ValueError(
            f"Image too large ({width}x{height}); "
            f"maximum is {MAX_DIM}x{MAX_DIM}."
        )

    return width, height
