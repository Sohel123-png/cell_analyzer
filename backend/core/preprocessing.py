from __future__ import annotations

import cv2
import numpy as np
from skimage.morphology import remove_small_objects


def load_image(image_path: str) -> np.ndarray:
    """
    Load a microscopy image from disk.

    Supports grayscale, RGB/BGR, PNG, JPEG/JFIF,
    and TIFF images supported by OpenCV.
    """

    image = cv2.imread(
        image_path,
        cv2.IMREAD_UNCHANGED,
    )

    if image is None:
        raise FileNotFoundError(
            f"Unable to read image: {image_path}"
        )

    return image


def select_analysis_channel(
    image: np.ndarray,
) -> np.ndarray:
    """
    Select the most informative image channel.

    Grayscale images are returned unchanged.

    For color microscopy images, choose the channel with
    the strongest high-percentile signal.
    """

    if image.ndim == 2:
        return image

    if image.ndim != 3:
        raise ValueError(
            f"Unsupported image shape: {image.shape}"
        )

    channels = cv2.split(image)

    scores = [
        float(np.percentile(channel, 99))
        for channel in channels
    ]

    best_index = int(np.argmax(scores))

    return channels[best_index]


def normalize_intensity(
    image: np.ndarray,
) -> np.ndarray:
    """
    Convert 8/12/16-bit microscopy intensity values to uint8.

    Uses robust percentiles for scaling and preserves the full
    useful dynamic range of high-bit-depth TIFF images.
    """

    image_float = image.astype(np.float32)

    finite_values = image_float[np.isfinite(image_float)]

    if finite_values.size == 0:
        return np.zeros(
            image.shape,
            dtype=np.uint8,
        )

    low = float(
        np.percentile(
            finite_values,
            0.5,
        )
    )

    high = float(
        np.percentile(
            finite_values,
            99.5,
        )
    )

    if high <= low:
        min_value = float(np.min(finite_values))
        max_value = float(np.max(finite_values))

        if max_value <= min_value:
            return np.zeros(
                image.shape,
                dtype=np.uint8,
            )

        low = min_value
        high = max_value

    normalized = (
        (image_float - low)
        / (high - low)
        * 255.0
    )

    normalized = np.clip(
        normalized,
        0,
        255,
    )

    return normalized.astype(
        np.uint8
    )


def denoise(
    image: np.ndarray,
    kernel_size: int = 3,
) -> np.ndarray:
    """
    Reduce high-frequency noise while retaining nuclear boundaries.
    """

    kernel_size = max(
        3,
        int(kernel_size),
    )

    if kernel_size % 2 == 0:
        kernel_size += 1

    return cv2.GaussianBlur(
        image,
        (
            kernel_size,
            kernel_size,
        ),
        0,
    )


def _foreground_threshold(
    image: np.ndarray,
) -> int:
    """
    Compute a conservative adaptive threshold.

    Otsu is still used as a baseline, but for dense fluorescence
    microscopy it can classify too much dim background as foreground.

    We therefore combine Otsu with a high percentile floor.
    """

    otsu_value, _ = cv2.threshold(
        image,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    p70 = float(
        np.percentile(image, 70)
    )

    p85 = float(
        np.percentile(image, 85)
    )

    # Conservative threshold:
    # - never lower than Otsu
    # - for bright/dense images, move toward the upper intensity tail
    adaptive_value = max(
        float(otsu_value),
        p70 * 0.85,
        p85 * 0.55,
    )

    return int(
        np.clip(
            adaptive_value,
            1,
            254,
        )
    )


def threshold_otsu(
    image: np.ndarray,
) -> np.ndarray:
    """
    Generate a foreground mask.

    Despite the legacy function name, the implementation uses
    Otsu as a baseline plus a conservative percentile guard.
    """

    threshold_value = _foreground_threshold(
        image
    )

    _, binary = cv2.threshold(
        image,
        threshold_value,
        255,
        cv2.THRESH_BINARY,
    )

    return binary


def clean_binary_mask(
    binary_image: np.ndarray,
    min_object_size: int | None = None,
) -> np.ndarray:
    """
    Clean the foreground mask.

    Uses scale-aware filtering instead of the old fixed 200-pixel
    threshold, followed by opening/closing to remove speckle and
    repair small gaps.
    """

    binary_mask = np.asarray(
        binary_image > 0,
        dtype=bool,
    )

    if not np.any(binary_mask):
        return np.zeros(
            binary_mask.shape,
            dtype=np.uint8,
        )

    height, width = binary_mask.shape

    if min_object_size is None:
        # Conservative lower bound for small nuclei, with a mild
        # increase for larger images.
        image_area = height * width

        min_object_size = int(
            np.clip(
                image_area * 0.00002,
                20,
                150,
            )
        )

    cleaned_mask = remove_small_objects(
        binary_mask,
        min_size=int(min_object_size),
    )

    cleaned = (
        cleaned_mask.astype(np.uint8)
        * 255
    )

    # Opening suppresses isolated bright specks.
    open_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (3, 3),
    )

    cleaned = cv2.morphologyEx(
        cleaned,
        cv2.MORPH_OPEN,
        open_kernel,
        iterations=1,
    )

    # Closing repairs tiny gaps inside nuclei.
    close_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (3, 3),
    )

    cleaned = cv2.morphologyEx(
        cleaned,
        cv2.MORPH_CLOSE,
        close_kernel,
        iterations=1,
    )

    return cleaned


def preprocess_pipeline(
    image_path: str,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Complete microscopy preprocessing pipeline.

    Pipeline:

        Raw image
            ↓
        Channel selection
            ↓
        Robust 8-bit normalization
            ↓
        Gaussian denoising
            ↓
        Conservative adaptive threshold
            ↓
        Small-object removal
            ↓
        Morphological opening/closing
    """

    image = load_image(
        image_path
    )

    analysis_channel = (
        select_analysis_channel(image)
    )

    gray = normalize_intensity(
        analysis_channel
    )

    blurred = denoise(
        gray,
        kernel_size=3,
    )

    binary = threshold_otsu(
        blurred
    )

    cleaned = clean_binary_mask(
        binary
    )

    return (
        gray,
        blurred,
        binary,
        cleaned,
    )
