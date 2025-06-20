import requests

PROXY_URL = "https://tinyurl.com/DrewProxy224"  # Your proxy URL
OUTPUT_FILE = "DaddyLive.m3u8"

def fetch_and_save_playlist():
    print(f"Fetching playlist from proxy: {PROXY_URL}")
    resp = requests.get(PROXY_URL)
    resp.raise_for_status()

    playlist_content = resp.text
    if not playlist_content.strip():
        print("⚠️ Warning: The fetched playlist is empty!")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(playlist_content)

    print(f"✅ Playlist saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_and_save_playlist()
