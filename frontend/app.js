"use strict";

/* ============================================================
   CELL ANALYZER — FRONTEND
============================================================ */

const API_BASE = window.location.origin;


/* ============================================================
   STATE
============================================================ */

const state = {

    selectedFile: null,

    currentResult: null,

    analysisId: null,

    featureRows: [],

    filteredRows: [],

    currentPage: 1,

    pageSize: 10,

    sortColumn: null,

    sortDirection: "asc",

    busy: false,

    lightboxItems: [],

    lightboxIndex: 0
};


/* ============================================================
   DOM HELPERS
============================================================ */

function $(id) {
    return document.getElementById(id);
}


function setText(id, value) {

    const element = $(id);

    if (!element) {
        return;
    }

    element.textContent =
        value === undefined ||
        value === null ||
        value === ""
            ? "-"
            : value;
}


function formatNumber(
    value,
    decimals = 2
) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "-";
    }

    const number =
        Number(value);

    if (
        Number.isNaN(number)
    ) {
        return "-";
    }

    return number.toLocaleString(
        "en-US",
        {
            minimumFractionDigits:
                decimals,

            maximumFractionDigits:
                decimals
        }
    );
}


function formatInteger(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "-";
    }

    const number =
        Number(value);

    if (
        Number.isNaN(number)
    ) {
        return "-";
    }

    return number.toLocaleString(
        "en-US"
    );
}


function formatPercent(
    value,
    decimals = 0
) {

    if (
        value === undefined ||
        value === null ||
        Number.isNaN(
            Number(value)
        )
    ) {
        return "-";
    }

    return `${Number(value).toFixed(decimals)}%`;
}


function formatBytes(bytes) {

    if (
        !bytes ||
        bytes <= 0
    ) {
        return "0 B";
    }

    const units = [
        "B",
        "KB",
        "MB",
        "GB"
    ];

    const index =
        Math.min(
            Math.floor(
                Math.log(bytes) /
                Math.log(1024)
            ),
            units.length - 1
        );

    return (
        (
            bytes /
            Math.pow(
                1024,
                index
            )
        ).toFixed(
            index === 0
                ? 0
                : 2
        )
        +
        " "
        +
        units[index]
    );
}


function escapeHTML(value) {

    return String(
        value ?? ""
    )
    .replace(
        /&/g,
        "&amp;"
    )
    .replace(
        /</g,
        "&lt;"
    )
    .replace(
        />/g,
        "&gt;"
    )
    .replace(
        /"/g,
        "&quot;"
    )
    .replace(
        /'/g,
        "&#039;"
    );
}


function debounce(
    fn,
    wait = 200
) {

    let timer = null;

    return (...args) => {

        clearTimeout(timer);

        timer = setTimeout(
            () => fn(...args),
            wait
        );
    };
}


/* ============================================================
   INITIALIZATION
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeUpload();

        initializeAnalysis();

        initializeNavigation();

        initializeLightbox();

        initializeFeatureControls();

        checkBackend();

        console.log(
            "✓ Cell Analyzer frontend ready"
        );
    }
);


/* ============================================================
   BACKEND HEALTH
============================================================ */

async function checkBackend() {

    try {

        const response =
            await fetch(
                `${API_BASE}/api/health`,
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Backend unavailable"
            );
        }


        const data =
            await response.json();


        console.log(
            "Backend:",
            data
        );


        updateBackendStatus(
            true
        );


    } catch (error) {

        console.error(
            "Backend health error:",
            error
        );


        updateBackendStatus(
            false
        );
    }
}


function updateBackendStatus(
    online
) {

    const dot =
        $("engineDot");

    const topDot =
        $("topStatusDot");


    if (online) {

        if (dot) {
            dot.classList.remove(
                "offline"
            );
        }

        if (topDot) {
            topDot.classList.remove(
                "offline"
            );
        }

        setText(
            "engineStatus",
            "Backend connected"
        );

        setText(
            "topStatusText",
            "System Ready"
        );

    } else {

        if (dot) {
            dot.classList.add(
                "offline"
            );
        }

        if (topDot) {
            topDot.classList.add(
                "offline"
            );
        }

        setText(
            "engineStatus",
            "Backend offline"
        );

        setText(
            "topStatusText",
            "Backend Offline"
        );
    }
}


/* ============================================================
   UPLOAD
============================================================ */

function initializeUpload() {

    const dropZone =
        $("dropZone");

    const input =
        $("imageInput");


    if (!dropZone || !input) {

        console.error(
            "Upload elements missing."
        );

        return;
    }


    dropZone.addEventListener(
        "click",
        () => {

            input.click();
        }
    );


    dropZone.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter" ||
                event.key === " "
            ) {

                event.preventDefault();

                input.click();
            }
        }
    );


    input.addEventListener(
        "change",
        event => {

            const file =
                event.target.files?.[0];

            if (file) {
                handleFile(
                    file
                );
            }
        }
    );


    dropZone.addEventListener(
        "dragover",
        event => {

            event.preventDefault();

            dropZone.classList.add(
                "dragover"
            );
        }
    );


    dropZone.addEventListener(
        "dragleave",
        () => {

            dropZone.classList.remove(
                "dragover"
            );
        }
    );


    dropZone.addEventListener(
        "drop",
        event => {

            event.preventDefault();

            dropZone.classList.remove(
                "dragover"
            );


            const file =
                event
                    .dataTransfer
                    .files?.[0];


            if (file) {

                handleFile(
                    file
                );
            }
        }
    );
}


