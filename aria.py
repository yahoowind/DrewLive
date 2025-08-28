import requests
import re

PLAYLIST_URL = "https://aria.bnkd.xyz/aria.m3u"
OUTPUT_FILE = "AriaPlus.m3u8"

# Only these groups are allowed
ALLOWED_GROUPS = [
    "Australia", "Canada", "Japan", "New Zealand",
    "North Korea", "United Kingdom", "United States", "Aria Web Channels"
]

def fetch_playlist(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def remap_group_title(line):
    """Force group-title to AriaPlus - <original group> if allowed"""
    if line.startswith("#EXTINF:"):
        match = re.search(r'group-title="([^"]*)"', line)
        original_group = match.group(1) if match else "Unknown"
        if original_group not in ALLOWED_GROUPS:
            return None  # discard if not in allowed groups
        # Remove old group-title
        line = re.sub(r'\s*group-title="[^"]*"', '', line)
        # Add new group-title
        parts = line.split(",", 1)
        header = parts[0].strip()
        title = parts[1] if len(parts) > 1 else ""
        header += f' group-title="AriaPlus - {original_group}"'
        return f"{header},{title}"
    return line

def process_playlist(lines):
    output_lines = ["#EXTM3U"]
    keep_channel = False
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            new_line = remap_group_title(line)
            if new_line:
                output_lines.append(new_line)
                keep_channel = True
            else:
                keep_channel = False
        elif line.startswith("http") and keep_channel:
            output_lines.append(line)
        # ignore other lines
    return "\n".join(output_lines)

if __name__ == "__main__":
    lines = fetch_playlist(PLAYLIST_URL)
    filtered_playlist = process_playlist(lines)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(filtered_playlist)
    print(f"✅ AriaPlus playlist filtered and saved to {OUTPUT_FILE}")
