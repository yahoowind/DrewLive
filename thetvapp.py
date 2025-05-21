import requests
import re

# Fetch the playlist
url = "http://drewlive24.duckdns.org:8090/tvpass/playlist?quality=all"
response = requests.get(url)
playlist = response.text

# Force every EXTINF to use group-title="TheTVApp"
updated_lines = []
for line in playlist.splitlines():
    if line.startswith("#EXTINF"):
        # Replace existing group-title or add it if missing
        if 'group-title="' in line:
            line = re.sub(r'group-title=".*?"', 'group-title="TheTVApp"', line)
        else:
            parts = line.split(",", 1)
            if len(parts) == 2:
                prefix, title = parts
                line = f'{prefix} group-title="TheTVApp",{title}'
    updated_lines.append(line)

# Write to file
with open("TheTVApp.m3u8", "w", encoding="utf-8") as f:
    f.write("\n".join(updated_lines))
