from __future__ import annotations

import numpy as np
import pandas as pd
from skimage.measure import regionprops_table


def extract_features(
    labels: np.ndarray,
    intensity_image: np.ndarray,
) -> pd.DataFrame:
    """
    Extract quantitative features for every segmented cell/nucleus.

    Parameters
    ----------
    labels:
        Labeled segmentation image.
        Background must be represented by 0.

    intensity_image:
        Original grayscale microscopy image.

    Returns
    -------
    pd.DataFrame
        One row per detected cell/nucleus containing morphological,
        positional, intensity, and quality-control features.
    """

    # ---------------------------------------------------------
    # Validate inputs
    # ---------------------------------------------------------

    if labels.ndim != 2:
        raise ValueError(
            "labels must be a 2D array."
        )

    if intensity_image.ndim != 2:
        raise ValueError(
            "intensity_image must be a 2D grayscale image."
        )

    if labels.shape != intensity_image.shape:
        raise ValueError(
            "labels and intensity_image must have "
            "the same dimensions."
        )

    # ---------------------------------------------------------
    # Region properties
    # ---------------------------------------------------------

    properties = (
        "label",
        "area",
        "perimeter",
        "eccentricity",
        "mean_intensity",
        "centroid",
        "bbox",
        "solidity",
        "extent",
    )

    table = regionprops_table(
        labels,
        intensity_image=intensity_image,
        properties=properties,
    )

    df = pd.DataFrame(table)

    # ---------------------------------------------------------
    # Handle empty segmentation
    # ---------------------------------------------------------

    if df.empty:
        return pd.DataFrame(
            columns=[
                "cell_id",
                "area",
                "perimeter",
                "circularity",
                "eccentricity",
                "mean_intensity",
                "centroid_y",
                "centroid_x",
                "bbox_min_y",
                "bbox_min_x",
                "bbox_max_y",
                "bbox_max_x",
                "width",
                "height",
                "aspect_ratio",
                "solidity",
                "extent",
                "quality_flag",
            ]
        )

    # ---------------------------------------------------------
    # Rename columns
    # ---------------------------------------------------------

    df = df.rename(
        columns={
            "label": "cell_id",
            "centroid-0": "centroid_y",
            "centroid-1": "centroid_x",
            "bbox-0": "bbox_min_y",
            "bbox-1": "bbox_min_x",
            "bbox-2": "bbox_max_y",
            "bbox-3": "bbox_max_x",
        }
    )

    # ---------------------------------------------------------
    # Bounding-box dimensions
    # ---------------------------------------------------------

    df["width"] = (
        df["bbox_max_x"]
        - df["bbox_min_x"]
    )

    df["height"] = (
        df["bbox_max_y"]
        - df["bbox_min_y"]
    )

    # ---------------------------------------------------------
    # Aspect ratio
    # ---------------------------------------------------------

    df["aspect_ratio"] = np.where(
        df["height"] > 0,
        df["width"] / df["height"],
        0.0,
    )

    # ---------------------------------------------------------
    # Circularity
    # ---------------------------------------------------------

    # Circularity:
    #
    #        4 * pi * Area
    #   ---------------------
    #        Perimeter²
    #
    # A perfect circle approaches 1.0.

    df["circularity"] = (
        4.0
        * np.pi
        * df["area"]
        / (
            df["perimeter"] ** 2
            + 1e-6
        )
    )

    # ---------------------------------------------------------
    # Quality-control rules
    # ---------------------------------------------------------

    # These are NOT biological diagnoses.
    #
    # They simply identify geometrically unusual regions
    # that may deserve manual review.

    quality_conditions = (
        (df["area"] < 500)
        | (df["circularity"] < 0.50)
        | (df["solidity"] < 0.80)
        | (df["aspect_ratio"] > 2.50)
        | (df["aspect_ratio"] < 0.40)
    )

    df["quality_flag"] = np.where(
        quality_conditions,
        "Review",
        "Good",
    )

    # ---------------------------------------------------------
    # Numerical cleanup
    # ---------------------------------------------------------

    numeric_columns = [
        "area",
        "perimeter",
        "circularity",
        "eccentricity",
        "mean_intensity",
        "centroid_y",
        "centroid_x",
        "width",
        "height",
        "aspect_ratio",
        "solidity",
        "extent",
    ]

    df[numeric_columns] = df[
        numeric_columns
    ].round(3)

    # ---------------------------------------------------------
    # Sort by cell ID
    # ---------------------------------------------------------

    df = df.sort_values(
        by="cell_id"
    ).reset_index(drop=True)

    return df