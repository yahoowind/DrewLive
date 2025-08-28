import requests
import re

PLAYLIST_URL = "https://aria.bnkd.xyz/aria.m3u"

# Only these countries/groups will be included
ALLOWED_COUNTRIES = [
    "Australia", "Canada", "Japan", "New Zealand",
    "North Korea", "United Kingdom", "United States", "Aria Web Channels"
]

ARIA_GROUP_NAME = "Aria Web Channels"

def fetch_playlist(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def force_group_title(line, group_name):
    """Force a new group-title on an #EXTINF line"""
    line = re.sub(r'\s*group-title="[^"]*"', '', line)
    if line.startswith("#EXTINF:"):
        parts = line.split(",", 1)
        header = parts[0].strip()
        title = parts[1] if len(parts) > 1 else ""
        header += f' group-title="AriaPlus - {group_name}"'
        return f"{header},{title}"
    return line

def parse_and_filter(lines):
    channels_by_country = {country: [] for country in ALLOWED_COUNTRIES}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            url = lines[i + 1].strip() if i + 1 < len(lines) else ""
            title_text = line.split(",", 1)[1] if "," in line else ""

            # Determine country/group
            country_found = None
            if "aria" in title_text.lower() or "aria" in url.lower():
                country_found = ARIA_GROUP_NAME
            else:
                for country in ALLOWED_COUNTRIES:
                    if country != ARIA_GROUP_NAME and country.lower() in title_text.lower():
                        country_found = country
                        break

            # Include only if it's in allowed countries
            if country_found:
                new_extinf = force_group_title(line, country_found)
                channels_by_country[country_found].append((new_extinf, url))

            i += 2  # skip URL line
        else:
            i += 1

    # Build final playlist sorted by ALLOWED_COUNTRIES order
    output_lines = ["#EXTM3U"]
    for country in ALLOWED_COUNTRIES:
        group_name = ARIA_GROUP_NAME if country == ARIA_GROUP_NAME else country
        for extinf, url in channels_by_country.get(group_name, []):
            output_lines.append(extinf)
            output_lines.append(url)

    return "\n".join(output_lines)

if __name__ == "__main__":
    lines = fetch_playlist(PLAYLIST_URL)
    filtered_playlist = parse_and_filter(lines)
    with open("AriaPlus.m3u8", "w", encoding="utf-8") as f:
        f.write(filtered_playlist)
    print("✅ AriaPlus playlist updated and channels grouped strictly by allowed countries.")
