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
import torch.nn.functional as F
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity
from tqdm import tqdm
from transformers import CLIPProcessor, CLIPVisionModelWithProjection


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


_CLIP_MODEL_ID = "openai/clip-vit-base-patch32"


def compute_clip_similarity(
    img1_path: str | Path, img2_path: str | Path
) -> float:
    """Compute CLIP-based semantic similarity between two images.

    Uses the CLIP vision encoder (ViT-B/32) to extract image embeddings
    and computes cosine similarity between them.  This measures how
    **semantically similar** the two images are — for example, whether the
    garment in the generated try-on output looks conceptually consistent
    with the input garment image.

    Values range from 0 to 1 (after clamping), where 1 indicates maximum
    semantic similarity.

    Args:
        img1_path: Path to the first image (e.g. generated result).
        img2_path: Path to the second image (e.g. input garment).

    Returns:
        Cosine similarity score as a Python float in [0, 1].
    """
    processor = CLIPProcessor.from_pretrained(_CLIP_MODEL_ID)
    model = CLIPVisionModelWithProjection.from_pretrained(_CLIP_MODEL_ID)
    model.eval()

    img1 = Image.open(img1_path).convert("RGB")
    img2 = Image.open(img2_path).convert("RGB")

    inputs = processor(images=[img1, img2], return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.image_embeds  # (2, D)

    similarity = F.cosine_similarity(
        embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0)
    )

    return float(similarity.clamp(min=0.0, max=1.0).item())


# ---------------------------------------------------------------------------
# Batch evaluation
# ---------------------------------------------------------------------------

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def evaluate_directory(
    results_dir: str | Path, ground_truth_dir: str | Path
) -> dict:
    """Compute all metrics for matching image pairs in two directories.

    Pairs are matched by filename: a file ``results_dir/foo.png`` is
    compared to ``ground_truth_dir/foo.png``.  Files present in only one
    directory are silently skipped.

    Args:
        results_dir: Directory containing generated try-on images.
        ground_truth_dir: Directory containing ground truth images.

    Returns:
        A dict with the following keys:

        - ``"per_pair"``: list of dicts, each containing ``filename``,
          ``ssim``, ``psnr``, ``lpips``, ``clip_sim``.
        - ``"mean_ssim"``, ``"mean_psnr"``, ``"mean_lpips"``,
          ``"mean_clip_sim"``: float averages across all pairs.
        - ``"count"``: number of pairs evaluated.
    """
    results_path = Path(results_dir)
    gt_path = Path(ground_truth_dir)

    result_files = {
        f.name for f in results_path.iterdir() if f.suffix.lower() in _IMAGE_EXTENSIONS
    }
    gt_files = {
        f.name for f in gt_path.iterdir() if f.suffix.lower() in _IMAGE_EXTENSIONS
    }
    common = sorted(result_files & gt_files)

    if not common:
        return {
            "per_pair": [],
            "mean_ssim": 0.0,
            "mean_psnr": 0.0,
            "mean_lpips": 0.0,
            "mean_clip_sim": 0.0,
            "count": 0,
        }

    # Cache LPIPS model for repeated calls.
    lpips_model = lpips_lib.LPIPS(net="alex")
    lpips_model.eval()

    per_pair: list[dict] = []

    for name in tqdm(common, desc="Evaluating pairs"):
        res_img = results_path / name
        gt_img = gt_path / name

        sp = compute_ssim_psnr(res_img, gt_img)
        lp = compute_lpips(res_img, gt_img, model=lpips_model)
        cs = compute_clip_similarity(res_img, gt_img)

        per_pair.append(
            {
                "filename": name,
                "ssim": sp["ssim"],
                "psnr": sp["psnr"],
                "lpips": lp,
                "clip_sim": cs,
            }
        )

    count = len(per_pair)
    return {
        "per_pair": per_pair,
        "mean_ssim": sum(p["ssim"] for p in per_pair) / count,
        "mean_psnr": sum(p["psnr"] for p in per_pair) / count,
        "mean_lpips": sum(p["lpips"] for p in per_pair) / count,
        "mean_clip_sim": sum(p["clip_sim"] for p in per_pair) / count,
        "count": count,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _main() -> None:
    """Parse arguments and run batch evaluation."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Compute image quality metrics between generated results "
        "and ground truth images."
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing generated try-on images.",
    )
    parser.add_argument(
        "--ground-truth-dir",
        required=True,
        help="Directory containing ground truth images.",
    )
    parser.add_argument(
        "--output-json",
        default="metrics_output.json",
        help="Path to write JSON results (default: metrics_output.json).",
    )
    args = parser.parse_args()

    results = evaluate_directory(args.results_dir, args.ground_truth_dir)

    with open(args.output_json, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)

    print(f"\nResults written to {args.output_json}")
    print(f"{'Metric':<15} {'Mean':>10}")
    print("-" * 26)
    print(f"{'SSIM':<15} {results['mean_ssim']:>10.4f}")
    print(f"{'PSNR (dB)':<15} {results['mean_psnr']:>10.2f}")
    print(f"{'LPIPS':<15} {results['mean_lpips']:>10.4f}")
    print(f"{'CLIP Sim':<15} {results['mean_clip_sim']:>10.4f}")
    print(f"{'Pairs':<15} {results['count']:>10d}")


if __name__ == "__main__":
    _main()
