import requests
import re

# Map of group names to URLs
sources = {
    "NBA": "https://iptv-scraper-re.vercel.app/nbawebcast",
    "MLB": "https://iptv-scraper-re.vercel.app/mlbwebcast",
    "NFL": "https://iptv-scraper-re.vercel.app/nflwebcast",
    "NHL": "https://iptv-scraper-re.vercel.app/nhlwebcast",
}

# Force single #EXTM3U with EPG tag
epg_url = "https://tinyurl.com/dummy2423-epg"
output_lines = [f'#EXTM3U url-tvg="{epg_url}"']

for group, url in sources.items():
    print(f"Fetching: {url}")
    response = requests.get(url)
    lines = response.text.strip().splitlines()

    for i, line in enumerate(lines):
        if line.startswith("#EXTINF"):
            if 'group-title="' in line:
                line = re.sub(r'group-title=".*?"', f'group-title="{group}"', line)
            else:
                line = line.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-id="Sports.Dummy.us" group-title="{group}"')
            output_lines.append(line)
        elif line.startswith("#EXTM3U"):
            continue  # skip any duplicate headers
        else:
            output_lines.append(line)

# Write to M3U file
with open("SportsWebcast.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("✅ Cleaned & saved as SportsWebcast.m3u with EPG added.")