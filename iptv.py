import requests
import re
from collections import defaultdict

playlist_urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/JapanTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DistroTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlexTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StirrTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TubiTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewLiveVOD.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Drew247TV.m3u8",
]

EPG_URL = "https://tinyurl.com/merged2423-epg"

def fetch_playlist(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.text.splitlines()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def extract_group_title(line):
    match = re.search(r'group-title="([^"]+)"', line)
    return match.group(1).strip() if match else "ZZZ_Unsorted"

def parse_and_group(lines):
    groups = defaultdict(list)
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            entry = [lines[i]]
            j = i + 1
            # Handle any #EXTVLCOPT lines
            while j < len(lines) and lines[j].startswith("#EXTVLCOPT"):
                entry.append(lines[j])
                j += 1
            if j < len(lines):
                entry.append(lines[j])  # the stream URL
                group = extract_group_title(lines[i])
                groups[group].append(entry)
            i = j + 1
        else:
            i += 1
    return groups

def merge_playlists():
    final_groups = defaultdict(list)

    for url in playlist_urls:
        lines = fetch_playlist(url)
        # Skip global header
        if lines and lines[0].strip().startswith("#EXTM3U"):
            lines = lines[1:]
        groups = parse_and_group(lines)
        for group, entries in groups.items():
            final_groups[group].extend(entries)

    with open("MergedPlaylist.m3u8", "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U url-tvg="{EPG_URL}"\n\n')
        for group in sorted(final_groups.keys(), key=lambda x: x.lower()):
            for entry in final_groups[group]:
                for line in entry:
                    f.write(f"{line}\n")
            f.write("\n")

    print("✅ MergedPlaylist.m3u8 written successfully with no changes to group names or channels.")

if __name__ == "__main__":
    merge_playlists()
