import requests
import re

PLAYLIST_URL = "https://aria.bnkd.xyz/aria.m3u"

ALLOWED_COUNTRIES = [
    "Australia", "Canada", "Japan", "New Zealand",
    "North Korea", "United Kingdom", "United States", "Aria Web Channels"
]

COUNTRY_ALIASES = {
    "Australia": ["Australia", "AUS"],
    "Canada": ["Canada", "CAN"],
    "Japan": ["Japan", "JP", "JPN", "NHK", "TV Asahi", "Fuji TV", "Tokyo"],
    "New Zealand": ["New Zealand", "NZ"],
    "North Korea": ["North Korea", "DPRK"],
    "United Kingdom": ["United Kingdom", "UK", "Britain", "England"],
    "United States": ["United States", "USA", "US", "America"],
    "Aria Web Channels": ["Aria Web Channels", "aria"]  # auto-include Aria channels
}

def fetch_playlist(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def force_group_title(line, group_name):
    line = re.sub(r'\s*group-title="[^"]*"', '', line)
    if line.startswith("#EXTINF:"):
        parts = line.split(",", 1)
        header = parts[0].strip()
        title = parts[1] if len(parts) > 1 else ""
        header += f' group-title="{group_name}"'
        return f"{header},{title}"
    return line

def parse_and_filter(lines):
    output_lines = ["#EXTM3U"]
    keep_channel = False

    for line in lines:
        if line.startswith("#EXTINF:"):
            title_text = line.split(",", 1)[1] if "," in line else ""
            search_area = line.lower() + " " + title_text.lower()

            matched_country = None
            for country in ALLOWED_COUNTRIES:
                aliases = COUNTRY_ALIASES.get(country, [])
                if any(alias.lower() in search_area for alias in aliases):
                    matched_country = country
                    break

            if matched_country:
                line = force_group_title(line, f'AriaPlus - {matched_country}')
                output_lines.append(line)
                keep_channel = True
            else:
                keep_channel = False

        elif line.startswith("http") and keep_channel:
            output_lines.append(line)

    return "\n".join(output_lines)

if __name__ == "__main__":
    lines = fetch_playlist(PLAYLIST_URL)
    filtered_playlist = parse_and_filter(lines)
    with open("AriaPlus.m3u8", "w", encoding="utf-8") as f:
        f.write(filtered_playlist)
    print("✅ AriaPlus playlist updated with only allowed countries + Aria Web Channels.")
