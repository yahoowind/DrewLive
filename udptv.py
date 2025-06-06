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
    timestamp = int(time.time())  # Force update param in URL
    final_url = f"{url}?_={timestamp}"
    r = requests.get(final_url, timeout=10)
    r.raise_for_status()
    return r.text.splitlines()

def apply_group_title(line):
    if 'group-title="' in line:
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP_TITLE}"', line)
    return re.sub(r'(,)', f' group-title="{FORCED_GROUP_TITLE}",', line, count=1)

def convert_lines(lines):
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            line = apply_group_title(line)
        result.append(line)
    return result

def write_output(lines):
    # Make sure header exists & has correct EPG
    if lines and lines[0].startswith("#EXTM3U"):
        lines[0] = f'#EXTM3U url-tvg="{EPG_URL}"'
    else:
        lines.insert(0, f'#EXTM3U url-tvg="{EPG_URL}"')
    
    # Insert timestamp comment after header to force file change every run
    timestamp_comment = f"# Last updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC"
    if len(lines) > 1 and not lines[1].startswith("# Last updated:"):
        lines.insert(1, timestamp_comment)
    else:
        lines[1] = timestamp_comment

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ Converted: {OUTPUT_FILE}")

if __name__ == "__main__":
    raw_lines = fetch_playlist(TEMPLATE_URL)
    converted = convert_lines(raw_lines)
    write_output(converted)
