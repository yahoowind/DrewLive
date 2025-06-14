import requests
import re
import time

URL_BASE = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Tims247Live.m3u"
OUTPUT_FILE = "Tims247Live.m3u"
FORCED_GROUP = "Tims247Live"
FORCED_TVG_ID = "24.7.Dummy.us"
CUSTOM_EPG = "https://tinyurl.com/dummy2423-epg"

def fetch_playlist(url_base):
    timestamp = int(time.time())
    url = f"{url_base}?_={timestamp}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def force_metadata(extinf_line):
    parts = extinf_line.split(",", 1)
    metadata = parts[0]
    title = parts[1] if len(parts) > 1 else ""

    if 'tvg-id="' in metadata:
        metadata = re.sub(r'tvg-id=".*?"', f'tvg-id="{FORCED_TVG_ID}"', metadata)
    else:
        metadata += f' tvg-id="{FORCED_TVG_ID}"'

    if 'group-title="' in metadata:
        metadata = re.sub(r'group-title=".*?"', f'group-title="{FORCED_GROUP}"', metadata)
    else:
        metadata += f' group-title="{FORCED_GROUP}"'

    return f"{metadata},{title}"

def build_playlist(raw):
    lines = raw.splitlines()
    output = []

    output.append(f'#EXTM3U url-tvg="{CUSTOM_EPG}"')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF"):
            output.append(force_metadata(line))
            i += 1

            while i < len(lines) and lines[i].startswith("#") and not lines[i].startswith("#EXTINF"):
                output.append(lines[i].strip())
                i += 1

            if i < len(lines) and not lines[i].startswith("#"):
                output.append(lines[i].strip())
                i += 1

        else:
            if line.startswith("#") or line == "":
                output.append(line)
            i += 1

    return "\n".join(output) + "\n"

def main():
    try:
        raw = fetch_playlist(URL_BASE)
    except Exception as e:
        print(f"❗ Fetch failed: {e}")
        return
    final = build_playlist(raw)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final)
    print(f"✅ Saved {OUTPUT_FILE} ({len(final.splitlines())} lines)")

if __name__ == "__main__":
    main()
