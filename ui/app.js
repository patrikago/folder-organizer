const modeCards = document.querySelectorAll(".mode-card");

const destinationSection =
    document.querySelector(".destination-section");

const folderPaths =
    document.querySelectorAll(".folder-path");

const browseButtons =
    document.querySelectorAll(".folder-input .icon-button");

const scanButton =
    document.querySelector(".source-scan-button");

const cardActions =
    document.querySelectorAll(".card-action");

const resultsSection =
    document.querySelector(".results");

const previewSection =
    document.querySelector("#preview-section");

const scanStatus =
    document.querySelector(".scan-status");

const infoButton =
    document.querySelector(".info-button");

const infoModal =
    document.querySelector("#info-modal");

const infoCloseButtons =
    document.querySelectorAll("[data-info-close]");


let selectedMode = "move";
let sourceFolder = "";
let destinationFolder = "";


function setInfoModal(isOpen) {

    infoModal.classList.toggle("visible", isOpen);

    infoModal.setAttribute(
        "aria-hidden",
        String(!isOpen)
    );

    infoButton.setAttribute(
        "aria-expanded",
        String(isOpen)
    );

    document.body.classList.toggle(
        "modal-open",
        isOpen
    );

    if (isOpen) {
        infoModal.querySelector(".info-close-button").focus();
    } else {
        infoButton.focus();
    }
}


infoButton.addEventListener(
    "click",
    () => setInfoModal(true)
);

infoCloseButtons.forEach(button => {
    button.addEventListener(
        "click",
        () => setInfoModal(false)
    );
});

document.addEventListener(
    "keydown",
    event => {
        if (event.key === "Escape" && infoModal.classList.contains("visible")) {
            setInfoModal(false);
        }
    }
);


async function restoreSourceFolder() {

    const savedSourceFolder =
        localStorage.getItem("iphone-organizer-source-folder");

    if (!savedSourceFolder) {
        return;
    }

    sourceFolder = savedSourceFolder;

    folderPaths[0].textContent =
        savedSourceFolder;

    updateOrganizeButtons();

    scanButton.click();
}


const updateBanner =
    document.querySelector("#update-banner");

const updateBannerText =
    document.querySelector("#update-banner-text");

const updateBannerLink =
    document.querySelector("#update-banner-link");

const updateBannerDismiss =
    document.querySelector("#update-banner-dismiss");


async function checkForUpdate() {

    try {
        const update = await pywebview.api.check_for_update();

        if (!update) {
            return;
        }

        updateBannerText.textContent =
            `A new version (${update.latest_version}) is available.`;

        updateBannerLink.onclick =
            () => pywebview.api.open_release_page(update.url);

        updateBanner.classList.remove("hidden");
    } catch (error) {
        // Fail silently - update checks should never block the app.
    }
}


updateBannerDismiss.addEventListener(
    "click",
    () => updateBanner.classList.add("hidden")
);


window.addEventListener(
    "pywebviewready",
    () => {
        restoreSourceFolder();
        checkForUpdate();
    }
);


function updateOrganizeButtons() {

    modeCards.forEach(card => {
        const isSelected = card.classList.contains("selected");

        card.querySelector(".card-action")
            .classList.toggle("visible", isSelected && Boolean(sourceFolder));

        card.querySelector(".card-feedback")
            .classList.toggle("visible", isSelected && !sourceFolder);
        });
}


// -----------------------------
// Mode selection
// -----------------------------

modeCards.forEach(card => {

    card.addEventListener("click", () => {

        modeCards.forEach(item => {
            item.classList.remove("selected");

            item.querySelector(".card-action")
                .classList.remove("visible");

            item.querySelector(".card-feedback")
                .classList.remove("visible");
        });

        card.classList.add("selected");

        if (sourceFolder) {
            card.querySelector(".card-action")
                .classList.add("visible");
        } else {
            card.querySelector(".card-feedback")
                .classList.add("visible");
        }

        selectedMode =
            card.dataset.mode;

        if (selectedMode === "copy") {

            destinationSection
                .classList.remove("hidden");

        } else {

            destinationSection
                .classList.add("hidden");

            destinationFolder = "";

            folderPaths[1].textContent =
                "Select where the organized copy should be saved...";
        }
    });

});

