import requests

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

LOCKED_CHANNEL_NAME = "TNT Sports 1 UK"
LOCKED_URL = "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MWU2NjUwNmQwZTE3LWNhYWEtMWRlNC1kYTdiLTlhNWEyY2M0/master.m3u8?md5=4soseisT-1VJHwpL0Q-NZw&expires=1750240697&t=1750197497"

# Your forced headers for that channel — add/remove as needed
FORCED_HEADERS = [
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
]

def update_playlist():
    try:
        response = requests.get(UPSTREAM_URL, timeout=20)
        response.raise_for_status()
        lines = response.text.splitlines()
        output = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if line.startswith("#EXTINF") and LOCKED_CHANNEL_NAME in line:
                print(f"🔒 Locked channel found at line {i}: {line}")
                output.append(line)
                i += 1

                # Skip existing EXT headers for this channel
                while i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                    i += 1

                # Insert your forced headers
                output.extend(FORCED_HEADERS)

                # Replace the URL with your locked URL
                output.append(LOCKED_URL)

                # Skip original URL line if present
                if i < len(lines) and not lines[i].startswith("#"):
                    print(f"Skipping original URL line at {i}: {lines[i]}")
                    i += 1
            else:
                output.append(line)
                i += 1

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output) + "\n")

        print(f"✅ Playlist updated with forced headers for '{LOCKED_CHANNEL_NAME}'.")

    except Exception as e:
        print(f"❌ Error updating playlist: {e}")

if __name__ == "__main__":
    update_playlist()
