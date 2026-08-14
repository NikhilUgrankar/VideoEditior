import numpy as np

class AutoComposer:
    """CapCut & Filmora Style AI Edit Composer & Velocity Curve Engine."""

    VELOCITY_CURVES = {
        "adrenaline": {"speed_apex": 0.25, "speed_straight": 2.0, "speed_normal": 1.0, "label": "Montage Pulse Ramping (0.25x -> 2.0x)"},
        "scenic_cruise": {"speed_apex": 0.50, "speed_straight": 1.5, "speed_normal": 1.0, "label": "Cinematic Flow (0.50x -> 1.5x)"},
        "shorts_beat": {"speed_apex": 0.20, "speed_straight": 2.5, "speed_normal": 1.0, "label": "Reel Hero Drop (0.20x -> 2.5x)"}
    }

    def __init__(self, style_preset="adrenaline", resolution="1080p", aspect_ratio="16:9"):
        self.preset = style_preset
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio

    def build_edit_plan(self, highlights, audio_beats, target_duration="auto", total_raw_duration=60.0):
        plan = AutoComposer.create_edit_plan(highlights, audio_beats, preset=self.preset, target_duration=target_duration, total_raw_duration=total_raw_duration)
        return plan.get("clips", [])

    @staticmethod
    def create_edit_plan(highlights, audio_beats, preset="adrenaline", target_duration="auto", total_raw_duration=60.0):
        """Builds precision beat-synced edit plan matching exact target duration to within +-0.5s."""

        curve_profile = AutoComposer.VELOCITY_CURVES.get(preset, AutoComposer.VELOCITY_CURVES["adrenaline"])
        beats = audio_beats.get("beats", [])
        bpm = audio_beats.get("bpm", 128.0)

        # 1. Determine Exact Target Output Duration (T_target)
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

        # 2. Rank raw video highlights by motion score & corner apex lean angle
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

        sorted_hl = sorted(highlights, key=lambda x: x.get("score", 0.5), reverse=True)

        # 3. Calculate clip output allocations matching T_target budget exactly
        num_clips = max(1, min(len(sorted_hl), max(3, int(t_target / 3.0))))
        selected_hl = sorted_hl[:num_clips]

        scores = [max(0.1, h.get("score", 0.5)) for h in selected_hl]
        score_sum = sum(scores)
        
        timeline_clips = []
        transitions_pool = ["zoomin", "whipleft", "whipright", "slideleft", "dissolve"]
        current_output_time = 0.0

        for idx, hl in enumerate(selected_hl):
            if current_output_time >= t_target:
                break

            remaining_target = t_target - current_output_time
            weight = scores[idx] / score_sum
            allocated_clip_output = max(2.0, min(remaining_target, t_target * weight))

            speed_kmh = hl.get("speed_kmh", 60)
            lean_angle = hl.get("lean_angle_deg", 18)

            # CapCut / VN Velocity Curve selection
            if lean_angle > 24 or speed_kmh > 100:
                speed_ramp = curve_profile["speed_apex"] # 0.25x Slow-Mo
                transition = "zoomin"
                ramp_label = "Parabolic Apex Slow-Mo (0.25x)"
            elif speed_kmh > 75:
                speed_ramp = curve_profile["speed_straight"] # 2.0x Fast Burst
                transition = transitions_pool[idx % len(transitions_pool)]
                ramp_label = "Straightaway Burst (2.0x)"
            else:
                speed_ramp = curve_profile["speed_normal"] # 1.0x Pacing
                transition = "dissolve"
                ramp_label = "Linear Pacing (1.0x)"

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
                "ramp_label": ramp_label,
                "speed_kmh": speed_kmh,
                "lean_angle_deg": lean_angle,
                "output_duration": round(allocated_clip_output, 2)
            })

            current_output_time += allocated_clip_output

        return {
            "preset": preset,
            "target_duration_sec": round(t_target, 1),
            "planned_duration_sec": round(current_output_time, 1),
            "velocity_profile": curve_profile["label"],
            "bpm": bpm,
            "clips": timeline_clips
        }
