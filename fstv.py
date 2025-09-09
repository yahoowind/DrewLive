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

# Insert tvg-id if missing, keep -1 and other attributes intact
def fix_tvg_id(content, placeholder):
    def repl(match):
        prefix, attrs, name = match.group(1), match.group(2), match.group(3)
        if 'tvg-id=' not in attrs:
            attrs = f'tvg-id="{placeholder}" {attrs.strip()}'
        return f"#EXTINF:{prefix} {attrs},{name}"
    
    # Matches #EXTINF:-1 <attrs>,Channel Name
    return re.sub(r'#EXTINF:(-?\d+)\s*([^\n,]*),(.*)', repl, content)

modified_content = fix_tvg_id(playlist_content, PLACEHOLDER_TVG_ID)

# Save playlist
os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_FILE)), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(modified_content)

print(f"✅ Playlist saved as {os.path.abspath(OUTPUT_FILE)} with tvg-id placeholder correctly applied")
