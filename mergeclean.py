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
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StreamEast.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/FSTV24.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Roku.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/LGTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/AriaPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Xumo.m3u8"
]

EPG_URL = "http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz"
OUTPUT_FILE = "MergedCleanPlaylist.m3u8"
REMOVED_FILE = "Removed_NSFW.m3u8"


def fetch_playlist(url):
    """Fetch playlist content from URL."""
    print(f"📡 Fetching: {url}")
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        content = res.content.decode('utf-8', errors='ignore').strip().splitlines()
        if "#EXTM3U" not in content:
            print(f"⚠️ Invalid playlist at {url}, skipping.")
            return []
        return content
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []


def parse_playlist(lines, source_url="Unknown"):
    """Parse EXTINF channels from a playlist."""
    parsed = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf = line
            headers = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith("#") and not lines[i].strip().startswith("#EXTINF:"):
                headers.append(lines[i].strip())
                i += 1
            if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("#"):
                url = lines[i].strip()
                if re.search(r'group-title="([^"]+)"', extinf):
                    parsed.append((extinf, tuple(headers), url))
                else:
                    print(f"⚠️ Skipped channel with no group-title in {source_url}")
                i += 1
            else:
                print(f"⚠️ Skipped invalid channel in {source_url}")
        else:
            i += 1
    print(f"✅ Parsed {len(parsed)} channels from {source_url}")
    return parsed


def is_nsfw(extinf, headers, url):
    """Check if channel is NSFW."""
    nsfw_keywords = ['nsfw', 'xxx', 'porn']
    extinf_lower = extinf.lower()
    headers_lower = ' '.join(headers).lower()
    url_lower = url.lower()
    group_match = re.search(r'group-title="([^"]+)"', extinf_lower)
    if group_match:
        group_title = group_match.group(1)
        if any(k in group_title for k in nsfw_keywords):
            return True
    combined_text = f"{extinf_lower} {headers_lower} {url_lower}"
    return any(k in combined_text for k in nsfw_keywords)


def write_merged_playlist(all_channels):
    """Write merged playlist sorted by group and title."""
    lines = [f'#EXTM3U url-tvg="{EPG_URL}"', ""]
    sortable = []

    for extinf, headers, url in all_channels:
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        if not group_match:
            continue
        group = group_match.group(1).strip()
        title_match = re.search(r',([^,]+)$', extinf)
        title = title_match.group(1).strip() if title_match else ""
        sortable.append((group.lower(), title.lower(), group, extinf, headers, url))

    sorted_channels = sorted(sortable)
    current_group = None
    count = 0

    for _, _, group_name, extinf, headers, url in sorted_channels:
        if group_name != current_group:
            if current_group is not None:
                lines.append("")
            lines.append(f"#EXTGRP:{group_name}")
            current_group = group_name
        lines.append(extinf)
        lines.extend(headers)
        lines.append(url)
        count += 1

    final_output = '\n'.join(lines) + '\n'
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_output)

    print(f"\n✅ Wrote {count} clean channels to {OUTPUT_FILE}")


def write_removed_channels(nsfw_channels):
    if not nsfw_channels:
        return
    with open(REMOVED_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for extinf, headers, url in nsfw_channels:
            f.write(extinf + "\n")
            for h in headers:
                f.write(h + "\n")
            f.write(url + "\n\n")
    print(f"🗑️ Logged {len(nsfw_channels)} removed NSFW entries to {REMOVED_FILE}")


if __name__ == "__main__":
    print(f"🚀 Starting merge: {datetime.now()}\n")

    all_channels = []

    for url in playlist_urls:
        lines = fetch_playlist(url)
        all_channels.extend(parse_playlist(lines, url))

    nsfw_channels = [entry for entry in all_channels if is_nsfw(*entry)]
    clean_channels = [entry for entry in all_channels if not is_nsfw(*entry)]

    write_removed_channels(nsfw_channels)
    write_merged_playlist(clean_channels)

    print(f"\n✅ Merge complete: {datetime.now()}")
