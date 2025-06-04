import requests
import re
import urllib.parse
import os

ALLOWED_COUNTRIES = {
    'UNITED STATES': 'DaddyLive USA',
    'UNITED KINGDOM': 'DaddyLive UK',
    'CANADA': 'DaddyLive CA',
    'AUSTRALIA': 'DaddyLive AU',
    'NEW ZEALAND': 'DaddyLive NZ'
}

SOURCE_URL = 'https://drewski2423-dproxy.hf.space/playlist/channels'
OUTPUT_FILE = 'DaddyLive.m3u8'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    return query_params.get('url', [url])[0]

def extract_group_title(line):
    match = re.search(r'group-title="([^"]+)"', line)
    return match.group(1).strip().upper() if match else None

def replace_group_title(line, old_group):
    return re.sub(r'group-title="[^"]+"', f'group-title="{ALLOWED_COUNTRIES[old_group]}"', line)

def main():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    result = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    i = 0
    kept = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF') and (i + 1) < len(lines):
            group_title = extract_group_title(line)

            if group_title and group_title in ALLOWED_COUNTRIES:
                # Rename group
                updated_line = replace_group_title(line, group_title)
                stream_url = unwrap_url(lines[i + 1].strip())

                result.append(updated_line)
                result.append(stream_url)
                kept += 1

            i += 2
        else:
            i += 1

    with open(os.path.join(BASE_DIR, OUTPUT_FILE), 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))

    print(f"[+] Wrote {kept} filtered channels with updated group names to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
