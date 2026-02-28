"""Tests for api.services.preprocessing – validation & resizing."""

from __future__ import annotations

import os
import tempfile

import pytest
from PIL import Image

from api.services.preprocessing import (
    resize_for_model,
    validate_image,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_image(
    width: int,
    height: int,
    mode: str = "RGB",
    fmt: str = "PNG",
) -> str:
    """Create a temporary image file and return its path."""
    img = Image.new(mode, (width, height), color="red")
    fd, path = tempfile.mkstemp(suffix=f".{fmt.lower()}")
    os.close(fd)
    img.save(path, format=fmt)
    return path


# ===== validate_image =====


class TestValidateImage:
    """Tests for validate_image."""

    def test_reject_too_small(self):
        path = _make_image(100, 100)
        try:
            with pytest.raises(ValueError, match="too small"):
                validate_image(path)
        finally:
            os.unlink(path)

    def test_reject_too_small_one_axis(self):
        path = _make_image(255, 512)
        try:
            with pytest.raises(ValueError, match="too small"):
                validate_image(path)
        finally:
            os.unlink(path)

    def test_reject_too_large(self):
        # Only create a small file and patch the size check –
        # actually creating a 5000×5000 image is fine for a test.
        path = _make_image(4097, 4097)
        try:
            with pytest.raises(ValueError, match="too large"):
                validate_image(path)
        finally:
            os.unlink(path)

    def test_reject_too_large_one_axis(self):
        path = _make_image(4097, 512)
        try:
            with pytest.raises(ValueError, match="too large"):
                validate_image(path)
        finally:
            os.unlink(path)

    def test_accept_valid(self):
        path = _make_image(512, 512)
        try:
            w, h = validate_image(path)
            assert w == 512
            assert h == 512
        finally:
            os.unlink(path)

    def test_accept_min_boundary(self):
        path = _make_image(256, 256)
        try:
            w, h = validate_image(path)
            assert (w, h) == (256, 256)
        finally:
            os.unlink(path)

    def test_accept_max_boundary(self):
        path = _make_image(4096, 4096)
        try:
            w, h = validate_image(path)
            assert (w, h) == (4096, 4096)
        finally:
            os.unlink(path)


# ===== resize_for_model =====


class TestResizeForModel:
    """Tests for resize_for_model."""

    def test_correct_dimensions(self):
        path = _make_image(800, 1200)
        try:
            out = resize_for_model(path)
            with Image.open(out) as img:
                assert img.size == (768, 1024)
        finally:
            os.unlink(path)
            if os.path.exists(out):
                os.unlink(out)

    def test_rgba_conversion(self):
        path = _make_image(512, 512, mode="RGBA")
        try:
            out = resize_for_model(path)
            with Image.open(out) as img:
                assert img.mode == "RGB"
        finally:
            os.unlink(path)
            if os.path.exists(out):
                os.unlink(out)

    def test_output_path_suffix(self):
        path = _make_image(512, 512)
        try:
            out = resize_for_model(path)
            assert out.endswith("_resized.jpg")
        finally:
            os.unlink(path)
            if os.path.exists(out):
                os.unlink(out)
