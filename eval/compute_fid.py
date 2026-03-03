"""FID (Fréchet Inception Distance) computation for virtual try-on evaluation.

Measures how realistic the distribution of generated images is compared to a
reference set of real images.  Used as a distributional metric alongside the
per-pair metrics in ``compute_metrics.py``.
"""

from __future__ import annotations

import argparse

import torch
import torch_fidelity


def compute_fid(generated_dir: str, real_dir: str) -> float:
    """Compute the Fréchet Inception Distance between two image directories.

    FID measures how similar the distribution of generated images is to a
    distribution of real images by comparing statistics of Inception-v3
    features.  **Lower scores indicate that the generated images are more
    realistic and diverse**, matching the real distribution more closely.

    Args:
        generated_dir: Path to the directory of generated images.
        real_dir: Path to the directory of real / ground truth images.

    Returns:
        The FID score as a Python float (lower is better).
    """
    use_cuda = torch.cuda.is_available()

    metrics = torch_fidelity.calculate_metrics(
        input1=generated_dir,
        input2=real_dir,
        fid=True,
        cuda=use_cuda,
    )

    return float(metrics["frechet_inception_distance"])


def _main() -> None:
    """Parse arguments and compute FID."""
    parser = argparse.ArgumentParser(
        description="Compute Fréchet Inception Distance (FID) between two "
        "directories of images."
    )
    parser.add_argument(
        "--generated-dir",
        required=True,
        help="Directory containing generated images.",
    )
    parser.add_argument(
        "--real-dir",
        required=True,
        help="Directory containing real / ground truth images.",
    )
    args = parser.parse_args()

    fid_score = compute_fid(args.generated_dir, args.real_dir)
    print(f"FID: {fid_score:.4f}")


if __name__ == "__main__":
    _main()
