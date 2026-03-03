"""Tests for api.services.postprocessing – Reinhard colour transfer."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from api.services.postprocessing import colour_transfer_reinhard


class TestColourTransferReinhard:
    """Tests for colour_transfer_reinhard."""

    def test_colour_transfer_shifts_toward_reference(self, tmp_path):
        """The result's blue channel mean should increase when transferring
        from a reddish source toward a bluish reference."""
        # Reddish source (high red, low blue in BGR → high blue, low red)
        source = np.full((256, 256, 3), (30, 50, 200), dtype=np.uint8)  # BGR
        source_path = str(tmp_path / "source.jpg")
        cv2.imwrite(source_path, source)

        # Bluish reference
        reference = np.full((256, 256, 3), (220, 50, 30), dtype=np.uint8)  # BGR
        reference_path = str(tmp_path / "reference.jpg")
        cv2.imwrite(reference_path, reference)

        output_path = colour_transfer_reinhard(source_path, reference_path)
        result = cv2.imread(output_path)

        # Blue channel (index 0 in BGR) should have shifted up toward reference
        assert result[:, :, 0].mean() > source[:, :, 0].mean()

    def test_colour_transfer_output_exists(self, tmp_path):
        """Output file should exist, end with _cc.jpg, and be readable."""
        grey = np.full((256, 256, 3), 128, dtype=np.uint8)

        source_path = str(tmp_path / "grey_src.jpg")
        cv2.imwrite(source_path, grey)

        reference_path = str(tmp_path / "grey_ref.jpg")
        cv2.imwrite(reference_path, grey)

        output_path = colour_transfer_reinhard(source_path, reference_path)

        assert output_path.endswith("_cc.jpg")
        assert cv2.imread(output_path) is not None
