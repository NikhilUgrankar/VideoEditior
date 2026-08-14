import os

class LUTGenerator:
    """Generates custom 3D LUT .cube files and FFmpeg color filters for Cinematic Moto Styles."""
    
    PRESETS = {
        "teal_orange": {
            "name": "Teal & Orange (Cinematic Action)",
            "description": "Signature Hollywood action look with cool teal shadows and warm orange highlights.",
            "ffmpeg_filter": "eq=contrast=1.18:brightness=0.01:saturation=1.35, colorbalance=rs=0.1:gs=-0.05:bs=-0.15:rh=0.15:gh=0.05:bh=-0.1"
        },
        "dark_moto": {
            "name": "Dark Moto (Stealth / Aggressive)",
            "description": "Deep moody blacks, high contrast, desaturated background with sharp metallic punch.",
            "ffmpeg_filter": "eq=contrast=1.35:brightness=-0.03:saturation=0.85, colorbalance=rs=-0.05:bs=0.05:rh=0.05:bh=-0.05"
        },
        "sunset_glow": {
            "name": "Golden Sunset (Warm Highway)",
            "description": "Warm golden hour glow with boosted amber tones and smooth highlight roll-off.",
            "ffmpeg_filter": "eq=contrast=1.1:brightness=0.02:saturation=1.4, colorbalance=rs=0.15:gs=0.08:bs=-0.12:rh=0.18:gh=0.1:bh=-0.08"
        },
        "crisp_hdr": {
            "name": "Vivid GoPro HDR",
            "description": "Ultra-vibrant, sharp, rich foliage greens and sky blues for GoPro / Insta360 daylight action.",
            "ffmpeg_filter": "eq=contrast=1.2:brightness=0.0:saturation=1.5, unsharp=5:5:1.0:5:5:0.0"
        },
        "vintage_road": {
            "name": "Retro Roadtrip 70s",
            "description": "Nostalgic film look with raised shadows, soft warm cast, and subtle grain.",
            "ffmpeg_filter": "eq=contrast=1.05:brightness=0.04:saturation=0.9, colorbalance=rs=0.08:gs=0.03:bs=-0.05"
        }
    }

    @staticmethod
    def get_ffmpeg_filter(preset_key):
        preset = LUTGenerator.PRESETS.get(preset_key, LUTGenerator.PRESETS["teal_orange"])
        return preset["ffmpeg_filter"]

    @staticmethod
    def create_cube_lut_file(preset_key, output_cube_path):
        """Generates a 17x17x17 .cube file for video editing software export if needed."""
        size = 17
        with open(output_cube_path, "w") as f:
            f.write("# Created by Auto-Edit Bike Video Editor\n")
            f.write("TITLE \"Cinematic Moto LUT\"\n")
            f.write(f"LUT_3D_SIZE {size}\n\n")
            
            for r_idx in range(size):
                r = r_idx / (size - 1)
                for g_idx in range(size):
                    g = g_idx / (size - 1)
                    for b_idx in range(size):
                        b = b_idx / (size - 1)
                        
                        # Apply transformation based on preset
                        if preset_key == "teal_orange":
                            out_r = min(1.0, max(0.0, r * 1.15 + (1 - b) * 0.1))
                            out_g = min(1.0, max(0.0, g * 1.05))
                            out_b = min(1.0, max(0.0, b * 0.85 + (1 - r) * 0.15))
                        elif preset_key == "dark_moto":
                            out_r = min(1.0, max(0.0, (r ** 1.3) * 1.1))
                            out_g = min(1.0, max(0.0, (g ** 1.3) * 1.0))
                            out_b = min(1.0, max(0.0, (b ** 1.2) * 1.1))
                        else: # Crisp HDR
                            out_r = min(1.0, max(0.0, r * 1.2 - 0.1))
                            out_g = min(1.0, max(0.0, g * 1.2 - 0.1))
                            out_b = min(1.0, max(0.0, b * 1.2 - 0.1))

                        f.write(f"{out_r:.6f} {out_g:.6f} {out_b:.6f}\n")
        return output_cube_path
