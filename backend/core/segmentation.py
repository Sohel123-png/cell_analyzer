from __future__ import annotations

import numpy as np
import numpy.typing as npt

from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.morphology import (
    binary_closing,
    binary_opening,
    disk,
    remove_small_objects,
)


Array = npt.NDArray[np.generic]


def _clean_binary_mask(mask: np.ndarray) -> np.ndarray:
    """Clean a binary foreground mask before watershed."""
    mask = np.asarray(mask > 0, dtype=bool)

    if not np.any(mask):
        return mask

    # Morphological cleanup. The small footprint is deliberately
    # conservative so genuine small nuclei are not erased.
    mask = binary_opening(mask, footprint=disk(1))
    mask = binary_closing(mask, footprint=disk(1))

    # Determine a scale-aware minimum object size.
    #
    # For very dense microscopy images, a fixed min_size=100 can leave
    # many tiny false-positive fragments. We estimate the typical
    # connected-component area and use a conservative fraction of it.
    #
    # First pass: remove only extremely tiny objects.
    height, width = mask.shape
    image_area = float(height * width)

    base_min_size = max(
        25,
        int(round(image_area * 0.00002)),
    )

    mask = remove_small_objects(
        mask,
        min_size=base_min_size,
    )

    if not np.any(mask):
        return mask

    return mask


def _adaptive_peak_parameters(
    distance: np.ndarray,
    cell_mask: np.ndarray,
) -> tuple[int, float]:
    """
    Estimate watershed peak parameters from the foreground scale.

    Returns
    -------
    min_distance:
        Minimum distance between cell-center seeds.
    threshold_abs:
        Minimum distance value accepted as a seed.
    """
    foreground = distance[cell_mask]

    if foreground.size == 0:
        return 10, 0.20

    positive = foreground[foreground > 0]

    if positive.size == 0:
        return 10, 0.20

    # A robust estimate of object radius.
    radius = float(np.percentile(positive, 70))

    # Keep seed spacing in a useful range for microscopy nuclei.
    min_distance = int(
        np.clip(
            round(radius * 0.9),
            6,
            24,
        )
    )

    # Avoid creating seeds from shallow distance-map noise.
    max_distance = float(np.max(distance))

    if max_distance <= 0:
        threshold_ratio = 0.20
    else:
        # Dense images generally benefit from a slightly stronger
        # seed threshold than the old fixed 0.20 setting.
        p80 = float(np.percentile(positive, 80))
        threshold_ratio = float(
            np.clip(
                max(p80 / max_distance, 0.25),
                0.25,
                0.55,
            )
        )

    return min_distance, threshold_ratio


def segment_cells(
    cleaned_binary: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Segment cells/nuclei using distance transform + adaptive watershed.

    Pipeline
    --------
    Binary mask
        ↓
    Morphological cleanup
        ↓
    Small-object filtering
        ↓
    Distance transform
        ↓
    Adaptive center-peak detection
        ↓
    Watershed
        ↓
    Labeled cell regions

    Parameters
    ----------
    cleaned_binary:
        Binary mask. Non-zero pixels represent foreground/cell regions.

    Returns
    -------
    labels:
        Final integer instance-label image. Background = 0.

    distance:
        Euclidean distance transform.

    markers:
        Watershed seed-marker image.
    """

    # ---------------------------------------------------------
    # STEP 1: Normalize input
    # ---------------------------------------------------------

    cell_mask = np.asarray(
        cleaned_binary > 0,
        dtype=bool,
    )

    # ---------------------------------------------------------
    # STEP 2: Morphological cleanup
    # ---------------------------------------------------------

    cell_mask = _clean_binary_mask(
        cell_mask
    )

    # ---------------------------------------------------------
    # STEP 3: Handle empty input
    # ---------------------------------------------------------

    if not np.any(cell_mask):
        empty = np.zeros(
            cell_mask.shape,
            dtype=np.int32,
        )

        distance = np.zeros(
            cell_mask.shape,
            dtype=np.float64,
        )

        return empty, distance, empty.copy()

    # ---------------------------------------------------------
    # STEP 4: Distance transform
    # ---------------------------------------------------------

    distance = np.asarray(
        ndi.distance_transform_edt(cell_mask),
        dtype=np.float64,
    )

    max_distance = float(
        np.max(distance)
    )

    if max_distance <= 0:
        empty = np.zeros(
            cell_mask.shape,
            dtype=np.int32,
        )

        return empty, distance, empty.copy()

    # ---------------------------------------------------------
    # STEP 5: Adaptive watershed seeds
    # ---------------------------------------------------------

    min_distance, threshold_ratio = (
        _adaptive_peak_parameters(
            distance,
            cell_mask,
        )
    )

    threshold_abs = (
        max_distance * threshold_ratio
    )

    coordinates = peak_local_max(
        distance,
        min_distance=min_distance,
        threshold_abs=threshold_abs,
        labels=cell_mask.astype(np.uint8),
        exclude_border=False,
    )

    # ---------------------------------------------------------
    # STEP 6: Fallback marker
    # ---------------------------------------------------------

    if coordinates.size == 0:
        max_position = np.unravel_index(
            np.argmax(distance),
            distance.shape,
        )

        coordinates = np.asarray(
            [max_position],
            dtype=np.intp,
        )

    coordinates = np.asarray(
        coordinates,
        dtype=np.intp,
    )

    # ---------------------------------------------------------
    # STEP 7: Marker image
    # ---------------------------------------------------------

    peak_mask = np.zeros(
        distance.shape,
        dtype=bool,
    )

    peak_mask[
        coordinates[:, 0],
        coordinates[:, 1],
    ] = True

    # ---------------------------------------------------------
    # STEP 8: Label markers
    # ---------------------------------------------------------

    markers, _ = ndi.label(
        peak_mask,
    )

    markers = np.asarray(
        markers,
        dtype=np.int32,
    )

    # ---------------------------------------------------------
    # STEP 9: Watershed
    # ---------------------------------------------------------

    labels = watershed(
        -distance,
        markers,
        mask=cell_mask,
    )

    labels = np.asarray(
        labels,
        dtype=np.int32,
    )

    return (
        labels,
        distance,
        markers,
    )
