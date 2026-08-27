from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from skimage.color import label2rgb

from backend.core.preprocessing import preprocess_pipeline
from backend.core.segmentation import segment_cells
from backend.core.feature_extraction import extract_features
from backend.core.image_understanding import understand_image


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"

DEFAULT_OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# MAIN ANALYSIS FUNCTION
# ============================================================

def analyze_image(
    image_path: str | Path,
    output_dir: str | Path | None = None,
) -> dict:
    """
    Run the complete microscopy image-analysis pipeline.

    Pipeline
    --------
    Image
        ↓
    Image Understanding
        ↓
    Preprocessing
        ↓
    Segmentation
        ↓
    Feature Extraction
        ↓
    Quality Control
        ↓
    Results + Visualizations
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # ========================================================
    # CREATE UNIQUE ANALYSIS DIRECTORY
    # ========================================================

    base_output = (
        Path(output_dir)
        if output_dir is not None
        else DEFAULT_OUTPUT_DIR
    )

    base_output.mkdir(
        parents=True,
        exist_ok=True,
    )

    analysis_id = uuid4().hex[:12]

    analysis_dir = (
        base_output / analysis_id
    )

    analysis_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # STEP 1 — IMAGE UNDERSTANDING
    # ========================================================

    image_understanding = understand_image(
        str(image_path)
    )

    # ========================================================
    # STEP 2 — PREPROCESSING
    # ========================================================

    (
        gray,
        blurred,
        binary,
        cleaned,
    ) = preprocess_pipeline(
        str(image_path)
    )

    # ========================================================
    # STEP 3 — SEGMENTATION
    # ========================================================

    (
        labels,
        distance,
        markers,
    ) = segment_cells(
        cleaned
    )

    cells_detected = int(
        labels.max()
    )

    # ========================================================
    # STEP 4 — FEATURE EXTRACTION
    # ========================================================

    df = extract_features(
        labels,
        intensity_image=gray,
    )

    # ========================================================
    # STEP 5 — ANALYSIS SUMMARY
    # ========================================================

    if df.empty:

        average_area = 0.0
        average_circularity = 0.0
        average_eccentricity = 0.0
        average_intensity = 0.0

        good_cells = 0
        review_cells = 0

    else:

        average_area = float(
            df["area"].mean()
        )

        average_circularity = float(
            df["circularity"].mean()
        )

        average_eccentricity = float(
            df["eccentricity"].mean()
        )

        average_intensity = float(
            df["mean_intensity"].mean()
        )

        good_cells = int(
            (
                df["quality_flag"] == "Good"
            ).sum()
        )

        review_cells = int(
            (
                df["quality_flag"] == "Review"
            ).sum()
        )

    # ========================================================
    # STEP 6 — SAVE CSV
    # ========================================================

    csv_path = (
        analysis_dir
        / "cell_features.csv"
    )

    df.to_csv(
        csv_path,
        index=False,
    )

    # ========================================================
    # COLORED SEGMENTATION
    # ========================================================

    colored_labels = label2rgb(
        labels,
        image=gray,
        bg_label=0,
    )

    # ========================================================
    # STEP 7 — SEGMENTATION VISUALIZATION
    # ========================================================

    segmentation_path = (
        analysis_dir
        / "segmentation_result.png"
    )

    fig, ax = plt.subplots(
        figsize=(10, 10)
    )

    ax.imshow(
        colored_labels
    )

    ax.set_title(
        f"Cell Segmentation ({cells_detected} Cells)"
    )

    ax.axis("off")

    plt.tight_layout()

    plt.savefig(
        segmentation_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    # ========================================================
    # STEP 8 — PIPELINE VISUALIZATION
    # ========================================================

    pipeline_path = (
        analysis_dir
        / "pipeline_stages.png"
    )

    fig, axes = plt.subplots(
        2,
        3,
        figsize=(15, 10),
    )

    axes[0, 0].imshow(
        gray,
        cmap="gray",
    )

    axes[0, 0].set_title(
        "1. Analysis Channel"
    )

    axes[0, 1].imshow(
        blurred,
        cmap="gray",
    )

    axes[0, 1].set_title(
        "2. Denoised"
    )

    axes[0, 2].imshow(
        binary,
        cmap="gray",
    )

    axes[0, 2].set_title(
        "3. Otsu Threshold"
    )

    axes[1, 0].imshow(
        cleaned,
        cmap="gray",
    )

    axes[1, 0].set_title(
        "4. Cleaned Mask"
    )

    axes[1, 1].imshow(
        distance,
        cmap="viridis",
    )

    axes[1, 1].set_title(
        "5. Distance Transform"
    )

    axes[1, 2].imshow(
        colored_labels
    )

    axes[1, 2].set_title(
        f"6. Segmentation ({cells_detected} Cells)"
    )

    for ax in axes.flat:
        ax.axis("off")

    plt.tight_layout()

    plt.savefig(
        pipeline_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    # ========================================================
    # STEP 9 — FEATURE DISTRIBUTIONS
    # ========================================================

    distributions_path = (
        analysis_dir
        / "feature_distributions.png"
    )

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(15, 4),
    )

    if not df.empty:

        axes[0].hist(
            df["area"],
            bins=15,
            edgecolor="black",
        )

        axes[0].set_title(
            "Cell Area Distribution"
        )

        axes[0].set_xlabel(
            "Area (pixels)"
        )

        axes[0].set_ylabel(
            "Number of Cells"
        )

        axes[1].hist(
            df["circularity"],
            bins=15,
            edgecolor="black",
        )

        axes[1].set_title(
            "Circularity Distribution"
        )

        axes[1].set_xlabel(
            "Circularity"
        )

        axes[1].set_ylabel(
            "Number of Cells"
        )

        axes[2].hist(
            df["mean_intensity"],
            bins=15,
            edgecolor="black",
        )

        axes[2].set_title(
            "Mean Intensity Distribution"
        )

        axes[2].set_xlabel(
            "Intensity"
        )

        axes[2].set_ylabel(
            "Number of Cells"
        )

    else:

        for ax in axes:

            ax.text(
                0.5,
                0.5,
                "No cells detected",
                ha="center",
                va="center",
            )

            ax.axis("off")

    plt.tight_layout()

    plt.savefig(
        distributions_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    # ========================================================
    # STEP 10 — FINAL API RESPONSE
    # ========================================================

    return {
        "analysis_id": analysis_id,

        "image_understanding": {
            "image": image_understanding[
                "image"
            ],

            "visual_characteristics": (
                image_understanding[
                    "visual_characteristics"
                ]
            ),

            "intensity": (
                image_understanding[
                    "intensity"
                ]
            ),

            "foreground": (
                image_understanding[
                    "foreground"
                ]
            ),

            "analysis": (
                image_understanding[
                    "analysis"
                ]
            ),
        },

        "analysis_summary": {
            "cells_detected": cells_detected,

            "good_cells": good_cells,

            "review_cells": review_cells,

            "average_area": round(
                average_area,
                2,
            ),

            "average_circularity": round(
                average_circularity,
                3,
            ),

            "average_eccentricity": round(
                average_eccentricity,
                3,
            ),

            "average_intensity": round(
                average_intensity,
                2,
            ),
        },

        "csv_generated": csv_path.exists(),

        "files": {
            "csv": (
                f"{analysis_id}/cell_features.csv"
            ),

            "segmentation": (
                f"{analysis_id}/segmentation_result.png"
            ),

            "pipeline": (
                f"{analysis_id}/pipeline_stages.png"
            ),

            "distributions": (
                f"{analysis_id}/feature_distributions.png"
            ),
        },
    }