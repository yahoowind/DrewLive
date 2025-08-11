import requests
import re

UPSTREAM_URL = "https://pigscanflyyy-scraper.vercel.app/tims"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"
FORCED_TVG_ID = "24.7.Dummy.us"

def fetch_url(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def modify_playlist(playlist_text):
    # Inject FORCED_GROUP and FORCED_TVG_ID into each #EXTINF line
    def repl(match):
        attrs = match.group(1)
        # Remove existing tvg-id and group-title if present
        attrs = re.sub(r'tvg-id="[^"]*"', '', attrs)
        attrs = re.sub(r'group-title="[^"]*"', '', attrs)
        attrs = attrs.strip()

        new_attrs = f'tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}"'
        if attrs:
            new_attrs = attrs + ' ' + new_attrs
        return f'#EXTINF:{new_attrs},'

    modified = re.sub(r'#EXTINF:([^\n]*),', repl, playlist_text)
    return modified

def main():
    print("Fetching upstream playlist...")
    playlist = fetch_url(UPSTREAM_URL)
    if playlist is None:
        print("Failed to fetch upstream playlist. Exiting.")
        return

    print("Modifying playlist with forced group and tvg-id...")
    modified_playlist = modify_playlist(playlist)

    print(f"Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(modified_playlist)

    print("Done.")

if __name__ == "__main__":
    main()
