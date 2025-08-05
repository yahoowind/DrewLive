import requests
import re

UPSTREAM_URL = "https://raw.githubusercontent.com/luongz/iptv-jp/refs/heads/main/jp.m3u"
OUTPUT_FILE = "JapanTV.m3u8"
FORCED_GROUP_NAME = "JapanTV"
TVG_HEADER = '#EXTM3U url-tvg="https://epg.freejptv.com/jp.xml,https://animenosekai.github.io/japanterebi-xmltv/guide.xml" tvg-shift=0'

def clean_and_force_group(m3u_content):
    lines = m3u_content.strip().splitlines()
    output_lines = [TVG_HEADER]
    skip_next = False

    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue

        if line.startswith("#EXTINF"):
            # Skip if it's an Information group
            if 'group-title="Information"' in line:
                skip_next = True
                continue

            # Force group-title to JapanTV
            if 'group-title="' in line:
                line = re.sub(r'group-title=".*?"', f'group-title="{FORCED_GROUP_NAME}"', line)
            else:
                line = line.replace('#EXTINF:', f'#EXTINF group-title="{FORCED_GROUP_NAME}":')
            output_lines.append(line)
            if i + 1 < len(lines):
                output_lines.append(lines[i + 1])
                skip_next = True

    return "\n".join(output_lines)

def main():
    print("📥 Downloading upstream playlist...")
    response = requests.get(UPSTREAM_URL)
    if response.status_code != 200:
        print(f"❌ Failed to download: HTTP {response.status_code}")
        return

    print("🧹 Cleaning and rewriting playlist...")
    modified_content = clean_and_force_group(response.text)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(modified_content)

    print(f"✅ Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
