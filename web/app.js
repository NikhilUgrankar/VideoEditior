document.addEventListener("DOMContentLoaded", () => {
    let uploadedFiles = [];
    let customMusicFile = null;
    let selectedPreset = "adrenaline";

    // DOM Elements
    const dropzone = document.getElementById("video-dropzone");
    const videoInput = document.getElementById("video-file-input");
    const videoList = document.getElementById("video-list");
    const sampleMusicSelect = document.getElementById("sample-music-select");
    const customMusicInput = document.getElementById("custom-music-input");
    const presetCards = document.querySelectorAll(".preset-card");
    const resolutionSelect = document.getElementById("resolution-select");
    const aspectSelect = document.getElementById("aspect-select");
    const lutSelect = document.getElementById("lut-select");
    const hudToggle = document.getElementById("hud-toggle");
    const renderBtn = document.getElementById("render-btn");
    
    const progressModal = document.getElementById("progress-modal");
    const progressFill = document.getElementById("modal-progress-fill");
    const statusText = document.getElementById("modal-status-text");
    const pctText = document.getElementById("modal-percentage-text");
    
    const placeholderPlayer = document.getElementById("placeholder-player");
    const outputVideoPlayer = document.getElementById("output-video-player");
    const exportBar = document.getElementById("export-bar");
    const downloadLink = document.getElementById("download-link");
    const exportMetaText = document.getElementById("export-meta-text");

    // File Drag & Drop handlers
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length) {
            handleVideoFiles(e.dataTransfer.files);
        }
    });

    videoInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            handleVideoFiles(e.target.files);
        }
    });

    const rawDurationBadge = document.getElementById("raw-total-duration-badge");
    const targetDurationSelect = document.getElementById("target-duration-select");

    async function handleVideoFiles(files) {
        for (let file of files) {
            uploadedFiles.push(file);
        }
        renderVideoList();
        await analyzeUploadedFootage();
    }

    async function analyzeUploadedFootage() {
        if (uploadedFiles.length === 0) return;
        
        rawDurationBadge.innerText = "Analyzing footage...";

        const formData = new FormData();
        for (let f of uploadedFiles) {
            formData.append("videos", f);
        }

        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                rawDurationBadge.innerText = `Total Upload: ${data.total_raw_duration_formatted}`;
            }
        } catch (e) {
            console.error("Analysis error:", e);
            rawDurationBadge.innerText = "Total Upload: Calculated";
        }
    }

    function renderVideoList() {
        videoList.innerHTML = "";
        uploadedFiles.forEach((file, index) => {
            const item = document.createElement("div");
            item.className = "media-item";
            item.innerHTML = `
                <span class="media-item-name">📹 ${file.name}</span>
                <span class="media-item-tag">${(file.size / (1024 * 1024)).toFixed(1)} MB</span>
            `;
            videoList.appendChild(item);
        });
    }

    // Music track selector
    sampleMusicSelect.addEventListener("change", (e) => {
        if (e.target.value === "custom") {
            customMusicInput.click();
        }
    });

    customMusicInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            customMusicFile = e.target.files[0];
            sampleMusicSelect.options[3].text = `🎵 Custom: ${customMusicFile.name}`;
            sampleMusicSelect.value = "custom";
        }
    });

    // Preset selection
    presetCards.forEach(card => {
        card.addEventListener("click", () => {
            presetCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            selectedPreset = card.dataset.preset;
        });
    });

    // Render Button trigger
    renderBtn.addEventListener("click", async () => {
        progressModal.hidden = false;
        progressFill.style.width = "5%";
        statusText.innerText = "Initializing ultrafast video engine...";
        pctText.innerText = "5%";

        const formData = new FormData();
        
        // Append video files if present
        if (uploadedFiles.length > 0) {
            for (let f of uploadedFiles) {
                formData.append("videos", f);
            }
        }
        
        // Append music file if custom
        if (customMusicFile) {
            formData.append("music", customMusicFile);
        }

        formData.append("preset", selectedPreset);
        formData.append("target_duration", targetDurationSelect.value);
        formData.append("resolution", resolutionSelect.value);
        formData.append("aspect_ratio", aspectSelect.value);
        formData.append("lut_preset", lutSelect.value);
        formData.append("show_hud", hudToggle.checked);

        try {
            const response = await fetch("/api/render", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || errData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();
            const jobId = data.job_id;

            // Poll job status
            pollStatus(jobId);

        } catch (err) {
            alert("Render Initialization Error: " + err.message);
            progressModal.hidden = true;
        }
    });

    async function pollStatus(jobId) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${jobId}`);
                if (!res.ok) return;

                const data = await res.json();

                const currentProgress = Math.max(5, Math.min(100, data.progress || 5));
                progressFill.style.width = `${currentProgress}%`;
                statusText.innerText = data.status_message || "Processing...";
                pctText.innerText = `${Math.round(currentProgress)}%`;

                if (data.status === "completed") {
                    clearInterval(interval);
                    progressModal.hidden = true;
                    
                    // Update video player
                    placeholderPlayer.hidden = true;
                    outputVideoPlayer.hidden = false;
                    outputVideoPlayer.src = data.output_url;
                    outputVideoPlayer.play();

                    exportBar.hidden = false;
                    downloadLink.href = data.output_url;
                    exportMetaText.innerText = `Rendered: ${data.resolution.toUpperCase()} 60FPS | ${data.aspect_ratio}`;
                } else if (data.status === "failed") {
                    clearInterval(interval);
                    progressModal.hidden = true;
                    alert("Rendering Error: " + (data.error || "Unknown server error"));
                }
            } catch (e) {
                console.error("Polling status error:", e);
            }
        }, 800);
    }
});
