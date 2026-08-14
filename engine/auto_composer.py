import math

class AutoComposer:
    """Builds an algorithmic timeline editing plan matching raw video clips to music beats."""

    def __init__(self, style_preset="adrenaline", resolution="1080p", aspect_ratio="16:9"):
        self.style_preset = style_preset
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio

    def create_edit_plan(self, video_highlights, audio_analysis, target_duration="auto", custom_clips=None):
        """
        Synthesizes raw video highlight clips into a timed, beat-synced editing timeline.
        Supports custom_clips list from Manual Timeline Editor or auto composition.
        """
        if custom_clips and len(custom_clips) > 0:
            # User manual timeline override
            total_dur = sum(float(c.get("src_end", 4.0)) - float(c.get("src_start", 0.0)) for c in custom_clips)
            return {
                "style_preset": self.style_preset,
                "resolution": self.resolution,
                "aspect_ratio": self.aspect_ratio,
                "total_duration": round(total_dur, 2),
                "bpm": audio_analysis.get("bpm", 120),
                "clips": custom_clips
            }

        beats = audio_analysis.get("beats", [])
        drops = audio_analysis.get("drops", [])
        music_duration = audio_analysis.get("duration", 60.0)

        # Calculate total available raw video highlights duration
        total_raw_highlights_duration = sum(h.get("duration", 4.0) for h in video_highlights) if video_highlights else 30.0

        if target_duration == "15":
            total_edit_time = 15.0
        elif target_duration == "30":
            total_edit_time = 30.0
        elif target_duration == "60":
            total_edit_time = 60.0
        elif target_duration == "180":
            total_edit_time = min(180.0, total_raw_highlights_duration)
        elif target_duration == "300":
            total_edit_time = min(300.0, total_raw_highlights_duration)
        elif target_duration == "full":
            total_edit_time = total_raw_highlights_duration
        else: # 'auto' or float string
            try:
                total_edit_time = float(target_duration)
            except Exception:
                total_edit_time = min(total_raw_highlights_duration, max(30.0, min(180.0, total_raw_highlights_duration * 0.7)))

        # Define clip duration target based on style & total edit time
        if self.style_preset == "shorts_beat":
            avg_clip_len = 1.2
        elif self.style_preset == "scenic_cruise":
            avg_clip_len = 4.5
        else: # adrenaline
            avg_clip_len = 2.5

        # If full length or long edit time, adjust average clip length proportionally
        if total_edit_time > 120:
            avg_clip_len = 5.0

        cut_timestamps = []
        accumulated = 0.0
        for b in beats:
            if b - accumulated >= avg_clip_len:
                cut_timestamps.append(b)
                accumulated = b
            if b >= total_edit_time:
                break

        if not cut_timestamps or cut_timestamps[-1] < total_edit_time:
            # Generate continuous timestamps up to total edit time
            curr = cut_timestamps[-1] if cut_timestamps else 0.0
            while curr < total_edit_time:
                curr += avg_clip_len
                cut_timestamps.append(round(curr, 2))

        timeline_clips = []
        curr_start_time = 0.0
        clip_idx = 0
        num_highlights = len(video_highlights)

        transitions_pool = ["dissolve", "whipleft", "whipright", "zoomin", "slideleft", "fade"]

        for cut_end in cut_timestamps:
            segment_duration = round(cut_end - curr_start_time, 2)
            if segment_duration <= 0.3:
                continue

            highlight = video_highlights[clip_idx % num_highlights] if num_highlights > 0 else {
                "video_path": "default.mp4", "start": 0.0, "end": 10.0, "score": 1.0
            }
            clip_idx += 1

            is_drop_moment = any(abs(cut_end - d) < 0.8 for d in drops)
            
            # ML Parabolic Speed Ramping Curve calculation
            if is_drop_moment:
                speed_ramp = 0.25  # Apex Slow-Mo drop
                transition = "zoomin"
                speed_curve = "Parabolic Apex Slow-Mo (0.25x)"
            elif segment_duration > 3.5:
                speed_ramp = 2.0   # Fast-Forward Straightaway
                transition = transitions_pool[len(timeline_clips) % len(transitions_pool)]
                speed_curve = "Straightaway Hyperlapse (2.0x)"
            else:
                speed_ramp = 1.0   # Linear Normal Pacing
                transition = "dissolve"
                speed_curve = "Linear Pacing (1.0x)"

            src_start = highlight.get("start", 0.0)
            src_needed_duration = segment_duration * speed_ramp
            src_end = src_start + src_needed_duration

            timeline_clips.append({
                "clip_id": len(timeline_clips) + 1,
                "video_path": highlight["video_path"],
                "src_start": round(src_start, 2),
                "src_end": round(src_end, 2),
                "timeline_start": round(curr_start_time, 2),
                "timeline_end": round(cut_end, 2),
                "timeline_duration": segment_duration,
                "speed_ramp": speed_ramp,
                "transition": transition,
                "score": highlight.get("score", 1.0),
                "speed_kmh": highlight.get("speed_kmh", 60),
                "lean_angle_deg": highlight.get("lean_angle_deg", 18),
                "is_drop": is_drop_moment
            })

            curr_start_time = cut_end

        return {
            "style_preset": self.style_preset,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
            "total_duration": round(curr_start_time, 2),
            "bpm": audio_analysis.get("bpm", 120),
            "clips": timeline_clips
        }
