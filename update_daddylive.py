import requests

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

# Lock this channel to always use your own URL
LOCKED_CHANNEL_NAME = "TNT Sports 1 UK"
LOCKED_URL = "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MWU2NjUwNmQwZTE3LWNhYWEtMWRlNC1kYTdiLTlhNWEyY2M0/master.m3u8?md5=IQziyw_JYyWNjkUZK5qmhA&expires=1750239117&t=1750195917"  # 🔁 replace this

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
                # Write EXTINF and the LOCKED URL only
                output.append(line)
                output.append(LOCKED_URL)
                i += 2  # skip the proxied line
            else:
                output.append(line)
                i += 1

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output))

        print(f"✅ Playlist updated. '{LOCKED_CHANNEL_NAME}' is now locked to your raw URL.")

    except Exception as e:
        print(f"❌ Error updating playlist: {e}")

if __name__ == "__main__":
    update_playlist()
