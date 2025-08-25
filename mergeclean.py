import requests
import re
from datetime import datetime

playlist_urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/JapanTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlexTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TubiTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewLiveVOD.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TVPass.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Radio.m3u8",
    "http://drewlive24.duckdns.org:8081/PPVLand.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StreamEast.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/FSTV24.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Roku.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "http://drewlive24.duckdns.org:8081/Tims247.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/LGTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/AriaPlus.m3u8",
    "http://drewlive24.duckdns.org:8081/Zuzz.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Xumo.m3u8"
]

EPG_URL = "http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz"
OUTPUT_FILE = "MergedPlaylist_Clean.m3u8"

# Filter keywords (case-insensitive)
NSFW_KEYWORDS = ['nsfw', 'xxx', 'porn', 'adult', 'sex', 'erotic']

def fetch_playlist(url):
    """Fetch playlist content."""
    print(f"📡 Fetching playlist: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content = response.content.decode("utf-8", errors="ignore")
        if "#EXTM3U" not in content:
            print(f"⚠️ Skipping invalid playlist from {url}")
            return []
        return content.splitlines()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []

def parse_playlist(lines, source="Unknown"):
    """Parse EXTINF channels from a playlist."""
    parsed = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf = line
            metadata = []
            i += 1

            # Collect metadata lines
            while i < len(lines) and lines[i].strip().startswith("#") and not lines[i].strip().startswith("#EXTINF:"):
                metadata.append(lines[i].strip())
                i += 1

            # Expect a valid stream URL
            if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("#"):
                url = lines[i].strip()
                # Skip NSFW channels
                combined_text = f"{extinf} {' '.join(metadata)} {url}".lower()
                if not any(k in combined_text for k in NSFW_KEYWORDS):
                    parsed.append((extinf, tuple(metadata), url))
                else:
                    print(f"🛑 Removed NSFW channel in {source}: {extinf}")
                i += 1
            else:
                print(f"⚠️ Skipping orphaned EXTINF in {source}: {extinf}")
                i += 1
        else:
            i += 1

    print(f"✅ Parsed {len(parsed)} channels from {source} (NSFW removed)")
    return parsed

def write_merged_playlist(channels):
    """Write merged playlist to file, sorted by group and name."""
    lines = [f'#EXTM3U url-tvg="{EPG_URL}"', ""]

    def get_group_title(extinf, metadata):
        m = re.search(r'group-title="([^"]+)"', extinf)
        if m:
            return m.group(1)
        for meta in metadata:
            if meta.startswith("#EXTGRP:"):
                return meta.split(":", 1)[1].strip()
        return "Ungrouped"

    def get_channel_name(extinf):
        m = re.search(r',([^,]+)$', extinf)
        return m.group(1).strip() if m else ""

    sorted_channels = sorted(
        channels,
        key=lambda c: (get_group_title(c[0], c[1]).lower(), get_channel_name(c[0]).lower())
    )

    current_group = None
    for extinf, metadata, url in sorted_channels:
        group = get_group_title(extinf, metadata)
        if group != current_group:
            if current_group is not None:
                lines.append("")
            lines.append(f"#EXTGRP:{group}")
            current_group = group

        lines.append(extinf)
        lines.extend(metadata)
        lines.append(url)

    if lines and lines[-1] != "":
        lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Merged playlist saved to {OUTPUT_FILE}")
    print(f"📺 Total channels: {len(channels)}")
    print(f"🕒 Saved at: {datetime.now()}")

if __name__ == "__main__":
    print(f"🚀 Starting merge at {datetime.now()}\n")
    all_channels = []

    for url in playlist_urls:
        lines = fetch_playlist(url)
        all_channels.extend(parse_playlist(lines, source=url))

    write_merged_playlist(all_channels)
    print(f"\n✅ Merge complete at {datetime.now()}")
