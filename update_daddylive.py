import requests

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

# Shared headers for both locked channels
FORCED_HEADERS = [
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
]

# Locked channels and their direct stream URLs
LOCKED_CHANNELS = {
    "TNT Sports 1 UK": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MWU2NjUwNmQwZTE3LWNhYWEtMWRlNC1kYTdiLTlhNWEyY2M0/master.m3u8?md5=4soseisT-1VJHwpL0Q-NZw&expires=1750240697&t=1750197497",
    "Discovery Channel": "https://hipaf6u2j3pwygg.nice-flower.store/v4/variant/VE1gTdz0mLzRnLv52bt9SMhFjdtM3ajFmc09SMkVDZldTMjRmM1UWL4gzY40yYyYDNtM2YhFTL4QTYxcDMwM2L.m3u8?md5=P_ZRKSUAQTEs1klzlorEJQ&expires=1750248906&t=1750205706",
}

def update_playlist():
    try:
        response = requests.get(UPSTREAM_URL, timeout=20)
        response.raise_for_status()
        lines = response.text.splitlines()
        output = []
        i = 0

        while i < len(lines):
            line = lines[i]

            matched = None
            for channel_name in LOCKED_CHANNELS:
                if line.startswith("#EXTINF") and channel_name in line:
                    matched = channel_name
                    break

            if matched:
                output.append(line)
                i += 1

                # Skip existing headers
                while i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                    i += 1

                # Insert shared headers
                output.extend(FORCED_HEADERS)

                # Replace URL
                output.append(LOCKED_CHANNELS[matched])

                # Skip original URL if it's still present
                if i < len(lines) and not lines[i].startswith("#"):
                    i += 1
            else:
                output.append(line)
                i += 1

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output) + "\n")

        print("✅ Playlist updated with locked streams and headers.")

    except Exception as e:
        print(f"❌ Error updating playlist: {e}")

if __name__ == "__main__":
    update_playlist()
