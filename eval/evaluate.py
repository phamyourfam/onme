"""Batch evaluation runner for offline virtual try-on metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import lpips
from tqdm import tqdm

from metrics.perceptual import compute_lpips
from metrics.semantic import compute_clip_similarity
from metrics.structural import compute_psnr, compute_ssim


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def evaluate_pair(img1_path: str, img2_path: str, lpips_model: object = None) -> dict:
    """Compute all supported metrics for a single image pair.

    Args:
        img1_path: Path to the generated or predicted image.
        img2_path: Path to the reference or ground-truth image.
        lpips_model: Optional pre-loaded LPIPS model to reuse across calls.

    Returns:
        A dictionary containing ``ssim``, ``psnr``, ``lpips``, and
        ``clip_sim`` scores.
    """
    return {
        "ssim": compute_ssim(img1_path, img2_path),
        "psnr": compute_psnr(img1_path, img2_path),
        "lpips": compute_lpips(img1_path, img2_path, model=lpips_model),
        "clip_sim": compute_clip_similarity(img1_path, img2_path),
    }


def evaluate_directory(results_dir: str, ground_truth_dir: str) -> dict:
    """Evaluate all filename-matched image pairs in two directories.

    The function pairs images by exact filename match. Files that exist in one
    directory but not the other are ignored.

    Args:
        results_dir: Directory containing generated result images.
        ground_truth_dir: Directory containing ground-truth reference images.

    Returns:
        A dictionary with per-pair results and aggregate mean metrics.
    """
    results_path = Path(results_dir)
    ground_truth_path = Path(ground_truth_dir)

    result_files = {
        path.name
        for path in results_path.iterdir()
        if path.is_file() and path.suffix.lower() in _IMAGE_EXTENSIONS
    }
    ground_truth_files = {
        path.name
        for path in ground_truth_path.iterdir()
        if path.is_file() and path.suffix.lower() in _IMAGE_EXTENSIONS
    }
    paired_filenames = sorted(result_files & ground_truth_files)

    if not paired_filenames:
        return {
            "per_pair": [],
            "mean_ssim": 0.0,
            "mean_psnr": 0.0,
            "mean_lpips": 0.0,
            "mean_clip_sim": 0.0,
            "count": 0,
        }

    lpips_model = lpips.LPIPS(net="alex")
    lpips_model.eval()

    per_pair: list[dict[str, Any]] = []
    for filename in tqdm(paired_filenames, desc="Evaluating pairs"):
        metrics = evaluate_pair(
            str(results_path / filename),
            str(ground_truth_path / filename),
            lpips_model=lpips_model,
        )
        per_pair.append({"filename": filename, **metrics})

    count = len(per_pair)
    return {
        "per_pair": per_pair,
        "mean_ssim": sum(entry["ssim"] for entry in per_pair) / count,
        "mean_psnr": sum(entry["psnr"] for entry in per_pair) / count,
        "mean_lpips": sum(entry["lpips"] for entry in per_pair) / count,
        "mean_clip_sim": sum(entry["clip_sim"] for entry in per_pair) / count,
        "count": count,
    }


def _print_summary(results: dict) -> None:
    """Print a small summary table for evaluated metrics.

    Args:
        results: Evaluation output from ``evaluate_directory``.
    """
    print(f"{'Metric':<15} {'Value':>12}")
    print("-" * 28)
    print(f"{'SSIM':<15} {results['mean_ssim']:>12.4f}")
    print(f"{'PSNR':<15} {results['mean_psnr']:>12.4f}")
    print(f"{'LPIPS':<15} {results['mean_lpips']:>12.4f}")
    print(f"{'CLIP Sim':<15} {results['mean_clip_sim']:>12.4f}")
    print(f"{'Pairs':<15} {results['count']:>12d}")


def main() -> None:
    """Parse command-line arguments and run directory evaluation.

    Args:
        None.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(
        description="Evaluate virtual try-on results against ground-truth images."
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing generated result images.",
    )
    parser.add_argument(
        "--ground-truth-dir",
        required=True,
        help="Directory containing ground-truth reference images.",
    )
    parser.add_argument(
        "--output-json",
        default="eval_results.json",
        help='Output JSON path (default: "eval_results.json").',
    )
    args = parser.parse_args()

    results = evaluate_directory(args.results_dir, args.ground_truth_dir)

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"Saved evaluation results to {output_path}")
    _print_summary(results)


if __name__ == "__main__":
    main()
