from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from backend.routes.analysis import analysis_bp


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"
OUTPUTS_DIR = BASE_DIR / "outputs"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# Allow frontend requests to backend
CORS(app)


# Maximum uploaded image size = 50 MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


# ============================================================
# REGISTER API BLUEPRINT
# ============================================================

app.register_blueprint(analysis_bp)


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def home():
    """
    Serve the main frontend application.
    """

    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        return jsonify({
            "success": False,
            "error": "frontend/index.html not found"
        }), 404

    return send_from_directory(
        str(FRONTEND_DIR),
        "index.html"
    )


@app.route("/<path:path>")
def frontend_files(path):
    """
    Serve frontend static files:

    /style.css
    /app.js
    /images/...
    """

    requested_file = FRONTEND_DIR / path

    if requested_file.exists() and requested_file.is_file():
        return send_from_directory(
            str(FRONTEND_DIR),
            path
        )

    # If frontend route doesn't exist,
    # return index.html.
    index_file = FRONTEND_DIR / "index.html"

    if index_file.exists():
        return send_from_directory(
            str(FRONTEND_DIR),
            "index.html"
        )

    return jsonify({
        "success": False,
        "error": "Frontend file not found"
    }), 404


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():
    """
    Backend health check.
    """

    return jsonify({
        "service": "cell-analyzer",
        "status": "ok"
    })


# ============================================================
# OUTPUT FILES
# ============================================================

@app.route(
    "/api/outputs/<analysis_id>/<filename>",
    methods=["GET"]
)
def get_output_file(analysis_id, filename):
    """
    Serve generated analysis files.

    Examples:

    /api/outputs/84b7b1927fe7/cell_features.csv

    /api/outputs/84b7b1927fe7/segmentation_result.png

    /api/outputs/84b7b1927fe7/pipeline_stages.png

    /api/outputs/84b7b1927fe7/feature_distributions.png
    """

    analysis_dir = OUTPUTS_DIR / analysis_id

    if not analysis_dir.exists():
        return jsonify({
            "success": False,
            "error": "Analysis not found"
        }), 404

    file_path = analysis_dir / filename

    if not file_path.exists() or not file_path.is_file():
        return jsonify({
            "success": False,
            "error": "Output file not found"
        }), 404

    return send_from_directory(
        str(analysis_dir),
        filename
    )


# ============================================================
# LIST ANALYSIS OUTPUTS
# ============================================================

@app.route(
    "/api/outputs/<analysis_id>",
    methods=["GET"]
)
def list_outputs(analysis_id):
    """
    Return all generated files for an analysis.
    """

    analysis_dir = OUTPUTS_DIR / analysis_id

    if not analysis_dir.exists():
        return jsonify({
            "success": False,
            "error": "Analysis not found"
        }), 404

    files = [
        file.name
        for file in analysis_dir.iterdir()
        if file.is_file()
    ]

    return jsonify({
        "success": True,
        "analysis_id": analysis_id,
        "files": files
    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    """
    JSON response for unknown API routes.
    """

    return jsonify({
        "success": False,
        "error": "Requested resource not found"
    }), 404


@app.errorhandler(413)
def file_too_large(error):
    """
    Image upload size exceeded.
    """

    return jsonify({
        "success": False,
        "error": "File too large. Maximum allowed size is 50 MB."
    }), 413


@app.errorhandler(500)
def internal_server_error(error):
    """
    Generic internal server error.
    """

    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print("              CELL ANALYZER")
    print("=" * 65)

    print()
    print("Project:")
    print(BASE_DIR)

    print()
    print("Frontend:")
    print(FRONTEND_DIR)

    print()
    print("Uploads:")
    print(UPLOADS_DIR)

    print()
    print("Outputs:")
    print(OUTPUTS_DIR)

    print()
    print("Frontend URL:")
    print("http://127.0.0.1:5000/")

    print()
    print("Health URL:")
    print("http://127.0.0.1:5000/api/health")

    print()
    print("=" * 65)
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )