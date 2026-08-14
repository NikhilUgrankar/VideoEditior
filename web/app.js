let uploadedFiles = [];
let customMusicFile = null;
let selectedPreset = "adrenaline";
let manualClipsSequence = [];

function switchTab(tabName) {
    const viewAuto = document.getElementById("view-auto");
    const viewManual = document.getElementById("view-manual");
    const tabAutoBtn = document.getElementById("tab-auto-btn");
    const tabManualBtn = document.getElementById("tab-manual-btn");

    if (tabName === "manual") {
        viewAuto.hidden = true;
        viewManual.hidden = false;
        tabAutoBtn.classList.remove("active");
        tabManualBtn.classList.add("active");
        renderManualTimeline();
    } else {
        viewAuto.hidden = false;
        viewManual.hidden = true;
        tabAutoBtn.classList.add("active");
        tabManualBtn.classList.remove("active");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("video-dropzone");
    const videoInput = document.getElementById("video-file-input");
    const videoList = document.getElementById("video-list");
    
    const rawDurationBadge = document.getElementById("raw-total-duration-badge");
    const targetDurationSelect = document.getElementById("target-duration-select");
    const sampleMusicSelect = document.getElementById("sample-music-select");
    const customMusicInput = document.getElementById("custom-music-input");
    const customSongBadge = document.getElementById("custom-music-filename-badge");
    const customSongName = document.getElementById("custom-song-name");
    
    const presetCards = document.querySelectorAll(".preset-card");
    const resolutionSelect = document.getElementById("resolution-select");
    const aspectSelect = document.getElementById("aspect-select");
    const lutSelect = document.getElementById("lut-select");
    
    const engineVolRange = document.getElementById("engine-vol-range");
    const engineVolVal = document.getElementById("engine-vol-val");
    const musicVolRange = document.getElementById("music-vol-range");
    const musicVolVal = document.getElementById("music-vol-val");
    
    const renderBtn = document.getElementById("render-btn");
    const renderManualBtn = document.getElementById("render-manual-btn");
    const addClipBtn = document.getElementById("add-clip-btn");

    const progressModal = document.getElementById("progress-modal");
    const progressFill = document.getElementById("modal-progress-fill");
    const statusText = document.getElementById("modal-status-text");
    const pctText = document.getElementById("modal-percentage-text");
    
    const placeholderPlayer = document.getElementById("placeholder-player");
    const outputVideoPlayer = document.getElementById("output-video-player");
    const exportBar = document.getElementById("export-bar");
    const downloadLink = document.getElementById("download-link");
    const exportMetaText = document.getElementById("export-meta-text");

    // Audio Mix Volume Slider listeners
    engineVolRange.addEventListener("input", (e) => {
        engineVolVal.innerText = `${Math.round(e.target.value * 100)}%`;
    });

    musicVolRange.addEventListener("input", (e) => {
        musicVolVal.innerText = `${Math.round(e.target.value * 100)}%`;
    });

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

                // Populate manual clips array for Interactive Timeline Editor
                if (data.highlights && data.highlights.length > 0) {
                    manualClipsSequence = data.highlights.map((h, i) => ({
                        clip_id: i + 1,
                        video_path: h.video_path,
                        filename: h.filename || `Clip ${i+1}`,
                        src_start: h.start || 0.0,
                        src_end: h.end || 5.0,
                        speed_ramp: 1.0,
                        transition: "dissolve",
                        speed_kmh: h.speed_kmh || 60,
                        lean_angle_deg: h.lean_angle_deg || 18
                    }));
                }
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

    // Custom Audio File Picker Handler
    customMusicInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            customMusicFile = e.target.files[0];
            customSongName.innerText = customMusicFile.name;
            customSongBadge.hidden = false;
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

    // Render Button trigger (AI Auto-Edit)
    renderBtn.addEventListener("click", () => triggerRender(false));

    // Render Manual Button trigger
    renderManualBtn.addEventListener("click", () => triggerRender(true));

    async function triggerRender(isManualMode) {
        progressModal.hidden = false;
        progressFill.style.width = "5%";
        statusText.innerText = "Initializing ultrafast video engine...";
        pctText.innerText = "5%";

        const formData = new FormData();
        
        if (uploadedFiles.length > 0) {
            for (let f of uploadedFiles) {
                formData.append("videos", f);
            }
        }
        
        if (customMusicFile) {
            formData.append("music", customMusicFile);
        }

        formData.append("music_genre", sampleMusicSelect.value);
        formData.append("preset", selectedPreset);
        formData.append("target_duration", targetDurationSelect.value);
        formData.append("resolution", resolutionSelect.value);
        formData.append("aspect_ratio", aspectSelect.value);
        formData.append("lut_preset", lutSelect.value);
        formData.append("engine_vol", engineVolRange.value);
        formData.append("music_vol", musicVolRange.value);
        formData.append("show_hud", false);

        if (isManualMode && manualClipsSequence.length > 0) {
            formData.append("custom_timeline_json", JSON.stringify(manualClipsSequence));
        }

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
            pollStatus(data.job_id);

        } catch (err) {
            alert("Render Initialization Error: " + err.message);
            progressModal.hidden = true;
        }
    }

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
                    
                    placeholderPlayer.hidden = true;
                    outputVideoPlayer.hidden = false;
                    outputVideoPlayer.src = data.output_url;
                    outputVideoPlayer.play();

                    exportBar.hidden = false;
                    downloadLink.href = data.output_url;
                    exportMetaText.innerText = `Rendered: ${data.resolution.toUpperCase()} 60FPS | ${data.aspect_ratio}`;
                    
                    // Auto switch to auto tab if rendering manual edit
                    switchTab('auto');
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

    // Manual Timeline Editor Rendering
    window.renderManualTimeline = function() {
        const list = document.getElementById("timeline-sequence-list");
        list.innerHTML = "";

        if (manualClipsSequence.length === 0) {
            list.innerHTML = `<div style="text-align:center; padding: 40px; color: var(--text-secondary);">
                <p>No video clips analyzed yet. Upload raw videos in the <strong>AI Auto-Edit Studio</strong> tab to auto-populate the interactive timeline.</p>
            </div>`;
            return;
        }

        manualClipsSequence.forEach((clip, index) => {
            const card = document.createElement("div");
            card.className = "clip-card";
            card.innerHTML = `
                <div class="clip-info">
                    <h4>Clip ${index + 1}: ${clip.filename || 'Raw Video'}</h4>
                    <p>Duration: ${(clip.src_end - clip.src_start).toFixed(1)}s | Speed: ${clip.speed_kmh} KM/H</p>
                </div>
                
                <div class="clip-controls-group">
                    <div class="form-group">
                        <label>Start (s)</label>
                        <input type="number" class="mini-input" step="0.5" value="${clip.src_start}" onchange="updateClipParam(${index}, 'src_start', this.value)">
                    </div>
                    <div class="form-group">
                        <label>End (s)</label>
                        <input type="number" class="mini-input" step="0.5" value="${clip.src_end}" onchange="updateClipParam(${index}, 'src_end', this.value)">
                    </div>
                    <div class="form-group">
                        <label>Speed Ramp</label>
                        <select class="mini-select" onchange="updateClipParam(${index}, 'speed_ramp', this.value)">
                            <option value="0.25" ${clip.speed_ramp == 0.25 ? 'selected' : ''}>0.25x Slow-Mo</option>
                            <option value="0.5" ${clip.speed_ramp == 0.5 ? 'selected' : ''}>0.5x Slow-Mo</option>
                            <option value="1.0" ${clip.speed_ramp == 1.0 ? 'selected' : ''}>1.0x Normal</option>
                            <option value="1.5" ${clip.speed_ramp == 1.5 ? 'selected' : ''}>1.5x Fast</option>
                            <option value="3.0" ${clip.speed_ramp == 3.0 ? 'selected' : ''}>3.0x Hyperlapse</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Transition</label>
                        <select class="mini-select" onchange="updateClipParam(${index}, 'transition', this.value)">
                            <option value="dissolve" ${clip.transition == 'dissolve' ? 'selected' : ''}>Crossfade</option>
                            <option value="whipleft" ${clip.transition == 'whipleft' ? 'selected' : ''}>Whip Left</option>
                            <option value="whipright" ${clip.transition == 'whipright' ? 'selected' : ''}>Whip Right</option>
                            <option value="zoomin" ${clip.transition == 'zoomin' ? 'selected' : ''}>Zoom In</option>
                            <option value="slideleft" ${clip.transition == 'slideleft' ? 'selected' : ''}>Slide Left</option>
                            <option value="fade" ${clip.transition == 'fade' ? 'selected' : ''}>Dip to Black</option>
                        </select>
                    </div>
                    <button class="btn-icon-danger" onclick="removeClip(${index})">✕</button>
                </div>
            `;
            list.appendChild(card);
        });
    };

    window.updateClipParam = function(index, param, value) {
        if (manualClipsSequence[index]) {
            manualClipsSequence[index][param] = parseFloat(value) || value;
        }
    };

    window.removeClip = function(index) {
        manualClipsSequence.splice(index, 1);
        renderManualTimeline();
    };

    addClipBtn.addEventListener("click", () => {
        manualClipsSequence.push({
            clip_id: manualClipsSequence.length + 1,
            video_path: uploadedFiles.length ? uploadedFiles[0].name : "sample.mp4",
            filename: uploadedFiles.length ? uploadedFiles[0].name : "Sample Video",
            src_start: 0.0,
            src_end: 5.0,
            speed_ramp: 1.0,
            transition: "dissolve",
            speed_kmh: 65,
            lean_angle_deg: 20
        });
        renderManualTimeline();
    });
});
