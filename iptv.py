import requests
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
        return res.text.strip().splitlines()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return []

def merge_playlists(urls, epg_url):
    all_lines = ['#EXTM3U url-tvg="{}"'.format(epg_url)]
    for url in urls:
        lines = fetch_playlist(url)
        if lines and lines[0].startswith("#EXTM3U"):
            lines = lines[1:]  # Skip the header to avoid duplication
        all_lines.append(f"\n#--- START OF {url.split('/')[-1]} ---")
        all_lines.extend(lines)
        all_lines.append(f"#--- END OF {url.split('/')[-1]} ---\n")
    
    with open("MergedPlaylist.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines))

    print("MergedPlaylist.m3u8 written with all source content untouched.")

if __name__ == "__main__":
    merge_playlists(playlist_urls, EPG_URL)
