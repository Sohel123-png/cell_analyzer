from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    jsonify,
    request,
    send_from_directory,
)
from werkzeug.utils import secure_filename

from backend.services.analysis_service import analyze_image


# ============================================================
# BLUEPRINT
# ============================================================

analysis_bp = Blueprint(
    "analysis",
    __name__,
    url_prefix="/api",
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parents[2]

UPLOAD_DIR = (
    BASE_DIR
    / "data"
    / "uploads"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# CONFIGURATION
# ============================================================

ALLOWED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".jfif",
    ".tif",
    ".tiff",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_allowed_file(
    filename: str,
) -> bool:
    """
    Check whether the uploaded file has
    a supported microscopy-image extension.
    """

    extension = Path(
        filename
    ).suffix.lower()

    return extension in ALLOWED_EXTENSIONS


def create_unique_filename(
    filename: str,
) -> str:
    """
    Create a safe unique filename.

    Example:
        image.jfif
        ->
        8f42c1a7_image.jfif
    """

    safe_filename = secure_filename(
        filename
    )

    extension = Path(
        safe_filename
    ).suffix.lower()

    unique_id = uuid4().hex[:8]

    return (
        f"{unique_id}_image{extension}"
    )


# ============================================================
# IMAGE ANALYSIS ENDPOINT
# ============================================================

@analysis_bp.route(
    "/analyze",
    methods=["POST"],
)
def analyze():
    """
    Upload a microscopy image and run
    the complete cell-analysis pipeline.

    Endpoint
    --------
    POST /api/analyze

    Form field
    ----------
    image:
        Microscopy image file.
    """

    # --------------------------------------------------------
    # 1. Check request contains an image
    # --------------------------------------------------------

    if "image" not in request.files:

        return jsonify({
            "success": False,
            "error": (
                "No image file provided. "
                "Use form field 'image'."
            ),
        }), 400

    uploaded_file = (
        request.files["image"]
    )

    # --------------------------------------------------------
    # 2. Validate filename
    # --------------------------------------------------------

    filename = (
        uploaded_file.filename
    )

    if not filename:

        return jsonify({
            "success": False,
            "error": (
                "No image selected."
            ),
        }), 400

    # --------------------------------------------------------
    # 3. Validate extension
    # --------------------------------------------------------

    if not is_allowed_file(
        filename
    ):

        return jsonify({
            "success": False,
            "error": (
                "Unsupported image format. "
                "Supported formats: PNG, JPG, "
                "JPEG, JFIF, TIF and TIFF."
            ),
        }), 400

    # --------------------------------------------------------
    # 4. Validate content length
    # --------------------------------------------------------

    content_length = request.content_length

    if (
        content_length is not None
        and content_length > MAX_FILE_SIZE
    ):

        return jsonify({
            "success": False,
            "error": (
                "File is too large. "
                "Maximum allowed size is 50 MB."
            ),
        }), 413

    # --------------------------------------------------------
    # 5. Generate unique filename
    # --------------------------------------------------------

    generated_filename = (
        create_unique_filename(
            filename
        )
    )

    image_path = (
        UPLOAD_DIR
        / generated_filename
    )

    # --------------------------------------------------------
    # 6. Save image
    # --------------------------------------------------------

    try:

        uploaded_file.save(
            str(image_path)
        )

    except OSError as exc:

        return jsonify({
            "success": False,
            "error": (
                f"Unable to save uploaded image: {exc}"
            ),
        }), 500

    # --------------------------------------------------------
    # 7. Run analysis
    # --------------------------------------------------------

    try:

        result = analyze_image(
            image_path=str(
                image_path
            ),
            output_dir=str(
                OUTPUT_DIR
            ),
        )

    except FileNotFoundError as exc:

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 400

    except ValueError as exc:

        return jsonify({
            "success": False,
            "error": str(exc),
        }), 400

    except Exception as exc:

        return jsonify({
            "success": False,
            "error": (
                "Image analysis failed."
            ),
            "details": str(exc),
        }), 500

    # --------------------------------------------------------
    # 8. Return result
    # --------------------------------------------------------

    return jsonify({
        "success": True,
        "message": (
            "Image analyzed successfully."
        ),
        "result": result,
    }), 200


# ============================================================
# OUTPUT FILE ENDPOINT
# ============================================================

@analysis_bp.route(
    "/outputs/<path:filename>",
    methods=["GET"],
)
def get_output(
    filename: str,
):
    """
    Serve generated analysis files.

    Example:

        /api/outputs/
        <analysis_id>/segmentation_result.png
    """

    return send_from_directory(
        OUTPUT_DIR,
        filename,
    )