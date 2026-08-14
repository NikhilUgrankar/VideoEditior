import os
import numpy as np
import scipy.io.wavfile as wavfile
import cv2

def generate_audio_genre(output_wav_path, genre="synthwave", duration_sec=60, bpm=128):
    """Generates synthetic audio tracks for 5 action genres."""
    sr = 22050
    total_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, False)
    beat_duration = 60.0 / bpm
    beat_samples = int(sr * beat_duration)

    if genre == "rock":
        # Heavy distortion guitar sine + fast double kick
        freqs = [82.41, 110.0, 146.83] # E2, A2, D3
        synth = sum(0.3 * np.sin(2 * np.pi * f * t) for f in freqs)
        # Distortion clipping
        synth = np.clip(synth * 2.5, -0.6, 0.6)
        
        kick = np.zeros(total_samples)
        for b_idx in range(0, total_samples, int(beat_samples / 2)):
            k_len = min(int(sr * 0.1), total_samples - b_idx)
            kick[b_idx:b_idx+k_len] = 0.9 * np.sin(2 * np.pi * 120 * np.linspace(0, 0.1, k_len)) * np.exp(-35 * np.linspace(0, 0.1, k_len))
        audio = synth + kick

    elif genre == "lofi":
        # Warm rhodes chords + soft vinyl crackle + slow 90 BPM beat
        chord_freqs = [261.63, 329.63, 392.0] # C4, E4, G4
        rhodes = sum(0.25 * np.sin(2 * np.pi * f * t) * np.exp(-0.8 * (t % beat_duration)) for f in chord_freqs)
        crackle = np.random.uniform(-0.03, 0.03, total_samples)
        audio = rhodes + crackle

    elif genre == "cinematic":
        # Deep orchestral low drone + epic ambient swell
        drone = 0.4 * np.sin(2 * np.pi * 43.65 * t) + 0.3 * np.sin(2 * np.pi * 87.31 * t)
        swell = 0.3 * np.sin(2 * np.pi * 174.61 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t))
        audio = drone + swell

    elif genre == "edm":
        # Sawtooth lead synth + heavy sub bass + aggressive 4-on-the-floor
        sub = 0.5 * np.sin(2 * np.pi * 55.0 * t)
        lead = 0.3 * (2 * (t * 220.0 - np.floor(0.5 + t * 220.0))) # Sawtooth
        kick = np.zeros(total_samples)
        for b_idx in range(0, total_samples, beat_samples):
            k_len = min(int(sr * 0.2), total_samples - b_idx)
            kick[b_idx:b_idx+k_len] = 1.0 * np.sin(2 * np.pi * 180 * np.linspace(0, 0.2, k_len)) * np.exp(-25 * np.linspace(0, 0.2, k_len))
        audio = sub + lead * 0.5 + kick

    else: # Synthwave
        bass_freq = 65.41
        bassline = 0.35 * np.sin(2 * np.pi * bass_freq * t) * (np.sin(2 * np.pi * (1 / beat_duration) * t) > 0)
        kick = np.zeros(total_samples)
        for b_idx in range(0, total_samples, beat_samples):
            k_len = min(int(sr * 0.15), total_samples - b_idx)
            kick[b_idx:b_idx+k_len] = 0.8 * np.sin(2 * np.pi * 150 * np.linspace(0, 0.15, k_len)) * np.exp(-30 * np.linspace(0, 0.15, k_len))
        audio = bassline + kick

    # Normalize audio
    audio = audio / np.max(np.abs(audio)) if np.max(np.abs(audio)) > 0 else audio
    audio_int16 = (audio * 32767).astype(np.int16)

    os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)
    wavfile.write(output_wav_path, sr, audio_int16)
    print(f"[Sample Generator] Created {genre} audio at {output_wav_path}")
    return output_wav_path

def generate_sample_bike_video(output_mp4_path, duration_sec=15, fps=60, width=1280, height=720):
    """Generates a synthetic animated bike ride video clip for testing."""
    os.makedirs(os.path.dirname(output_mp4_path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_mp4_path, fourcc, fps, (width, height))

    total_frames = int(duration_sec * fps)
    
    for frame_idx in range(total_frames):
        t = frame_idx / fps
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:] = (15, 23, 42)

        road_top_y = int(height * 0.4)
        road_pts = np.array([
            [width * 0.45, road_top_y],
            [width * 0.55, road_top_y],
            [width * 0.95, height],
            [width * 0.05, height]
        ], np.int32)
        cv2.fillPoly(img, [road_pts], (30, 41, 59))

        offset = (int(t * 800) % 200)
        for y in range(road_top_y + offset, height, 180):
            scale = (y - road_top_y) / (height - road_top_y)
            cx = width * 0.5
            w_dash = int(12 * scale + 2)
            h_dash = int(40 * scale + 4)
            cv2.rectangle(img, (int(cx - w_dash), y), (int(cx + w_dash), y + h_dash), (0, 215, 255), -1)

        cv2.line(img, (int(width * 0.2), height - 80), (int(width * 0.8), height - 80), (148, 163, 184), 12)
        cv2.circle(img, (int(width * 0.5), height - 80), 30, (239, 68, 68), -1)
        out.write(img)

    out.release()
    print(f"[Sample Generator] Created sample bike video at {output_mp4_path}")
    return output_mp4_path

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_audio_genre(os.path.join(base_dir, "synthwave_beat.wav"), genre="synthwave", bpm=128)
    generate_audio_genre(os.path.join(base_dir, "rock_beat.wav"), genre="rock", bpm=140)
    generate_audio_genre(os.path.join(base_dir, "lofi_beat.wav"), genre="lofi", bpm=90)
    generate_audio_genre(os.path.join(base_dir, "cinematic_beat.wav"), genre="cinematic", bpm=110)
    generate_audio_genre(os.path.join(base_dir, "edm_beat.wav"), genre="edm", bpm=130)
    generate_sample_bike_video(os.path.join(base_dir, "sample_bike_ride_1.mp4"))
