"""Aggregate evaluation metrics into a single JSON for the frontend.

Combines per-model metric outputs from ``compute_metrics.py`` and FID scores
from ``compute_fid.py`` into a unified JSON file that the web frontend's
metrics page reads.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _load_json(path: str | Path) -> dict:
    """Load and return parsed JSON from *path*."""
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def _build_model_entry(name: str, metrics: dict, fid: float) -> dict:
    """Build a single model entry for the output JSON."""
    return {
        "name": name,
        "fid": fid,
        "lpips": metrics.get("mean_lpips"),
        "ssim": metrics.get("mean_ssim"),
        "psnr": metrics.get("mean_psnr"),
        "clip_score": metrics.get("mean_clip_sim"),
        "avg_latency_ms": None,
        "sample_count": metrics.get("count"),
    }


def _build_ablation(ablation_dir: str | Path | None) -> dict:
    """Build ablation section from directory of JSON files.

    Expected files: ``with_clahe.json``, ``without_clahe.json``,
    ``with_cc.json``, ``without_cc.json``.  Each should contain at
    minimum the keys ``mean_ssim``, ``mean_lpips``, ``mean_psnr``.
    """
    null_entry = {"ssim": None, "lpips": None, "psnr": None}
    result = {
        "with_clahe": null_entry,
        "without_clahe": null_entry,
        "with_colour_correction": null_entry,
        "without_colour_correction": null_entry,
    }

    if ablation_dir is None:
        return result

    ablation_path = Path(ablation_dir)
    mapping = {
        "with_clahe.json": "with_clahe",
        "without_clahe.json": "without_clahe",
        "with_cc.json": "with_colour_correction",
        "without_cc.json": "without_colour_correction",
    }

    for filename, key in mapping.items():
        filepath = ablation_path / filename
        if filepath.exists():
            data = _load_json(filepath)
            result[key] = {
                "ssim": data.get("mean_ssim"),
                "lpips": data.get("mean_lpips"),
                "psnr": data.get("mean_psnr"),
            }

    return result


def aggregate(
    catvton_metrics_path: str,
    ootd_metrics_path: str,
    catvton_fid: float,
    ootd_fid: float,
    ablation_dir: str | None = None,
) -> dict:
    """Build the unified metrics dict.

    Args:
        catvton_metrics_path: Path to CatVTON ``compute_metrics.py`` output.
        ootd_metrics_path: Path to OOTDiffusion ``compute_metrics.py`` output.
        catvton_fid: FID score for CatVTON.
        ootd_fid: FID score for OOTDiffusion.
        ablation_dir: Optional directory containing ablation JSON files.

    Returns:
        A dict matching the frontend ``MetricsData`` TypeScript interface.
    """
    catvton_data = _load_json(catvton_metrics_path)
    ootd_data = _load_json(ootd_metrics_path)

    return {
        "models": [
            _build_model_entry("CatVTON", catvton_data, catvton_fid),
            _build_model_entry("OOTDiffusion", ootd_data, ootd_fid),
        ],
        "ablation": _build_ablation(ablation_dir),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def _main() -> None:
    """Parse arguments and write aggregated metrics JSON."""
    parser = argparse.ArgumentParser(
        description="Aggregate evaluation metric outputs into a single JSON "
        "file for the frontend metrics page."
    )
    parser.add_argument(
        "--catvton-metrics",
        required=True,
        help="Path to CatVTON metrics JSON from compute_metrics.py.",
    )
    parser.add_argument(
        "--ootd-metrics",
        required=True,
        help="Path to OOTDiffusion metrics JSON from compute_metrics.py.",
    )
    parser.add_argument(
        "--catvton-fid",
        required=True,
        type=float,
        help="FID score for CatVTON.",
    )
    parser.add_argument(
        "--ootd-fid",
        required=True,
        type=float,
        help="FID score for OOTDiffusion.",
    )
    parser.add_argument(
        "--ablation-dir",
        default=None,
        help="Optional directory with ablation JSON files "
        "(with_clahe.json, without_clahe.json, with_cc.json, without_cc.json).",
    )
    parser.add_argument(
        "--output",
        default="../web/static/metrics.json",
        help='Output path (default: "../web/static/metrics.json").',
    )
    args = parser.parse_args()

    result = aggregate(
        catvton_metrics_path=args.catvton_metrics,
        ootd_metrics_path=args.ootd_metrics,
        catvton_fid=args.catvton_fid,
        ootd_fid=args.ootd_fid,
        ablation_dir=args.ablation_dir,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(f"Aggregated metrics written to {output_path}")


if __name__ == "__main__":
    _main()