/* ============================================================
   FILE
============================================================ */

function handleFile(file) {

    const allowed =
        [
            "png",
            "jpg",
            "jpeg",
            "jfif",
            "tif",
            "tiff"
        ];


    const extension =
        file.name
            .split(".")
            .pop()
            .toLowerCase();


    if (
        !allowed.includes(
            extension
        )
    ) {

        showMessage(
            "Unsupported image format. Use PNG, JPG, JPEG, JFIF, TIF or TIFF.",
            "error"
        );

        return;
    }


    const maxSize =
        50 *
        1024 *
        1024;


    if (
        file.size >
        maxSize
    ) {

        showMessage(
            "Image is too large. Maximum size is 50 MB.",
            "error"
        );

        return;
    }


    state.selectedFile =
        file;


    resetResults();


    showSelectedFile(
        file
    );


    enableAnalyze(
        true
    );


    clearMessage();


    console.log(
        "Selected file:",
        file.name
    );
}


/* ============================================================
   SELECTED FILE
============================================================ */

function showSelectedFile(
    file
) {

    const box =
        $("selectedFile");

    const preview =
        $("uploadPreview");

    const thumb =
        $("fileThumb");


    setText(
        "fileName",
        file.name
    );


    setText(
        "fileSize",
        formatBytes(
            file.size
        )
    );


    if (box) {

        box.classList.remove(
            "hidden"
        );
    }


    if (thumb) {

        thumb.textContent =
            "IMG";


        const url =
            URL.createObjectURL(
                file
            );


        thumb.style.backgroundImage =
            `url("${url}")`;

        thumb.style.backgroundSize =
            "cover";

        thumb.style.backgroundPosition =
            "center";

        thumb.textContent =
            "";
    }


    showPreview(
        file,
        preview
    );
}


/* ============================================================
   IMAGE PREVIEW
============================================================ */

function showPreview(
    file,
    container
) {

    const image =
        $("previewImage");


    if (
        !image ||
        !container
    ) {
        return;
    }


    const url =
        URL.createObjectURL(
            file
        );


    image.src =
        url;


    image.onload =
        () => {

            setText(
                "previewDimensions",
                `${image.naturalWidth} × ${image.naturalHeight}px`
            );

            URL.revokeObjectURL(
                url
            );
        };


    container.classList.remove(
        "hidden"
    );
}


/* ============================================================
   REMOVE FILE
============================================================ */

function setupRemoveButton() {

    const button =
        $("removeFile");


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        event => {

            event.stopPropagation();

            state.selectedFile =
                null;


            const input =
                $("imageInput");


            if (input) {
                input.value =
                    "";
            }


            const fileBox =
                $("selectedFile");


            const preview =
                $("uploadPreview");


            if (fileBox) {
                fileBox.classList.add(
                    "hidden"
                );
            }


            if (preview) {
                preview.classList.add(
                    "hidden"
                );
            }


            enableAnalyze(
                false
            );


            resetResults();

            clearMessage();
        }
    );
}


/* Run after DOM */

document.addEventListener(
    "DOMContentLoaded",
    setupRemoveButton
);


/* ============================================================
   ANALYSIS
============================================================ */

function initializeAnalysis() {

    const button =
        $("analyzeButton");


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        () => analyzeImage()
    );
}


