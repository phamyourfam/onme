"""Structural image quality metrics for offline evaluation."""

from __future__ import annotations

import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def _load_rgb_image(image_path: str) -> np.ndarray:
    """Load an image as an RGB NumPy array.

    Args:
        image_path: Path to the image file.

    Returns:
        The image as a float64 NumPy array with shape ``(H, W, 3)``.
    """
    return np.asarray(Image.open(image_path).convert("RGB"), dtype=np.float64)


def compute_ssim(img1_path: str, img2_path: str) -> float:
    """Compute the Structural Similarity Index between two RGB images.

    SSIM measures perceived image quality by comparing luminance, contrast,
    and structural information between two images. Higher scores indicate
    better structural agreement: identical images score ``1.0``, visually
    similar images are typically close to ``1.0``, and poor matches trend
    toward ``0.0`` or below. The valid mathematical range is ``[-1.0, 1.0]``.

    Args:
        img1_path: Path to the first image.
        img2_path: Path to the second image.

    Returns:
        The SSIM score as a Python float.
    """
    image_1 = _load_rgb_image(img1_path)
    image_2 = _load_rgb_image(img2_path)

    score = structural_similarity(
        image_1,
        image_2,
        channel_axis=-1,
        data_range=255.0,
    )
    return float(score)


def compute_psnr(img1_path: str, img2_path: str) -> float:
    """Compute the Peak Signal-to-Noise Ratio between two RGB images.

    PSNR measures pixel-level fidelity in decibels (dB). Higher scores mean
    the images are more alike, while lower scores indicate more distortion.
    Identical images produce an infinite score. PSNR is typically non-negative
    and has no strict upper bound in practice.

    Args:
        img1_path: Path to the first image.
        img2_path: Path to the second image.

    Returns:
        The PSNR score as a Python float.
    """
    image_1 = _load_rgb_image(img1_path)
    image_2 = _load_rgb_image(img2_path)

    score = peak_signal_noise_ratio(image_1, image_2, data_range=255.0)
    return float(score)