cardActions.forEach(button => {
    button.addEventListener("click", event => {
        event.stopPropagation();
        organizeFiles();
    });
});


// -----------------------------
// Browse buttons
// -----------------------------

browseButtons[0].addEventListener(
    "click",
    async () => {

        const folder =
            await pywebview.api.select_folder();

        if (!folder) {
            return;
        }

        sourceFolder = folder;

        localStorage.setItem(
            "iphone-organizer-source-folder",
            folder
        );

        folderPaths[0].textContent =
            folder;

        updateOrganizeButtons();
    }
);


browseButtons[1].addEventListener(
    "click",
    async () => {

        const folder =
            await pywebview.api.select_folder();

        if (!folder) {
            return;
        }

        destinationFolder = folder;

        folderPaths[1].textContent =
            folder;
    }
);


// -----------------------------
// Scan folder
// -----------------------------

scanButton.addEventListener(
    "click",
    async () => {

        if (!sourceFolder) {

            alert(
                "Please select a source folder first."
            );

            return;
        }

        scanButton.disabled = true;

        scanButton.title =
            "Scanning folder...";

        scanButton.setAttribute(
            "aria-label",
            "Scanning folder..."
        );

        try {

            const results =
                await pywebview.api.scan_folder(
                    sourceFolder
                );

            if (!results) {

                alert(
                    "Unable to scan this folder."
                );

                return;
            }

            updateStats(results);

            const preview =
                await pywebview.api.get_preview();

            updatePreview(preview);

            resultsSection
                .classList.add("visible");

            document.querySelector("#preview-title")
                .classList.remove("hidden");

            previewSection
                .classList.add("visible");

            scanStatus
                .classList.add("scanned");

            scanStatus.closest(".actions")
                .classList.add("hidden");

        } catch (error) {

            console.error(error);

            alert(
                "Something went wrong while scanning."
            );

        } finally {

            scanButton.disabled = false;

            scanButton.title =
                "Scan selected folder";

            scanButton.setAttribute(
                "aria-label",
                "Scan selected folder"
            );
        }
    }
);


// -----------------------------
// Update statistics
// -----------------------------

function updateStats(results) {

    const statValues =
        document.querySelectorAll(
            ".stat-card strong"
        );

    statValues[0].textContent =
        results.total_files;

    statValues[1].textContent =
        results.photos;

    statValues[2].textContent =
        results.videos;

    statValues[3].textContent =
        results.other;

    statValues[4].textContent =
        results.zero_byte_files;

    statValues[5].textContent =
        results.duplicates;
}


// -----------------------------
// Escape HTML
// -----------------------------

function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}


// -----------------------------
// Update preview
// -----------------------------

