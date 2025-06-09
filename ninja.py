import requests
import time

PLAYLIST_URL = "http://drewlive24.duckdns.org:8090/playlist"
FORCED_GROUP = "BinaryNinjaTV"
FORCED_EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "BinaryNinjaTV.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DrewPlaylistBot/1.0; +http://drewlive24.duckdns.org)"
}

def fetch_playlist(retries=3, delay=3):
    for attempt in range(retries):
        try:
            response = requests.get(PLAYLIST_URL, timeout=15, headers=HEADERS)
            if response.status_code == 200 and "#EXTM3U" in response.text:
                return response.text
            else:
                print(f"[WARN] Attempt {attempt+1}: Received status {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Attempt {attempt+1}: {e}")
        time.sleep(delay)
    return None

def process_playlist(text):
    lines = text.splitlines()
    output_lines = []

    for line in lines:
        if line.startswith("#EXTM3U"):
            output_lines.append(f'#EXTM3U tvg-url="{FORCED_EPG_URL}"')
        elif line.startswith("#EXTINF"):
            if 'group-title="' in line:
                start = line.find('group-title="')
                end = line.find('"', start + 13)
                line = line[:start] + f'group-title="{FORCED_GROUP}"' + line[end+1:]
            else:
                line = line.replace('#EXTINF:-1', f'#EXTINF:-1 group-title="{FORCED_GROUP}"')
            output_lines.append(line)
        else:
            output_lines.append(line)

    return "\n".join(output_lines)

def save_playlist(text):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[DONE] Playlist saved to '{OUTPUT_FILE}'")

def main():
    print("[INFO] Fetching playlist...")
    raw = fetch_playlist()
    if not raw:
        print("[FATAL] Could not retrieve playlist after multiple attempts.")
        return

    print("[INFO] Processing playlist...")
    updated = process_playlist(raw)

    print("[INFO] Saving output...")
    save_playlist(updated)

if __name__ == "__main__":
    main()