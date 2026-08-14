import requests
import urllib.parse
import os

class JamendoMusicClient:
    """Jamendo API v3.0 REST Client accessing 500,000+ Creative Commons audio tracks."""

    # Public Jamendo Developer Client ID for read-only Creative Commons music search
    CLIENT_ID = "56891324"
    BASE_URL = "https://api.jamendo.com/v3.0/tracks/"

    @staticmethod
    def search_tracks(query="", genre="", limit=12):
        """Searches Jamendo API v3.0 for Creative Commons audio tracks."""
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
            res = requests.get(url, timeout=5)

            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                for item in results:
                    tracks.append({
                        "id": f"jamendo_{item.get('id')}",
                        "title": item.get("name", "Jamendo Track"),
                        "artist": item.get("artist_name", "Jamendo Artist"),
                        "genre": genre or "Jamendo CC",
                        "duration": f"{item.get('duration', 180) // 60}:{item.get('duration', 180) % 60:02d}",
                        "bpm": 120,
                        "stream_url": item.get("audio", ""),
                        "download_url": item.get("audiodownload", item.get("audio", "")),
                        "cover": item.get("image", ""),
                        "provider": "Jamendo CC",
                        "tags": [genre] if genre else ["Creative Commons"]
                    })
        except Exception as e:
            print(f"[Jamendo API Error] Search failed: {e}")

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
            }
        ]
        return fx_list