async function analyzeImage() {

    if (
        state.busy ||
        !state.selectedFile
    ) {
        return;
    }


    state.busy =
        true;


    setLoading(
        true
    );


    clearMessage();


    const formData =
        new FormData();


    formData.append(
        "image",
        state.selectedFile
    );


    try {

        console.log(
            "Uploading image..."
        );


        const response =
            await fetch(
                `${API_BASE}/api/analyze`,
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        console.log(
            "Analysis response:",
            data
        );


        if (
            !response.ok
        ) {

            throw new Error(
                data.error ||
                `Server returned ${response.status}`
            );
        }


        if (
            !data.success ||
            !data.result
        ) {

            throw new Error(
                data.error ||
                "Analysis failed."
            );
        }


        state.currentResult =
            data.result;


        state.analysisId =
            data.result.analysis_id;


        await renderCompleteResult(
            data.result
        );


        showMessage(
            "Image analyzed successfully.",
            "success"
        );


        /*
         * Move to results.
         */

        window.history.replaceState(
            null,
            "",
            "#results"
        );


        activateNav(
            "results"
        );


        setTimeout(
            () => {

                $("results")?.scrollIntoView({
                    behavior:
                        "smooth",
                    block:
                        "start"
                });

            },
            150
        );


    } catch (error) {

        console.error(
            "Analysis error:",
            error
        );


        showMessage(
            error.message ||
            "Unable to analyze image.",
            "error",
            { retryable: true }
        );


    } finally {

        state.busy =
            false;


        setLoading(
            false
        );
    }
}


/* ============================================================
   RENDER RESULT
============================================================ */

async function renderCompleteResult(
    result
) {

    renderUnderstanding(
        result.image_understanding
    );


    renderSummary(
        result.analysis_summary
    );


    renderImages(
        result
    );


    renderCSV(
        result
    );


    await loadFeatures(
        result
    );


    $("understandingSection")
        ?.classList.remove(
            "hidden"
        );


    $("results")
        ?.classList.remove(
            "hidden"
        );


    $("features")
        ?.classList.remove(
            "hidden"
        );
}


/* ============================================================
   IMAGE UNDERSTANDING
============================================================ */

function renderUnderstanding(
    understanding
) {

    if (!understanding) {
        return;
    }


    const image =
        understanding.image ||
        {};


    const visual =
        understanding.visual_characteristics ||
        {};


    const foreground =
        understanding.foreground ||
        {};


    const analysis =
        understanding.analysis ||
        {};


    setText(
        "imageCategory",
        visual.image_category
    );


    setText(
        "observedStructure",
        visual.observed_structure
    );


    setText(
        "imagingStyle",
        visual.imaging_style
    );


    setText(
        "brightness",
        visual.brightness
    );


    setText(
        "contrast",
        visual.contrast
    );


    setText(
        "imageChannels",
        image.channels
    );


    setText(
        "estimatedObjects",
        foreground.estimated_objects
    );


    setText(
        "resolution",
        image.width &&
        image.height
            ? `${image.width} × ${image.height}px`
            : "-"
    );


    const badge =
        $("readyBadge");


    if (badge) {

        badge.textContent =
            analysis.analysis_ready
                ? "Analysis Ready"
                : "Review Required";


        badge.classList.toggle(
            "not-ready",
            !analysis.analysis_ready
        );
    }


    setText(
        "readinessMessage",
        analysis.readiness_message
    );


    const list =
        $("recommendationList");


    if (
        list &&
        Array.isArray(
            analysis.recommended_analysis
        )
    ) {

        list.innerHTML =
            "";


        analysis
            .recommended_analysis
            .forEach(
                item => {

                    const tag =
                        document.createElement(
                            "span"
                        );


                    tag.textContent =
                        item;


                    list.appendChild(
                        tag
                    );
                }
            );
    }
}


/* ============================================================
   SUMMARY
============================================================ */

function renderSummary(
    summary
) {

    if (!summary) {
        return;
    }


    setText(
        "cellsDetected",
        formatInteger(
            summary.cells_detected
        )
    );


    setText(
        "goodCells",
        formatInteger(
            summary.good_cells
        )
    );


    setText(
        "reviewCells",
        formatInteger(
            summary.review_cells
        )
    );


    setText(
        "averageArea",
        formatNumber(
            summary.average_area,
            2
        )
    );


    setText(
        "averageCircularity",
        formatNumber(
            summary.average_circularity,
            3
        )
    );


    setText(
        "averageEccentricity",
        formatNumber(
            summary.average_eccentricity,
            3
        )
    );


    setText(
        "averageIntensity",
        formatNumber(
            summary.average_intensity,
            2
        )
    );


    setText(
        "analysisId",
        state.analysisId
            ? `ID · ${state.analysisId}`
            : "-"
    );


    /*
     * QC pass rate. Prefer a backend-provided
     * value if present, otherwise derive it
     * from good / total counts.
     */

    const total =
        Number(
            summary.cells_detected
        );

    const good =
        Number(
            summary.good_cells
        );


    let passRate =
        summary.qc_pass_rate !== undefined &&
        summary.qc_pass_rate !== null
            ? Number(
                summary.qc_pass_rate
            )
            : null;


    if (
        passRate === null &&
        Number.isFinite(total) &&
        total > 0 &&
        Number.isFinite(good)
    ) {

        passRate =
            (
                good /
                total
            ) *
            100;
    }


    setText(
        "qcPassRate",
        passRate === null
            ? "-"
            : formatPercent(
                passRate,
                passRate % 1 === 0
                    ? 0
                    : 1
            )
    );


    const bar =
        $("qcBarFill");


    if (bar) {

        bar.style.width =
            `${Math.max(0, Math.min(100, passRate || 0))}%`;
    }
}


/* ============================================================
   OUTPUT URL
============================================================ */

function makeOutputURL(
    result,
    filePath
) {

    if (
        !result ||
        !result.analysis_id ||
        !filePath
    ) {
        return "";
    }


    let filename =
        String(
            filePath
        )
        .replace(
            /\\/g,
            "/"
        )
        .trim();


    /*
     * Backend response can contain:
     *
     * analysis_id/file.png
     *
     * Remove the analysis ID because
     * the URL adds it separately.
     */

    const prefix =
        `${result.analysis_id}/`;


    if (
        filename.startsWith(
            prefix
        )
    ) {

        filename =
            filename.substring(
                prefix.length
            );
    }


    filename =
        filename
            .split("/")
            .pop();


    return (
        `${API_BASE}/api/outputs/` +
        `${encodeURIComponent(
            result.analysis_id
        )}/` +
        `${encodeURIComponent(
            filename
        )}`
    );
}


/* ============================================================
   RENDER IMAGES
============================================================ */

function renderImages(
    result
) {

    const files =
        result.files ||
        {};


    const segmentationURL =
        makeOutputURL(
            result,
            files.segmentation
        );


    const pipelineURL =
        makeOutputURL(
            result,
            files.pipeline
        );


    const distributionURL =
        makeOutputURL(
            result,
            files.distributions
        );


    /*
     * Original
     */

    const original =
        $("originalImage");


    if (
        original &&
        state.selectedFile
    ) {

        const url =
            URL.createObjectURL(
                state.selectedFile
            );


        original.src =
            url;


        original.onload =
            () => {

                URL.revokeObjectURL(
                    url
                );
            };
    }


    /*
     * Segmentation
     */

    setImage(
        "segmentationImage",
        segmentationURL,
        "segmentationEmpty"
    );


    /*
     * Pipeline
     */

    setImage(
        "pipelineImage",
        pipelineURL,
        "pipelineEmpty"
    );


    /*
     * Distribution
     */

    setImage(
        "distributionImage",
        distributionURL,
        "distributionEmpty"
    );


    /*
     * Open buttons
     */

    setButtonLink(
        "openSegmentation",
        segmentationURL
    );


    setButtonLink(
        "openPipeline",
        pipelineURL
    );


    setButtonLink(
        "openDistributions",
        distributionURL
    );
}


function setImage(
    imageId,
    url,
    emptyId
) {

    const image =
        $(imageId);

    const empty =
        $(emptyId);


    if (
        !image ||
        !url
    ) {

        if (empty) {

            empty.classList.remove(
                "hidden"
            );
        }

        return;
    }


    image.src =
        url;


    image.onload =
        () => {

            if (empty) {

                empty.classList.add(
                    "hidden"
                );
            }
        };


    image.onerror =
        () => {

            console.error(
                "Image failed:",
                url
            );


            image.removeAttribute(
                "src"
            );


            if (empty) {

                empty.textContent =
                    "Preview unavailable.";

                empty.classList.remove(
                    "hidden"
                );
            }
        };
}


function setButtonLink(
    id,
    url
) {

    const button =
        $(id);


    if (
        !button ||
        !url
    ) {

        if (button) {

            button.disabled =
                true;
        }

        return;
    }


    button.disabled =
        false;


    button.onclick =
        () => {

            window.open(
                url,
                "_blank"
            );
        };
}


/* ============================================================
   CSV
============================================================ */

function renderCSV(
    result
) {

    const url =
        makeOutputURL(
            result,
            result.files?.csv
        );


    const link =
        $("csvDownload");


    if (
        link &&
        url
    ) {

        link.href =
            url;


        link.download =
            "cell_features.csv";
    }
}


/* ============================================================
   FEATURES
============================================================ */

async function loadFeatures(
    result
) {

    const table =
        $("featuresTable");


    if (!table) {
        return;
    }


    const csvURL =
        makeOutputURL(
            result,
            result.files?.csv
        );


    if (!csvURL) {

        renderTableMessage(
            "Feature dataset unavailable."
        );

        return;
    }


    try {

        console.log(
            "Loading CSV:",
            csvURL
        );


        const response =
            await fetch(
                csvURL,
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `CSV request failed: ${response.status}`
            );
        }


        const csv =
            await response.text();


        const rows =
            parseCSV(
                csv
            );


        state.featureRows =
            convertCSVRows(
                rows
            );


        state.filteredRows =
            [
                ...state.featureRows
            ];


        state.currentPage =
            1;


        const search =
            $("featureSearch");


        if (search) {

            search.value =
                "";
        }


        renderFeatureTable();


    } catch (error) {

        console.error(
            "CSV error:",
            error
        );


        renderTableMessage(
            "Unable to load cell measurements."
        );
    }
}


