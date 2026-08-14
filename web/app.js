let lastCopilotData = null;

// Apply all AI Co-Pilot suggestions in 1 click
function applyAllAISuggestions() {
    if (!lastCopilotData) return;
    const c = lastCopilotData;

    // 1. Apply Preset Theme
    if (c.preset_theme && c.preset_theme.suggested) {
        selectedPreset = c.preset_theme.suggested;
        document.querySelectorAll(".preset-card").forEach(card => {
            card.classList.toggle("active", card.dataset.preset === selectedPreset);
        });
    }

    // 2. Apply Color LUT Profile
    if (c.color_lut && c.color_lut.suggested) {
        selectedLUT = c.color_lut.suggested;
        const lutSelect = document.getElementById("lut-select");
        if (lutSelect) lutSelect.value = selectedLUT;
        document.querySelectorAll(".lut-swatch-card").forEach(card => {
            const isMatch = card.getAttribute("onclick") && card.getAttribute("onclick").includes(selectedLUT);
            card.classList.toggle("active", !!isMatch);
        });
    }

    // 3. Apply Dual Audio Mix Ratio
    if (c.audio_mix) {
        const engineVolRange = document.getElementById("engine-vol-range");
        const engineVolVal = document.getElementById("engine-vol-val");
        const musicVolRange = document.getElementById("music-vol-range");
        const musicVolVal = document.getElementById("music-vol-val");

        if (engineVolRange) {
            engineVolRange.value = c.audio_mix.engine_vol;
            if (engineVolVal) engineVolVal.innerText = `${Math.round(c.audio_mix.engine_vol * 100)}%`;
        }
        if (musicVolRange) {
            musicVolRange.value = c.audio_mix.music_vol;
            if (musicVolVal) musicVolVal.innerText = `${Math.round(c.audio_mix.music_vol * 100)}%`;
        }
    }

    // 4. Apply Target Duration
    if (c.target_duration && c.target_duration.suggested) {
        const targetDurationSelect = document.getElementById("target-duration-select");
        if (targetDurationSelect) {
            targetDurationSelect.value = c.target_duration.suggested;
        }
    }

    // Visual Feedback Toast
    alert("✨ AI Co-Pilot Suggestions Applied! Theme, Color LUT, Audio Mix, and Edit Duration configured.");
}

// Global Tab Switcher
function switchTab(tabName) {
    const tabs = ["auto", "manual", "music", "lut"];
    tabs.forEach(t => {
        const view = document.getElementById(`view-${t}`);
        const btn = document.getElementById(`tab-${t}-btn`);
        if (view) view.hidden = (t !== tabName);
        if (btn) btn.classList.toggle("active", t === tabName);
    });

    if (tabName === "manual") {
        renderManualTimeline();
    } else if (tabName === "music") {
        loadCreatorMusicCatalog();
    }
}

