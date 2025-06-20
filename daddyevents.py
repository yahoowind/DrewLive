import requests

PROXY_URL = "https://tinyurl.com/DaddyEvents24"
OUTPUT_FILE = "DaddyLiveEvents.m3u8"

def fetch_and_save_playlist():
    print(f"🔍 Fetching playlist from: {PROXY_URL}")
    resp = requests.get(PROXY_URL)

    print(f"➡️ Status Code: {resp.status_code}")
    print(f"➡️ Final URL: {resp.url}")

    try:
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return

    playlist_content = resp.text
    if not playlist_content.strip():
        print("⚠️ Warning: The fetched playlist is empty!")
        return

    print(f"📦 Sample Content:\n{playlist_content[:300]}...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(playlist_content)

    print(f"✅ Playlist saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_and_save_playlist()
