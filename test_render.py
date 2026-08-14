import os
import sys
from setup_ffmpeg import ensure_ffmpeg
from engine import VideoAnalyzer, BeatDetector, AutoComposer, FFmpegRenderer
from sample_media.generate_samples import generate_synthwave_sample_beat, generate_sample_bike_video

def run_test():
    print("=== Auto-Edit Bike Video Studio End-to-End Test ===")
    
    ffmpeg_exe, ffprobe_exe = ensure_ffmpeg()
    print(f"FFmpeg binary: {ffmpeg_exe}")
    print(f"FFprobe binary: {ffprobe_exe}")

    sample_audio = os.path.join("sample_media", "synthwave_beat.wav")
    sample_video = os.path.join("sample_media", "sample_bike_ride_1.mp4")
    
    if not os.path.exists(sample_audio):
        generate_synthwave_sample_beat(sample_audio, duration_sec=20)
    if not os.path.exists(sample_video):
        generate_sample_bike_video(sample_video, duration_sec=10)

    print("\n1. Analyzing Video Motion Energy...")
    analyzer = VideoAnalyzer(ffprobe_path=ffprobe_exe)
    highlights = analyzer.analyze_motion_and_highlights(sample_video)
    print(f"Detected {len(highlights)} highlight segments: {highlights[:2]}")

    print("\n2. Analyzing Audio Beat Track...")
    beat_detector = BeatDetector(ffmpeg_path=ffmpeg_exe)
    audio_info = beat_detector.analyze_beats(sample_audio)
    print(f"Audio BPM: {audio_info['bpm']}, Total Beats: {len(audio_info['beats'])}")

    print("\n3. Building Edit Plan (Adrenaline Preset)...")
    composer = AutoComposer(style_preset="adrenaline", resolution="1080p", aspect_ratio="16:9")
    edit_plan = composer.create_edit_plan(highlights, audio_info, target_duration=10.0)
    print(f"Generated plan with {len(edit_plan['clips'])} clip transitions")

    print("\n4. Rendering Final Video with FFmpeg...")
    renderer = FFmpegRenderer(ffmpeg_path=ffmpeg_exe)
    out_video = os.path.join("exports", "test_cinematic_edit.mp4")
    
    def log_pct(pct, msg):
        print(f"   [{pct}%] {msg}")

    success = renderer.render_edit(edit_plan, sample_audio, out_video, lut_preset="teal_orange", show_hud=False, progress_callback=log_pct)
    
    if success and os.path.exists(out_video):
        size_mb = os.path.getsize(out_video) / (1024 * 1024)
        print(f"\nSUCCESS! Rendered output video to {out_video} ({size_mb:.2f} MB)")
    else:
        print("\nFAILED to render video.")

if __name__ == "__main__":
    run_test()
