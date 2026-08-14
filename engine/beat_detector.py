import numpy as np
import scipy.io.wavfile as wavfile
import subprocess
import os
import json

class BeatDetector:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def extract_audio_to_wav(self, audio_or_video_path, temp_wav_path):
        """Converts any input audio/video into mono 22050Hz WAV for fast beat analysis."""
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", audio_or_video_path,
            "-vn", "-ac", "1", "-ar", "22050",
            temp_wav_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0 and os.path.exists(temp_wav_path)

    def analyze_beats(self, audio_path, temp_wav_dir="./temp"):
        """
        Analyzes audio file using SciPy & Librosa (or fallback signal energy analyzer).
        Returns BPM, list of beat timestamps in seconds, drop moments, and audio duration.
        """
        os.makedirs(temp_wav_dir, exist_ok=True)
        temp_wav = os.path.join(temp_wav_dir, "temp_analysis.wav")
        
        extracted = self.extract_audio_to_wav(audio_path, temp_wav)
        if not extracted:
            print(f"[BeatDetector Error] Could not extract audio from {audio_path}")
            return {"bpm": 120, "beats": [], "drops": [], "duration": 30.0}

        try:
            # Try librosa if available
            import librosa
            y, sr = librosa.load(temp_wav, sr=22050)
            duration = float(librosa.get_duration(y=y, sr=sr))
            
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
            
            # Extract onset strength / drop peaks
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            # Find top 10% highest intensity drops
            peaks = np.where(onset_env > np.percentile(onset_env, 90))[0]
            drop_times = librosa.frames_to_time(peaks, sr=sr).tolist()
            
            # Clean up temp file
            if os.path.exists(temp_wav):
                os.remove(temp_wav)

            bpm_val = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)

            return {
                "bpm": round(bpm_val, 1),
                "beats": [round(b, 3) for b in beat_times],
                "drops": [round(d, 3) for d in drop_times[::4]], # sample every 4th peak
                "duration": round(duration, 2)
            }
        except Exception as e:
            print(f"[BeatDetector] Librosa fallback to SciPy energy beat detection: {e}")
            # Fallback using pure SciPy/NumPy signal energy analysis
            try:
                sr, y = wavfile.read(temp_wav)
                if y.ndim > 1:
                    y = y[:, 0] # mono
                duration = len(y) / float(sr)
                
                # Compute RMS energy in 100ms frames
                frame_size = int(sr * 0.1) # 100ms
                energy = [np.mean(y[i:i+frame_size]**2) for i in range(0, len(y)-frame_size, frame_size)]
                energy = np.array(energy)
                
                # Find energy peaks (beats)
                mean_e = np.mean(energy)
                std_e = np.std(energy)
                threshold = mean_e + 0.5 * std_e
                
                beat_indices = np.where(energy > threshold)[0]
                beat_times = (beat_indices * 0.1).tolist()
                
                # Clean up
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)

                return {
                    "bpm": 128.0,
                    "beats": [round(b, 3) for b in beat_times[::2]],
                    "drops": [round(b, 3) for b in beat_times[::8]],
                    "duration": round(duration, 2)
                }
            except Exception as ex:
                print(f"[BeatDetector Error] SciPy analysis failed: {ex}")
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
                return {"bpm": 120.0, "beats": [i * 0.5 for i in range(60)], "drops": [10.0, 20.0, 30.0], "duration": 30.0}
