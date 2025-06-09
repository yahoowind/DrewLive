import requests
import re

UPSTREAM_URL = "http://tvpass.org/playlist/m3u"
OUTPUT_FILE = "TVPass.m3u"
FORCED_GROUP = "TVPass"

def fetch_playlist():
    res = requests.get(UPSTREAM_URL, timeout=15)
    res.raise_for_status()
    return res.text.splitlines()

def force_group_title(line):
    if 'group-title="' in line:
        # Replace existing group-title only
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP}"', line)
    else:
        # Insert group-title before the first comma (metadata block)
        match = re.match(r'(#EXTINF:-?\d+)(.*?)(,.*)', line)
        if match:
            prefix, attrs, title = match.groups()
            # Insert group-title while preserving all other attributes
            new_attrs = f'{attrs} group-title="{FORCED_GROUP}"'
            return f'{prefix}{new_attrs}{title}'
        else:
            return line  # Fail-safe: return unchanged

def process_and_write_playlist(lines):
    output_lines = []

    for i, line in enumerate(lines):
        if line.startswith("#EXTINF"):
            output_lines.append(force_group_title(line))
            # Append the stream URL right after
            if i + 1 < len(lines):
                output_lines.append(lines[i + 1].strip())
        elif line.startswith("#EXTM3U"):
            output_lines.append(line)
        elif not lines[i-1].startswith("#EXTINF"):
            output_lines.append(line)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"[✅] {OUTPUT_FILE} saved with brute-forced group-title='{FORCED_GROUP}' and 0 logo/tvg-id loss.")

if __name__ == "__main__":
    playlist_lines = fetch_playlist()
    process_and_write_playlist(playlist_lines)
