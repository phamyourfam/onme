"""Semantic image similarity metrics for offline evaluation."""

from __future__ import annotations

import torch
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPProcessor, CLIPVisionModelWithProjection


_CLIP_MODEL_ID = "openai/clip-vit-base-patch32"
_model = None
_processor = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _get_model() -> tuple[CLIPVisionModelWithProjection, CLIPProcessor]:
    """Load and cache the CLIP vision model and processor.

    Returns:
        A tuple containing the cached CLIP vision model and processor.
    """
    global _model, _processor

    if _model is None or _processor is None:
        _processor = CLIPProcessor.from_pretrained(_CLIP_MODEL_ID)
        _model = CLIPVisionModelWithProjection.from_pretrained(_CLIP_MODEL_ID)
        _model.eval()
        _model.to(_device)

    return _model, _processor


def compute_clip_similarity(img1_path: str, img2_path: str) -> float:
    """Compute CLIP embedding similarity between two images.

    CLIP similarity measures semantic alignment rather than raw pixel match.
    In this evaluation pipeline it approximates whether the generated garment
    remains semantically consistent with the reference garment or target image.
    Higher scores are better, with values near ``1.0`` indicating very strong
    semantic agreement and values near ``0.0`` indicating weak alignment.

    Args:
        img1_path: Path to the first image.
        img2_path: Path to the second image.

    Returns:
        A CLIP similarity score normalised to the ``[0.0, 1.0]`` range.
    """
    model, processor = _get_model()

    image_1 = Image.open(img1_path).convert("RGB")
    image_2 = Image.open(img2_path).convert("RGB")
    inputs = processor(images=[image_1, image_2], return_tensors="pt")
    pixel_values = inputs["pixel_values"].to(_device)

    with torch.no_grad():
        outputs = model(pixel_values=pixel_values)
        embeddings = outputs.image_embeds
        cosine_similarity = F.cosine_similarity(
            embeddings[0].unsqueeze(0),
            embeddings[1].unsqueeze(0),
            dim=1,
        ).clamp(min=-1.0, max=1.0)

    similarity = (cosine_similarity + 1.0) / 2.0
    return float(similarity.item())
