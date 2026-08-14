import math

class AutoComposer:
    """Builds an algorithmic timeline editing plan matching raw video clips to music beats."""

    def __init__(self, style_preset="adrenaline", resolution="1080p", aspect_ratio="16:9"):
        self.style_preset = style_preset
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio

    def create_edit_plan(self, video_highlights, audio_analysis, target_duration=60.0):
        """
        Synthesizes raw video highlight clips into a timed, beat-synced editing timeline.
        """
        beats = audio_analysis.get("beats", [])
        drops = audio_analysis.get("drops", [])
        music_duration = audio_analysis.get("duration", 60.0)

        total_edit_time = min(target_duration, music_duration)
        if total_edit_time <= 0:
            total_edit_time = 30.0

        # Define clip duration target based on style
        if self.style_preset == "shorts_beat":
            avg_clip_len = 1.2 # Fast punchy cuts for YouTube Shorts
        elif self.style_preset == "scenic_cruise":
            avg_clip_len = 4.5 # Longer panoramic cuts
        else: # adrenaline
            avg_clip_len = 2.2 # Dynamic speed ramped cuts

        # Group beat markers into cut points
        cut_timestamps = []
        accumulated = 0.0
        for b in beats:
            if b - accumulated >= avg_clip_len:
                cut_timestamps.append(b)
                accumulated = b
            if b >= total_edit_time:
                break

        if not cut_timestamps:
            # Fallback cut timestamps
            num_cuts = int(total_edit_time / avg_clip_len)
            cut_timestamps = [round((i + 1) * avg_clip_len, 2) for i in range(num_cuts)]

        # Map highlight video segments onto the cut timestamps
        timeline_clips = []
        curr_start_time = 0.0
        clip_idx = 0
        num_highlights = len(video_highlights)

        for cut_end in cut_timestamps:
            segment_duration = round(cut_end - curr_start_time, 2)
            if segment_duration <= 0.3:
                continue

            # Pick next high-scoring video highlight segment
            highlight = video_highlights[clip_idx % num_highlights] if num_highlights > 0 else {
                "video_path": "default.mp4", "start": 0.0, "end": 10.0, "score": 1.0
            }
            clip_idx += 1

            # Determine speed ramping & transition for this segment
            is_drop_moment = any(abs(cut_end - d) < 0.8 for d in drops)
            
            if is_drop_moment:
                speed_ramp = 0.5 # Slow-mo epic drop
                transition = "whip_pan"
                color_intensity = "high"
            elif segment_duration > 3.0:
                speed_ramp = 2.0 # Cruise fast-forward
                transition = "zoom_blur"
                color_intensity = "normal"
            else:
                speed_ramp = 1.0
                transition = "fade"
                color_intensity = "normal"

            # Calculate source video trim times
            src_start = highlight.get("start", 0.0)
            # Adjust source duration based on speed ramp speedup/slowmo
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
