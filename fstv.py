import requests
import time

URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/FSTVLive.m3u"
OUTPUT_FILE = "FSTVLive.m3u"

def fetch_playlist(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def build_playlist(raw):
    lines = raw.splitlines()
    output = []

    if lines:
        output.append(lines[0])  # Keep original #EXTM3U or header
        i = 1
    else:
        return ""

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF"):
            output.append(line)
            i += 1

            # Add any metadata lines that follow (e.g., logos, comments)
            while i < len(lines) and lines[i].startswith("#") and not lines[i].startswith("#EXTINF"):
                output.append(lines[i].strip())
                i += 1

            # Append timestamp to actual stream URL
            if i < len(lines) and not lines[i].startswith("#"):
                stream_url = lines[i].strip()
                if stream_url.endswith(".m3u8"):
                    stream_url += f"?t={int(time.time())}"
                output.append(stream_url)
                i += 1

        else:
            output.append(line)
            i += 1

    return "\n".join(output) + "\n"

def main():
    try:
        raw = fetch_playlist(URL)
        final = build_playlist(raw)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(final)
        print(f"✅ Saved {OUTPUT_FILE} with cache-busted URLs.")
    except Exception as e:
        print(f"❗ Error: {e}")

if __name__ == "__main__":
    main()