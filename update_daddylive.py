import requests

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

# Shared headers for both locked channels
FORCED_HEADERS = [
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
]

# Locked channels and their direct stream number ID's
LOCKED_CHANNELS = {
    "NBC10 Philadelphia": "277",
    "TNT Sports 1 UK": "31",
    "Discovery Channel": "313",
    "Discovery Life Channel": "311",
    "Disney Channel": "312",
    "Disney XD": "314",
    "E! Entertainment": "315",
    "ESPN Deportes": "375",
    "ESPN USA": "44",
    "ESPN2 USA": "45",
    "ESPNews": "288",
    "ESPNU USA": "316",
    "Fox Business": "297",
    "Fox News": "347",
    "Fox Sports 1": "39",
    "FOX USA": "54",
    "Freeform": "301",
    "FOX USA": "54",
    "FUSE TV USA": "279",
    "FX Movie Channel": "381",
    "FX USA": "317",
    "FXX USA": "298",
    "Game Show Network": "319",
    "GOLF Channel USA": "318",
    "Hallmark Movies & Mysteries": "296",
    "HBO USA": "321",
    "Headline News": "323",
    "HGTV": "382",
    "History USA": "322",
    "Investigation Discovery (ID USA)": "324",
    "ION USA": "325",
    "Law & Crime Network": "278",
    "Lifetime Movies Network": "389",
    "Lifetime Network": "326",
    "Magnolia Network": "299",
    "MSNBC": "327",
    "MTV USA": "371",
    "National Geographic (NGC)": "328",
    "NBC Sports Philadelphia": "777",
    "NBC USA": "53",
    "NewsNation USA": "292",
    "NICK": "330",
    "NICK JR": "329",
    "Oprah Winfrey Network (OWN)": "331",
    "Oxygen True Crime": "332",        
    "Pac-12 Network USA": "287",        
    "Paramount Network": "334",
    "Reelz Channel": "293",
    "Science Channel": "294",
    "SEC Network USA": "385",
    
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
