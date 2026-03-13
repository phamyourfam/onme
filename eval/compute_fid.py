"""FID computation for offline virtual try-on evaluation."""

from __future__ import annotations

import argparse

import torch
import torch_fidelity


def compute_fid(generated_dir: str, real_dir: str) -> float:
    """Compute Fréchet Inception Distance between two image directories.

    FID compares the feature distribution of generated images against a real
    reference distribution. Lower scores are better and indicate that the
    generated set is closer to the real set in realism and diversity.

    Args:
        generated_dir: Path to the directory containing generated images.
        real_dir: Path to the directory containing real reference images.

    Returns:
        The FID score as a Python float.
    """
    use_cuda = torch.cuda.is_available()

    metrics = torch_fidelity.calculate_metrics(
        input1=generated_dir,
        input2=real_dir,
        fid=True,
        cuda=use_cuda,
    )

    return float(metrics["frechet_inception_distance"])


def main() -> None:
    """Parse command-line arguments and print an FID score."""
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
    main()
