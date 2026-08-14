import os
import numpy as np
import scipy.io.wavfile as wavfile
import cv2

def generate_synthwave_sample_beat(output_wav_path, duration_sec=30, bpm=128):
    """Generates a high-energy electronic synthwave action beat WAV file for sample video edits."""
    sr = 22050
    total_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, False)
    
    # 1. Bassline synth wave (128 BPM = 0.46875s per beat)
    beat_duration = 60.0 / bpm
    bass_freq = 65.41 # C2
    bassline = 0.3 * np.sin(2 * np.pi * bass_freq * t) * (np.sin(2 * np.pi * (1 / beat_duration) * t) > 0)

    # 2. Kick Drum pulse on every beat
    kick = np.zeros(total_samples)
    beat_samples = int(sr * beat_duration)
    for b_idx in range(0, total_samples, beat_samples):
        k_len = min(int(sr * 0.15), total_samples - b_idx)
        kt = np.linspace(0, 0.15, k_len, False)
        # Pitch drop kick
        k_freq = np.linspace(150, 40, k_len)
        kick[b_idx:b_idx+k_len] = 0.8 * np.sin(2 * np.pi * k_freq * kt) * np.exp(-30 * kt)

    # 3. Snare / Hi-hat synth noise on beats 2 and 4
    snare = np.zeros(total_samples)
    for b_idx in range(beat_samples, total_samples, beat_samples * 2):
        s_len = min(int(sr * 0.1), total_samples - b_idx)
        noise = np.random.uniform(-1, 1, s_len)
        snare[b_idx:b_idx+s_len] = 0.5 * noise * np.exp(-20 * np.linspace(0, 0.1, s_len))

    # Combine audio
    audio = bassline + kick + snare
    audio = audio / np.max(np.abs(audio)) # normalize
    audio_int16 = (audio * 32767).astype(np.int16)

    os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)
    wavfile.write(output_wav_path, sr, audio_int16)
    print(f"[Sample Generator] Created sample beat audio at {output_wav_path}")
    return output_wav_path

def generate_sample_bike_video(output_mp4_path, duration_sec=15, fps=60, width=1280, height=720):
    """Generates a synthetic animated bike ride video clip (highway lines, speed motion blur) for testing."""
    os.makedirs(os.path.dirname(output_mp4_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_mp4_path, fourcc, fps, (width, height))

    total_frames = int(duration_sec * fps)
    
    for frame_idx in range(total_frames):
        t = frame_idx / fps
        # Create dark atmospheric road canvas
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:] = (15, 23, 42) # Slate dark blue night theme

        # Draw road horizon perspective
        road_top_y = int(height * 0.4)
        road_pts = np.array([
            [width * 0.45, road_top_y],
            [width * 0.55, road_top_y],
            [width * 0.95, height],
            [width * 0.05, height]
        ], np.int32)
        cv2.fillPoly(img, [road_pts], (30, 41, 59))

        # Animated yellow lane dash lines moving down
        offset = (int(t * 800) % 200)
        for y in range(road_top_y + offset, height, 180):
            scale = (y - road_top_y) / (height - road_top_y)
            cx = width * 0.5
            w_dash = int(12 * scale + 2)
            h_dash = int(40 * scale + 4)
            cv2.rectangle(img, (int(cx - w_dash), y), (int(cx + w_dash), y + h_dash), (0, 215, 255), -1)

        # Draw simulated bike handle bar & windshield outline
        cv2.line(img, (int(width * 0.2), height - 80), (int(width * 0.8), height - 80), (148, 163, 184), 12)
        cv2.circle(img, (int(width * 0.5), height - 80), 30, (239, 68, 68), -1)
        
        # Add frame index / speed text indicator
        simulated_speed = 80 + int(40 * np.sin(t * 2))
        cv2.putText(img, f"RAW BIKE FOOTAGE | {simulated_speed} KM/H", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        out.write(img)

    out.release()
    print(f"[Sample Generator] Created sample bike video at {output_mp4_path}")
    return output_mp4_path

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_synthwave_sample_beat(os.path.join(base_dir, "synthwave_beat.wav"))
    generate_sample_bike_video(os.path.join(base_dir, "sample_bike_ride_1.mp4"))
