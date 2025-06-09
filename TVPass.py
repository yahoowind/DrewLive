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
    # If group-title present, replace it; else add it after #EXTINF: part
    if 'group-title="' in line:
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP}"', line)
    else:
        return line.replace('#EXTINF:', f'#EXTINF:-1 group-title="{FORCED_GROUP}" ', 1)

def process_and_write_playlist(lines):
    output_lines = []

    for i, line in enumerate(lines):
        if line.startswith("#EXTINF"):
            # Force group-title but keep rest metadata intact
            new_line = force_group_title(line)
            output_lines.append(new_line)
            # Append next line (URL) if exists
            if i + 1 < len(lines):
                output_lines.append(lines[i + 1].strip())
        elif line.startswith("#EXTM3U"):
            # Keep #EXTM3U header as is, no forced tvg-url
            output_lines.append(line)
        else:
            # Other lines (comments, logos, tv ids, etc.) stay untouched
            if not line.startswith("#EXTINF") and (i == 0 or not lines[i-1].startswith("#EXTINF")):
                output_lines.append(line)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"[✅] {OUTPUT_FILE} updated with forced group-title='{FORCED_GROUP}' and untouched metadata.")

if __name__ == "__main__":
    playlist_lines = fetch_playlist()
    process_and_write_playlist(playlist_lines)