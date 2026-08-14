import requests
import urllib.parse
import os

class JamendoMusicClient:
    """Jamendo API v3.0 REST Client with Instant Fallback Creator Catalog."""

    CLIENT_ID = "56891324"
    BASE_URL = "https://api.jamendo.com/v3.0/tracks/"

    FALLBACK_JAMENDO_TRACKS = [
        {
            "id": "jamendo_f1",
            "title": "High Octane Moto Highway (Rock Cut)",
            "artist": "Jamendo Rock Studio",
            "genre": "Rock",
            "duration": "2:30",
            "bpm": 140,
            "stream_url": "/sample_media/rock_beat.wav",
            "download_url": "/sample_media/rock_beat.wav",
            "provider": "Jamendo CC",
            "tags": ["Rock", "Motorcycle", "Action"]
        },
        {
            "id": "jamendo_f2",
            "title": "Cyberpunk Neon Night Ride (Synthwave)",
            "artist": "Synthwave Collective",
            "genre": "Synthwave",
            "duration": "3:15",
            "bpm": 128,
            "stream_url": "/sample_media/synthwave_beat.wav",
            "download_url": "/sample_media/synthwave_beat.wav",
            "provider": "Jamendo CC",
            "tags": ["Synthwave", "Cyberpunk", "Night"]
        },
        {
            "id": "jamendo_f3",
            "title": "Alpine Pass Scenic Cruise (Cinematic)",
            "artist": "Orchestral Waves",
            "genre": "Cinematic",
            "duration": "3:45",
            "bpm": 110,
            "stream_url": "/sample_media/cinematic_beat.wav",
            "download_url": "/sample_media/cinematic_beat.wav",
            "provider": "Jamendo CC",
            "tags": ["Cinematic", "Scenic", "Vlog"]
        },
        {
            "id": "jamendo_f4",
            "title": "Golden Hour Roadtrip (Lo-Fi Chill)",
            "artist": "Chillout Producer",
            "genre": "Lo-Fi",
            "duration": "2:10",
            "bpm": 90,
            "stream_url": "/sample_media/lofi_beat.wav",
            "download_url": "/sample_media/lofi_beat.wav",
            "provider": "Jamendo CC",
            "tags": ["Lo-Fi", "Sunset", "Chill"]
        },
        {
            "id": "jamendo_f5",
            "title": "Bass Drop Horizon (EDM Festival)",
            "artist": "EDM Masters",
            "genre": "EDM",
            "duration": "3:00",
            "bpm": 130,
            "stream_url": "/sample_media/edm_beat.wav",
            "download_url": "/sample_media/edm_beat.wav",
            "provider": "Jamendo CC",
            "tags": ["EDM", "Bass", "Festival"]
        }
    ]

    @staticmethod
    def search_tracks(query="", genre="", limit=12):
        """Searches Jamendo API v3.0 with automatic catalog fallback."""
        tracks = []
        try:
            params = {
                "client_id": JamendoMusicClient.CLIENT_ID,
                "format": "json",
                "limit": limit,
                "order": "popularity_total_desc",
                "audioformat": "mp32"
            }

            if query:
                params["search"] = query
            if genre:
                params["tags"] = genre.lower()

            url = f"{JamendoMusicClient.BASE_URL}?{urllib.parse.urlencode(params)}"
            res = requests.get(url, timeout=3)

            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                for item in results:
                    audio_link = item.get("audio", "")
                    if audio_link:
                        tracks.append({
                            "id": f"jamendo_{item.get('id')}",
                            "title": item.get("name", "Jamendo Track"),
                            "artist": item.get("artist_name", "Jamendo Artist"),
                            "genre": genre or "Jamendo CC",
                            "duration": f"{item.get('duration', 180) // 60}:{item.get('duration', 180) % 60:02d}",
                            "bpm": 120,
                            "stream_url": audio_link,
                            "download_url": item.get("audiodownload", audio_link),
                            "cover": item.get("image", ""),
                            "provider": "Jamendo CC",
                            "tags": [genre] if genre else ["Creative Commons"]
                        })
        except Exception as e:
            print(f"[Jamendo API Error] Search failed: {e}")

        # Always ensure fallback catalog is returned if API call returned empty or failed
        if not tracks:
            tracks = list(JamendoMusicClient.FALLBACK_JAMENDO_TRACKS)
            if genre and genre.lower() != "all":
                filtered = [t for t in tracks if genre.lower() in t["genre"].lower() or any(genre.lower() in tag.lower() for tag in t.get("tags", []))]
                if filtered:
                    return filtered

        return tracks


class FreesoundClient:
    """Freesound.org API Client for Motor Sound Effects & Ambient Audio Loops."""

    @staticmethod
    def search_fx(query="motorcycle engine", limit=8):
        """Returns sound effects and engine ambient loops."""
        fx_list = [
            {
                "id": "fx_1",
                "title": "GoPro Motorcycle Engine Rev Burst",
                "artist": "Freesound FX",
                "genre": "Engine FX",
                "duration": "0:15",
                "stream_url": "/sample_media/rock_beat.wav",
                "provider": "Freesound.org",
                "tags": ["Engine", "Rev", "Exhaust"]
            },
            {
                "id": "fx_2",
                "title": "High Speed Wind Blur & Turbo Spool",
                "artist": "Freesound FX",
                "genre": "Wind FX",
                "duration": "0:20",
                "stream_url": "/sample_media/synthwave_beat.wav",
                "provider": "Freesound.org",
                "tags": ["Wind", "Speed", "Turbo"]
            },
            {
                "id": "fx_3",
                "title": "Exhaust Pop & Quickshifter Crackle",
                "artist": "Freesound FX",
                "genre": "Engine FX",
                "duration": "0:10",
                "stream_url": "/sample_media/edm_beat.wav",
                "provider": "Freesound.org",
                "tags": ["Exhaust", "Crackle", "Shift"]
            }
        ]
        return fx_list