/* ============================================================
   CSV PARSER
============================================================ */

function parseCSV(text) {

    const result = [];

    let row = [];

    let value = "";

    let quoted = false;


    for (
        let i = 0;
        i < text.length;
        i++
    ) {

        const char =
            text[i];


        const next =
            text[i + 1];


        if (
            char === '"' &&
            quoted &&
            next === '"'
        ) {

            value += '"';

            i++;

            continue;
        }


        if (
            char === '"'
        ) {

            quoted =
                !quoted;

            continue;
        }


        if (
            char === "," &&
            !quoted
        ) {

            row.push(
                value.trim()
            );

            value =
                "";

            continue;
        }


        if (
            (
                char === "\n" ||
                char === "\r"
            ) &&
            !quoted
        ) {

            if (
                char === "\r" &&
                next === "\n"
            ) {

                i++;
            }


            row.push(
                value.trim()
            );


            result.push(
                row
            );


            row =
                [];

            value =
                "";

            continue;
        }


        value +=
            char;
    }


    if (
        value.length ||
        row.length
    ) {

        row.push(
            value.trim()
        );


        result.push(
            row
        );
    }


    return result;
}


/* ============================================================
   CONVERT CSV
============================================================ */

function convertCSVRows(
    rows
) {

    if (
        rows.length < 2
    ) {
        return [];
    }


    const headers =
        rows[0].map(
            header =>
                header
                    .trim()
                    .toLowerCase()
        );


    function indexOf(
        ...names
    ) {

        for (
            const name of names
        ) {

            const index =
                headers.indexOf(
                    name
                );


            if (
                index !== -1
            ) {

                return index;
            }
        }


        return -1;
    }


    const id =
        indexOf(
            "cell_id",
            "label",
            "id"
        );


    const area =
        indexOf(
            "area"
        );


    const perimeter =
        indexOf(
            "perimeter"
        );


    const circularity =
        indexOf(
            "circularity"
        );


    const eccentricity =
        indexOf(
            "eccentricity"
        );


    const intensity =
        indexOf(
            "mean_intensity",
            "intensity"
        );


    const qc =
        indexOf(
            "quality_flag",
            "quality",
            "qc"
        );


    return rows
        .slice(1)
        .filter(
            row =>
                row &&
                row.some(
                    cell =>
                        String(
                            cell
                        ).trim()
                )
        )
        .map(
            row => ({

                cellId:
                    id >= 0
                        ? row[id]
                        : "-",

                area:
                    area >= 0
                        ? Number(
                            row[area]
                        )
                        : null,

                perimeter:
                    perimeter >= 0
                        ? Number(
                            row[perimeter]
                        )
                        : null,

                circularity:
                    circularity >= 0
                        ? Number(
                            row[circularity]
                        )
                        : null,

                eccentricity:
                    eccentricity >= 0
                        ? Number(
                            row[eccentricity]
                        )
                        : null,

                intensity:
                    intensity >= 0
                        ? Number(
                            row[intensity]
                        )
                        : null,

                qc:
                    qc >= 0
                        ? row[qc]
                        : "-"
            })
        );
}


