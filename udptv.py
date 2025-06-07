import requests
import re

UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP = 'UDPTV Live Streams'

# Lines matching these patterns will be removed entirely from the output
REMOVE_PATTERNS = [
    re.compile(r'^# (Last updated|Updated):', re.IGNORECASE),
    re.compile(r'^### IF YOU ARE A RESELLER OR LEECHER', re.IGNORECASE),
]

def fetch_playlist():
    try:
        res = requests.get(UPSTREAM_URL, timeout=10)
        res.raise_for_status()
        return res.text.splitlines()
    except Exception as e:
        print(f"Failed to fetch playlist: {e}")
        return []

def should_remove_line(line):
    return any(pattern.match(line) for pattern in REMOVE_PATTERNS)

def patch_group_title(extinf_line):
    # Replace or add group-title with FORCED_GROUP, keep everything else intact
    if 'group-title="' in extinf_line:
        # Replace existing group-title value
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP}"', extinf_line)
    else:
        # Add group-title just after #EXTINF: part, keep existing duration if any
        return re.sub(r'(#EXTINF:-?\d*)', fr'\1 group-title="{FORCED_GROUP}"', extinf_line)

def process_and_write(lines):
    output = [f'#EXTM3U url-tvg="{EPG_URL}"\n']  # Write header with EPG

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Remove unwanted lines outright
        if should_remove_line(line):
            i += 1
            continue

        if line.startswith("#EXTINF"):
            patched_line = patch_group_title(line)
            output.append(patched_line + "\n")

            # Next line should be the stream URL; include as-is if present
            if i + 1 < len(lines):
                output.append(lines[i + 1].strip() + "\n")
                i += 2
            else:
                i += 1
        else:
            # Preserve any other lines (like comments, blank lines, or options)
            output.append(line + "\n")
            i += 1

    # Write all to file (overwrite every time)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(output)

    print(f"{OUTPUT_FILE} has been updated successfully with forced group '{FORCED_GROUP}'.")

if __name__ == "__main__":
    playlist_lines = fetch_playlist()
    if playlist_lines:
        process_and_write(playlist_lines)
    else:
        print("No playlist content fetched. File not updated.")
