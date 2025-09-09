import requests
import re
import os

# Config
UPSTREAM_URL = "https://bit.ly/4nnJx6S"
OUTPUT_FILE = "FSTV24.m3u8"
GROUP_PREFIX = "FSTV24"
PLACEHOLDER_TVG_ID = "24.7.Dummy.us"

# Fetch upstream playlist
try:
    response = requests.get(UPSTREAM_URL, timeout=15)
    response.raise_for_status()
    playlist_content = response.text
except Exception as e:
    print(f"Failed to fetch playlist: {e}")
    exit(1)

# Modify EXTINF lines: lowercase group-title tag, ensure tvg-id exists
def modify_extinf(content, prefix, placeholder_tvg_id):
    def repl(match):
        attrs, name = match.group(1), match.group(2)

        # Ensure tvg-id exists
        if re.search(r'tvg-id="[^"]*"', attrs):
            pass  # keep existing tvg-id
        else:
            attrs += f' tvg-id="{placeholder_tvg_id}"'

        # Lowercase group-title and prefix
        if re.search(r'GROUP-title="[^"]*"', attrs, re.IGNORECASE):
            attrs = re.sub(
                r'GROUP-title="([^"]*)"',
                lambda m: f'group-title="{prefix} - {m.group(1)}"',
                attrs,
                flags=re.IGNORECASE
            )
        else:
            attrs += f' group-title="{prefix}"'

        return f"#EXTINF:{attrs},{name}"

    return re.sub(r'#EXTINF:([^\n,]+),(.*)', repl, content)

modified_content = modify_extinf(playlist_content, GROUP_PREFIX, PLACEHOLDER_TVG_ID)

# Ensure folder exists and save playlist
os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_FILE)), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(modified_content)

print(f"✅ Playlist saved as {os.path.abspath(OUTPUT_FILE)} with tvg-id set to placeholder if missing")
