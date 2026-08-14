# Auto-Edit Bike Video Studio (Moto-Edit Pro AI)

An automated AI-assisted video editing software tailored specifically for raw motorcycle and bicycle ride footage. It automatically analyzes motion energy, optical flow, and music beat drops to synthesize high-energy, YouTube-ready cinematic edits with dynamic speed ramping, color LUTs, audio ducking, and customizable HUD telemetry.

![Moto-Edit Studio Pro](https://img.shields.gradient.net/badge-1080p_4K_60FPS-active)

## Key Features

- **Multi-Camera Input Support**: Compatible with GoPro (HEVC/MP4 60/120fps), Insta360 (INSV/MP4), Android & iOS mobile video formats.
- **Resolution & Aspect Ratio Presets**:
  - **1080p 60FPS** (Fast high-frame-rate export) & **4K 60FPS** (Ultra HD Master)
  - **16:9 Widescreen**, **2.35:1 Anamorphic Cinema Letterbox**, and **9:16 Vertical YouTube Shorts / Instagram Reels**
- **Optical Flow & Motion Scoring (`video_analyzer.py`)**: Automatically detects high-excitement riding (accelerations, cornering lean angles, high-speed bursts) versus static traffic light waits.
- **Beat Synchronization (`beat_detector.py`)**: Analyzes tempo (BPM), beat onsets, and drop moments from custom audio files (`.mp3`, `.wav`) or built-in synthwave beat tracks.
- **Dynamic Speed Ramping**: Cuts and speed ramps (e.g. 2.5x cruise speedup into 0.5x apex turn slow-mo) timed precisely to music downbeats.
- **Cinematic Color LUTs**:
  - 🎬 **Teal & Orange** (Hollywood Action)
  - 🦇 **Dark Moto** (Stealth / High Contrast)
  - 🌅 **Golden Sunset** (Warm Glow)
  - 🏔️ **Vivid GoPro HDR** (High Saturation)
  - 🎞️ **Retro 70s Roadtrip**
- **Telemetry HUD Overlay**: Render optional animated speedometer gauge, tilt/lean angle meter, and branding overlays.
- **Interactive Web Studio**: Built with modern dark glassmorphism styling, real-time render progress modal, and one-click MP4 export.

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/NikhilUgrankar/VideoEditior.git
cd VideoEditior
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup FFmpeg (Automatic static download for Windows)
```bash
python setup_ffmpeg.py
```

### 4. Run the Studio Server
```bash
python server.py
```

Open your browser and navigate to: **`http://localhost:8000`**

---

## Architecture Overview

```
                           +-------------------------------------+
                           |   Cinematic Studio UI (Frontend)    |
                           |  - Drag & Drop Raw Video / Music    |
                           |  - Style Presets & Beat Visualizer   |
                           |  - Timeline & HUD Telemetry Tweaker |
                           |  - Export & Video Preview           |
                           +------------------+------------------+
                                              | (REST API & WS)
                                              v
                           +-------------------------------------+
                           |     FastAPI Backend & Processing    |
                           +------------------+------------------+
                                              |
     +-----------------------+----------------+-----------------------+
     |                       |                                        |
     v                       v                                        v
+------------------+ +------------------+                   +-------------------+
| Motion & Sound   | | Music Beat       |                   | Auto Composer &   |
| Analyzer         | | Detector         |                   | FFmpeg Pipeline   |
| (OpenCV/SciPy)   | | (Librosa/Numpy)  |                   | (Speed Ramps/LUTs)|
+------------------+ +------------------+                   +-------------------+
```

---

## License
MIT License
