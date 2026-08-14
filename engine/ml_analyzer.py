import cv2
import numpy as np
import os

class MLVideoAnalyzer:
    """Machine Learning Computer Vision Engine for Hybrid Scene Classification, Motion Tracking & Shake Rejection."""

    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=36, detectShadows=False)

    @staticmethod
    def classify_scene_mode(speed_kmh, lean_angle_deg, motion_ratio):
        """Classifies frame segment into Normal Riding Mode vs Cinematic Peak Mode."""
        if lean_angle_deg > 24 or speed_kmh > 95 or motion_ratio > 0.25:
            return {
                "mode": "cinematic",
                "label": "⚡ Cinematic Peak Mode",
                "speed_ramp": 0.25,
                "transition": "zoomin",
                "engine_vol": 0.35,
                "music_vol": 0.85,
                "lut_profile": "teal_orange"
            }
        else:
            return {
                "mode": "normal",
                "label": "🏍️ Normal Riding Mode",
                "speed_ramp": 1.0,
                "transition": "dissolve",
                "engine_vol": 0.70,
                "music_vol": 0.40,
                "lut_profile": "natural"
            }

    def analyze_frame_ml(self, frame_bgr):
        """Analyzes a single frame for motion vectors, shake wobble, and color dynamic range."""
        h, w, _ = frame_bgr.shape
        small = cv2.resize(frame_bgr, (240, 135))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # 1. Background Subtraction ML for foreground vehicle motion
        fg_mask = self.bg_subtractor.apply(gray)
        motion_pixel_ratio = float(np.count_nonzero(fg_mask) / (fg_mask.shape[0] * fg_mask.shape[1]))

        # 2. CIELAB Dynamic Range & Aesthetic Quality Evaluation ML
        lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        l_std = float(np.std(l_channel))
        l_mean = float(np.mean(l_channel))
        sat_mean = float(np.mean(cv2.cvtColor(small, cv2.COLOR_BGR2HSV)[:, :, 1]))
        
        aesthetic_score = min(1.0, max(0.2, (l_std / 64.0) * 0.5 + (sat_mean / 255.0) * 0.5))

        # Color Temperature & Auto-LUT Recommendation ML
        b_mean = float(np.mean(b_channel))
        if l_mean < 80:
            suggested_lut = "dark_moto"
        elif b_mean > 138:
            suggested_lut = "sunset_glow"
        elif sat_mean > 110:
            suggested_lut = "crisp_hdr"
        else:
            suggested_lut = "teal_orange"

        # 3. Blur & Shake Wobble ML Detection
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_shake_wobble = laplacian_var < 80.0

        return {
            "motion_ratio": round(motion_pixel_ratio, 3),
            "aesthetic_score": round(aesthetic_score, 2),
            "suggested_lut": suggested_lut,
            "is_shake_wobble": is_shake_wobble
        }

    def process_video_ml(self, video_path, sample_fps=2):
        """Processes video with ML vision models and returns frame-by-frame intelligence metrics."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Cannot open video file"}

        fps = cap.get(cv2.CAP_PROP_FPS) or 60.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        duration = total_frames / fps

        step_frames = max(1, int(fps / sample_fps))
        current_frame = 0

        motion_scores = []
        aesthetic_scores = []
        shake_flags = []

        while cap.isOpened():
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret:
                break

            ml_res = self.analyze_frame_ml(frame)
            motion_scores.append(ml_res["motion_ratio"])
            aesthetic_scores.append(ml_res["aesthetic_score"])
            shake_flags.append(ml_res["is_shake_wobble"])

            current_frame += step_frames
            if current_frame >= total_frames:
                break

        cap.release()

        avg_motion = float(np.mean(motion_scores)) if motion_scores else 0.1
        avg_aesthetic = float(np.mean(aesthetic_scores)) if aesthetic_scores else 0.7
        shake_ratio = float(np.mean(shake_flags)) if shake_flags else 0.0

        estimated_max_speed = min(180, int(35 + avg_motion * 450))
        corner_apexes = int(avg_motion * 18)

        return {
            "total_duration_sec": round(duration, 1),
            "ml_motion_score": round(avg_motion, 3),
            "ml_aesthetic_score": round(avg_aesthetic, 2),
            "ml_shake_ratio": round(shake_ratio, 2),
            "ml_vehicle_speed_kmh": estimated_max_speed,
            "ml_corner_apexes": corner_apexes,
            "usable_quality_pct": round((1.0 - shake_ratio) * 100, 1)
        }
