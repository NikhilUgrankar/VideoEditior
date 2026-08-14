import numpy as np

class BeatDetector:
    """Librosa / SciPy Style Audio Beat Grid & Transient Peak Analyzer for Beat-Synced Editing."""

    def __init__(self, sample_rate=22050, ffmpeg_path=None):
        self.sample_rate = sample_rate
        self.ffmpeg_path = ffmpeg_path

    def analyze_audio_track(self, audio_path):
        """Analyzes audio file to compute BPM and beat timestamps array."""
        return self.analyze_beats(audio_path)

    def analyze_beats(self, audio_path):
        """Analyzes audio file to compute BPM and beat timestamps array."""
        try:
            import wave
            with wave.open(audio_path, 'rb') as wf:
                framerate = wf.getframerate()
                nframes = wf.getnframes()
                audio_data = np.frombuffer(wf.readframes(nframes), dtype=np.int16)

            duration = nframes / float(framerate)
            if len(audio_data) == 0 or duration <= 0:
                return self._fallback_beat_grid(128.0, 30.0)

            # Mono channel
            if len(audio_data.shape) > 1:
                audio_data = audio_data[:, 0]

            # Envelope onset energy calculation
            audio_abs = np.abs(audio_data.astype(np.float32))
            hop = int(framerate * 0.05) # 50ms hop
            envelope = [np.mean(audio_abs[i:i+hop]) for i in range(0, len(audio_abs), hop)]
            
            # Simple peak detection for BPM estimation
            peaks = []
            env_mean = np.mean(envelope)
            for i in range(1, len(envelope)-1):
                if envelope[i] > env_mean * 1.2 and envelope[i] > envelope[i-1] and envelope[i] > envelope[i+1]:
                    peaks.append(i * 0.05)

            bpm = 128.0
            if len(peaks) > 4:
                diffs = np.diff(peaks)
                avg_interval = float(np.median(diffs))
                if avg_interval > 0.2 and avg_interval < 2.0:
                    bpm = round(60.0 / avg_interval, 1)

            beat_interval = 60.0 / bpm
            beats = [round(i * beat_interval, 3) for i in range(int(duration / beat_interval))]

            return {
                "bpm": bpm,
                "total_beats": len(beats),
                "beat_interval_sec": round(beat_interval, 3),
                "beats": beats
            }
        except Exception as e:
            print(f"[BeatDetector Warning] Wave analysis fallback: {e}")
            return self._fallback_beat_grid(128.0, 60.0)

    def snap_to_nearest_beat(self, target_time, beats):
        """Snaps a cut timestamp to the nearest musical beat drop."""
        if not beats:
            return target_time
        beats_arr = np.array(beats)
        idx = (np.abs(beats_arr - target_time)).argmin()
        return float(beats_arr[idx])

    def _fallback_beat_grid(self, bpm=128.0, duration=60.0):
        interval = 60.0 / bpm
        beats = [round(i * interval, 3) for i in range(int(duration / interval))]
        return {
            "bpm": bpm,
            "total_beats": len(beats),
            "beat_interval_sec": round(interval, 3),
            "beats": beats
        }
