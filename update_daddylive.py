import requests

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

LOCKED_CHANNEL_NAME = "TNT Sports 1 UK"
LOCKED_URL = "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MWU2NjUwNmQwZTE3LWNhYWEtMWRlNC1kYTdiLTlhNWEyY2M0/master.m3u8?md5=4soseisT-1VJHwpL0Q-NZw&expires=1750240697&t=1750197497"

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
                # Write EXTINF line (channel info)
                output.append(line)
                i += 1

                # Write all header lines (#EXTVLCOPT:...) that follow
                while i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                    output.append(lines[i])
                    i += 1

                # Replace next line (the URL) with locked URL
                if i < len(lines):
                    output.append(LOCKED_URL)
                    i += 1  # skip old URL line
                else:
                    # no URL line? just add locked URL anyway
                    output.append(LOCKED_URL)

            else:
                output.append(line)
                i += 1

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output) + "\n")

        print(f"✅ Playlist updated. '{LOCKED_CHANNEL_NAME}' URL replaced but headers preserved.")

    except Exception as e:
        print(f"❌ Error updating playlist: {e}")

if __name__ == "__main__":
    update_playlist()