/* ============================================================
   FEATURES CONTROLS
============================================================ */

function initializeFeatureControls() {

    const search =
        $("featureSearch");


    const pageSize =
        $("featurePageSize");


    const previous =
        $("featurePrev");


    const next =
        $("featureNext");


    if (search) {

        const debounced =
            debounce(
                value => filterFeatures(value),
                180
            );


        search.addEventListener(
            "input",
            () => {

                debounced(
                    search.value
                );
            }
        );
    }


    if (pageSize) {

        pageSize.addEventListener(
            "change",
            () => {

                state.pageSize =
                    Number(
                        pageSize.value
                    );


                state.currentPage =
                    1;


                renderFeatureTable();
            }
        );
    }


    if (previous) {

        previous.addEventListener(
            "click",
            () => {

                if (
                    state.currentPage >
                    1
                ) {

                    state.currentPage--;

                    renderFeatureTable();
                }
            }
        );
    }


    if (next) {

        next.addEventListener(
            "click",
            () => {

                const totalPages =
                    Math.max(
                        1,
                        Math.ceil(
                            state.filteredRows.length /
                            state.pageSize
                        )
                    );


                if (
                    state.currentPage <
                    totalPages
                ) {

                    state.currentPage++;

                    renderFeatureTable();
                }
            }
        );
    }


    /*
     * Sorting
     */

    document
        .querySelectorAll(
            "#cellFeaturesTable thead th"
        )
        .forEach(
            header => {

                const trigger =
                    () => {

                        const column =
                            header.dataset.sort;


                        if (!column) {
                            return;
                        }


                        sortFeatures(
                            column
                        );
                    };


                header.addEventListener(
                    "click",
                    trigger
                );


                header.addEventListener(
                    "keydown",
                    event => {

                        if (
                            event.key === "Enter" ||
                            event.key === " "
                        ) {

                            event.preventDefault();

                            trigger();
                        }
                    }
                );
            }
        );
}


/* ============================================================
   FILTER
============================================================ */

function filterFeatures(
    query
) {

    const search =
        String(
            query
        )
        .trim()
        .toLowerCase();


    if (!search) {

        state.filteredRows =
            [
                ...state.featureRows
            ];

    } else {

        state.filteredRows =
            state.featureRows.filter(
                row => {

                    return (

                        String(
                            row.cellId
                        )
                        .toLowerCase()
                        .includes(search)

                        ||

                        String(
                            row.qc
                        )
                        .toLowerCase()
                        .includes(search)

                        ||

                        String(
                            row.area
                        )
                        .includes(search)

                        ||

                        String(
                            row.circularity
                        )
                        .includes(search)

                        ||

                        String(
                            row.eccentricity
                        )
                        .includes(search)
                    );
                }
            );
    }


    state.currentPage =
        1;


    renderFeatureTable();
}


