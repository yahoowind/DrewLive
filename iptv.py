import requests

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

def fetch_raw_lines(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text.splitlines()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def merge_without_touching(urls, epg_url):
    merged_lines = [f'#EXTM3U url-tvg="{epg_url}"']
    for url in urls:
        lines = fetch_raw_lines(url)
        if not lines:
            continue

        # Strip duplicate headers if present
        if lines[0].strip().startswith("#EXTM3U"):
            lines = lines[1:]

        merged_lines.append(f"\n# --- START: {url.split('/')[-1]} ---")
        merged_lines.extend(lines)
        merged_lines.append(f"# --- END: {url.split('/')[-1]} ---\n")

    with open("MergedPlaylist.m3u8", "w", encoding="utf-8") as out:
        out.write("\n".join(merged_lines))

    print("MergedPlaylist.m3u8 written with no changes to source content.")

if __name__ == "__main__":
    merge_without_touching(playlist_urls, EPG_URL)
