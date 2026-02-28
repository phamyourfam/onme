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


def resize_for_model(
    file_path: str,
    target_w: int = 768,
    target_h: int = 1024,
) -> str:
    """Resize *file_path* to (*target_w*, *target_h*) using LANCZOS resampling.

    Non-RGB images (e.g. RGBA, P) are converted to RGB before resizing.
    The result is saved as JPEG (quality 95) alongside the original with a
    ``_resized`` suffix.

    Returns:
        The path to the newly created resized image.
    """
    with Image.open(file_path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        resized = img.resize((target_w, target_h), Image.LANCZOS)

    stem = Path(file_path).stem
    parent = Path(file_path).parent
    out_path = parent / f"{stem}_resized.jpg"
    resized.save(str(out_path), format="JPEG", quality=95)
    return str(out_path)


def normalise_lighting(file_path: str) -> str:
    """Apply CLAHE (Contrast-Limited Adaptive Histogram Equalisation) to *file_path*.

    The image is converted from BGR to LAB colour space.  CLAHE is applied
    to the L (lightness) channel, then the result is converted back to BGR
    and saved alongside the original with a ``_clahe`` suffix.

    Returns:
        Path to the newly created normalised image.
    """
    import cv2
    import numpy as np

    img_bgr = cv2.imread(file_path)
    if img_bgr is None:
        raise ValueError(f"Cannot read image: {file_path}")

    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l_chan)

    merged = cv2.merge([l_clahe, a_chan, b_chan])
    result_bgr = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    stem = Path(file_path).stem
    parent = Path(file_path).parent
    ext = Path(file_path).suffix or ".jpg"
    out_path = parent / f"{stem}_clahe{ext}"
    cv2.imwrite(str(out_path), result_bgr)
    return str(out_path)
