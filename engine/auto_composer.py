import numpy as np
from engine.ml_analyzer import MLVideoAnalyzer

class AutoComposer:
    """CapCut & Filmora Style Intelligent Hybrid Scene Composer & Precision Budget Engine."""

    def __init__(self, style_preset="adrenaline", resolution="1080p", aspect_ratio="16:9"):
        self.preset = style_preset
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio

    def build_edit_plan(self, highlights, audio_beats, target_duration="auto", total_raw_duration=60.0):
        plan = AutoComposer.create_edit_plan(highlights, audio_beats, preset=self.preset, target_duration=target_duration, total_raw_duration=total_raw_duration)
        return plan.get("clips", [])

    @staticmethod
    def create_edit_plan(highlights, audio_beats, preset="adrenaline", target_duration="auto", total_raw_duration=60.0):
        """Builds precision hybrid edit plan dynamically alternating between Normal Riding & Cinematic Peaks."""

        beats = audio_beats.get("beats", [])
        bpm = audio_beats.get("bpm", 128.0)

        # 1. Determine Target Output Duration Budget (T_target)
        raw_dur = max(10.0, float(total_raw_duration))
        if target_duration == "full":
            t_target = raw_dur
        elif target_duration == "vlog":
            t_target = max(15.0, raw_dur * 0.5)
        elif target_duration == "highlights":
            t_target = max(10.0, raw_dur * 0.35)
        elif target_duration == "reel":
            t_target = min(90.0, max(15.0, raw_dur * 0.1))
        elif target_duration == "placeholder":
            t_target = min(120.0, raw_dur * 0.5)
        else:
            try:
                t_target = max(5.0, float(target_duration))
            except Exception:
                t_target = min(120.0, raw_dur * 0.5)

        if not highlights:
            highlights = [{
                "video_path": "sample_media/sample_bike_ride_1.mp4",
                "start": 0.0,
                "end": raw_dur,
                "duration": raw_dur,
                "score": 0.8,
                "speed_kmh": 65,
                "lean_angle_deg": 22
            }]

        num_clips = max(1, min(len(highlights), max(4, int(t_target / 3.0))))
        selected_hl = highlights[:num_clips]

        scores = [max(0.1, h.get("score", 0.5)) for h in selected_hl]
        score_sum = sum(scores)
        
        timeline_clips = []
        current_output_time = 0.0
        cinematic_scenes_count = 0
        normal_scenes_count = 0

        for idx, hl in enumerate(selected_hl):
            if current_output_time >= t_target:
                break

            remaining_target = t_target - current_output_time
            weight = scores[idx] / score_sum
            allocated_clip_output = max(2.0, min(remaining_target, t_target * weight))

            speed_kmh = hl.get("speed_kmh", 60)
            lean_angle = hl.get("lean_angle_deg", 18)
            motion_score = hl.get("score", 0.5)

            # ML Intelligent Hybrid Scene Classification (Normal vs Cinematic)
            scene_class = MLVideoAnalyzer.classify_scene_mode(speed_kmh, lean_angle, motion_score)
            
            if scene_class["mode"] == "cinematic":
                cinematic_scenes_count += 1
            else:
                normal_scenes_count += 1

            speed_ramp = scene_class["speed_ramp"]
            transition = scene_class["transition"]
            engine_vol = scene_class["engine_vol"]
            music_vol = scene_class["music_vol"]

            # Exact Speed Ramp Allocation Equation: T_source_trim = T_allocated_output * speed_ramp
            needed_source_duration = allocated_clip_output * speed_ramp
            src_start = hl.get("start", 0.0)
            src_end = src_start + needed_source_duration

            # AI Beat-Synced Snap
            if beats:
                beats_arr = np.array(beats)
                closest_beat_idx = (np.abs(beats_arr - (current_output_time + allocated_clip_output))).argmin()
                snapped_output_end = float(beats_arr[closest_beat_idx])
                if snapped_output_end > current_output_time + 1.0:
                    allocated_clip_output = snapped_output_end - current_output_time
                    needed_source_duration = allocated_clip_output * speed_ramp
                    src_end = src_start + needed_source_duration

            timeline_clips.append({
                "clip_id": idx + 1,
                "video_path": hl["video_path"],
                "filename": hl.get("filename", f"Clip {idx+1}"),
                "src_start": round(src_start, 2),
                "src_end": round(src_end, 2),
                "speed_ramp": speed_ramp,
                "transition": transition,
                "scene_mode": scene_class["mode"],
                "scene_label": scene_class["label"],
                "engine_vol": engine_vol,
                "music_vol": music_vol,
                "speed_kmh": speed_kmh,
                "lean_angle_deg": lean_angle,
                "output_duration": round(allocated_clip_output, 2)
            })

            current_output_time += allocated_clip_output

        return {
            "preset": preset,
            "target_duration_sec": round(t_target, 1),
            "planned_duration_sec": round(current_output_time, 1),
            "cinematic_scenes": cinematic_scenes_count,
            "normal_scenes": normal_scenes_count,
            "hybrid_breakdown": f"Hybrid Editing: {normal_scenes_count} Normal Ride Scenes / {cinematic_scenes_count} Cinematic Slow-Mo Peaks",
            "bpm": bpm,
            "clips": timeline_clips
        }
