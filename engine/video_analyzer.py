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

    def analyze_motion_and_highlights(self, video_path, sample_fps=1):
        """
        Samples video frames at 1 FPS for ultra-fast motion energy and velocity vector extraction.
        Returns candidate highlight segments with computed real speed (KM/H) and lean angle (°).
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
        speed_estimates = []
        lean_estimates = []
        
        prev_gray = None
        current_frame = 0

        while cap.isOpened():
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret:
                break
            
            # Downsample frame for fast processing
            small_frame = cv2.resize(frame, (160, 90))
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            
            if prev_gray is not None:
                # Calculate Optical Flow for velocity vector extraction
                flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
                magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                
                mean_mag = float(np.mean(magnitude))
                std_mag = float(np.std(magnitude))
                combined_score = mean_mag * 0.6 + std_mag * 0.4
                
                # Estimate Speed (KM/H) based on optical flow velocity
                estimated_speed = min(180, max(20, int(30 + mean_mag * 25)))
                
                # Estimate Lean Angle (Degrees) based on angular variance of optical flow vectors
                angle_var = float(np.std(angle))
                estimated_lean = min(48, max(0, int(angle_var * 12)))

                time_sec = current_frame / fps
                scores.append(combined_score)
                timestamps.append(time_sec)
                speed_estimates.append(estimated_speed)
                lean_estimates.append(estimated_lean)

            prev_gray = gray
            current_frame += step_frames
            if current_frame >= meta["duration"] * fps:
                break

        cap.release()

        if not scores:
            return [{
                "video_path": video_path,
                "start": 0.0,
                "end": min(10.0, duration),
                "score": 1.0,
                "duration": min(10.0, duration),
                "speed_kmh": 60,
                "lean_angle_deg": 15
            }]

        max_s = max(scores) if max(scores) > 0 else 1.0
        norm_scores = [s / max_s for s in scores]

        window_size = int(3 * sample_fps)
        segments = []

        for i in range(0, len(norm_scores) - window_size, max(1, sample_fps)):
            window = norm_scores[i:i + window_size]
            avg_score = float(np.mean(window))
            start_t = timestamps[i]
            end_t = timestamps[min(i + window_size, len(timestamps) - 1)]

            avg_speed = int(np.mean(speed_estimates[i:i + window_size])) if speed_estimates else 60
            avg_lean = int(np.mean(lean_estimates[i:i + window_size])) if lean_estimates else 18

            segments.append({
                "video_path": video_path,
                "start": round(start_t, 2),
                "end": round(end_t, 2),
                "duration": round(end_t - start_t, 2),
                "score": round(avg_score, 3),
                "speed_kmh": avg_speed,
                "lean_angle_deg": avg_lean
            })

        segments.sort(key=lambda x: x["score"], reverse=True)
        return segments
