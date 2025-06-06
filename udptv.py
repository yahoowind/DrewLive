import requests
import re
import time
from collections import deque

# Upstream URL (fetch live streams from here)
UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
# Template playlist on GitHub (has your metadata: group-title, tvg-id, logos)
TEMPLATE_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/UDPTV.m3u"
# EPG Guide URL
EPG_URL = "https://tinyurl.com/merged2423-epg"
# Output file
OUTPUT_FILE = "UDPTV.m3u"
# Fixed group title (if you want to force or override group-title)
FORCED_GROUP_TITLE = None  # Set to None to keep template groups intact

def fetch_playlist(url):
    timestamp = int(time.time())
    fetch_url = f"{url}?_={timestamp}"
    r = requests.get(fetch_url, timeout=10)
    r.raise_for_status()
    return r.text.splitlines()

def force_update_url(url):
    # Append/update force param to bust cache every run
    timestamp = int(time.time())
    if "?" in url:
        if re.search(r'force=\d+', url):
            return re.sub(r'force=\d+', f'force={timestamp}', url)
        else:
            return url + f"&force={timestamp}"
    else:
        return url + f"?force={timestamp}"

def apply_forced_group_title(line):
    if not FORCED_GROUP_TITLE:
        return line
    if 'group-title="' in line:
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP_TITLE}"', line)
    return re.sub(r'(,)', f' group-title="{FORCED_GROUP_TITLE}",', line, count=1)

def merge_playlists(template_lines, upstream_lines):
    # We assume upstream_lines contains alternating lines:
    # #EXTINF metadata line, then stream URL line
    # We will replace URLs in the template with URLs from upstream in order
    result = []
    upstream_urls = deque()

    # Extract URLs from upstream (every line that is not #EXTINF)
    for line in upstream_lines:
        line = line.strip()
        if line and not line.startswith("#EXTINF"):
            upstream_urls.append(force_update_url(line))

    i = 0
    while i < len(template_lines):
        line = template_lines[i].strip()
        if line.startswith("#EXTINF"):
            # Optionally force group-title in metadata line
            line = apply_forced_group_title(line)
            result.append(line)
            # Next line is supposed to be URL - replace with next from upstream_urls
            i += 1
            if i < len(template_lines):
                if upstream_urls:
                    new_url = upstream_urls.popleft()
                    result.append(new_url)
                else:
                    # No more upstream URLs - keep original URL line
                    result.append(template_lines[i].strip())
        else:
            # Header lines or anything else - just copy as is
            result.append(line)
        i += 1

    # Make sure the #EXTM3U line includes the EPG URL
    if result and result[0].startswith("#EXTM3U"):
        result[0] = f'#EXTM3U url-tvg="{EPG_URL}"'
    else:
        result.insert(0, f'#EXTM3U url-tvg="{EPG_URL}"')

    return result

def write_output(lines):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ Merged and wrote playlist to {OUTPUT_FILE}")

if __name__ == "__main__":
    # Fetch both playlists (template and upstream)
    template = fetch_playlist(TEMPLATE_URL)
    upstream = fetch_playlist(UPSTREAM_URL)

    # Merge keeping template metadata and logos, updating URLs from upstream forcibly
    merged = merge_playlists(template, upstream)

    # Write output
    write_output(merged)
