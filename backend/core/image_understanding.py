from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".jfif",
    ".tif",
    ".tiff",
}


def understand_image(
    image_path: str,
) -> dict:
    """
    Perform basic computer-vision-based image understanding.

    This module does NOT claim a biological diagnosis or identify
    a specific cell line. It describes observable image properties
    and recommends an analysis workflow.

    Parameters
    ----------
    image_path:
        Path to the microscopy image.

    Returns
    -------
    dict
        Image characteristics, observable structures,
        quality information, and recommended analysis.
    """

    path = Path(image_path)

    # ---------------------------------------------------------
    # 1. Validate file
    # ---------------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {path}"
        )

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format: {extension}"
        )

    # ---------------------------------------------------------
    # 2. Read image
    # ---------------------------------------------------------

    image = cv2.imread(
        str(path),
        cv2.IMREAD_UNCHANGED,
    )

    if image is None:
        raise ValueError(
            "Unable to read image."
        )

    # ---------------------------------------------------------
    # 3. Basic image information
    # ---------------------------------------------------------

    height, width = image.shape[:2]

    if image.ndim == 2:

        channels = 1
        image_mode = "Grayscale"

        gray = image

    else:

        channels = image.shape[2]

        image_mode = "Color"

        if channels >= 3:

            gray = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2GRAY,
            )

        else:

            gray = image[:, :, 0]

    # ---------------------------------------------------------
    # 4. Intensity statistics
    # ---------------------------------------------------------

    gray_float = gray.astype(
        np.float32
    )

    min_intensity = float(
        np.min(gray_float)
    )

    max_intensity = float(
        np.max(gray_float)
    )

    mean_intensity = float(
        np.mean(gray_float)
    )

    std_intensity = float(
        np.std(gray_float)
    )

    # ---------------------------------------------------------
    # 5. Contrast estimation
    # ---------------------------------------------------------

    if std_intensity < 20:

        contrast = "Low"

    elif std_intensity < 60:

        contrast = "Moderate"

    else:

        contrast = "High"

    # ---------------------------------------------------------
    # 6. Brightness estimation
    # ---------------------------------------------------------

    if mean_intensity < 60:

        brightness = "Dark"

    elif mean_intensity < 190:

        brightness = "Moderate"

    else:

        brightness = "Bright"

    # ---------------------------------------------------------
    # 7. Foreground detection
    # ---------------------------------------------------------

    # Otsu threshold gives us an approximate foreground mask.
    #
    # This is not biological classification.
    # It only estimates whether bright structures are present.

    _, binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    foreground_pixels = np.count_nonzero(
        binary
    )

    total_pixels = binary.size

    foreground_ratio = (
        foreground_pixels
        / total_pixels
    )

    # ---------------------------------------------------------
    # 8. Estimate whether the image contains
    #    bright object-like structures
    # ---------------------------------------------------------

    object_like_structure = (
        0.005
        <= foreground_ratio
        <= 0.70
    )

    # ---------------------------------------------------------
    # 9. Connected component analysis
    # ---------------------------------------------------------

    # OpenCV connectedComponentsWithStats requires an
    # 8-bit, single-channel mask.
    binary_uint8 = np.asarray(binary)

    if binary_uint8.ndim != 2:
        binary_uint8 = np.squeeze(binary_uint8)

    if binary_uint8.dtype != np.uint8:
        binary_uint8 = (
            binary_uint8 > 0
        ).astype(np.uint8)

    # Normalize foreground to 255.
    binary_uint8 = np.where(
        binary_uint8 > 0,
        255,
        0,
    ).astype(np.uint8)

    num_labels, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(
            binary_uint8,
            connectivity=8,
        )
    )

    object_areas = stats[
        1:,
        cv2.CC_STAT_AREA,
    ]

    # Ignore very small noise components.
    meaningful_objects = object_areas[
        object_areas >= 100
    ]

    estimated_objects = int(
        len(meaningful_objects)
    )

    # ---------------------------------------------------------
    # 10. Determine observable structure
    # ---------------------------------------------------------

    if object_like_structure and estimated_objects > 0:

        observed_structure = (
            "Bright object-like structures"
        )

    elif object_like_structure:

        observed_structure = (
            "Potential foreground structures"
        )

    else:

        observed_structure = (
            "No clear object-like foreground"
        )

    # ---------------------------------------------------------
    # 11. Microscopy-style heuristic
    # ---------------------------------------------------------

    microscopy_score = 0

    if image_mode == "Grayscale":
        microscopy_score += 1

    if contrast in {
        "Moderate",
        "High",
    }:
        microscopy_score += 1

    if object_like_structure:
        microscopy_score += 1

    if estimated_objects >= 2:
        microscopy_score += 1

    if microscopy_score >= 3:

        image_category = (
            "Microscopy-like image"
        )

    elif microscopy_score == 2:

        image_category = (
            "Potential microscopy image"
        )

    else:

        image_category = (
            "General image"
        )

    # ---------------------------------------------------------
    # 12. Fluorescence-like appearance
    # ---------------------------------------------------------

    if (
        image_mode == "Grayscale"
        and brightness in {
            "Dark",
            "Moderate",
        }
        and object_like_structure
        and max_intensity >= 200
    ):

        imaging_style = (
            "Fluorescence-like appearance"
        )

    elif (
        image_mode == "Grayscale"
        and object_like_structure
    ):

        imaging_style = (
            "Grayscale microscopy-like appearance"
        )

    else:

        imaging_style = (
            "Imaging modality not determined"
        )

    # ---------------------------------------------------------
    # 13. Recommended analysis
    # ---------------------------------------------------------

    recommended_analysis = []

    if object_like_structure:

        recommended_analysis.extend(
            [
                "Object segmentation",
                "Morphological measurements",
                "Intensity analysis",
            ]
        )

    if estimated_objects > 1:

        recommended_analysis.append(
            "Object-level quality control"
        )

    if not recommended_analysis:

        recommended_analysis.append(
            "Image quality review"
        )

    # ---------------------------------------------------------
    # 14. Analysis readiness
    # ---------------------------------------------------------

    if (
        object_like_structure
        and estimated_objects > 0
        and max_intensity > min_intensity
    ):

        analysis_ready = True

        readiness_message = (
            "Image contains detectable "
            "foreground structures and is "
            "ready for object-level analysis."
        )

    else:

        analysis_ready = False

        readiness_message = (
            "Image may require manual review "
            "before object-level analysis."
        )

    # ---------------------------------------------------------
    # 15. Return structured information
    # ---------------------------------------------------------

    return {
        "image": {
            "file_name": path.name,
            "format": extension.replace(
                ".",
                ""
            ).upper(),
            "width": int(width),
            "height": int(height),
            "channels": int(channels),
            "mode": image_mode,
        },

        "visual_characteristics": {
            "image_category": image_category,
            "imaging_style": imaging_style,
            "observed_structure": observed_structure,
            "brightness": brightness,
            "contrast": contrast,
        },

        "intensity": {
            "minimum": round(
                min_intensity,
                2,
            ),
            "maximum": round(
                max_intensity,
                2,
            ),
            "mean": round(
                mean_intensity,
                2,
            ),
            "standard_deviation": round(
                std_intensity,
                2,
            ),
        },

        "foreground": {
            "foreground_ratio": round(
                float(foreground_ratio),
                4,
            ),
            "estimated_objects": (
                estimated_objects
            ),
        },

        "analysis": {
            "analysis_ready": analysis_ready,
            "readiness_message": (
                readiness_message
            ),
            "recommended_analysis": (
                recommended_analysis
            ),
        },
    }