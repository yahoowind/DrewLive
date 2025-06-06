import requests
import re
import urllib.parse
from collections import defaultdict

# All playlists URLs
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
]

# URLs that are proxied (on 3000 and 3001)
PROXY_DOMAINS = [
    "drewlive24.duckdns.org:3000",
    "drewlive24.duckdns.org:3001"
]

EPG_URL = "https://tinyurl.com/merged2423-epg"

def is_proxied_url(url):
    return any(proxy_domain in url for proxy_domain in PROXY_DOMAINS)

def unwrap_url(url):
    """
    If the url is a proxy URL with ?url=actualURL, extract and return actualURL.
    Otherwise, return original url.
    """
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    if 'url' in query_params:
        return query_params['url'][0]
    return url

def fetch_playlist(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

def extract_group_title(extinf_line):
    match = re.search(r'group-title="(.*?)"', extinf_line)
    return match.group(1).strip() if match else "Unknown"

def parse_entries(content, unwrap_proxy):
    """
    Parse the playlist content and unwrap urls only if unwrap_proxy is True
    """
    lines = content.strip().splitlines()
    grouped_entries = defaultdict(list)
    seen_urls = set()
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            entry = [line]
            j = i + 1
            # Collect any #EXTVLCOPT lines following EXTINF
            while j < len(lines) and lines[j].startswith("#EXTVLCOPT"):
                entry.append(lines[j].strip())
                j += 1
            if j < len(lines):
                raw_url = lines[j].strip()
                if unwrap_proxy and is_proxied_url(raw_url):
                    url = unwrap_url(raw_url)
                else:
                    url = raw_url
                if url not in seen_urls:
                    entry.append(url)
                    group = extract_group_title(line)
                    grouped_entries[group].append(entry)
                    seen_urls.add(url)
                i = j + 1
            else:
                i = j
        else:
            i += 1
    return grouped_entries

def merge_playlists(urls, epg_url):
    merged_groups = defaultdict(list)

    for url in urls:
        content = fetch_playlist(url)
        if content:
            # unwrap_proxy only if playlist URL contains 3000 or 3001 proxy domain
            unwrap_proxy = any(proxy in url for proxy in PROXY_DOMAINS)
            groups = parse_entries(content, unwrap_proxy)
            for group_name, entries in groups.items():
                merged_groups[group_name].extend(entries)

    sorted_group_names = sorted(merged_groups.keys(), key=lambda g: g.lower())

    with open("MergedPlaylist.m3u8", "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U url-tvg="{epg_url}"\n\n')
        for group_name in sorted_group_names:
            f.write(f'#--- Group: {group_name} ---\n')
            for entry in merged_groups[group_name]:
                for line in entry:
                    f.write(f"{line}\n")
            f.write("\n")

    print("MergedPlaylist.m3u8 has been written successfully.")

if __name__ == "__main__":
    merge_playlists(playlist_urls, EPG_URL)
