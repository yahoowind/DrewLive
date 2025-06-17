# daddylive.py
import requests

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

def update_playlist():
    try:
        response = requests.get(UPSTREAM_URL, timeout=20)
        response.raise_for_status()
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(response.text)
        print("✅ Playlist updated successfully.")
    except Exception as e:
        print(f"❌ Failed to update playlist: {e}")

if __name__ == "__main__":
    update_playlist()