/* ============================================================
   SORT
============================================================ */

function sortFeatures(
    column
) {

    if (
        state.sortColumn ===
        column
    ) {

        state.sortDirection =
            state.sortDirection ===
            "asc"
                ? "desc"
                : "asc";

    } else {

        state.sortColumn =
            column;

        state.sortDirection =
            "asc";
    }


    const direction =
        state.sortDirection ===
        "asc"
            ? 1
            : -1;


    state.filteredRows.sort(
        (
            first,
            second
        ) => {

            const a =
                first[column];

            const b =
                second[column];


            if (
                typeof a ===
                "number" &&
                typeof b ===
                "number"
            ) {

                return (
                    a -
                    b
                ) *
                direction;
            }


            return String(
                a ?? ""
            )
            .localeCompare(
                String(
                    b ?? ""
                )
            ) *
            direction;
        }
    );


    state.currentPage =
        1;


    renderFeatureTable();
}


/* ============================================================
   TABLE RENDER
============================================================ */

function renderFeatureTable() {

    const body =
        $("featuresTable");


    if (!body) {
        return;
    }


    const rows =
        state.filteredRows;


    const total =
        rows.length;


    const totalPages =
        Math.max(
            1,
            Math.ceil(
                total /
                state.pageSize
            )
        );


    if (
        state.currentPage >
        totalPages
    ) {

        state.currentPage =
            totalPages;
    }


    const start =
        (
            state.currentPage -
            1
        ) *
        state.pageSize;


    const end =
        Math.min(
            start +
            state.pageSize,
            total
        );


    const visible =
        rows.slice(
            start,
            end
        );


    if (
        visible.length === 0
    ) {

        const message =
            state.featureRows.length === 0
                ? "Analyze an image to view cell-level measurements."
                : "No cells match your search.";


        body.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="empty-table"
                >
                    ${escapeHTML(message)}
                </td>
            </tr>
        `;

    } else {

        body.innerHTML =
            visible
                .map(
                    row => {

                        const good =
                            String(
                                row.qc
                            )
                            .toLowerCase() ===
                            "good";


                        const qcClass =
                            good
                                ? "qc-good"
                                : "qc-review";


                        return `

                            <tr>

                                <td>
                                    ${escapeHTML(
                                        row.cellId
                                    )}
                                </td>

                                <td>
                                    ${formatNumber(
                                        row.area,
                                        2
                                    )}
                                </td>

                                <td>
                                    ${formatNumber(
                                        row.perimeter,
                                        2
                                    )}
                                </td>

                                <td>
                                    ${formatNumber(
                                        row.circularity,
                                        3
                                    )}
                                </td>

                                <td>
                                    ${formatNumber(
                                        row.eccentricity,
                                        3
                                    )}
                                </td>

                                <td>
                                    ${formatNumber(
                                        row.intensity,
                                        2
                                    )}
                                </td>

                                <td>
                                    <span
                                        class="qc-badge ${qcClass}"
                                    >
                                        ${escapeHTML(
                                            row.qc
                                        )}
                                    </span>
                                </td>

                            </tr>
                        `;
                    }
                )
                .join("");
    }


    /*
     * Summary
     */

    setText(
        "featureCount",
        `${state.featureRows.length} cells`
    );


    setText(
        "visibleFeatureCount",
        total === 0
            ? "Showing 0"
            : `Showing ${start + 1}–${end}`
    );


    renderPagination(
        totalPages
    );


    updateSortIndicators();
}


/* ============================================================
   PAGINATION
============================================================ */

function renderPagination(
    totalPages
) {

    const container =
        $("featurePageNumbers");


    const previous =
        $("featurePrev");


    const next =
        $("featureNext");


    if (!container) {
        return;
    }


    container.innerHTML =
        "";


    if (previous) {

        previous.disabled =
            state.currentPage <= 1;
    }


    if (next) {

        next.disabled =
            state.currentPage >=
            totalPages;
    }


    const pages =
        getPages(
            state.currentPage,
            totalPages
        );


    pages.forEach(
        page => {

            if (
                page ===
                "..."
            ) {

                const span =
                    document.createElement(
                        "span"
                    );


                span.className =
                    "pagination-ellipsis";


                span.textContent =
                    "…";


                container.appendChild(
                    span
                );


                return;
            }


            const button =
                document.createElement(
                    "button"
                );


            button.type =
                "button";


            button.className =
                "pagination-page";


            button.textContent =
                page;


            button.setAttribute(
                "aria-label",
                `Page ${page}`
            );


            if (
                page ===
                state.currentPage
            ) {

                button.classList.add(
                    "active"
                );

                button.setAttribute(
                    "aria-current",
                    "page"
                );
            }


            button.addEventListener(
                "click",
                () => {

                    state.currentPage =
                        page;


                    renderFeatureTable();
                }
            );


            container.appendChild(
                button
            );
        }
    );
}


/* ============================================================
   PAGE LIST
============================================================ */

function getPages(
    current,
    total
) {

    if (
        total <= 7
    ) {

        return Array.from(
            {
                length:
                    total
            },
            (_, i) =>
                i + 1
        );
    }


    const pages =
        [1];


    if (
        current > 4
    ) {

        pages.push(
            "..."
        );
    }


    const start =
        Math.max(
            2,
            current - 1
        );


    const end =
        Math.min(
            total - 1,
            current + 1
        );


    for (
        let page = start;
        page <= end;
        page++
    ) {

        pages.push(
            page
        );
    }


    if (
        current <
        total - 3
    ) {

        pages.push(
            "..."
        );
    }


    pages.push(
        total
    );


    return pages;
}


/* ============================================================
   SORT INDICATORS
============================================================ */

function updateSortIndicators() {

    document
        .querySelectorAll(
            "#cellFeaturesTable thead th"
        )
        .forEach(
            header => {

                header.classList.remove(
                    "sorted"
                );


                header.removeAttribute(
                    "aria-sort"
                );


                const existing =
                    header.querySelector(
                        ".sort-arrow"
                    );


                if (existing) {

                    existing.remove();
                }


                if (
                    header.dataset.sort ===
                    state.sortColumn
                ) {

                    header.classList.add(
                        "sorted"
                    );


                    header.setAttribute(
                        "aria-sort",
                        state.sortDirection ===
                        "asc"
                            ? "ascending"
                            : "descending"
                    );


                    const arrow =
                        document.createElement(
                            "span"
                        );


                    arrow.className =
                        "sort-arrow";


                    arrow.textContent =
                        state.sortDirection ===
                        "asc"
                            ? " ↑"
                            : " ↓";


                    header.appendChild(
                        arrow
                    );
                }
            }
        );
}


/* ============================================================
   TABLE MESSAGE
============================================================ */

function renderTableMessage(
    message
) {

    const body =
        $("featuresTable");


    if (!body) {
        return;
    }


    body.innerHTML = `
        <tr>
            <td
                colspan="7"
                class="empty-table"
            >
                ${escapeHTML(message)}
            </td>
        </tr>
    `;


    setText(
        "featureCount",
        "0 cells"
    );


    setText(
        "visibleFeatureCount",
        "Showing 0"
    );
}


/* ============================================================
   NAVIGATION
============================================================ */

function initializeNavigation() {

    document
        .querySelectorAll(
            ".nav-item"
        )
        .forEach(
            link => {

                link.addEventListener(
                    "click",
                    event => {

                        event.preventDefault();


                        const id =
                            link.dataset.nav;


                        const target =
                            $(id);


                        if (
                            !target
                        ) {

                            return;
                        }


                        activateNav(
                            id
                        );


                        window.history.replaceState(
                            null,
                            "",
                            `#${id}`
                        );


                        target.scrollIntoView({
                            behavior:
                                "smooth",

                            block:
                                "start"
                        });
                    }
                );
            }
        );


    /*
     * Initial hash.
     */

    const initial =
        window.location.hash
            .replace(
                "#",
                ""
            );


    if (
        initial &&
        ["analysis", "results", "features"]
            .includes(initial)
    ) {

        activateNav(
            initial
        );
    }
}


