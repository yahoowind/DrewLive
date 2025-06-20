import requests
from datetime import datetime
import os

PROXY_URL = "https://tinyurl.com/DaddyEvents24"
OUTPUT_FILE = os.path.abspath("DaddyLiveEvents.m3u8")

def fetch_and_save_playlist():
    print(f"🔍 Fetching playlist from: {PROXY_URL}")
    resp = requests.get(PROXY_URL)

    print(f"➡️ Status Code: {resp.status_code}")
    print(f"➡️ Final Redirected URL: {resp.url}")

    try:
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return

    playlist_content = resp.text.strip()
    if not playlist_content:
        print("⚠️ Warning: The fetched playlist is empty!")
        return

    # Add timestamp header to verify freshness
    timestamp = f"# Updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    full_content = timestamp + playlist_content

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"✅ Playlist updated and saved to:\n  {OUTPUT_FILE}")
    print("📦 First few lines:\n" + "\n".join(full_content.splitlines()[:5]))

if __name__ == "__main__":
    fetch_and_save_playlist()
