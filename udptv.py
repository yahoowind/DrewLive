import requests
import re
import time

TEMPLATE_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/UDPTV.m3u"
UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"

def fetch_lines(url):
    r = requests.get(f"{url}?_={int(time.time())}", timeout=10)
    r.raise_for_status()
    return r.text.splitlines()

def clean_upstream(lines):
    urls = []
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF") or line.startswith("http"):
            urls.append(line)
    # Remove Discord/donate/messages
    return [line for line in urls if not any(x in line.lower() for x in [
        "donate", "discord", "join our", "last updated", "support", "#extm3u"
    ])]

def force_url(url):
    timestamp = int(time.time())
    if "?" in url:
        return re.sub(r'(force=)\d+', f'\\1{timestamp}', url) if "force=" in url else url + f"&force={timestamp}"
    return url + f"?force={timestamp}"

def merge_metadata_with_streams(template_lines, new_stream_urls):
    final = []
    url_iter = iter([force_url(u) for u in new_stream_urls if u.startswith("http")])
    for line in template_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("http://") or line.startswith("https://"):
            try:
                final.append(next(url_iter))  # Inject fresh URL
            except StopIteration:
                final.append(line)  # Keep old if we run out
        else:
            final.append(line)  # Keep metadata untouched
    return final

def write_output(lines):
    if lines and lines[0].startswith("#EXTM3U"):
        lines[0] = f'#EXTM3U url-tvg="{EPG_URL}"'
    else:
        lines.insert(0, f'#EXTM3U url-tvg="{EPG_URL}"')
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ Playlist updated: {OUTPUT_FILE}")

if __name__ == "__main__":
    print("📡 Pulling upstream URLs only...")
    upstream_clean = clean_upstream(fetch_lines(UPSTREAM_URL))
    print("📦 Fetching your metadata template...")
    template = fetch_lines(TEMPLATE_URL)
    print("🔗 Merging fresh URLs into metadata...")
    merged = merge_metadata_with_streams(template, upstream_clean)
    write_output(merged)
