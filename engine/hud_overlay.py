import os
from PIL import Image, ImageDraw, ImageFont
import math

class HUDOverlayGenerator:
    """Generates transparent PNG HUD overlays (Speedometer, Lean Angle, Telemetry) for FFmpeg video overlay."""

    @staticmethod
    def create_hud_image(width=1920, height=1080, speed_kmh=120, lean_angle_deg=28, output_path="temp_hud.png"):
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Bottom-left HUD Telemetry Box
        cx, cy = 180, height - 160
        radius = 90

        # Semi-transparent dark circular background
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(15, 23, 42, 180), outline=(56, 189, 248, 220), width=3)

        # Outer Speedometer ticks
        for angle_deg in range(-135, 136, 15):
            rad = math.radians(angle_deg - 90)
            x1 = cx + (radius - 12) * math.cos(rad)
            y1 = cy + (radius - 12) * math.sin(rad)
            x2 = cx + radius * math.cos(rad)
            y2 = cy + radius * math.sin(rad)
            draw.line([(x1, y1), (x2, y2)], fill=(148, 163, 184, 250), width=2)

        # Speedometer Needle
        speed_percent = min(1.0, speed_kmh / 220.0)
        needle_angle_deg = -135 + (speed_percent * 270)
        n_rad = math.radians(needle_angle_deg - 90)
        nx = cx + (radius - 20) * math.cos(n_rad)
        ny = cy + (radius - 20) * math.sin(n_rad)
        draw.line([(cx, cy), (nx, ny)], fill=(239, 68, 68, 255), width=4)

        # Speed text
        draw.text((cx - 25, cy - 20), f"{int(speed_kmh)}", fill=(255, 255, 255, 255), font_size=28)
        draw.text((cx - 20, cy + 12), "KM/H", fill=(56, 189, 248, 255), font_size=12)

        # Bottom-right Lean Angle / G-Force Indicator
        lx, ly = width - 180, height - 160
        draw.rectangle([lx - 90, ly - 40, lx + 90, ly + 40], fill=(15, 23, 42, 180), outline=(245, 158, 11, 220), width=2)
        draw.text((lx - 75, ly - 30), "LEAN ANGLE", fill=(148, 163, 184, 250), font_size=11)
        draw.text((lx - 45, ly - 10), f"{int(lean_angle_deg)}°", fill=(245, 158, 11, 255), font_size=32)

        # Top-left Branding watermark badge
        draw.rounded_rectangle([40, 40, 240, 80], radius=8, fill=(15, 23, 42, 200), outline=(236, 72, 153, 200), width=2)
        draw.text((55, 50), "MOTO CINEMATIC", fill=(255, 255, 255, 255), font_size=16)

        img.save(output_path, "PNG")
        return output_path
