"""Perceptual image similarity metrics for offline evaluation."""

from __future__ import annotations

from typing import Any

import lpips
import numpy as np
import torch
from PIL import Image


_LPIPS_SIZE = (256, 256)


def _load_lpips_tensor(image_path: str, device: torch.device) -> torch.Tensor:
    """Load and normalise an image tensor for LPIPS evaluation.

    Args:
        image_path: Path to the image file.
        device: Torch device that should receive the tensor.

    Returns:
        A normalised image tensor with shape ``(1, 3, H, W)`` on ``device``.
    """
    image = Image.open(image_path).convert("RGB").resize(_LPIPS_SIZE)
    array = np.asarray(image, dtype=np.float32)
    tensor = torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0)
    tensor = (tensor / 255.0) * 2.0 - 1.0
    return tensor.to(device)


def _get_model_device(model: Any) -> torch.device:
    """Return the device of an LPIPS model.

    Args:
        model: An LPIPS model instance.

    Returns:
        The device hosting the model parameters.
    """
    first_parameter = next(model.parameters(), None)
    if first_parameter is None:
        return torch.device("cpu")
    return first_parameter.device


def compute_lpips(img1_path: str, img2_path: str, model: object = None) -> float:
    """Compute LPIPS perceptual distance between two images.

    LPIPS measures learned perceptual similarity using deep network features.
    Lower scores mean the images look more alike to human observers, with
    identical images typically near ``0.0`` and larger values indicating more
    perceptual difference. In practice, scores commonly fall roughly in the
    ``0.0`` to ``1.0`` range for image comparison tasks.

    Args:
        img1_path: Path to the first image.
        img2_path: Path to the second image.
        model: Optional pre-loaded ``lpips.LPIPS`` model. When omitted, a new
            AlexNet-backed LPIPS model is created.

    Returns:
        The LPIPS distance as a Python float.
    """
    lpips_model = model if model is not None else lpips.LPIPS(net="alex")
    lpips_model.eval()

    device = _get_model_device(lpips_model)
    tensor_1 = _load_lpips_tensor(img1_path, device)
    tensor_2 = _load_lpips_tensor(img2_path, device)

    with torch.no_grad():
        distance = lpips_model(tensor_1, tensor_2)

    return float(distance.detach().cpu().item())
