import requests
import re
import time

# 🧾 Your handcrafted playlist with correct metadata
TEMPLATE_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/UDPTV.m3u"

# 🔄 Live upstream source with updated stream URLs
UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"

# 📺 EPG stays in template — not touched
# 🏷️ Forced group title (no matter what was in template or upstream)
FORCED_GROUP_TITLE = "UDPTV Live Streams"

# 📤 Final output file
OUTPUT_FILE = "UDPTV.m3u"

def fetch_lines(url):
    r = requests.get(f"{url}?_={int(time.time())}", timeout=10)
    r.raise_for_status()
    return r.text.splitlines()

def clean_upstream(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#") and "created by" in line.lower():
            continue  # Strip watermark lines
        if not line.startswith("#"):
            cleaned.append(line)  # Only keep URLs
    return cleaned

def force_url(url):
    timestamp = int(time.time())
    if "?" in url:
        return re.sub(r'(force=)\d+', f'\\1{timestamp}', url) if "force=" in url else url + f"&force={timestamp}"
    return url + f"?force={timestamp}"

def enforce_group_title(extinf_line):
    if 'group-title="' in extinf_line:
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP_TITLE}"', extinf_line)
    return re.sub(r'(,)', f' group-title="{FORCED_GROUP_TITLE}",', extinf_line, count=1)

def merge(template_lines, upstream_urls):
    final = []
    url_iter = iter([force_url(u) for u in upstream_urls])

    for line in template_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            final.append(enforce_group_title(line))
        elif line.startswith("http://") or line.startswith("https://"):
            try:
                final.append(next(url_iter))  # Replace with fresh forced URL
            except StopIteration:
                final.append(line)  # Just in case upstream is short
        else:
            final.append(line)  # Leave any other lines alone (like #EXTM3U)
    return final

def write_output(lines):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ Wrote: {OUTPUT_FILE} with enforced group & fresh URLs")

if __name__ == "__main__":
    print("🔄 Grabbing template & upstream...")
    template = fetch_lines(TEMPLATE_URL)
    upstream = clean_upstream(fetch_lines(UPSTREAM_URL))
    merged = merge(template, upstream)
    write_output(merged)
