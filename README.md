<div align="center">

# 🔬 Cell Analyzer

**An end-to-end Computer Vision platform for microscopy image analysis, cell/nuclei segmentation, quantitative feature extraction, and automated quality control.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-REST%20API-black?logo=flask)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![scikit-image](https://img.shields.io/badge/scikit--image-Segmentation-orange)](https://scikit-image.org/)
[![License](https://img.shields.io/badge/License-Portfolio%2FEducational-lightgrey)](#-license)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)](#-current-status--limitations)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?logo=render&logoColor=white)](https://cell-analyzer.onrender.com)

### 🔗 [**Try the Live Demo →**](https://cell-analyzer.onrender.com)

> ⏳ Hosted on Render's free tier — the app may take 30–50 seconds to wake up on the first request if it's been idle. Subsequent requests are fast.

**If this project helped you or looks interesting, please consider giving it a ⭐ — it genuinely helps!**

[Overview](#-1-project-overview) •
[Architecture](#-4-system-architecture) •
[Pipeline](#-6-computer-vision-pipeline) •
[API](#-10-api-endpoints) •
[Install](#-14-installation) •
[Contributing](#-contributing)

</div>

---

## 📑 Table of Contents

1. [Project Overview](#-1-project-overview)
2. [Problem Statement](#-2-problem-statement)
3. [Project Objectives](#-3-project-objectives)
4. [System Architecture](#-4-system-architecture)
5. [Application Architecture](#-5-application-architecture)
6. [Computer Vision Pipeline](#-6-computer-vision-pipeline)
7. [Project Structure](#-7-project-structure)
8. [Frontend Workflow](#-8-frontend-workflow)
9. [Backend Workflow](#-9-backend-workflow)
10. [API Endpoints](#-10-api-endpoints)
11. [Input / Output](#-11-input--output)
12. [Example Analysis](#-12-example-analysis)
13. [Benchmarking](#-13-benchmarking)
14. [Installation](#-14-installation)
15. [Usage](#-15-usage)
16. [Technologies](#-16-technologies)
17. [Current Status & Limitations](#-17-current-status--limitations)
18. [Future Improvements](#-18-future-improvements)
19. [Contributing](#-contributing)
20. [Author](#-19-author)

---

## 🧬 1. Project Overview

**Cell Analyzer** is a locally-hosted web application that lets a user upload a microscopy image and automatically:

- Understands the image (type, resolution, channels, brightness, contrast)
- Segments individual cells/nuclei using a classical computer-vision pipeline
- Extracts per-object quantitative features (area, circularity, eccentricity, intensity)
- Flags each object with a Quality Control (QC) status
- Visualizes the full pipeline, segmentation mask, and feature distributions
- Exports all per-cell measurements as a downloadable CSV

It is built as a **full-stack computer vision application** — not just a script — with a Flask REST API backend and a browser-based dashboard frontend.

---

## ❓ 2. Problem Statement

Manual analysis of microscopy images (counting cells, measuring shape/size, flagging poor-quality detections) is:

- **Slow** — manual annotation of a single image can take significant time
- **Subjective** — results vary between annotators
- **Not reproducible** — no consistent, auditable pipeline
- **Hard to scale** — doesn't work well across large image batches

Cell Analyzer addresses this by providing a **reproducible, automated, end-to-end pipeline** that goes from raw microscopy image → structured, exportable, per-cell data — accessible through both a UI and a REST API.

---

## 🎯 3. Project Objectives

- Build a complete image-understanding + segmentation + feature-extraction pipeline using classical CV techniques
- Support real-world microscopy formats, including high-bit-depth TIFF (8/12/16-bit)
- Expose the pipeline via a clean REST API so it can be integrated into other systems
- Provide a human-friendly dashboard for upload, visualization, and CSV export
- Include an automated QC layer to flag low-confidence detections for human review
- Provide a benchmarking workflow against public annotated microscopy datasets

---

## 🏗️ 4. System Architecture

```text
                         CELL ANALYZER
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
          Web Application             REST API
                 │                         │
        ┌────────┴────────┐                │
        │ HTML / CSS / JS │                │
        └────────┬────────┘                │
                 │                         ▼
                 │                    Flask Backend
                 │                         │
                 │                         ▼
                 │                 Analysis Service
                 │                         │
                 │         ┌───────────────┼───────────────┐
                 │         ▼               ▼               ▼
                 │   Preprocessing   Segmentation   Feature Extraction
                 │         │               │               │
                 │         └───────────────┼───────────────┘
                 │                         ▼
                 │                  Quality Control
                 │                         │
                 └─────────────────────────┤
                                           ▼
                                  Analysis Results
                                           │
                     ┌─────────────────────┼─────────────────────┐
                     ▼                     ▼                     ▼
                 Cell Count          Cell Features          Visualizations
                 Area                Circularity             Segmentation
                 Intensity           Eccentricity            Pipeline
                 QC Status                                    Distributions
```

---

## 🖥️ 5. Application Architecture

```text
Browser
  ↓
Frontend (HTML/CSS/JS)
  ↓
REST API  (multipart/form-data)
  ↓
Flask Backend
  ↓
Analysis Service
  ├── Preprocessing
  ├── Segmentation
  ├── Feature Extraction
  └── Quality Control
  ↓
Results (JSON + Visualizations + CSV)
```

The frontend never processes images directly — it only uploads and renders results. All computer vision work happens server-side, which keeps the API stateless and reusable by any client (web UI, script, another service).

---

## 🧠 6. Computer Vision Pipeline

```text
                MICROSCOPY IMAGE
                       │
                       ▼
              Image Understanding
                       │
                       ▼
               Channel Selection
                       │
                       ▼
             Intensity Normalization
                       │
                       ▼
                  Denoising
                       │
                       ▼
              Adaptive Threshold
                       │
                       ▼
             Morphological Cleanup
                       │
                       ▼
             Distance Transform
                       │
                       ▼
          Watershed Instance Segmentation
                       │
                       ▼
             Object Feature Extraction
                       │
                       ▼
                  QC Analysis
                       │
              ┌────────┴────────┐
              ▼                 ▼
          Good Cells         Review Cells
              │                 │
              └────────┬────────┘
                       ▼
                Results Dashboard
```

### Pipeline stage summary

| Stage | What happens |
|---|---|
| **Image Understanding** | Detects format, bit-depth, channels, brightness/contrast, and whether the image looks "microscopy-like" and analysis-ready |
| **Channel Selection** | Picks the most informative channel for grayscale/multi-channel images |
| **Intensity Normalization** | Rescales 8/12/16-bit intensity ranges into a consistent working range |
| **Denoising** | Gaussian smoothing to suppress sensor/acquisition noise |
| **Adaptive Thresholding** | Separates foreground (cells) from background using Otsu/adaptive methods |
| **Morphological Cleanup** | Removes small artifacts, fills holes, smooths object boundaries |
| **Distance Transform** | Computes distance-to-background map, used to separate touching cells |
| **Watershed Segmentation** | Splits touching/clustered cells into individual instances |
| **Feature Extraction** | Computes per-object area, perimeter, circularity, eccentricity, mean intensity |
| **Quality Control** | Classifies each detected object as `Good` or `Review` based on shape/size heuristics |

---

## 📁 7. Project Structure

```text
cell_analyzer/
│
├── backend/
│   ├── app.py                       # Flask app entrypoint (serves API + frontend)
│   ├── routes/
│   │   └── analysis.py              # /api/analyze, /api/health routes
│   ├── services/
│   │   └── analysis_service.py      # Orchestrates the full analysis pipeline
│   └── core/
│       ├── preprocessing.py         # Normalization, denoising, thresholding
│       ├── segmentation.py          # Distance transform + watershed
│       ├── feature_extraction.py    # Morphological / intensity features
│       └── image_understanding.py   # Image characteristics & readiness checks
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js                       # Upload, API calls, result rendering
│
├── data/
│   └── uploads/                     # Uploaded images (runtime)
│
├── outputs/                         # Generated visualizations & CSVs
│
├── benchmark.py
├── benchmark_bbbc039_fixed.py       # Benchmark against BBBC039 dataset
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

### Module responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Flask application setup + serves frontend and API |
| `routes/analysis.py` | Defines the analysis API endpoints |
| `services/analysis_service.py` | End-to-end orchestration of the analysis pipeline |
| `core/preprocessing.py` | Loading, normalization, denoising, thresholding |
| `core/segmentation.py` | Distance transform + watershed instance segmentation |
| `core/feature_extraction.py` | Morphological and intensity feature computation |
| `core/image_understanding.py` | Basic image characteristics and analysis-readiness |
| `frontend/app.js` | Upload handling, API calls, dashboard rendering |

---

## 🌐 8. Frontend Workflow

```text
┌──────────────────────────────────────────────────────────────┐
│                     CELL ANALYZER UI                          │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│   Upload Image                                                │
│        │                                                      │
│        ▼                                                      │
│   Image Preview                                                │
│        │                                                      │
│        ▼                                                      │
│   Analyze Image                                                │
│        │                                                      │
│        ▼                                                      │
│   Image Understanding                                          │
│        │                                                      │
│        ▼                                                      │
│   Analysis Summary                                             │
│        │                                                      │
│        ├───────────────┬───────────────────┐                  │
│        ▼               ▼                   ▼                  │
│   Segmentation      Pipeline          Distributions            │
│        │               │                   │                  │
│        └───────────────┴───────────────────┘                  │
│                        │                                       │
│                        ▼                                       │
│                  Cell Features                                 │
│                        │                                       │
│                        ▼                                       │
│                    CSV Export                                  │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

### UI Preview (mockup)

```text
┌──────────────────────────────────────────────────────────────┐
│ 🔬 CELL ANALYZER                              System Ready    │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  MICROSCOPY ANALYSIS                                          │
│  Upload Microscopy Image                                      │
│                                                                │
│       ┌───────────────────────────────────────┐               │
│       │                                       │               │
│       │       Drop your image here            │               │
│       │       or click to browse              │               │
│       │                                       │               │
│       │       PNG · JPG · TIFF · JFIF         │               │
│       └───────────────────────────────────────┘               │
│                                                                │
│                 [ Analyze Image → ]                            │
│                                                                │
├──────────────────────────────────────────────────────────────┤
│ IMAGE UNDERSTANDING                                            │
│                                                                │
│ Image Type        Microscopy-like image                       │
│ Resolution         1024 × 1024                                │
│ Channels           3                                           │
│ Brightness         Dark                                        │
│ Contrast           Moderate                                    │
│                                                                │
├──────────────────────────────────────────────────────────────┤
│ ANALYSIS SUMMARY                                               │
│                                                                │
│     17              14              3               82%       │
│   CELLS          GOOD           REVIEW          QC PASS        │
│                                                                │
│ Avg Area       Circularity      Eccentricity     Intensity    │
│ 22,167 px²         0.658            0.635          204.66      │
│                                                                │
├──────────────────────────────────────────────────────────────┤
│ VISUAL ANALYSIS                                                │
│                                                                │
│ Original Image              Segmentation Result                │
│                                                                │
│      [ IMAGE ]                    [ MASK ]                     │
│                                                                │
├──────────────────────────────────────────────────────────────┤
│ CELL FEATURES                                                  │
│                                                                │
│ ID │ Area │ Circularity │ Eccentricity │ Intensity │ QC        │
│ 1  │ ...  │ ...         │ ...          │ ...       │ Good      │
│ 2  │ ...  │ ...         │ ...          │ ...       │ Review    │
│                                                                │
│                    [ Download CSV ]                            │
└──────────────────────────────────────────────────────────────┘
```

> 💡 **Tip:** Replace the ASCII mockup above with an actual screenshot/GIF of your running app (`docs/screenshot.png`) — repos with real screenshots get noticeably more stars and engagement.

---

## ⚙️ 9. Backend Workflow

```text
USER
 │
 │ Upload microscopy image
 ▼
FRONTEND
 │
 │ multipart/form-data
 ▼
POST /api/analyze
 │
 ▼
FLASK ROUTE
 │
 ▼
ANALYSIS SERVICE
 │
 ├── Image Understanding
 ├── Preprocessing
 ├── Segmentation
 ├── Feature Extraction
 └── QC
 │
 ▼
RESULT OBJECT
 │
 ├── Summary Metrics
 ├── Visualization Paths
 ├── Image Understanding
 └── Analysis ID
 │
 ▼
FRONTEND
 │
 ├── Dashboard
 ├── Segmentation
 ├── Pipeline
 ├── Feature Table
 └── CSV Download
```

---

## 🔌 10. API Endpoints

### Health Check

```http
GET /api/health
```

**Response**

```json
{
  "service": "cell-analyzer",
  "status": "ok"
}
```

### Analyze an Image

```http
POST /api/analyze
Content-Type: multipart/form-data
```

**Form field**

| Field | Type | Description |
|---|---|---|
| `image` | file | Microscopy image (PNG, JPG/JPEG, JFIF, or TIFF) |

**Example (Python)**

```python
import requests

with open("example.tif", "rb") as image_file:
    response = requests.post(
        "http://127.0.0.1:5000/api/analyze",
        files={"image": image_file},
        timeout=120,
    )

print(response.status_code)
print(response.json())
```

The response includes an analysis ID, summary metrics, image-understanding details, and generated output filenames (visualizations + CSV).

---

## 📥 11. Input / Output

**Input**
- Formats: PNG, JPG/JPEG, JFIF, TIFF
- Bit depth: 8-bit, 12-bit, 16-bit
- Color: grayscale or multi-channel

**Output**
- Segmentation mask (visual overlay)
- Full pipeline stage visualization
- Feature distribution plots
- Per-cell CSV report:

| id | area | perimeter | circularity | eccentricity | mean_intensity | qc_status |
|---|---|---|---|---|---|---|
| 1 | 21,340 | 542.1 | 0.71 | 0.58 | 198.2 | Good |
| 2 | 8,102 | 320.4 | 0.41 | 0.89 | 231.7 | Review |

---

## 🧪 12. Example Analysis

```text
Input:  microscopy_sample.tif  (1024 × 1024, 3 channels)

Detected Cells:        17
Good Cells:             14
Review Cells:            3
QC Pass Rate:           82%

Avg. Area:          22,167 px²
Avg. Circularity:      0.658
Avg. Eccentricity:     0.635
Avg. Intensity:        204.66
```

> 💡 Add real before/after images here (`original.png` vs `segmentation.png`) once you have sample outputs — visual proof of results is one of the biggest drivers of GitHub stars.

---

## 📊 13. Benchmarking

The repository includes a benchmark workflow to evaluate segmentation quality against public, annotated microscopy datasets (e.g. **BBBC039**).

```bash
python benchmark_bbbc039_fixed.py `
  --images "benchmarks\manual_tests\images_raw\images" `
  --masks "benchmarks\manual_tests\masks_raw\masks" `
  --output outputs\bbbc039_test.csv
```

> ⚠️ **Note on current benchmark results:** Benchmarking is an active development area. The current workflow reports object-count and pixel-level metrics, but the prediction side is derived from the *rendered segmentation visualization* rather than a dedicated raw instance-label endpoint. Treat current numbers as **preliminary engineering metrics**, not validated biological accuracy. See [Limitations](#-17-current-status--limitations) for details.

### Dataset

Benchmark datasets are **intentionally not committed** to this repository. Download the relevant public dataset separately and place image/annotation files in the local benchmark directories. Large datasets and generated outputs should stay out of Git history (see `.gitignore`).

---

## 🚀 14. Installation

### 1. Clone the repository

```bash
git clone https://github.com/Sohel123-png/cell_analyzer.git
cd cell_analyzer
```

### 2. Create a virtual environment

Using standard Python:

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or using `uv`:

```bash
uv venv
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the application

```bash
python -m backend.app
```

Open your browser at:

```
http://127.0.0.1:5000/
```

### 5. Verify the API

```bash
python -c "import requests; r=requests.get('http://127.0.0.1:5000/api/health'); print(r.status_code); print(r.json())"
```

Expected output:

```json
{
  "service": "cell-analyzer",
  "status": "ok"
}
```

---

## ▶️ 15. Usage

You can either try it instantly on the **[live demo](https://cell-analyzer.onrender.com)**, or run it locally:

1. Open `http://127.0.0.1:5000/` (local) or the [live demo URL](https://cell-analyzer.onrender.com) in your browser
2. Drag & drop (or browse) a microscopy image — PNG, JPG, TIFF, or JFIF
3. Click **Analyze Image**
4. Review:
   - Image Understanding summary
   - Analysis Summary (counts, QC pass rate, averages)
   - Segmentation & pipeline visualizations
   - Feature distribution plots
   - Per-cell feature table
5. Download results as CSV

---

## 🛠️ 16. Technologies

**Backend**
- Python
- Flask
- OpenCV
- NumPy
- SciPy
- scikit-image
- Pandas

**Frontend**
- HTML5
- CSS3
- Vanilla JavaScript

**Computer Vision**
- Otsu / adaptive thresholding
- Morphological image processing
- Euclidean distance transform
- Watershed segmentation
- Connected-component analysis

---

## ⚠️ 17. Current Status & Limitations

This project is in **active development** and should be treated as an engineering/portfolio project, not a clinical or production-validated tool.

- Segmentation quality depends heavily on image modality, staining, illumination, object density, and overall image quality
- The current pipeline uses **classical computer vision**, not a trained deep-learning segmentation model
- Image-understanding labels (e.g. "microscopy-like", brightness/contrast descriptors) are **heuristic**, not biological diagnosis
- Objects flagged `Review` should always be inspected by a human
- Benchmark metrics (BBBC039, etc.) are **preliminary engineering metrics** — the prediction side is currently derived from rendered segmentation output rather than a dedicated raw instance-label endpoint, so results should not be interpreted as validated accuracy
- Not intended for clinical, diagnostic, or production biological research use

---

## 🔮 18. Future Improvements

- [ ] Raw instance-mask output directly from the backend (for rigorous benchmarking)
- [ ] More rigorous instance-level matching metrics (IoU-based matching, precision/recall)
- [ ] Better modality-aware preprocessing (brightfield vs fluorescence vs phase-contrast)
- [ ] Automated parameter selection based on detected image characteristics
- [ ] Deep-learning segmentation models (U-Net / Cellpose-style approaches)
- [ ] Confidence scoring and uncertainty visualization
- [ ] Batch-processing support for multiple images
- [ ] Docker deployment
- [ ] Automated benchmark reports and experiment tracking

---

## 🌟 Why This Project

Cell Analyzer was built to demonstrate a **complete, end-to-end computer vision system** — not a single isolated image-processing script.

```text
Image Understanding
        +
   Preprocessing
        +
   Segmentation
        +
Feature Engineering
        +
 Quality Control
        +
   REST API
        +
    Web UI
        +
  Benchmarking
        =
 A full CV product
```

**Engineering highlights:**

- Built an end-to-end microscopy image analysis platform
- Implemented a classical computer-vision segmentation pipeline (thresholding → morphology → distance transform → watershed)
- Added support for high-bit-depth TIFF microscopy images (8/12/16-bit)
- Designed a Flask REST API for image analysis
- Built a browser-based analysis dashboard using vanilla JavaScript
- Added per-object morphological and intensity measurements
- Added automated QC classification and downloadable CSV reports
- Added a benchmark workflow using annotated public microscopy datasets

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. **Fork** the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a **Pull Request**

Good first areas to contribute:
- Deep-learning segmentation backend (U-Net / Cellpose integration)
- Docker packaging
- Improved benchmark metrics (instance-level IoU matching)
- Batch upload support
- UI/UX improvements to the dashboard

If you find this project useful, please ⭐ **star the repo** — it helps others discover it and motivates continued development.

---

## 👤 19. Author

**Sohel Ali**
GitHub: [@Sohel123-png](https://github.com/Sohel123-png)

---

## 📄 License

This project is currently provided for **educational and portfolio use**. Add a formal open-source license (e.g. MIT, Apache-2.0) before distributing it as a reusable package.

</div>
