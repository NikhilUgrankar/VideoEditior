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
from sample_media.generate_samples import generate_audio_genre, generate_sample_bike_video

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
    generate_audio_genre(SAMPLE_BEAT, genre="synthwave")
if not os.path.exists(SAMPLE_VIDEO):
    generate_sample_bike_video(SAMPLE_VIDEO)

GENRE_MUSIC_MAP = {
    "sample": os.path.join(SAMPLE_DIR, "synthwave_beat.wav"),
    "rock": os.path.join(SAMPLE_DIR, "rock_beat.wav"),
    "lofi": os.path.join(SAMPLE_DIR, "lofi_beat.wav"),
    "cinematic": os.path.join(SAMPLE_DIR, "cinematic_beat.wav"),
    "edm": os.path.join(SAMPLE_DIR, "edm_beat.wav")
}

def process_render_job(job_id: str, video_paths: List[str], music_path: str, preset: str, resolution: str, aspect_ratio: str, lut_preset: str, show_hud: bool, target_duration: str = "auto", engine_vol: float = 0.5, music_vol: float = 0.8, custom_clips: Optional[list] = None):
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
        edit_plan = composer.create_edit_plan(all_highlights, audio_info, target_duration=target_duration, custom_clips=custom_clips)

        output_filename = f"cinematic_bike_edit_{job_id[:8]}.mp4"
        output_filepath = os.path.join(EXPORTS_DIR, output_filename)

        jobs_db[job_id]["status_message"] = f"Executing FFmpeg filter graph ({resolution.upper()} 60FPS)..."
        
        def update_progress(pct, msg):
            jobs_db[job_id]["progress"] = round(50.0 + (pct * 0.48), 1)
            jobs_db[job_id]["status_message"] = msg

        renderer = FFmpegRenderer(ffmpeg_path=FFMPEG_EXE)
        success = renderer.render_edit(edit_plan, music_path, output_filepath, lut_preset=lut_preset, show_hud=show_hud, engine_vol=engine_vol, music_vol=music_vol, progress_callback=update_progress)

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


@app.post("/api/analyze")
async def analyze_videos(videos: List[UploadFile] = File(default=[])):
    """Pre-analysis returning highlights, raw duration breakdown, and recommended audio tracks."""
    analyzer = VideoAnalyzer(ffprobe_path=FFPROBE_EXE)
    total_duration = 0.0
    video_count = 0
    all_highlights = []

    if videos and len(videos) > 0:
        for v in videos:
            if v.filename:
                temp_p = os.path.join(UPLOADS_DIR, f"temp_meta_{v.filename}")
                with open(temp_p, "wb") as f:
                    shutil.copyfileobj(v.file, f)
                meta = analyzer.get_metadata(temp_p)
                duration = meta.get("duration", 0.0)
                total_duration += duration
                video_count += 1
                
                # Get highlights for manual timeline editor
                hl = analyzer.analyze_motion_and_highlights(temp_p)
                for h in hl:
                    h["filename"] = v.filename
                all_highlights.extend(hl[:5]) # top 5 clips per video

                if os.path.exists(temp_p):
                    try:
                        os.remove(temp_p)
                    except Exception:
                        pass

    if total_duration <= 0:
        total_duration = 30.0

    formatted_time = f"{int(total_duration // 60)}m {int(total_duration % 60)}s" if total_duration >= 60 else f"{int(total_duration)}s"

    return {
        "video_count": video_count,
        "total_raw_duration_sec": round(total_duration, 1),
        "total_raw_duration_formatted": formatted_time,
        "highlights": all_highlights[:12],
        "recommended_music": [
            {"id": "sample", "name": "⚡ Synthwave Action Beat (128 BPM)"},
            {"id": "rock", "name": "🏍️ Heavy Moto Rock / Metal (140 BPM)"},
            {"id": "lofi", "name": "🎧 Highway Lo-Fi Chill (90 BPM)"},
            {"id": "cinematic", "name": "🌌 Cinematic Epic Ambient (110 BPM)"},
            {"id": "edm", "name": "💥 EDM Bass Drop (130 BPM)"}
        ]
    }


@app.post("/api/render")
async def start_render(
    videos: List[UploadFile] = File(default=[]),
    music: Optional[UploadFile] = File(default=None),
    music_genre: str = Form("sample"),
    preset: str = Form("adrenaline"),
    target_duration: str = Form("auto"),
    resolution: str = Form("1080p"),
    aspect_ratio: str = Form("16:9"),
    lut_preset: str = Form("teal_orange"),
    show_hud: bool = Form(False),
    engine_vol: float = Form(0.5),
    music_vol: float = Form(0.8),
    custom_timeline_json: Optional[str] = Form(None)
):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOADS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    saved_video_paths = []
    
    if videos and len(videos) > 0:
        for v in videos:
            if v.filename:
                v_path = os.path.join(job_dir, v.filename)
                with open(v_path, "wb") as f:
                    shutil.copyfileobj(v.file, f)
                saved_video_paths.append(v_path)
    
    if not saved_video_paths:
        saved_video_paths.append(SAMPLE_VIDEO)

    if music and music.filename:
        music_path = os.path.join(job_dir, music.filename)
        with open(music_path, "wb") as f:
            shutil.copyfileobj(music.file, f)
    else:
        music_path = GENRE_MUSIC_MAP.get(music_genre, GENRE_MUSIC_MAP["sample"])

    custom_clips = None
    if custom_timeline_json:
        try:
            custom_clips = json.loads(custom_timeline_json)
        except Exception:
            custom_clips = None

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

    thread = threading.Thread(
        target=process_render_job,
        args=(job_id, saved_video_paths, music_path, preset, resolution, aspect_ratio, lut_preset, show_hud, target_duration, engine_vol, music_vol, custom_clips)
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
