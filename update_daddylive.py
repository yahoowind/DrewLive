import requests

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

# Special unproxied entry to preserve
SPECIAL_ENTRY = '''#EXTINF:-1  tvg-id="TNT.Sports.1.HD.uk" tvg-logo="https://github.com/tv-logo/tv-logos/blob/main/countries/united-kingdom/tnt-sports-1-uk.png?raw=true" group-title="DaddyLive UK",TNT Sports 1 UK
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0
#EXTVLCOPT:http-origin=https://veplay.top
#EXTVLCOPT:http-referrer=https://veplay.top/
https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MWU2NjUwNmQwZTE3LWNhYWEtMWRlNC1kYTdiLTlhNWEyY2M0/master.m3u8?md5=4soseisT-1VJHwpL0Q-NZw&expires=1750240697&t=1750197497
'''

def update_playlist():
    try:
        response = requests.get(UPSTREAM_URL, timeout=20)
        response.raise_for_status()

        new_content = response.text

        # If the special entry is not already in the new playlist, add it at the top
        if "TNT Sports 1 UK" not in new_content:
            new_content = SPECIAL_ENTRY.strip() + "\n" + new_content

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)

        print("✅ Playlist updated successfully with preserved special entry.")
    except Exception as e:
        print(f"❌ Failed to update playlist: {e}")

if __name__ == "__main__":
    update_playlist()
