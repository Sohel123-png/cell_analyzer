"""
Cell Analyzer - Ground Truth Benchmark

Benchmarks the running Flask API against microscopy images with GT masks.

Supported dataset layouts
--------------------------

1) Project / annotation layout:

    benchmarks/
    ├── sample_001/
    │   ├── images/
    │   │   └── sample_001.png
    │   └── masks/
    │       ├── cell_01.png
    │       ├── cell_02.png
    │       └── ...
    └── sample_002/
        ├── images/
        └── masks/

2) Flat layout:

    images/
        img1.png
        img2.png

    masks/
        img1.png
        img2.png

    In flat layout, each GT mask can be a binary/label mask.

What it reports
---------------

- Ground-truth object count
- Predicted object count
- Absolute count error
- Relative count error (%)
- Pixel Dice
- Pixel IoU
- Pixel Precision
- Pixel Recall
- API status

IMPORTANT
---------
The current Cell Analyzer API returns a rendered segmentation PNG,
not the raw instance-label mask. Therefore pixel metrics below are
computed against a foreground mask inferred from the rendered
segmentation PNG. This is useful for a first benchmark, but it is
NOT equivalent to evaluating the raw instance labels.

For a rigorous scientific benchmark, expose the raw predicted label
mask from the backend and replace infer_prediction_mask() with a
direct label-mask load.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
import pandas as pd
import requests


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".jfif",
    ".tif",
    ".tiff",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark Cell Analyzer against ground-truth masks."
    )

    parser.add_argument(
        "--images",
        required=True,
        help=(
            "Image root folder. Supports a flat folder or folders "
            "containing an images/ subfolder."
        ),
    )

    parser.add_argument(
        "--masks",
        required=True,
        help=(
            "Ground-truth mask root folder. In project layout, masks "
            "can be stored under each sample's masks/ folder."
        ),
    )

    parser.add_argument(
        "--api",
        default="http://127.0.0.1:5000",
        help="Cell Analyzer API base URL.",
    )

    parser.add_argument(
        "--output",
        default="outputs/benchmark_report.csv",
        help="Benchmark CSV output path.",
    )

    parser.add_argument(
        "--min-mask-area",
        type=int,
        default=10,
        help="Ignore GT components/masks smaller than this area.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="API request timeout in seconds.",
    )

    return parser.parse_args()


def iter_images(root: Path) -> Iterable[Path]:
    """
    Find images recursively while avoiding generated output folders.
    """
    ignored = {
        "outputs",
        "__pycache__",
        ".git",
        ".venv",
    }

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        if any(part in ignored for part in path.parts):
            continue

        yield path


def read_gray(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)

    if image is None:
        raise ValueError(f"Could not read image: {path}")

    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return image


def normalise_binary(mask: np.ndarray) -> np.ndarray:
    """
    Convert arbitrary mask values to a boolean foreground mask.
    """
    return mask > 0


def gt_from_mask_file(mask_path: Path) -> tuple[np.ndarray, int]:
    """
    Read one GT mask.

    Returns:
        binary mask
        object count estimated with connected components
    """
    mask = read_gray(mask_path)
    binary = normalise_binary(mask)

    if not binary.any():
        return binary, 0

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary.astype(np.uint8),
        connectivity=8,
    )

    object_count = 0

    for label_id in range(1, num_labels):
        area = int(stats[label_id, cv2.CC_STAT_AREA])

        if area >= 10:
            object_count += 1

    return binary, object_count


def collect_gt(
    image_path: Path,
    image_root: Path,
    mask_root: Path,
    min_mask_area: int,
) -> tuple[np.ndarray, int, str]:
    """
    Locate GT masks for an image.

    Priority:
    1. <same sample>/masks/*.png when the image is inside images/
    2. <mask_root>/<image_stem>.<ext>
    3. <mask_root>/<image_stem>_mask.<ext>
    4. <mask_root>/<image_stem>/*.png/tif
    """
    relative = image_path.relative_to(image_root)

    # Layout: sample/images/image.png -> sample/masks/*.png
    if image_path.parent.name.lower() == "images":
        sample_dir = image_path.parent.parent
        candidate_dir = sample_dir / "masks"

        if candidate_dir.exists():
            mask_files = [
                p
                for p in sorted(candidate_dir.iterdir())
                if p.is_file()
                and p.suffix.lower() in IMAGE_EXTENSIONS
            ]

            if mask_files:
                union = None
                total_objects = 0

                for mask_path in mask_files:
                    mask, count = gt_from_mask_file(mask_path)

                    if mask.sum() < min_mask_area:
                        continue

                    if union is None:
                        union = np.zeros_like(mask, dtype=bool)

                    union |= mask
                    total_objects += count

                if union is not None:
                    return union, total_objects, "sample/masks"

    # Flat / same-stem mask
    stem = image_path.stem

    direct_candidates = [
        mask_root / f"{stem}.png",
        mask_root / f"{stem}.jpg",
        mask_root / f"{stem}.jpeg",
        mask_root / f"{stem}.tif",
        mask_root / f"{stem}.tiff",
        mask_root / f"{stem}_mask.png",
        mask_root / f"{stem}_mask.tif",
    ]

    for candidate in direct_candidates:
        if candidate.exists():
            mask = read_gray(candidate)
            binary = mask > 0

            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
                binary.astype(np.uint8),
                connectivity=8,
            )

            count = 0

            for label_id in range(1, num_labels):
                if stats[label_id, cv2.CC_STAT_AREA] >= min_mask_area:
                    count += 1

            return binary, count, "flat/same-stem"

    # Mask directory named after image
    candidate_dir = mask_root / stem

    if candidate_dir.exists():
        mask_files = [
            p
            for p in sorted(candidate_dir.iterdir())
            if p.is_file()
            and p.suffix.lower() in IMAGE_EXTENSIONS
        ]

        if mask_files:
            union = None
            total_objects = 0

            for mask_path in mask_files:
                mask, count = gt_from_mask_file(mask_path)

                if mask.sum() < min_mask_area:
                    continue

                if union is None:
                    union = np.zeros_like(mask, dtype=bool)

                union |= mask
                total_objects += count

            if union is not None:
                return union, total_objects, "stem-mask-folder"

    raise FileNotFoundError(
        f"No GT mask found for image: {relative}"
    )


def get_output_url(
    api_base: str,
    analysis_id: str,
    returned_path: str,
) -> str:
    """
    Convert:
        <analysis_id>/segmentation_result.png
    into:
        /api/outputs/<analysis_id>/segmentation_result.png
    """
    filename = Path(returned_path.replace("\\", "/")).name

    return (
        f"{api_base.rstrip('/')}/api/outputs/"
        f"{analysis_id}/{filename}"
    )


def infer_prediction_mask(segmentation_png: np.ndarray) -> np.ndarray:
    """
    Infer foreground from the rendered segmentation visualization.

    The app currently renders segmented regions using colors over a
    microscopy background. We therefore use colorfulness (channel
    spread) + brightness rather than assuming grayscale foreground.

    This is intentionally conservative and should be replaced with
    a raw predicted label-mask endpoint for rigorous benchmarking.
    """
    if segmentation_png is None:
        raise ValueError("Segmentation image is empty.")

    if segmentation_png.ndim == 2:
        foreground = segmentation_png > 10
        return foreground

    rgb = cv2.cvtColor(segmentation_png, cv2.COLOR_BGR2RGB)

    max_channel = rgb.max(axis=2).astype(np.int16)
    min_channel = rgb.min(axis=2).astype(np.int16)

    saturation_like = max_channel - min_channel

    # Colored overlays are typically much less grayscale-like.
    color_pixels = saturation_like >= 20

    # Also allow bright near-white segmentation artifacts to be counted
    # only when they are not pure background.
    brightness = rgb.mean(axis=2)

    candidate = color_pixels & (brightness >= 15)

    # Clean isolated rendering noise.
    candidate_u8 = candidate.astype(np.uint8)

    kernel = np.ones((3, 3), np.uint8)

    candidate_u8 = cv2.morphologyEx(
        candidate_u8,
        cv2.MORPH_OPEN,
        kernel,
    )

    candidate_u8 = cv2.morphologyEx(
        candidate_u8,
        cv2.MORPH_CLOSE,
        kernel,
    )

    return candidate_u8.astype(bool)


def resize_mask(
    mask: np.ndarray,
    target_shape: tuple[int, int],
) -> np.ndarray:
    if mask.shape == target_shape:
        return mask

    resized = cv2.resize(
        mask.astype(np.uint8),
        (target_shape[1], target_shape[0]),
        interpolation=cv2.INTER_NEAREST,
    )

    return resized.astype(bool)


def segmentation_metrics(
    gt: np.ndarray,
    pred: np.ndarray,
) -> dict[str, float]:
    gt = gt.astype(bool)
    pred = pred.astype(bool)

    tp = int(np.logical_and(gt, pred).sum())
    fp = int(np.logical_and(~gt, pred).sum())
    fn = int(np.logical_and(gt, ~pred).sum())

    denominator = 2 * tp + fp + fn

    dice = (
        2 * tp / denominator
        if denominator > 0
        else 1.0
    )

    union = tp + fp + fn

    iou = (
        tp / union
        if union > 0
        else 1.0
    )

    precision = (
        tp / (tp + fp)
        if tp + fp > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn > 0
        else 0.0
    )

    return {
        "dice": dice,
        "iou": iou,
        "precision": precision,
        "recall": recall,
    }


def benchmark_one(
    image_path: Path,
    image_root: Path,
    mask_root: Path,
    api_base: str,
    timeout: int,
    min_mask_area: int,
) -> dict:
    start = time.perf_counter()

    row = {
        "image": str(image_path),
        "status": "error",
        "error": "",
    }

    try:
        gt_mask, gt_count, gt_source = collect_gt(
            image_path,
            image_root,
            mask_root,
            min_mask_area,
        )

        image_shape = gt_mask.shape

        with image_path.open("rb") as file_handle:
            response = requests.post(
                f"{api_base.rstrip('/')}/api/analyze",
                files={
                    "image": (
                        image_path.name,
                        file_handle,
                        "application/octet-stream",
                    )
                },
                timeout=timeout,
            )

        row["http_status"] = response.status_code

        if not response.ok:
            raise RuntimeError(
                f"API returned HTTP {response.status_code}: "
                f"{response.text[:300]}"
            )

        payload = response.json()

        if not payload.get("success"):
            raise RuntimeError(
                payload.get("error", "API reported failure")
            )

        result = payload["result"]

        analysis_id = result["analysis_id"]

        predicted_count = int(
            result.get("analysis_summary", result).get(
                "cells_detected",
                0,
            )
        )

        segmentation_path = (
            result.get("files", {}).get(
                "segmentation"
            )
        )

        if not segmentation_path:
            raise RuntimeError(
                "API did not return segmentation output."
            )

        segmentation_url = get_output_url(
            api_base,
            analysis_id,
            segmentation_path,
        )

        segmentation_response = requests.get(
            segmentation_url,
            timeout=timeout,
        )

        if not segmentation_response.ok:
            raise RuntimeError(
                "Could not fetch segmentation output: "
                f"HTTP {segmentation_response.status_code}"
            )

        encoded = np.frombuffer(
            segmentation_response.content,
            dtype=np.uint8,
        )

        segmentation_png = cv2.imdecode(
            encoded,
            cv2.IMREAD_COLOR,
        )

        if segmentation_png is None:
            raise RuntimeError(
                "Could not decode segmentation PNG."
            )

        pred_mask = infer_prediction_mask(
            segmentation_png
        )

        pred_mask = resize_mask(
            pred_mask,
            image_shape,
        )

        metrics = segmentation_metrics(
            gt_mask,
            pred_mask,
        )

        abs_count_error = abs(
            predicted_count - gt_count
        )

        relative_count_error = (
            abs_count_error / gt_count * 100
            if gt_count > 0
            else np.nan
        )

        row.update(
            {
                "status": "ok",
                "analysis_id": analysis_id,
                "gt_count": gt_count,
                "predicted_count": predicted_count,
                "count_error": abs_count_error,
                "count_error_pct": relative_count_error,
                "dice": metrics["dice"],
                "iou": metrics["iou"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "gt_foreground_pct": (
                    gt_mask.mean() * 100
                ),
                "pred_foreground_pct": (
                    pred_mask.mean() * 100
                ),
                "gt_source": gt_source,
                "runtime_sec": (
                    time.perf_counter() - start
                ),
            }
        )

    except Exception as exc:
        row["status"] = "error"
        row["error"] = str(exc)
        row["runtime_sec"] = (
            time.perf_counter() - start
        )

    return row


def main() -> int:
    args = parse_args()

    image_root = Path(args.images).resolve()
    mask_root = Path(args.masks).resolve()
    output_path = Path(args.output).resolve()

    if not image_root.exists():
        print(f"ERROR: images folder not found: {image_root}")
        return 1

    if not mask_root.exists():
        print(f"ERROR: masks folder not found: {mask_root}")
        return 1

    images = list(iter_images(image_root))

    if not images:
        print("ERROR: no supported images found.")
        return 1

    print()
    print("=" * 70)
    print("CELL ANALYZER BENCHMARK")
    print("=" * 70)
    print(f"Images : {image_root}")
    print(f"Masks  : {mask_root}")
    print(f"API    : {args.api}")
    print(f"Found  : {len(images)} image(s)")
    print("=" * 70)
    print()

    # Validate API before spending time on benchmark images.
    try:
        health = requests.get(
            f"{args.api.rstrip('/')}/api/health",
            timeout=10,
        )

        health.raise_for_status()

        print("API health: OK")
        print()

    except Exception as exc:
        print(f"ERROR: API health check failed: {exc}")
        print(
            "Start Flask first with: "
            "python -m backend.app"
        )
        return 1

    results = []

    for index, image_path in enumerate(images, start=1):
        print(
            f"[{index}/{len(images)}] "
            f"{image_path.name}"
        )

        result = benchmark_one(
            image_path=image_path,
            image_root=image_root,
            mask_root=mask_root,
            api_base=args.api,
            timeout=args.timeout,
            min_mask_area=args.min_mask_area,
        )

        results.append(result)

        if result["status"] == "ok":
            print(
                "  "
                f"GT={result['gt_count']}  "
                f"Pred={result['predicted_count']}  "
                f"Dice={result['dice']:.3f}  "
                f"IoU={result['iou']:.3f}  "
                f"Precision={result['precision']:.3f}  "
                f"Recall={result['recall']:.3f}"
            )
        else:
            print(
                "  ERROR:",
                result.get("error", "unknown"),
            )

    df = pd.DataFrame(results)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        output_path,
        index=False,
    )

    successful = df[df["status"] == "ok"].copy()

    print()
    print("=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    if successful.empty:
        print("No successful benchmark runs.")
        print(f"Report: {output_path}")
        return 1

    metric_columns = [
        "dice",
        "iou",
        "precision",
        "recall",
        "count_error",
        "count_error_pct",
        "runtime_sec",
    ]

    available = [
        column
        for column in metric_columns
        if column in successful.columns
    ]

    summary = successful[available].mean(
        numeric_only=True
    )

    print(
        f"Successful images : "
        f"{len(successful)}/{len(df)}"
    )

    if "dice" in summary:
        print(
            f"Mean Dice         : "
            f"{summary['dice']:.3f}"
        )

    if "iou" in summary:
        print(
            f"Mean IoU          : "
            f"{summary['iou']:.3f}"
        )

    if "precision" in summary:
        print(
            f"Mean Precision    : "
            f"{summary['precision']:.3f}"
        )

    if "recall" in summary:
        print(
            f"Mean Recall       : "
            f"{summary['recall']:.3f}"
        )

    if "count_error" in summary:
        print(
            f"Mean Count Error  : "
            f"{summary['count_error']:.2f}"
        )

    if "count_error_pct" in summary:
        print(
            f"Mean Count Error %: "
            f"{summary['count_error_pct']:.2f}%"
        )

    print()
    print(f"Report saved to: {output_path}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
