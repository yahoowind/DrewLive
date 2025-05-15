import requests

# List of raw GitHub URLs (DaddyLive first)
urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
      "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/JapanTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DistroTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlexTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StirrTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TubiTV.m3u8"
]

output_file = "MergedPlaylist.m3u8"

with open(output_file, "w", encoding="utf-8") as outfile:
    outfile.write("#EXTM3U\n\n")
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            lines = response.text.splitlines()
            for line in lines:
                # Skip duplicated headers
                if line.strip() and not line.startswith("#EXTM3U"):
                    outfile.write(line + "\n")
            outfile.write("\n")
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")

print(f"Successfully created {output_file}")