"""Unit tests for offline metric computation."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from evaluate import evaluate_pair
from metrics.perceptual import compute_lpips
from metrics.semantic import compute_clip_similarity
from metrics.structural import compute_psnr, compute_ssim


def _save_solid_image(path: Path, rgb: tuple[int, int, int], size: tuple[int, int] = (256, 256)) -> None:
    """Create and save a solid-colour RGB test image.

    Args:
        path: Output file path.
        rgb: RGB colour tuple.
        size: Output image size.
    """
    Image.new("RGB", size, color=rgb).save(path)


def test_ssim_identical_images_near_one(tmp_path: Path) -> None:
    """SSIM should be very close to one for identical images."""
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    _save_solid_image(image_a, (120, 160, 200))
    _save_solid_image(image_b, (120, 160, 200))

    score = compute_ssim(str(image_a), str(image_b))
    assert score > 0.99


def test_ssim_different_images_below_half(tmp_path: Path) -> None:
    """SSIM should be low for strongly different solid colours."""
    image_a = tmp_path / "red.png"
    image_b = tmp_path / "blue.png"
    _save_solid_image(image_a, (255, 0, 0))
    _save_solid_image(image_b, (0, 0, 255))

    score = compute_ssim(str(image_a), str(image_b))
    assert score < 0.5


def test_psnr_identical_images_high(tmp_path: Path) -> None:
    """PSNR should be very high (or infinite) for identical images."""
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    _save_solid_image(image_a, (64, 128, 192))
    _save_solid_image(image_b, (64, 128, 192))

    score = compute_psnr(str(image_a), str(image_b))
    assert score > 40 or score == float("inf")


def test_lpips_identical_images_near_zero(tmp_path: Path) -> None:
    """LPIPS should be close to zero for identical images."""
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    _save_solid_image(image_a, (30, 180, 90))
    _save_solid_image(image_b, (30, 180, 90))

    score = compute_lpips(str(image_a), str(image_b))
    assert score < 0.01


def test_lpips_different_images_above_threshold(tmp_path: Path) -> None:
    """LPIPS should be clearly higher for distinct colours."""
    image_a = tmp_path / "red.png"
    image_b = tmp_path / "blue.png"
    _save_solid_image(image_a, (255, 0, 0))
    _save_solid_image(image_b, (0, 0, 255))

    score = compute_lpips(str(image_a), str(image_b))
    assert score > 0.3


def test_clip_similar_images_high(tmp_path: Path) -> None:
    """CLIP similarity should stay high for slight variations of one image."""
    image_a = tmp_path / "base.png"
    image_b = tmp_path / "variant.png"
    _save_solid_image(image_a, (110, 120, 130))
    _save_solid_image(image_b, (115, 125, 135))

    score = compute_clip_similarity(str(image_a), str(image_b))
    assert score > 0.8


def test_evaluate_pair_returns_all_metrics(tmp_path: Path) -> None:
    """evaluate_pair should return all expected metric keys."""
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    _save_solid_image(image_a, (70, 70, 70))
    _save_solid_image(image_b, (80, 80, 80))

    result = evaluate_pair(str(image_a), str(image_b))
    assert set(result.keys()) == {"ssim", "psnr", "lpips", "clip_sim"}
