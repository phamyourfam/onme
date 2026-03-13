"""Aggregate model and ablation metrics into frontend dashboard JSON."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _load_json(path: str | Path) -> dict:
    """Load and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON content as a dictionary.
    """
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _build_model_entry(name: str, metrics: dict | None, fid: float | None) -> dict:
    """Build one model entry in the required dashboard schema.

    Args:
        name: Model display name.
        metrics: Metrics dictionary from ``evaluate.py`` output or ``None``.
        fid: FID score for the model or ``None``.

    Returns:
        A model entry dictionary for output JSON.
    """
    metrics_dict = metrics or {}
    return {
        "name": name,
        "fid": fid,
        "lpips": metrics_dict.get("mean_lpips"),
        "ssim": metrics_dict.get("mean_ssim"),
        "psnr": metrics_dict.get("mean_psnr"),
        "clip_score": metrics_dict.get("mean_clip_sim"),
        "avg_latency_ms": None,
        "sample_count": int(metrics_dict.get("count", 0) or 0),
    }


def _ablation_metric_block(summary: dict | None) -> dict:
    """Convert ablation condition summary into dashboard metric block.

    Args:
        summary: Condition summary dictionary or ``None``.

    Returns:
        Dictionary with ``ssim``, ``lpips``, and ``psnr`` keys.
    """
    if not summary:
        return {"ssim": None, "lpips": None, "psnr": None}
    return {
        "ssim": summary.get("mean_ssim"),
        "lpips": summary.get("mean_lpips"),
        "psnr": summary.get("mean_psnr"),
    }


def _build_ablation(ablation_json_path: str | None) -> dict:
    """Build ablation section in the exact required output shape.

    Args:
        ablation_json_path: Optional path to ``ablation_results.json``.

    Returns:
        Ablation section matching frontend schema.
    """
    base = {
        "with_clahe": {"ssim": None, "lpips": None, "psnr": None},
        "without_clahe": {"ssim": None, "lpips": None, "psnr": None},
        "with_colour_correction": {"ssim": None, "lpips": None, "psnr": None},
        "without_colour_correction": {"ssim": None, "lpips": None, "psnr": None},
        "significance": {
            "clahe_p_value": None,
            "colour_transfer_p_value": None,
        },
    }

    if not ablation_json_path:
        return base

    ablation_data = _load_json(ablation_json_path)
    baseline = ablation_data.get("baseline")
    clahe_only = ablation_data.get("clahe_only")
    colour_only = ablation_data.get("colour_transfer_only")
    significance = ablation_data.get("significance", {})

    base["without_clahe"] = _ablation_metric_block(baseline)
    base["with_clahe"] = _ablation_metric_block(clahe_only)
    base["without_colour_correction"] = _ablation_metric_block(baseline)
    base["with_colour_correction"] = _ablation_metric_block(colour_only)
    base["significance"] = {
        "clahe_p_value": significance.get("clahe_p_value"),
        "colour_transfer_p_value": significance.get("colour_transfer_p_value"),
    }
    return base


def aggregate_metrics(
    catvton_metrics_path: str,
    ootd_metrics_path: str,
    catvton_fid: float | None,
    ootd_fid: float | None,
    catv2ton_metrics_path: str | None = None,
    catv2ton_fid: float | None = None,
    ablation_json_path: str | None = None,
) -> dict:
    """Aggregate model metrics, FID scores, and ablation data.

    Args:
        catvton_metrics_path: Path to CatVTON evaluation JSON.
        ootd_metrics_path: Path to OOTDiffusion evaluation JSON.
        catvton_fid: CatVTON FID score.
        ootd_fid: OOTDiffusion FID score.
        catv2ton_metrics_path: Optional path to CatV2TON evaluation JSON.
        catv2ton_fid: Optional CatV2TON FID score.
        ablation_json_path: Optional path to ablation results JSON.

    Returns:
        Aggregated metrics dictionary matching dashboard schema.
    """
    catvton_metrics = _load_json(catvton_metrics_path)
    ootd_metrics = _load_json(ootd_metrics_path)

    models = [
        _build_model_entry("CatVTON", catvton_metrics, catvton_fid),
        _build_model_entry("OOTDiffusion", ootd_metrics, ootd_fid),
    ]

    if catv2ton_metrics_path:
        catv2ton_metrics = _load_json(catv2ton_metrics_path)
        models.append(_build_model_entry("CatV2TON", catv2ton_metrics, catv2ton_fid))

    return {
        "models": models,
        "ablation": _build_ablation(ablation_json_path),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    """Parse command-line arguments and write aggregated metrics JSON.

    Args:
        None.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(
        description="Aggregate model and ablation metrics into dashboard JSON."
    )
    parser.add_argument("--catvton-metrics", required=True)
    parser.add_argument("--ootd-metrics", required=True)
    parser.add_argument("--catv2ton-metrics", required=False)
    parser.add_argument("--catvton-fid", required=True, type=float)
    parser.add_argument("--ootd-fid", required=True, type=float)
    parser.add_argument("--catv2ton-fid", required=False, type=float)
    parser.add_argument("--ablation-json", required=False)
    parser.add_argument("--output", default="../web/static/metrics.json")
    args = parser.parse_args()

    aggregated = aggregate_metrics(
        catvton_metrics_path=args.catvton_metrics,
        ootd_metrics_path=args.ootd_metrics,
        catvton_fid=args.catvton_fid,
        ootd_fid=args.ootd_fid,
        catv2ton_metrics_path=args.catv2ton_metrics,
        catv2ton_fid=args.catv2ton_fid,
        ablation_json_path=args.ablation_json,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(aggregated, indent=2), encoding="utf-8")
    print(f"Aggregated metrics written to {output_path}")


if __name__ == "__main__":
    main()
