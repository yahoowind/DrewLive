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

def force_group_title(line, country):
    # Remove any existing group-title attribute
    line = re.sub(r'\s*group-title="[^"]*"', '', line)
    # Clean extra spaces
    line = re.sub(r'\s{2,}', ' ', line).strip()

    if line.startswith("#EXTINF:"):
        parts = line.split(",", 1)
        header = parts[0]
        title = parts[1] if len(parts) > 1 else ""

        # Compose new group-title: AriaPlus - CountryName
        new_group = f'AriaPlus - {country}'

        # Append forced group-title exactly after the duration part
        header = header.strip() + f' group-title="{new_group}"'

        return f"{header},{title}"
    return line

def parse_and_filter(lines):
    output_lines = ["#EXTM3U"]
    keep_channel = False
    current_country = ""

    for line in lines:
        if line.startswith("#EXTINF"):
            country_match = re.search(r'group-title="([^"]+)"', line)
            country = country_match.group(1) if country_match else ""

            matched_country = ""
            for c in ALLOWED_COUNTRIES:
                if c.lower() in country.lower():
                    matched_country = c
                    break

            if matched_country:
                line = force_group_title(line, matched_country)
                output_lines.append(line)
                keep_channel = True
                current_country = matched_country
            else:
                keep_channel = False
                current_country = ""
        elif line.startswith("http"):
            if keep_channel:
                output_lines.append(line)
    return "\n".join(output_lines)

if __name__ == "__main__":
    lines = fetch_playlist(PLAYLIST_URL)
    filtered_playlist = parse_and_filter(lines)
    with open("AriaPlus.m3u8", "w", encoding="utf-8") as f:
        f.write(filtered_playlist)
    print("✅ AriaPlus playlist updated with categorized group-titles per country.")
