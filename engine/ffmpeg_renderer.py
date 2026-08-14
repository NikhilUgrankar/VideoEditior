import os
import subprocess
import json
import time
from .lut_generator import LUTGenerator
from .hud_overlay import HUDOverlayGenerator

class FFmpegRenderer:
    """Renders final cinematic edit using FFmpeg with LUTs, speed ramps, HUD overlay & audio ducking."""

    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def render_edit(self, edit_plan, music_path, output_path, lut_preset="teal_orange", show_hud=True, progress_callback=None):
        """
        Executes FFmpeg filter graph to stitch clips, apply speed ramping, color LUTs,
        telemetry HUD overlay, and audio beat track.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        clips = edit_plan.get("clips", [])
        resolution = edit_plan.get("resolution", "1080p")
        aspect_ratio = edit_plan.get("aspect_ratio", "16:9")

        # Determine target resolution dimensions
        if resolution == "4k":
            target_w, target_h = (3840, 2160) if aspect_ratio != "9:16" else (2160, 3840)
        else:
            target_w, target_h = (1920, 1080) if aspect_ratio != "9:16" else (1080, 1920)

        lut_filter = LUTGenerator.get_ffmpeg_filter(lut_preset)

        # Generate temporary HUD Overlay image if enabled
        hud_png = None
        if show_hud:
            hud_png = os.path.join(os.path.dirname(output_path), "temp_hud_overlay.png")
            HUDOverlayGenerator.create_hud_image(width=target_w, height=target_h, speed_kmh=145, lean_angle_deg=34, output_path=hud_png)

        if not clips:
            print("[FFmpegRenderer Error] No clips in edit plan.")
            return False

        inputs = []
        filter_chains = []
        concat_v_inputs = []

        # Process Video Clips
        for idx, clip in enumerate(clips):
            v_path = clip["video_path"]
            src_s = clip["src_start"]
            src_dur = max(0.5, clip["src_end"] - clip["src_start"])
            speed = clip.get("speed_ramp", 1.0)

            inputs.extend(["-ss", str(src_s), "-t", str(src_dur), "-i", v_path])

            pts_mult = round(1.0 / speed, 3)
            crop_filter = f"crop=ih*9/16:ih" if aspect_ratio == "9:16" else "null"

            v_chain = (
                f"[{idx}:v]{crop_filter},"
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
                f"crop={target_w}:{target_h},"
                f"setpts={pts_mult}*PTS,"
                f"fps=60,"
                f"{lut_filter}[v{idx}];"
            )
            filter_chains.append(v_chain)
            concat_v_inputs.append(f"[v{idx}]")

        # Music Audio Input
        music_input_idx = len(clips)
        if music_path and os.path.exists(music_path):
            inputs.extend(["-i", music_path])
            music_available = True
        else:
            music_available = False

        # HUD Overlay Input
        hud_input_idx = music_input_idx + (1 if music_available else 0)
        if show_hud and hud_png and os.path.exists(hud_png):
            inputs.extend(["-i", hud_png])
            hud_available = True
        else:
            hud_available = False

        # Concat video streams
        num_v = len(concat_v_inputs)
        concat_v_str = "".join(concat_v_inputs) + f"concat=n={num_v}:v=1:a=0[vconcat];"
        filter_chains.append(concat_v_str)

        main_v_node = "[vconcat]"

        # Letterbox for 2.35:1 aspect ratio option
        if aspect_ratio == "2.35:1":
            letterbox_h = int(target_h * 0.12)
            filter_chains.append(f"{main_v_node}drawbox=y=0:h={letterbox_h}:color=black:t=fill,drawbox=y=ih-{letterbox_h}:h={letterbox_h}:color=black:t=fill[vletter];")
            main_v_node = "[vletter]"

        # Telemetry HUD Overlay
        if hud_available:
            filter_chains.append(f"{main_v_node}[{hud_input_idx}:v]overlay=0:0[vhud];")
            final_v_out = "[vhud]"
        else:
            final_v_out = main_v_node

        full_filter_graph = "".join(filter_chains)

        cmd = [
            self.ffmpeg_path, "-y",
            *inputs,
            "-filter_complex", full_filter_graph,
            "-map", final_v_out
        ]

        if music_available:
            cmd.extend(["-map", f"{music_input_idx}:a", "-c:a", "aac", "-b:a", "320k"])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "19",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ])

        print(f"[FFmpegRenderer] Executing FFmpeg Render command:\n{' '.join(cmd)}")
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            
            if hud_png and os.path.exists(hud_png):
                try:
                    os.remove(hud_png)
                except Exception:
                    pass

            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                if progress_callback:
                    progress_callback(100.0, "Rendering complete!")
                print(f"[FFmpegRenderer] Successfully rendered video ({os.path.getsize(output_path)} bytes) to {output_path}")
                return True
            else:
                print(f"[FFmpegRenderer Error] Return Code {res.returncode}:\n{res.stderr}")
                return False

        except Exception as e:
            print(f"[FFmpegRenderer Error] Exception during render: {e}")
            if hud_png and os.path.exists(hud_png):
                try:
                    os.remove(hud_png)
                except Exception:
                    pass
            return False