function activateNav(
    id
) {

    document
        .querySelectorAll(
            ".nav-item"
        )
        .forEach(
            item => {

                item.classList.toggle(
                    "active",
                    item.dataset.nav ===
                    id
                );
            }
        );
}


/* ============================================================
   LIGHTBOX
============================================================ */

function initializeLightbox() {

    const lightbox =
        $("lightbox");

    const lightboxImage =
        $("lightboxImage");

    const close =
        $("closeLightbox");

    const prevButton =
        $("lightboxPrev");

    const nextButton =
        $("lightboxNext");


    if (
        !lightbox ||
        !lightboxImage
    ) {
        return;
    }


    const targets = [
        { id: "originalImage", label: "Original" },
        { id: "segmentationImage", label: "Segmentation" },
        { id: "pipelineImage", label: "Pipeline" },
        { id: "distributionImage", label: "Distributions" }
    ];


    function openLightbox(
        index
    ) {

        const item =
            state.lightboxItems[index];


        if (!item) {
            return;
        }


        state.lightboxIndex =
            index;


        lightboxImage.src =
            item.src;


        setText(
            "lightboxCaption",
            item.label
        );


        lightbox.classList.remove(
            "hidden"
        );


        const multiple =
            state.lightboxItems.length > 1;


        prevButton?.classList.toggle(
            "hidden",
            !multiple
        );

        nextButton?.classList.toggle(
            "hidden",
            !multiple
        );
    }


    function closeLightbox() {

        lightbox.classList.add(
            "hidden"
        );

        lightboxImage.src =
            "";
    }


    function step(
        delta
    ) {

        if (
            state.lightboxItems.length === 0
        ) {
            return;
        }


        const nextIndex =
            (
                state.lightboxIndex +
                delta +
                state.lightboxItems.length
            ) %
            state.lightboxItems.length;


        openLightbox(
            nextIndex
        );
    }


    /*
     * Click result images.
     */

    targets.forEach(
        target => {

            const image =
                $(target.id);


            if (!image) {
                return;
            }


            image.addEventListener(
                "click",
                () => {

                    if (
                        !image.src
                    ) {
                        return;
                    }


                    state.lightboxItems =
                        targets
                            .map(
                                entry => {

                                    const el =
                                        $(entry.id);


                                    return el && el.src
                                        ? {
                                            src: el.src,
                                            label: entry.label
                                        }
                                        : null;
                                }
                            )
                            .filter(
                                Boolean
                            );


                    const index =
                        state.lightboxItems.findIndex(
                            item =>
                                item.src ===
                                image.src
                        );


                    openLightbox(
                        index === -1
                            ? 0
                            : index
                    );
                }
            );
        }
    );


    /*
     * Close
     */

    close?.addEventListener(
        "click",
        closeLightbox
    );


    prevButton?.addEventListener(
        "click",
        () => step(-1)
    );


    nextButton?.addEventListener(
        "click",
        () => step(1)
    );


    lightbox.addEventListener(
        "click",
        event => {

            if (
                event.target ===
                lightbox
            ) {

                closeLightbox();
            }
        }
    );


    document.addEventListener(
        "keydown",
        event => {

            if (
                lightbox.classList.contains(
                    "hidden"
                )
            ) {
                return;
            }


            if (
                event.key ===
                "Escape"
            ) {

                closeLightbox();
            }


            if (
                event.key ===
                "ArrowLeft"
            ) {

                step(-1);
            }


            if (
                event.key ===
                "ArrowRight"
            ) {

                step(1);
            }
        }
    );
}


