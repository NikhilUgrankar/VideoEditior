import os
import subprocess
import json
import cv2
import numpy as np

class VideoAnalyzer:
    def __init__(self, ffprobe_path="ffprobe"):
        self.ffprobe_path = ffprobe_path

    def get_metadata(self, video_path):
        """Extract video metadata using ffprobe and OpenCV fallback."""
        meta = {
            "path": video_path,
            "filename": os.path.basename(video_path),
            "width": 1920,
            "height": 1080,
            "fps": 60.0,
            "duration": 0.0,
            "total_frames": 0,
            "has_audio": False,
            "codec": "unknown"
        }
        
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout:
                info = json.loads(res.stdout)
                streams = info.get("streams", [])
                format_info = info.get("format", {})
                
                meta["duration"] = float(format_info.get("duration", 0.0))
                
                for s in streams:
                    if s.get("codec_type") == "video":
                        meta["width"] = int(s.get("width", 1920))
                        meta["height"] = int(s.get("height", 1080))
                        meta["codec"] = s.get("codec_name", "h264")
                        fps_str = s.get("avg_frame_rate", "60/1")
                        if "/" in fps_str:
                            num, den = fps_str.split("/")
                            meta["fps"] = float(num) / float(den) if float(den) > 0 else 60.0
                        else:
                            meta["fps"] = float(fps_str)
                    elif s.get("codec_type") == "audio":
                        meta["has_audio"] = True
        except Exception as e:
            print(f"[VideoAnalyzer Error] FFprobe metadata failed for {video_path}: {e}")

        # OpenCV fallback for duration/fps if ffprobe fails or duration is 0
        if meta["duration"] <= 0:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS) or 60.0
                frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
                meta["fps"] = fps
                meta["total_frames"] = int(frames)
                meta["duration"] = frames / fps if fps > 0 else 0
                meta["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
                meta["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
                cap.release()

        return meta

    def analyze_motion_and_highlights(self, video_path, sample_fps=2):
        """
        Samples video frames to generate motion scores over time.
        Returns candidate highlight segments with start, end, and excitement score.
        """
        meta = self.get_metadata(video_path)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        fps = meta["fps"]
        duration = meta["duration"]
        if duration <= 0:
            cap.release()
            return []

        step_frames = max(1, int(fps / sample_fps))
        scores = []
        timestamps = []
        
        prev_gray = None
        current_frame = 0

        while cap.isOpened():
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize frame for ultra-fast motion estimation
            small_frame = cv2.resize(frame, (320, 180))
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            
            if prev_gray is not None:
                # Frame difference motion magnitude
                diff = cv2.absdiff(gray, prev_gray)
                motion_score = float(np.mean(diff))
                
                # Enhance score with standard deviation to catch directional motion / curves
                std_score = float(np.std(diff))
                combined_score = motion_score * 0.7 + std_score * 0.3
                
                time_sec = current_frame / fps
                scores.append(combined_score)
                timestamps.append(time_sec)

            prev_gray = gray
            current_frame += step_frames
            if current_frame >= meta["duration"] * fps:
                break

        cap.release()

        if not scores:
            # Fallback segment if analysis yields no frames
            return [{
                "video_path": video_path,
                "start": 0.0,
                "end": min(10.0, duration),
                "score": 1.0,
                "duration": min(10.0, duration)
            }]

        # Normalize scores to 0-1 range
        max_s = max(scores) if max(scores) > 0 else 1.0
        norm_scores = [s / max_s for s in scores]

        # Extract continuous highlight clips (window of 3 to 10 seconds with high score)
        window_size = int(4 * sample_fps) # 4 second window
        segments = []

        for i in range(0, len(norm_scores) - window_size, int(sample_fps * 2)):
            window = norm_scores[i:i + window_size]
            avg_score = float(np.mean(window))
            start_t = timestamps[i]
            end_t = timestamps[min(i + window_size, len(timestamps) - 1)]

            segments.append({
                "video_path": video_path,
                "start": round(start_t, 2),
                "end": round(end_t, 2),
                "duration": round(end_t - start_t, 2),
                "score": round(avg_score, 3)
            })

        # Sort segments by highest action/motion excitement score
        segments.sort(key=lambda x: x["score"], reverse=True)
        return segments
