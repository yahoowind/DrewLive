import requests

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"
UNPROXIED_CHANNEL = "TNT Sports 1 UK"

def update_playlist():
    try:
        response = requests.get(UPSTREAM_URL, timeout=20)
        response.raise_for_status()
        lines = response.text.splitlines()
        output_lines = []
        skip_proxy = False

        for i, line in enumerate(lines):
            if line.startswith("#EXTINF") and UNPROXIED_CHANNEL in line:
                skip_proxy = True
                output_lines.append(line)  # Keep the EXTINF line
                if i + 1 < len(lines):
                    output_lines.append(lines[i + 1])  # Keep the next URL line
            elif skip_proxy:
                skip_proxy = False  # Skip the proxy logic for this pair
            elif not skip_proxy:
                output_lines.append(line)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))

        print("✅ Playlist updated successfully, with one unproxied channel.")

    except Exception as e:
        print(f"❌ Failed to update playlist: {e}")

if __name__ == "__main__":
    update_playlist()