/* ============================================================
   MESSAGE
============================================================ */

function showMessage(
    message,
    type,
    options = {}
) {

    const box =
        $("messageBox");


    if (!box) {
        return;
    }


    box.innerHTML =
        "";


    const text =
        document.createElement(
            "span"
        );


    text.textContent =
        message;


    box.appendChild(
        text
    );


    if (
        options.retryable &&
        state.selectedFile
    ) {

        const retry =
            document.createElement(
                "button"
            );


        retry.type =
            "button";


        retry.className =
            "message-retry";


        retry.textContent =
            "Try again";


        retry.addEventListener(
            "click",
            () => analyzeImage()
        );


        box.appendChild(
            retry
        );
    }


    box.className =
        `message ${type}`;


    box.classList.remove(
        "hidden"
    );
}


function clearMessage() {

    const box =
        $("messageBox");


    if (!box) {
        return;
    }


    box.innerHTML =
        "";


    box.className =
        "message hidden";
}


/* ============================================================
   LOADING
============================================================ */

function setLoading(
    loading
) {

    const loader =
        $("loadingState");

    const button =
        $("analyzeButton");


    if (loader) {

        loader.classList.toggle(
            "hidden",
            !loading
        );
    }


    if (button) {

        button.disabled =
            loading ||
            !state.selectedFile;
    }


    const label =
        $("analyzeButtonLabel");


    if (label) {

        label.textContent =
            loading
                ? "Analyzing..."
                : "Analyze Image";
    }
}


/* ============================================================
   ANALYZE BUTTON
============================================================ */

function enableAnalyze(
    enabled
) {

    const button =
        $("analyzeButton");


    if (!button) {
        return;
    }


    button.disabled =
        !enabled ||
        state.busy;
}


/* ============================================================
   RESET
============================================================ */

function resetResults() {

    state.currentResult =
        null;

    state.analysisId =
        null;

    state.featureRows =
        [];

    state.filteredRows =
        [];

    state.currentPage =
        1;

    state.lightboxItems =
        [];

    state.lightboxIndex =
        0;


    [
        "understandingSection",
        "results",
        "features"
    ]
    .forEach(
        id => {

            const element =
                $(id);


            if (element) {

                element.classList.add(
                    "hidden"
                );
            }
        }
    );


    /*
     * Clear result images.
     */

    [
        "segmentationImage",
        "pipelineImage",
        "distributionImage"
    ]
    .forEach(
        id => {

            const image =
                $(id);


            if (image) {

                image.removeAttribute(
                    "src"
                );
            }
        }
    );


    /*
     * Reset open buttons.
     */

    [
        "openSegmentation",
        "openPipeline",
        "openDistributions"
    ]
    .forEach(
        id => {

            const button =
                $(id);


            if (button) {

                button.disabled =
                    true;

                button.onclick =
                    null;
            }
        }
    );


    /*
     * Reset QC bar.
     */

    const bar =
        $("qcBarFill");


    if (bar) {

        bar.style.width =
            "0%";
    }


    /*
     * Reset table.
     */

    renderTableMessage(
        "Analyze an image to view cell-level measurements."
    );
}


/* ============================================================
   PUBLIC DEBUG API
============================================================ */

window.CellAnalyzer = {

    analyze:
        analyzeImage,

    health:
        checkBackend,

    getState:
        () => state

};