// Multi-Source Royalty Free Music Catalog Search
async function loadCreatorMusicCatalog(query = "", genre = "", provider = currentMusicProvider) {
    const grid = document.getElementById("music-tracks-grid");
    if (!grid) return;
    
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:30px; color:var(--text-secondary);">
        Fetching ${provider.toUpperCase()} music catalog...
    </div>`;

    try {
        const res = await fetch(`/api/music/search?q=${encodeURIComponent(query)}&genre=${encodeURIComponent(genre)}&provider=${provider}`);
        const data = await res.json();
        
        grid.innerHTML = "";
        const tracks = data.tracks || [];

        if (tracks.length === 0) {
            grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:30px; color:var(--text-secondary);">
                No tracks found. Try selecting another genre or provider.
            </div>`;
            return;
        }

        tracks.forEach(track => {
            const card = document.createElement("div");
            card.className = "track-card";
            const safeTitle = (track.title || "Track").replace(/'/g, "\\'");
            const safeArtist = (track.artist || "Artist").replace(/'/g, "\\'");
            const safeGenre = (track.genre || "Music").replace(/'/g, "\\'");

            card.innerHTML = `
                <div class="track-info">
                    <button class="btn-play-icon" onclick="playTrackPreview('${track.stream_url}', this)">▶</button>
                    <div class="track-meta">
                        <h4>${track.title}</h4>
                        <p>${track.artist} • ${track.duration} | <span class="badge-genre">${track.provider || 'Jamendo CC'}</span></p>
                    </div>
                </div>
                <button class="btn-secondary btn-small" onclick="selectCreatorTrack('${track.id}', '${safeTitle}', '${safeArtist}', '${safeGenre}')">⚡ Use Track</button>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        console.error("Music fetch error:", e);
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:30px; color:var(--text-secondary);">
            Catalog ready. Select a track below to stream audio.
        </div>`;
    }
}

function selectMusicProvider(provider) {
    currentMusicProvider = provider;
    document.querySelectorAll(".provider-btn").forEach(b => b.classList.remove("active"));
    const activeBtn = document.getElementById(`provider-${provider}-btn`);
    if (activeBtn) activeBtn.classList.add("active");
    loadCreatorMusicCatalog("", "", provider);
}

function filterGenre(genre) {
    document.querySelectorAll(".genre-chip").forEach(c => c.classList.remove("active"));
    if (window.event && window.event.target) {
        window.event.target.classList.add("active");
    }
    loadCreatorMusicCatalog("", genre);
}

function playTrackPreview(url, btn) {
    if (!url) return;
    const globalPlayer = document.getElementById("global-music-player");
    if (!globalPlayer) return;
    
    if (!audioCtx) {
        try {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyserNode = audioCtx.createAnalyser();
            const source = audioCtx.createMediaElementSource(globalPlayer);
            source.connect(analyserNode);
            analyserNode.connect(audioCtx.destination);
            drawWaveform();
        } catch (e) {
            console.warn("AudioContext setup:", e);
        }
    }

    if (currentlyPlayingTrackUrl === url && !globalPlayer.paused) {
        globalPlayer.pause();
        if (btn) btn.innerText = "▶";
        currentlyPlayingTrackUrl = null;
    } else {
        document.querySelectorAll(".btn-play-icon").forEach(b => b.innerText = "▶");
        globalPlayer.src = url;
        globalPlayer.play();
        if (btn) btn.innerText = "⏸";
        currentlyPlayingTrackUrl = url;
    }
}

function drawWaveform() {
    const canvas = document.getElementById("waveform-canvas");
    if (!canvas || !analyserNode) return;
    const ctx = canvas.getContext("2d");
    const bufferLength = analyserNode.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
        animFrameId = requestAnimationFrame(draw);
        analyserNode.getByteFrequencyData(dataArray);

        ctx.fillStyle = "rgba(11, 15, 25, 0.4)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / bufferLength) * 2.5;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const barHeight = (dataArray[i] / 255) * canvas.height;
            const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
            gradient.addColorStop(0, "#0284c7");
            gradient.addColorStop(1, "#0d9488");

            ctx.fillStyle = gradient;
            ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            x += barWidth + 1;
        }
    }
    draw();
}

function selectCreatorTrack(id, title, artist, genre) {
    selectedMusicTrack = { id, title, artist, genre };
    const activeTrackTitle = document.getElementById("active-track-title");
    const activeTrackArtist = document.getElementById("active-track-artist");
    const activeGenreBadge = document.getElementById("active-genre-badge");

    if (activeTrackTitle) activeTrackTitle.innerText = title;
    if (activeTrackArtist) activeTrackArtist.innerText = artist;
    if (activeGenreBadge) activeGenreBadge.innerText = genre;
    switchTab('auto');
}

// Color LUT Selector
function selectLUT(lutKey, element) {
    selectedLUT = lutKey;
    const lutSelect = document.getElementById("lut-select");
    if (lutSelect) lutSelect.value = lutKey;

    document.querySelectorAll(".lut-swatch-card").forEach(c => c.classList.remove("active"));
    if (element) {
        element.classList.add("active");
    }
    switchTab('auto');
}

// Interactive Manual Timeline Editor Renderer
function renderManualTimeline() {
    const list = document.getElementById("timeline-sequence-list");
    if (!list) return;
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
}

function updateClipParam(index, param, value) {
    if (manualClipsSequence[index]) {
        manualClipsSequence[index][param] = parseFloat(value) || value;
    }
}

function removeClip(index) {
    manualClipsSequence.splice(index, 1);
    renderManualTimeline();
}

// App Initialization when DOM Ready
document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("video-dropzone");
    const videoInput = document.getElementById("video-file-input");
    const videoList = document.getElementById("video-list");
    
    const rawDurationBadge = document.getElementById("raw-total-duration-badge");
    const targetDurationSelect = document.getElementById("target-duration-select");
    const customDurationBox = document.getElementById("custom-duration-input-box");
    const customDurationSeconds = document.getElementById("custom-duration-seconds");

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
    const musicSearchBtn = document.getElementById("music-search-btn");
    const musicSearchInput = document.getElementById("music-search-input");

    const progressModal = document.getElementById("progress-modal");
    const progressFill = document.getElementById("modal-progress-fill");
    const statusText = document.getElementById("modal-status-text");
    const pctText = document.getElementById("modal-percentage-text");
    
    const placeholderPlayer = document.getElementById("placeholder-player");
    const outputVideoPlayer = document.getElementById("output-video-player");
    const exportBar = document.getElementById("export-bar");
    const downloadLink = document.getElementById("download-link");
    const exportMetaText = document.getElementById("export-meta-text");

    // Load music catalog immediately on load
    loadCreatorMusicCatalog();

    // Custom Duration toggle handler
    if (targetDurationSelect && customDurationBox) {
        targetDurationSelect.addEventListener("change", (e) => {
            if (e.target.value === "custom") {
                customDurationBox.hidden = false;
                customDurationBox.style.display = "block";
            } else {
                customDurationBox.hidden = true;
                customDurationBox.style.display = "none";
            }
        });
    }

    // Audio Mix Volume Sliders
    if (engineVolRange && engineVolVal) {
        engineVolRange.addEventListener("input", (e) => {
            engineVolVal.innerText = `${Math.round(e.target.value * 100)}%`;
        });
    }

    if (musicVolRange && musicVolVal) {
        musicVolRange.addEventListener("input", (e) => {
            musicVolVal.innerText = `${Math.round(e.target.value * 100)}%`;
        });
    }

    // Dropzone handlers
    if (dropzone) {
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
    }

    if (videoInput) {
        videoInput.addEventListener("change", (e) => {
            if (e.target.files.length) {
                handleVideoFiles(e.target.files);
            }
        });
    }

    async function handleVideoFiles(files) {
        for (let file of files) {
            uploadedFiles.push(file);
        }
        renderVideoList();
        await analyzeUploadedFootage();
    }

    async function analyzeUploadedFootage() {
        if (uploadedFiles.length === 0) return;
        if (rawDurationBadge) rawDurationBadge.innerText = "Analyzing footage...";

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
                if (rawDurationBadge) rawDurationBadge.innerText = `Total Upload: ${data.total_raw_duration_formatted}`;

                const c = data.copilot;
                if (c) {
                    lastCopilotData = c;
                    
                    // Enable AI Apply button & update readout
                    const applyBtn = document.getElementById("apply-ai-btn");
                    const copilotRideType = document.getElementById("copilot-ride-type");
                    const aiPresetText = document.getElementById("ai-preset-text");
                    const aiLutText = document.getElementById("ai-lut-text");
                    const aiAudioText = document.getElementById("ai-audio-text");
                    const aiDurationText = document.getElementById("ai-duration-text");

                    if (applyBtn) applyBtn.disabled = false;
                    if (copilotRideType) copilotRideType.innerText = `AI Ride Classification: ${c.ride_type} (Peak ${c.max_speed_kmh} KM/H, ${c.max_lean_deg}° Lean)`;
                    if (aiPresetText) aiPresetText.innerText = c.preset_theme.suggested.toUpperCase();
                    if (aiLutText) aiLutText.innerText = c.color_lut.suggested.toUpperCase();
                    if (aiAudioText) aiAudioText.innerText = `${Math.round(c.audio_mix.engine_vol*100)}% Mic / ${Math.round(c.audio_mix.music_vol*100)}% Music`;
                    if (aiDurationText) aiDurationText.innerText = `${c.target_duration.suggested}s`;
                }

                const ai = data.ai_suggestions;
                if (ai && ai.smart_durations) {
                    const totalSec = ai.total_raw_sec;
                    
                    targetDurationSelect.innerHTML = `
                        <option value="${ai.smart_durations.full.value}" selected>${ai.smart_durations.full.label}</option>
                        <option value="${ai.smart_durations.vlog.value}">${ai.smart_durations.vlog.label}</option>
                        <option value="${ai.smart_durations.highlights.value}">${ai.smart_durations.highlights.label}</option>
                        <option value="${ai.smart_durations.reel.value}">${ai.smart_durations.reel.label}</option>
                        <option value="custom">⏱️ Custom Time Range (Use Range Slider / Type Seconds)</option>
                    `;

                    const customSlider = document.getElementById("custom-time-slider");
                    const customSecInput = document.getElementById("custom-duration-seconds");
                    const customReadout = document.getElementById("custom-slider-readout");

                    if (customSlider) {
                        customSlider.min = 5;
                        customSlider.max = Math.round(totalSec);
                        const defaultCustom = Math.round(totalSec * 0.5);
                        customSlider.value = defaultCustom;
                        if (customSecInput) customSecInput.value = defaultCustom;
                        if (customReadout) customReadout.innerText = formatDurationText(defaultCustom);
                    }

                    const activeGenreBadge = document.getElementById("active-genre-badge");
                    if (activeGenreBadge) activeGenreBadge.innerText = ai.match_badge || "AI Matched";
                }

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
            if (rawDurationBadge) rawDurationBadge.innerText = "Total Upload: Calculated";
        }
    }

    function formatDurationText(sec) {
        sec = parseFloat(sec) || 0;
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60);
        return m > 0 ? `${m}m ${s}s (${sec}s)` : `${s}s (${sec}s)`;
    }

    // Range Slider & Numeric Input Bidirectional Sync
    const customSlider = document.getElementById("custom-time-slider");
    const customSecInput = document.getElementById("custom-duration-seconds");
    const customReadout = document.getElementById("custom-slider-readout");

    if (customSlider) {
        customSlider.addEventListener("input", (e) => {
            const val = e.target.value;
            if (customSecInput) customSecInput.value = val;
            if (customReadout) customReadout.innerText = formatDurationText(val);
        });
    }

    if (customSecInput) {
        customSecInput.addEventListener("input", (e) => {
            const val = e.target.value;
            if (customSlider) customSlider.value = val;
            if (customReadout) customReadout.innerText = formatDurationText(val);
        });
    }

    function renderVideoList() {
        if (!videoList) return;
        videoList.innerHTML = "";
        uploadedFiles.forEach((file) => {
            const item = document.createElement("div");
            item.className = "media-item";
            item.innerHTML = `
                <span class="media-item-name">📹 ${file.name}</span>
                <span class="media-item-tag">${(file.size / (1024 * 1024)).toFixed(1)} MB</span>
            `;
            videoList.appendChild(item);
        });
    }

    // Custom Music File Upload
    if (customMusicInput) {
        customMusicInput.addEventListener("change", (e) => {
            if (e.target.files.length) {
                customMusicFile = e.target.files[0];
                if (customSongName) customSongName.innerText = customMusicFile.name;
                if (customSongBadge) customSongBadge.hidden = false;
                
                const activeTrackTitle = document.getElementById("active-track-title");
                const activeTrackArtist = document.getElementById("active-track-artist");
                const activeGenreBadge = document.getElementById("active-genre-badge");

                if (activeTrackTitle) activeTrackTitle.innerText = `🎵 Custom: ${customMusicFile.name}`;
                if (activeTrackArtist) activeTrackArtist.innerText = "Device Audio Upload";
                if (activeGenreBadge) activeGenreBadge.innerText = "Custom File";
            }
        });
    }

    // Preset Selection
    presetCards.forEach(card => {
        card.addEventListener("click", () => {
            presetCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            selectedPreset = card.dataset.preset;
        });
    });

    // LUT Select dropdown sync
    if (lutSelect) {
        lutSelect.addEventListener("change", (e) => {
            selectedLUT = e.target.value;
        });
    }

    // Music Search Button Listener
    if (musicSearchBtn && musicSearchInput) {
        musicSearchBtn.addEventListener("click", () => {
            loadCreatorMusicCatalog(musicSearchInput.value);
        });
    }

    // Render Actions
    if (renderBtn) renderBtn.addEventListener("click", () => triggerRender(false));
    if (renderManualBtn) renderManualBtn.addEventListener("click", () => triggerRender(true));

    async function triggerRender(isManualMode) {
        if (progressModal) progressModal.hidden = false;
        if (progressFill) progressFill.style.width = "5%";
        if (statusText) statusText.innerText = "Initializing ultrafast video engine...";
        if (pctText) pctText.innerText = "5%";

        const formData = new FormData();
        
        if (uploadedFiles.length > 0) {
            for (let f of uploadedFiles) {
                formData.append("videos", f);
            }
        }
        
        if (customMusicFile) {
            formData.append("music", customMusicFile);
        }

        // Custom Duration calculation
        let durationVal = targetDurationSelect ? targetDurationSelect.value : "full";
        if (durationVal === "custom" && customDurationSeconds) {
            durationVal = customDurationSeconds.value || "120";
        }

        formData.append("music_genre", selectedMusicTrack.id);
        formData.append("preset", selectedPreset);
        formData.append("target_duration", durationVal);
        formData.append("resolution", resolutionSelect ? resolutionSelect.value : "1080p");
        formData.append("aspect_ratio", aspectSelect ? aspectSelect.value : "16:9");
        formData.append("lut_preset", selectedLUT || (lutSelect ? lutSelect.value : "teal_orange"));
        formData.append("engine_vol", engineVolRange ? engineVolRange.value : 0.5);
        formData.append("music_vol", musicVolRange ? musicVolRange.value : 0.8);
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
            if (progressModal) progressModal.hidden = true;
        }
    }

    async function pollStatus(jobId) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${jobId}`);
                if (!res.ok) return;

                const data = await res.json();
                const currentProgress = Math.max(5, Math.min(100, data.progress || 5));
                
                if (progressFill) progressFill.style.width = `${currentProgress}%`;
                if (statusText) statusText.innerText = data.status_message || "Processing...";
                if (pctText) pctText.innerText = `${Math.round(currentProgress)}%`;

                if (data.status === "completed") {
                    clearInterval(interval);
                    if (progressModal) progressModal.hidden = true;
                    
                    if (placeholderPlayer) placeholderPlayer.hidden = true;
                    if (outputVideoPlayer) {
                        outputVideoPlayer.hidden = false;
                        outputVideoPlayer.src = data.output_url;
                        outputVideoPlayer.play();
                    }

                    if (exportBar) exportBar.hidden = false;
                    if (downloadLink) downloadLink.href = data.output_url;
                    if (exportMetaText) exportMetaText.innerText = `Rendered: ${data.resolution.toUpperCase()} 60FPS | ${data.aspect_ratio}`;
                    
                    switchTab('auto');
                } else if (data.status === "failed") {
                    clearInterval(interval);
                    if (progressModal) progressModal.hidden = true;
                    alert("Rendering Error: " + (data.error || "Unknown server error"));
                }
            } catch (e) {
                console.error("Polling error:", e);
            }
        }, 800);
    }

    if (addClipBtn) {
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
    }
});
