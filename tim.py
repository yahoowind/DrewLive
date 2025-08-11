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
        duration = match.group(1)  # e.g. "-1"
        attrs_str = match.group(2) or ""  # attributes like tvg-id, group-title, etc.
        channel_name = match.group(3) or ""  # channel name

        # Remove existing tvg-id and group-title attrs
        attrs_str = re.sub(r'tvg-id="[^"]*"', '', attrs_str)
        attrs_str = re.sub(r'group-title="[^"]*"', '', attrs_str)

        attrs_str = attrs_str.strip()
        # Add forced attributes, preserving any other attributes
        forced_attrs = f'tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}"'

        if attrs_str:
            new_attrs = attrs_str + ' ' + forced_attrs
        else:
            new_attrs = forced_attrs

        # Rebuild the #EXTINF line:
        return f'#EXTINF:{duration} {new_attrs},{channel_name}'

    pattern = re.compile(r'#EXTINF:([-\d\.]+)\s*([^,]*),(.*)')
    return pattern.sub(repl, playlist_text)

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
