import requests
import re
import os

# Config
UPSTREAM_URL = "https://bit.ly/4nnJx6S"
OUTPUT_FILE = "FSTV24.m3u8"
PLACEHOLDER_TVG_ID = "24.7.Dummy.us"

# Fetch upstream playlist
try:
    response = requests.get(UPSTREAM_URL, timeout=15)
    response.raise_for_status()
    playlist_content = response.text
except Exception as e:
    print(f"Failed to fetch playlist: {e}")
    exit(1)

# Modify EXTINF lines: ensure tvg-id exists, keep everything else unchanged
def ensure_tvg_id(content, placeholder_tvg_id):
    def repl(match):
        attrs, name = match.group(1), match.group(2)

        # Ensure tvg-id exists
        if not re.search(r'tvg-id="[^"]*"', attrs):
            attrs += f' tvg-id="{placeholder_tvg_id}"'

        return f"#EXTINF:{attrs},{name}"

    return re.sub(r'#EXTINF:([^\n,]+),(.*)', repl, content)

modified_content = ensure_tvg_id(playlist_content, PLACEHOLDER_TVG_ID)

# Ensure folder exists and save playlist
os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_FILE)), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(modified_content)

print(f"✅ Playlist saved as {os.path.abspath(OUTPUT_FILE)} with placeholder tvg-id added where missing")
