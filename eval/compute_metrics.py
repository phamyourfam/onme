"""Offline evaluation metrics for virtual try-on image quality.

Computes quantitative metrics between generated try-on results and ground
truth images.  Used for dissertation evaluation — comparing CatVTON vs
OOTDiffusion and measuring the impact of classical CV preprocessing via
ablation study.
"""

from __future__ import annotations

from pathlib import Path

import lpips as lpips_lib
import numpy as np
import torch
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def compute_ssim_psnr(img1_path: str | Path, img2_path: str | Path) -> dict:
    """Compute SSIM and PSNR between two images.

    **SSIM (Structural Similarity Index)** measures the perceived quality
    difference between two images by comparing luminance, contrast, and
    structure.  Values range from -1 to 1, where 1 indicates identical
    images.  Higher is better.

    **PSNR (Peak Signal-to-Noise Ratio)** measures the ratio between the
    maximum possible signal power and the power of corrupting noise,
    expressed in decibels (dB).  Higher values indicate less distortion;
    identical images yield an infinite PSNR.

    Args:
        img1_path: Path to the first image (e.g. generated result).
        img2_path: Path to the second image (e.g. ground truth).

    Returns:
        A dict with keys ``"ssim"`` and ``"psnr"``, both as Python floats.
    """
    img1 = np.asarray(Image.open(img1_path).convert("RGB"), dtype=np.float64)
    img2 = np.asarray(Image.open(img2_path).convert("RGB"), dtype=np.float64)

    ssim_value: float = structural_similarity(
        img1, img2, channel_axis=-1, data_range=255.0
    )
    psnr_value: float = peak_signal_noise_ratio(img1, img2, data_range=255.0)

    return {"ssim": float(ssim_value), "psnr": float(psnr_value)}


def compute_lpips(
    img1_path: str | Path,
    img2_path: str | Path,
    model: lpips_lib.LPIPS | None = None,
) -> float:
    """Compute LPIPS perceptual distance between two images.

    LPIPS (Learned Perceptual Image Patch Similarity) measures the
    perceptual distance between two images using deep features extracted
    from a pre-trained network.  **Lower values indicate that the images
    look more similar to human observers.**  A score of 0 means the images
    are perceptually identical.

    Args:
        img1_path: Path to the first image (e.g. generated result).
        img2_path: Path to the second image (e.g. ground truth).
        model: Pre-loaded ``lpips.LPIPS`` model.  If ``None``, a new model
            with the AlexNet backbone is instantiated automatically.

    Returns:
        The LPIPS distance as a Python float (lower is better).
    """
    if model is None:
        model = lpips_lib.LPIPS(net="alex")
    model.eval()

    img1 = Image.open(img1_path).convert("RGB").resize((256, 256))
    img2 = Image.open(img2_path).convert("RGB").resize((256, 256))

    tensor1 = torch.from_numpy(np.asarray(img1, dtype=np.float32)).permute(2, 0, 1).unsqueeze(0) / 127.5 - 1.0
    tensor2 = torch.from_numpy(np.asarray(img2, dtype=np.float32)).permute(2, 0, 1).unsqueeze(0) / 127.5 - 1.0

    with torch.no_grad():
        distance = model(tensor1, tensor2)

    return float(distance.item())
