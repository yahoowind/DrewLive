import requests
import re

PLAYLIST_URL = "https://theariatv.github.io/aria.m3u"

ALLOWED_COUNTRIES = [
    "Australia", "Canada", "Japan", "New Zealand",
    "North Korea", "United Kingdom", "United States"
]

def fetch_playlist(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def parse_and_filter(lines):
    output_lines = ["#EXTM3U"]
    keep_channel = False
    for line in lines:
        if line.startswith("#EXTINF"):
            country_match = re.search(r"group-title=\"([^\"]+)\"", line)
            country = country_match.group(1) if country_match else ""
            if any(c.lower() in country.lower() for c in ALLOWED_COUNTRIES):
                # Replace or add group-title to AriaPlus
                if "group-title=" in line:
                    line = re.sub(r'group-title="[^"]+"', 'group-title="AriaPlus"', line)
                else:
                    line = line.replace("#EXTINF", '#EXTINF group-title="AriaPlus"', 1)
                output_lines.append(line)
                keep_channel = True
            else:
                keep_channel = False
        elif line.startswith("http"):
            if keep_channel:
                output_lines.append(line)
    return "\n".join(output_lines)

if __name__ == "__main__":
    lines = fetch_playlist(PLAYLIST_URL)
    filtered_playlist = parse_and_filter(lines)
    with open("AriaPlus.m3u8", "w", encoding="utf-8") as f:
        f.write(filtered_playlist)
    print("Filtered playlist saved as AriaPlus.m3u8 with group-title forced to AriaPlus.")
