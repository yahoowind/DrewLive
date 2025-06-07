import requests
import re
import urllib.parse

ALLOWED_COUNTRIES = {
    'UNITED STATES': 'DaddyLive USA',
    'UNITED KINGDOM': 'DaddyLive UK',
    'CANADA': 'DaddyLive CA',
    'AUSTRALIA': 'DaddyLive AU',
    'NEW ZEALAND': 'DaddyLive NZ'
}

SOURCE_URL = 'https://drewski2423-dproxy.hf.space/playlist/channels'
OUTPUT_FILE = 'DaddyLive.m3u8'

def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    return params.get('url', [url])[0]

def extract_group_title(line):
    m = re.search(r'group-title="([^"]+)"', line)
    return m.group(1).strip().upper() if m else None

def replace_group_title(line, old_group):
    return re.sub(r'group-title="[^"]+"', f'group-title="{ALLOWED_COUNTRIES[old_group]}"', line)

def main():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    result = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF') and (i + 1) < len(lines):
            group = extract_group_title(line)
            if group in ALLOWED_COUNTRIES:
                line = replace_group_title(line, group)
            result.append(line)
            url = unwrap_url(lines[i + 1].strip())
            result.append(url)
            i += 2
        else:
            # Any other lines just append as is
            result.append(line)
            i += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))

    print(f"[+] Playlist updated with forced group names and fresh URLs in {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
