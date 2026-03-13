"""Generate dissertation figures from evaluation and ablation outputs."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image


def _load_json(path: str | Path) -> dict:
    """Load and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON dictionary.
    """
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _save_figure(fig: plt.Figure, output_dir: Path, stem: str) -> None:
    """Save a matplotlib figure as dissertation-ready PNG and SVG.

    Args:
        fig: Matplotlib figure object.
        output_dir: Directory where files are written.
        stem: Base filename without extension.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)


def _style_axes(ax: plt.Axes) -> None:
    """Apply clean academic styling to a plot axis.

    Args:
        ax: Matplotlib axis to style.
    """
    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_model_metric_bars(results: dict, output_dir: Path) -> None:
    """Plot grouped bars comparing models across metrics.

    Args:
        results: Aggregated results JSON dictionary.
        output_dir: Output directory for generated plots.
    """
    models = results.get("models", [])
    if not models:
        return

    metric_specs = [
        ("ssim", "SSIM"),
        ("psnr", "PSNR"),
        ("lpips", "LPIPS"),
        ("clip_score", "CLIP"),
        ("fid", "FID"),
    ]

    model_names = [model["name"] for model in models]
    x_positions = list(range(len(metric_specs)))
    width = 0.8 / max(len(models), 1)

    fig, ax = plt.subplots(figsize=(10, 5))
    colours = ["#6B7280", "#9CA3AF", "#4B5563"]

    for model_index, model in enumerate(models):
        offsets = [x + (model_index - (len(models) - 1) / 2) * width for x in x_positions]
        values = [
            float(model.get(metric_key)) if model.get(metric_key) is not None else 0.0
            for metric_key, _ in metric_specs
        ]
        ax.bar(
            offsets,
            values,
            width=width,
            color=colours[model_index % len(colours)],
            label=model_names[model_index],
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels([label for _, label in metric_specs])
    ax.set_ylabel("Metric Value")
    ax.set_title("Model Comparison Across Evaluation Metrics")
    ax.legend(frameon=False)
    _style_axes(ax)
    _save_figure(fig, output_dir, "model_metrics_grouped_bar")


def plot_ablation_bars(ablation: dict, output_dir: Path) -> None:
    """Plot ablation with/without bars for preprocessing steps.

    Args:
        ablation: Ablation section from aggregated metrics JSON.
        output_dir: Output directory for generated plots.
    """
    steps = [
        (
            "CLAHE",
            ablation.get("without_clahe", {}),
            ablation.get("with_clahe", {}),
        ),
        (
            "Colour Correction",
            ablation.get("without_colour_correction", {}),
            ablation.get("with_colour_correction", {}),
        ),
    ]

    metric_key = "ssim"
    labels = [step[0] for step in steps]
    without_values = [float(step[1].get(metric_key) or 0.0) for step in steps]
    with_values = [float(step[2].get(metric_key) or 0.0) for step in steps]

    x_positions = list(range(len(steps)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(
        [x - width / 2 for x in x_positions],
        without_values,
        width=width,
        color="#9CA3AF",
        label="Without",
    )
    ax.bar(
        [x + width / 2 for x in x_positions],
        with_values,
        width=width,
        color="#4B5563",
        label="With",
    )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("SSIM")
    ax.set_title("Ablation Study: With vs Without Preprocessing")
    ax.legend(frameon=False)
    _style_axes(ax)
    _save_figure(fig, output_dir, "ablation_with_without_bar")


def plot_ssim_boxplots(results: dict, output_dir: Path) -> None:
    """Plot per-pair SSIM distributions as model box plots.

    Args:
        results: Dictionary keyed by model name with evaluate.py outputs.
        output_dir: Output directory for generated plots.
    """
    labels = []
    values = []
    for model_name, metrics in results.items():
        per_pair = metrics.get("per_pair", [])
        scores = [float(item.get("ssim", 0.0)) for item in per_pair if "ssim" in item]
        if scores:
            labels.append(model_name)
            values.append(scores)

    if not values:
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.boxplot(values, labels=labels, patch_artist=True)
    ax.set_ylabel("SSIM")
    ax.set_title("Per-pair SSIM Distribution by Model")
    _style_axes(ax)
    _save_figure(fig, output_dir, "ssim_boxplot_by_model")


def plot_sample_grid(sample_root: str, output_dir: Path) -> None:
    """Create a sample comparison grid from a prepared directory structure.

    Expected subdirectories under ``sample_root`` are ``person``, ``garment``,
    and one directory per model result. Files are matched by filename.

    Args:
        sample_root: Root directory containing sample image folders.
        output_dir: Output directory for generated plots.
    """
    root = Path(sample_root)
    if not root.exists():
        return

    person_dir = root / "person"
    garment_dir = root / "garment"
    model_dirs = [path for path in root.iterdir() if path.is_dir() and path.name not in {"person", "garment"}]
    if not person_dir.exists() or not garment_dir.exists() or not model_dirs:
        return

    filenames = sorted(path.name for path in person_dir.iterdir() if path.is_file())
    if not filenames:
        return

    sample_count = min(6, len(filenames))
    selected = random.sample(filenames, sample_count)

    columns = ["person", "garment"] + [path.name for path in model_dirs]
    fig, axes = plt.subplots(sample_count, len(columns), figsize=(2.2 * len(columns), 2.6 * sample_count))

    if sample_count == 1:
        axes = [axes]

    for row_idx, filename in enumerate(selected):
        image_paths = [person_dir / filename, garment_dir / filename] + [directory / filename for directory in model_dirs]
        for col_idx, image_path in enumerate(image_paths):
            axis = axes[row_idx][col_idx] if sample_count > 1 else axes[col_idx]
            if image_path.exists():
                axis.imshow(Image.open(image_path).convert("RGB"))
            axis.set_xticks([])
            axis.set_yticks([])
            if row_idx == 0:
                axis.set_title(columns[col_idx], fontsize=10)

    fig.suptitle("Sample Comparison Grid", fontsize=12)
    _save_figure(fig, output_dir, "sample_comparison_grid")


def main() -> None:
    """Parse command-line arguments and generate evaluation figures.

    Args:
        None.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(
        description="Generate dissertation visualisations from evaluation outputs."
    )
    parser.add_argument("--results-json", required=True, help="Path to aggregated results JSON.")
    parser.add_argument("--ablation-json", required=False, help="Path to ablation results JSON.")
    parser.add_argument("--output-dir", required=True, help="Directory for figure outputs.")
    parser.add_argument(
        "--per-pair-jsons",
        nargs="*",
        default=[],
        help="Optional model_name=path pairs for per-pair box plots.",
    )
    parser.add_argument(
        "--sample-root",
        default=None,
        help="Optional root directory for sample comparison grid generation.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    aggregated = _load_json(args.results_json)

    plot_model_metric_bars(aggregated, output_dir)
    plot_ablation_bars(aggregated.get("ablation", {}), output_dir)

    per_pair_payload: dict[str, dict] = {}
    for item in args.per_pair_jsons:
        if "=" not in item:
            continue
        model_name, json_path = item.split("=", 1)
        per_pair_payload[model_name] = _load_json(json_path)
    if per_pair_payload:
        plot_ssim_boxplots(per_pair_payload, output_dir)

    if args.sample_root:
        plot_sample_grid(args.sample_root, output_dir)

    if args.ablation_json:
        _ = _load_json(args.ablation_json)

    print(f"Saved figures to {output_dir}")


if __name__ == "__main__":
    main()
