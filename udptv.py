import requests
import re
import time

# 🧾 GitHub Template Playlist (Raw .m3u file)
TEMPLATE_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/UDPTV.m3u"
# 📺 EPG Guide
EPG_URL = "https://tinyurl.com/merged2423-epg"
# 🏷️ Fixed group title for all entries
FORCED_GROUP_TITLE = "UDPTV Live Streams"
# 📤 Output file (do NOT rename)
OUTPUT_FILE = "UDPTV.m3u"

def fetch_playlist(url):
    # Add timestamp query param here to force fresh fetch from GitHub raw (no cache)
    timestamp = int(time.time())
    fetch_url = f"{url}?_={timestamp}"
    r = requests.get(fetch_url, timeout=10)
    r.raise_for_status()
    return r.text.splitlines()

def apply_group_title(line):
    if 'group-title="' in line:
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP_TITLE}"', line)
    return re.sub(r'(,)', f' group-title="{FORCED_GROUP_TITLE}",', line, count=1)

def force_update_url(url):
    # Append or update force param to make URL unique each time
    timestamp = int(time.time())
    if "?" in url:
        if re.search(r'force=\d+', url):
            # Replace existing force param
            return re.sub(r'force=\d+', f'force={timestamp}', url)
        else:
            return url + f"&force={timestamp}"
    else:
        return url + f"?force={timestamp}"

def convert_lines(lines):
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            line = apply_group_title(line)
            result.append(line)
        elif line.startswith("http://") or line.startswith("https://"):
            # Force update the stream URLs here
            updated_url = force_update_url(line)
            result.append(updated_url)
        else:
            result.append(line)
    return result

def write_output(lines):
    if lines and lines[0].startswith("#EXTM3U"):
        lines[0] = f'#EXTM3U url-tvg="{EPG_URL}"'
    else:
        lines.insert(0, f'#EXTM3U url-tvg="{EPG_URL}"')

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ Converted & forced update: {OUTPUT_FILE}")

if __name__ == "__main__":
    raw_lines = fetch_playlist(TEMPLATE_URL)
    converted = convert_lines(raw_lines)
    write_output(converted)