function updatePreview(preview) {

    const photos =
        document.querySelector(
            "#photo-years"
        );

    const videos =
        document.querySelector(
            "#video-years"
        );

    photos.innerHTML = "";

    videos.innerHTML = "";

    const photoTotal =
    Object.values(preview.photos)
        .reduce((total, count) => total + count, 0);

    const videoTotal =
        Object.values(preview.videos)
            .reduce((total, count) => total + count, 0);

    document.querySelector("#photo-total").textContent =
        `${photoTotal} file${photoTotal === 1 ? "" : "s"}`;

    document.querySelector("#video-total").textContent =
        `${videoTotal} file${videoTotal === 1 ? "" : "s"}`;

    const photoFallbackYears =
        new Set(preview.photo_fallback_years || []);

    const videoFallbackYears =
        new Set(preview.video_fallback_years || []);

    renderYearList(
        photos,
        preview.photos,
        "No photos found",
        photoFallbackYears
    );

    renderYearList(
        videos,
        preview.videos,
        "No videos found",
        videoFallbackYears
    );

    // Metadata warning (informational)

    const metadataWarning =
        document.querySelector(
            "#metadata-warning"
        );

    if (preview.missing_metadata > 0) {

        const items =
            preview.missing_metadata_details || [];

        const listItems = items.map(item => `
            <li>
                <span class="warning-list-name">
                    ${escapeHtml(item.file)}
                </span>
                <span class="warning-list-meta">
                    ${escapeHtml(item.type)} &middot; filed under ${item.year}
                </span>
            </li>
        `).join("");

        metadataWarning.innerHTML = `
            <div class="warning-icon" aria-hidden="true">!</div>

            <div class="warning-body">
                <strong>
                    ${preview.missing_metadata}
                    files without reliable capture dates
                </strong>

                <p>
                    These files will be organized using
                    their file modified date.
                </p>

                <details class="warning-details">
                    <summary>Show files</summary>
                    <ul class="warning-list">
                        ${listItems}
                    </ul>
                </details>
            </div>
        `;

        metadataWarning.style.display =
            "flex";

    } else {

        metadataWarning.style.display =
            "none";
    }


    // Duplicate warning (urgent — filenames will be mutated)

    const duplicateWarning =
        document.querySelector(
            "#duplicate-warning"
        );

    if (preview.duplicates > 0) {

        const groups =
            preview.duplicate_details || [];

        const listItems = groups.map(group => {

            const occurrences =
                group.occurrences.map(occurrence => `
                    <li>
                        ${escapeHtml(occurrence.type)}${occurrence.year ? ` &middot; ${occurrence.year}` : ""}
                        &rarr;
                        <strong>${escapeHtml(occurrence.renamed_to)}</strong>
                    </li>
                `).join("");

            return `
                <li>
                    <span class="warning-list-name">
                        ${escapeHtml(group.file)}
                    </span>
                    <ul class="warning-sublist">
                        ${occurrences}
                    </ul>
                </li>
            `;
        }).join("");

        duplicateWarning.innerHTML = `
            <div class="warning-icon" aria-hidden="true">!</div>

            <div class="warning-body">
                <strong>
                    ${preview.duplicates}
                    duplicate filenames detected
                </strong>

                <p>
                    Duplicate files will be renamed
                    automatically instead of overwritten.
                </p>

                <details class="warning-details">
                    <summary>Show duplicates</summary>
                    <ul class="warning-list">
                        ${listItems}
                    </ul>
                </details>
            </div>
        `;

        duplicateWarning.style.display =
            "flex";

    } else {

        duplicateWarning.style.display =
            "none";
    }
}

// -----------------------------
// Render Year List
// -----------------------------

function renderYearList(container, years, emptyMessage, fallbackYears = new Set()) {

    container.innerHTML = "";

    const entries =
        Object.entries(years);

    if (entries.length === 0) {

        container.innerHTML = `
            <div class="year-empty">
                ${emptyMessage}
            </div>
        `;

        return;
    }

    entries.forEach(([year, count]) => {

        const hasFallbackDates =
            fallbackYears.has(Number(year));

        container.innerHTML += `
            <div class="year-row">
                <span>
                    ${year}
                    ${hasFallbackDates ? `
                        <span class="fallback-icon" title="Some ${year} files rely on the file modified date instead of a true capture date"></span>
                    ` : ""}
                </span>
                <strong>${count}</strong>
            </div>
        `;
    });
}

// -----------------------------
// Organize files
// -----------------------------

async function organizeFiles() {

        if (!sourceFolder) {

            alert(
                "Please select a source folder first."
            );

            return;
        }


        if (
            selectedMode === "copy"
            &&
            !destinationFolder
        ) {

            alert(
                "Please select a destination folder."
            );

            return;
        }


        const confirmed =
            confirm(
                selectedMode === "move"
                    ? "This will move your files into Photos and Videos folders. Continue?"
                    : "This will create an organized copy of your files. Continue?"
            );


        if (!confirmed) {
            return;
        }


        try {

            const result =
                await pywebview.api.organize_files(
                    selectedMode,
                    destinationFolder
                );


            if (!result.success) {

                alert(result.message);

                return;
            }


            const count =
                selectedMode === "move"
                    ? result.moved
                    : result.copied;


            alert(
                `Organization complete!\n\n${count} files processed.`
            );


        } catch (error) {

            console.error(error);

            alert(
                "Something went wrong while organizing."
            );

        }
}