import requests
import urllib.parse
import os
import shutil

class PixabayMusicClient:
    """Client for Pixabay Music API & Curated Creator Audio Library."""
    
    # Public Pixabay API key or fallback curated catalog
    API_KEY = "38841459-994c6ef51e89ef5332fbc137c" # Public Pixabay API key
    BASE_URL = "https://pixabay.com/api/"

    CURATED_CATALOG = [
        {
            "id": "pixabay_1",
            "title": "Adrenaline Moto Rush (Action Hype)",
            "artist": "Creator Beats",
            "genre": "Action",
            "duration": "2:45",
            "bpm": 135,
            "stream_url": "/sample_media/synthwave_beat.wav",
            "tags": ["Action", "GoPro", "Engine", "Hype"]
        },
        {
            "id": "pixabay_2",
            "title": "Heavy Moto Distortion (Rock / Metal)",
            "artist": "Riff Master",
            "genre": "Rock",
            "duration": "3:10",
            "bpm": 140,
            "stream_url": "/sample_media/rock_beat.wav",
            "tags": ["Rock", "Metal", "Power", "Exhaust"]
        },
        {
            "id": "pixabay_3",
            "title": "Highway Sunset Breeze (Lo-Fi Chill Vlog)",
            "artist": "Vlog Vibes",
            "genre": "Lo-Fi",
            "duration": "2:15",
            "bpm": 90,
            "stream_url": "/sample_media/lofi_beat.wav",
            "tags": ["Vlog", "Chill", "Sunset", "Reels"]
        },
        {
            "id": "pixabay_4",
            "title": "Panoramic Alpine Pass (Epic Cinematic)",
            "artist": "Symphonic Studio",
            "genre": "Cinematic",
            "duration": "4:20",
            "bpm": 110,
            "stream_url": "/sample_media/cinematic_beat.wav",
            "tags": ["Cinematic", "Mountains", "SlowMo", "Drone"]
        },
        {
            "id": "pixabay_5",
            "title": "Cyberpunk Night Cruise (EDM Bass Drop)",
            "artist": "Neon Waves",
            "genre": "EDM",
            "duration": "3:30",
            "bpm": 130,
            "stream_url": "/sample_media/edm_beat.wav",
            "tags": ["EDM", "Bass", "Night", "Speed"]
        }
    ]

    @staticmethod
    def search_music(query="", genre=""):
        """Searches Pixabay Music API and returns streamable tracks."""
        tracks = list(PixabayMusicClient.CURATED_CATALOG)
        
        # Query Pixabay API if search parameter provided
        if query or genre:
            try:
                search_q = f"{query} {genre}".strip()
                url = f"https://pixabay.com/api/?key={PixabayMusicClient.API_KEY}&q={urllib.parse.quote(search_q)}&media_type=audio"
                res = requests.get(url, timeout=4)
                if res.status_code == 200:
                    data = res.json()
                    hits = data.get("hits", [])
                    for idx, item in enumerate(hits[:10]):
                        tracks.append({
                            "id": f"pixabay_api_{item.get('id', idx)}",
                            "title": item.get("tags", "Creator Audio Track").title(),
                            "artist": item.get("user", "Pixabay Artist"),
                            "genre": genre or "Creator Beat",
                            "duration": f"{item.get('duration', 180) // 60}:{item.get('duration', 180) % 60:02d}",
                            "bpm": 120,
                            "stream_url": item.get("audio", item.get("pageURL", "")),
                            "download_url": item.get("audio", ""),
                            "tags": [t.strip() for t in item.get("tags", "").split(",") if t]
                        })
            except Exception as e:
                print(f"[Pixabay Music Error] API fetch failed: {e}")

        # Filter by genre if specified
        if genre and genre.lower() != "all":
            filtered = [t for t in tracks if genre.lower() in t["genre"].lower() or any(genre.lower() in tag.lower() for tag in t.get("tags", []))]
            if filtered:
                return filtered

        return tracks
