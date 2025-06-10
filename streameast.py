import requests
import re

URL = "https://iptv-scraper-re.vercel.app/streameast"
OUTPUT_FILE = "StreamEast.m3u"
FORCED_GROUP = "StreamEast"
FORCED_TVG_ID = "24.7.Dummy.us"
CUSTOM_EPG = "https://tinyurl.com/dummy2423-epg"

def fetch_playlist(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def force_metadata(extinf_line):
    parts = extinf_line.split(",", 1)
    metadata = parts[0]
    title = parts[1] if len(parts) > 1 else ""

    # Force or replace tvg-id
    if 'tvg-id="' in metadata:
        metadata = re.sub(r'tvg-id=".*?"', f'tvg-id="{FORCED_TVG_ID}"', metadata)
    else:
        metadata += f' tvg-id="{FORCED_TVG_ID}"'

    # Force or replace group-title
    if 'group-title="' in metadata:
        metadata = re.sub(r'group-title=".*?"', f'group-title="{FORCED_GROUP}"', metadata)
    else:
        metadata += f' group-title="{FORCED_GROUP}"'

    return f"{metadata},{title}"

def build_playlist(raw):
    lines = raw.splitlines()
    output = []

    # Ensure the #EXTM3U header is at the top
    if not lines[0].startswith("#EXTM3U"):
        lines.insert(0, "#EXTM3U")
    output.append(f'#EXTM3U url-tvg="{CUSTOM_EPG}"')

    i = 1
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF"):
            # Force metadata line
            output.append(force_metadata(line))
            i += 1

            # Collect any optional headers
            while i < len(lines) and lines[i].startswith("#") and not lines[i].startswith("#EXTINF"):
                output.append(lines[i].strip())
                i += 1

            # Add the actual stream URL
            if i < len(lines) and not lines[i].startswith("#"):
                output.append(lines[i].strip())
                i += 1

        else:
            # Pass through any unrecognized headers cleanly
            if line.startswith("#") or line.strip() == "":
                output.append(line)
            i += 1

    return "\n".join(output) + "\n"

def main():
    try:
        raw = fetch_playlist(URL)
    except Exception as e:
        print(f"❗ Fetch failed: {e}")
        return
    final = build_playlist(raw)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final)
    print(f"✅ Saved {OUTPUT_FILE} ({len(final.splitlines())} lines)")

if __name__ == "__main__":
    main()