import requests
import re
import time

UPSTREAM_URL = "https://pigscanflyyy-scraper.vercel.app/tims"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"
FORCED_TVG_ID = "24.7.Dummy.us"

def fetch_url(url, retries=5, delay=5):
    headers = {"User-Agent": "Mozilla/5.0 (GitHubActions; Python Requests)"}
    for attempt in range(1, retries + 1):
        try:
            print(f"Fetching {url} (Attempt {attempt}/{retries})...")
            r = requests.get(url, headers=headers, timeout=45)
            print(f"Status: {r.status_code}")
            if r.status_code != 200:
                time.sleep(delay)
                continue
            return r.text
        except Exception as e:
            print(f"Error: {e}, retrying in {delay}s...")
            time.sleep(delay)
    return None

def modify_playlist(playlist_text):
    def repl(match):
        attrs = match.group(1)
        attrs = re.sub(r'tvg-id="[^"]*"', '', attrs)
        attrs = re.sub(r'group-title="[^"]*"', '', attrs)
        attrs = attrs.strip()
        new_attrs = f'tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}"'
        if attrs:
            new_attrs = attrs + ' ' + new_attrs
        return f'#EXTINF:{new_attrs},'
    return re.sub(r'#EXTINF:([^\n]*),', repl, playlist_text)

def main():
    playlist = fetch_url(UPSTREAM_URL)
    if playlist is None:
        print("Failed to fetch upstream playlist. Exiting.")
        return
    modified_playlist = modify_playlist(playlist)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(modified_playlist)
    print("✅ Done.")

if __name__ == "__main__":
    main()
