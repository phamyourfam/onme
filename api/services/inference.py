"""Replicate-backed inference service for virtual try-on models."""

from __future__ import annotations

import replicate
import httpx

# TODO: Verify version hashes at https://replicate.com before running inference.
MODEL_REGISTRY: dict[str, str] = {
    "catvton": "zhengchong/catvton:PUT_VERSION_HASH_HERE",
    "ootdiffusion": "PUT_OWNER/ootdiffusion:PUT_VERSION_HASH_HERE",
}

MODEL_INPUT_KEYS: dict[str, dict[str, str]] = {
    "catvton": {"person": "image", "garment": "cloth"},
    "ootdiffusion": {"person": "model_image", "garment": "cloth_image"},
}


def run_inference_sync(
    model_name: str,
    person_image_path: str,
    garment_image_path: str,
) -> str:
    """Run a synchronous inference call against the Replicate API.

    Opens both image files as binary and sends them to the Replicate model
    identified by *model_name*.  This function is synchronous because it
    is intended to run inside a background thread.

    Args:
        model_name: Key into ``MODEL_REGISTRY`` (e.g. ``"catvton"``).
        person_image_path: Local path to the person image file.
        garment_image_path: Local path to the garment image file.

    Returns:
        The output URL string produced by the model.

    Raises:
        ValueError: If *model_name* is not found in ``MODEL_REGISTRY``.
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model '{model_name}'. "
            f"Available: {list(MODEL_REGISTRY)}"
        )

    model_id = MODEL_REGISTRY[model_name]
    keys = MODEL_INPUT_KEYS[model_name]

    with open(person_image_path, "rb") as person_file, \
         open(garment_image_path, "rb") as garment_file:
        output = replicate.run(
            model_id,
            input={
                keys["person"]: person_file,
                keys["garment"]: garment_file,
            },
        )

    # Replicate may return a single URL string or a list of URLs.
    if isinstance(output, list):
        return str(output[0])
    return str(output)


def download_result(url: str, save_path: str) -> str:
    """Download a file from *url* and save it to *save_path*.

    Args:
        url: The remote URL to fetch (typically a Replicate CDN link).
        save_path: Local filesystem path where the content will be written.

    Returns:
        The *save_path* that was written to.
    """
    with httpx.Client(timeout=60.0) as client:
        response = client.get(url)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
    return save_path


def run_and_save_sync(
    model_name: str,
    person_image_path: str,
    garment_image_path: str,
    output_path: str,
) -> str:
    """Run inference and download the result in one call.

    Convenience wrapper that calls :func:`run_inference_sync` followed by
    :func:`download_result`.

    Args:
        model_name: Key into ``MODEL_REGISTRY``.
        person_image_path: Local path to the person image file.
        garment_image_path: Local path to the garment image file.
        output_path: Local path where the result image will be saved.

    Returns:
        The *output_path* that was written to.
    """
    url = run_inference_sync(model_name, person_image_path, garment_image_path)
    return download_result(url, output_path)
