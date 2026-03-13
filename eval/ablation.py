"""Ablation study runner for preprocessing impact analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scipy.stats import wilcoxon

from evaluate import evaluate_directory


def _extract_summary(metrics: dict) -> dict:
    """Extract aggregate metrics needed for ablation reporting.

    Args:
        metrics: Evaluation output dictionary from ``evaluate_directory``.

    Returns:
        A dictionary containing mean metric values and sample count.
    """
    return {
        "mean_ssim": metrics.get("mean_ssim"),
        "mean_psnr": metrics.get("mean_psnr"),
        "mean_lpips": metrics.get("mean_lpips"),
        "mean_clip_sim": metrics.get("mean_clip_sim"),
        "count": metrics.get("count", 0),
    }


def _compute_deltas(baseline: dict, condition: dict) -> dict:
    """Compute metric deltas between a condition and baseline.

    Args:
        baseline: Baseline condition summary metrics.
        condition: Comparison condition summary metrics.

    Returns:
        A dictionary of signed metric deltas.
    """
    return {
        "ssim_delta": condition["mean_ssim"] - baseline["mean_ssim"],
        "psnr_delta": condition["mean_psnr"] - baseline["mean_psnr"],
        "lpips_delta": condition["mean_lpips"] - baseline["mean_lpips"],
        "clip_sim_delta": condition["mean_clip_sim"] - baseline["mean_clip_sim"],
    }


def _ssim_map(per_pair: list[dict]) -> dict[str, float]:
    """Build a filename-to-SSIM map from per-pair records.

    Args:
        per_pair: Per-pair entries produced by ``evaluate_directory``.

    Returns:
        Mapping from filename to SSIM score.
    """
    return {item["filename"]: float(item["ssim"]) for item in per_pair}


def _wilcoxon_p_value(baseline_pairs: list[dict], condition_pairs: list[dict]) -> float | None:
    """Compute Wilcoxon signed-rank p-value on paired SSIM samples.

    Args:
        baseline_pairs: Baseline per-pair metric entries.
        condition_pairs: Condition per-pair metric entries.

    Returns:
        The p-value as a float, or ``None`` if not computable.
    """
    baseline_map = _ssim_map(baseline_pairs)
    condition_map = _ssim_map(condition_pairs)

    common_filenames = sorted(set(baseline_map) & set(condition_map))
    if not common_filenames:
        return None

    baseline_scores = [baseline_map[name] for name in common_filenames]
    condition_scores = [condition_map[name] for name in common_filenames]

    if len(baseline_scores) < 2:
        return None

    if all(abs(a - b) < 1e-12 for a, b in zip(baseline_scores, condition_scores)):
        return 1.0

    statistic, p_value = wilcoxon(baseline_scores, condition_scores)
    _ = statistic
    return float(p_value)


def run_ablation(
    baseline_dir: str,
    clahe_dir: str,
    colour_dir: str,
    both_dir: str,
    ground_truth_dir: str,
) -> dict:
    """Run all ablation conditions and compute comparative statistics.

    Args:
        baseline_dir: Directory for outputs with no preprocessing.
        clahe_dir: Directory for outputs with CLAHE only.
        colour_dir: Directory for outputs with colour transfer only.
        both_dir: Directory for outputs with both preprocessing steps.
        ground_truth_dir: Directory containing ground-truth images.

    Returns:
        Structured ablation results with summaries, deltas, and p-values.
    """
    baseline_eval = evaluate_directory(baseline_dir, ground_truth_dir)
    clahe_eval = evaluate_directory(clahe_dir, ground_truth_dir)
    colour_eval = evaluate_directory(colour_dir, ground_truth_dir)
    both_eval = evaluate_directory(both_dir, ground_truth_dir)

    baseline_summary = _extract_summary(baseline_eval)
    clahe_summary = _extract_summary(clahe_eval)
    colour_summary = _extract_summary(colour_eval)
    both_summary = _extract_summary(both_eval)

    clahe_p_value = _wilcoxon_p_value(
        baseline_eval.get("per_pair", []),
        clahe_eval.get("per_pair", []),
    )
    colour_p_value = _wilcoxon_p_value(
        baseline_eval.get("per_pair", []),
        colour_eval.get("per_pair", []),
    )

    return {
        "baseline": baseline_summary,
        "clahe_only": clahe_summary,
        "colour_transfer_only": colour_summary,
        "both": both_summary,
        "deltas": {
            "clahe_impact": _compute_deltas(baseline_summary, clahe_summary),
            "colour_transfer_impact": _compute_deltas(baseline_summary, colour_summary),
        },
        "significance": {
            "clahe_p_value": clahe_p_value,
            "colour_transfer_p_value": colour_p_value,
        },
    }


def main() -> None:
    """Parse command-line arguments and run the ablation pipeline.

    Args:
        None.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(
        description="Run preprocessing ablation study and significance testing."
    )
    parser.add_argument(
        "--baseline-dir",
        required=True,
        help="Directory containing baseline results (no preprocessing).",
    )
    parser.add_argument(
        "--clahe-dir",
        required=True,
        help="Directory containing CLAHE-only results.",
    )
    parser.add_argument(
        "--colour-dir",
        required=True,
        help="Directory containing colour-transfer-only results.",
    )
    parser.add_argument(
        "--both-dir",
        required=True,
        help="Directory containing results with both preprocessing steps.",
    )
    parser.add_argument(
        "--ground-truth-dir",
        required=True,
        help="Directory containing ground-truth images.",
    )
    parser.add_argument(
        "--output-json",
        default="ablation_results.json",
        help='Output JSON path (default: "ablation_results.json").',
    )
    args = parser.parse_args()

    result = run_ablation(
        baseline_dir=args.baseline_dir,
        clahe_dir=args.clahe_dir,
        colour_dir=args.colour_dir,
        both_dir=args.both_dir,
        ground_truth_dir=args.ground_truth_dir,
    )

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Saved ablation results to {output_path}")


if __name__ == "__main__":
    main()
