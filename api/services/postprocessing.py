"""Classical computer-vision postprocessing for OnMe virtual try-on results."""

from __future__ import annotations

import os

import cv2
import numpy as np


def colour_transfer_reinhard(source_path: str, reference_path: str) -> str:
    """Apply Reinhard colour transfer from *reference_path* onto *source_path*.

    Shifts the per-channel mean and standard deviation of the source image
    (the VTON inference result) so that they match those of the reference
    image (the original garment) in LAB colour space.

    The corrected image is saved alongside the source with a ``_cc`` suffix
    (e.g. ``result.jpg`` → ``result_cc.jpg``).

    Reference:
        Reinhard et al., "Color Transfer between Images", IEEE CG&A, 2001.

    Args:
        source_path: Path to the VTON result image (colours may have drifted).
        reference_path: Path to the original garment image (ground-truth colours).

    Returns:
        The file path of the colour-corrected output image.
    """
    source = cv2.imread(source_path)
    reference = cv2.imread(reference_path)

    # Convert BGR → LAB and work in float64 for precision
    source_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype(np.float64)
    reference_lab = cv2.cvtColor(reference, cv2.COLOR_BGR2LAB).astype(np.float64)

    # Shift each LAB channel independently
    for ch in range(3):
        src_mean, src_std = source_lab[:, :, ch].mean(), source_lab[:, :, ch].std()
        ref_mean, ref_std = reference_lab[:, :, ch].mean(), reference_lab[:, :, ch].std()

        source_lab[:, :, ch] = (
            (source_lab[:, :, ch] - src_mean) * (ref_std / (src_std + 1e-6)) + ref_mean
        )

    # Clip, convert back to uint8 BGR, and save
    result = np.clip(source_lab, 0, 255).astype(np.uint8)
    result_bgr = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)

    base, ext = os.path.splitext(source_path)
    output_path = f"{base}_cc{ext}"
    cv2.imwrite(output_path, result_bgr)

    return output_path


def run_postprocessing(result_path: str, garment_reference_path: str) -> str:
    """Run the full postprocessing pipeline on a VTON result image.

    Currently applies Reinhard colour correction only.  Designed as the
    single entry-point for postprocessing so that future steps (e.g. face
    restoration, sharpening) can be added without changing callers.

    Args:
        result_path: Path to the raw inference output image.
        garment_reference_path: Path to the original garment image used as
            the colour reference.

    Returns:
        The file path of the final postprocessed image.
    """
    return colour_transfer_reinhard(result_path, garment_reference_path)
