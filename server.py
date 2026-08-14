import os
import uuid
import threading
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

from setup_ffmpeg import ensure_ffmpeg
from engine import VideoAnalyzer, BeatDetector, AutoComposer, FFmpegRenderer
from sample_media.generate_samples import generate_synthwave_sample_beat, generate_sample_bike_video

app = FastAPI(title="Auto-Edit Bike Video Studio API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_media")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(SAMPLE_DIR, exist_ok=True)

# Ensure FFmpeg is present
FFMPEG_EXE, FFPROBE_EXE = ensure_ffmpeg()

# Active Jobs state store
jobs_db = {}

# Ensure sample files exist
SAMPLE_BEAT = os.path.join(SAMPLE_DIR, "synthwave_beat.wav")
SAMPLE_VIDEO = os.path.join(SAMPLE_DIR, "sample_bike_ride_1.mp4")

if not os.path.exists(SAMPLE_BEAT):
    generate_synthwave_sample_beat(SAMPLE_BEAT)
if not os.path.exists(SAMPLE_VIDEO):
    generate_sample_bike_video(SAMPLE_VIDEO)

def process_render_job(job_id: str, video_paths: List[str], music_path: str, preset: str, resolution: str, aspect_ratio: str, lut_preset: str, show_hud: bool):
    """Background rendering worker function."""
    try:
        jobs_db[job_id]["status"] = "processing"
        jobs_db[job_id]["progress"] = 10.0
        jobs_db[job_id]["status_message"] = "Analyzing optical flow & motion score..."

        analyzer = VideoAnalyzer(ffprobe_path=FFPROBE_EXE)
        all_highlights = []
        
        for idx, v_path in enumerate(video_paths):
            highlights = analyzer.analyze_motion_and_highlights(v_path)
            all_highlights.extend(highlights)
            pct = 10.0 + (idx + 1) / len(video_paths) * 20.0
            jobs_db[job_id]["progress"] = round(pct, 1)

        jobs_db[job_id]["status_message"] = "Extracting music beat markers & tempo BPM..."
        jobs_db[job_id]["progress"] = 35.0
        
        beat_detector = BeatDetector(ffmpeg_path=FFMPEG_EXE)
        audio_info = beat_detector.analyze_beats(music_path, temp_wav_dir=os.path.join(UPLOADS_DIR, job_id))

        jobs_db[job_id]["status_message"] = "Building edit graph & timing speed ramps..."
        jobs_db[job_id]["progress"] = 50.0

        composer = AutoComposer(style_preset=preset, resolution=resolution, aspect_ratio=aspect_ratio)
        edit_plan = composer.create_edit_plan(all_highlights, audio_info, target_duration=min(45.0, audio_info["duration"]))

        output_filename = f"cinematic_bike_edit_{job_id[:8]}.mp4"
        output_filepath = os.path.join(EXPORTS_DIR, output_filename)

        jobs_db[job_id]["status_message"] = f"Executing FFmpeg filter graph ({resolution.upper()} 60FPS)..."
        
        def update_progress(pct, msg):
            jobs_db[job_id]["progress"] = round(50.0 + (pct * 0.48), 1)
            jobs_db[job_id]["status_message"] = msg

        renderer = FFmpegRenderer(ffmpeg_path=FFMPEG_EXE)
        success = renderer.render_edit(edit_plan, music_path, output_filepath, lut_preset=lut_preset, show_hud=show_hud, progress_callback=update_progress)

        if success:
            jobs_db[job_id]["status"] = "completed"
            jobs_db[job_id]["progress"] = 100.0
            jobs_db[job_id]["status_message"] = "Render Complete!"
            jobs_db[job_id]["output_url"] = f"/exports/{output_filename}"
        else:
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = "FFmpeg encoding error"

    except Exception as e:
        print(f"[Job Error] Job {job_id} failed: {e}")
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)


@app.post("/api/render")
async def start_render(
    videos: Optional[List[UploadFile]] = File(None),
    music: Optional[UploadFile] = File(None),
    preset: str = Form("adrenaline"),
    resolution: str = Form("1080p"),
    aspect_ratio: str = Form("16:9"),
    lut_preset: str = Form("teal_orange"),
    show_hud: bool = Form(True)
):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOADS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    saved_video_paths = []
    
    if videos and len(videos) > 0 and videos[0].filename != "":
        for v in videos:
            v_path = os.path.join(job_dir, v.filename)
            with open(v_path, "wb") as f:
                shutil.copyfileobj(v.file, f)
            saved_video_paths.append(v_path)
    else:
        # Fallback to built-in sample bike ride video
        saved_video_paths.append(SAMPLE_VIDEO)

    if music and music.filename != "":
        music_path = os.path.join(job_dir, music.filename)
        with open(music_path, "wb") as f:
            shutil.copyfileobj(music.file, f)
    else:
        music_path = SAMPLE_BEAT

    jobs_db[job_id] = {
        "id": job_id,
        "status": "queued",
        "progress": 0.0,
        "status_message": "Queued for processing...",
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "output_url": None,
        "error": None
    }

    # Start background processing thread
    thread = threading.Thread(
        target=process_render_job,
        args=(job_id, saved_video_paths, music_path, preset, resolution, aspect_ratio, lut_preset, show_hud)
    )
    thread.start()

    return {"job_id": job_id, "status": "queued"}


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs_db:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    return jobs_db[job_id]


# Serve exports directory for video downloading/playing
app.mount("/exports", StaticFiles(directory=EXPORTS_DIR), name="exports")

# Serve Web UI files
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")

if __name__ == "__main__":
    print(f"\n========================================================")
    print(f" MOTO-EDIT STUDIO PRO SERVER RUNNING AT: http://localhost:8000")
    print(f"========================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
