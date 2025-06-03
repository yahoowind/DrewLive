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
BASE_DIR = os.path.expanduser('~/Desktop/IPTV/Scripts')
TVIDS_FILE = os.path.join(BASE_DIR, 'tvids.txt')
LOGOS_FILE = os.path.join(BASE_DIR, 'logos.txt')


def load_mapping(file_path):
    mapping = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '|' in line:
                name, val = line.strip().split('|', 1)
                mapping[name.strip().lower()] = val.strip()
    return mapping


def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    return query_params.get('url', [url])[0]


def get_group_title(line):
    for country, group in ALLOWED_COUNTRIES.items():
        if country.lower() in line.lower():
            return group
    return None


def update_extinf(line, tv_ids, logos):
    if ',' not in line:
        return line
    prefix, display_name = line.split(',', 1)
    key = display_name.strip().lower()

    if tv_ids.get(key):
        if 'tvg-id="' in prefix:
            prefix = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{tv_ids[key]}"', prefix)
        else:
            prefix += f' tvg-id="{tv_ids[key]}"'

    if logos.get(key):
        if 'tvg-logo="' in prefix:
            prefix = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logos[key]}"', prefix)
        else:
            prefix += f' tvg-logo="{logos[key]}"'

    return f'{prefix},{display_name}'


def main():
    tv_ids = load_mapping(TVIDS_FILE)
    logos = load_mapping(LOGOS_FILE)

    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    result = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            group = get_group_title(line)
            if not group:
                i += 2  # skip line and URL
                continue

            # Apply group-title
            if 'group-title="' in line:
                line = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', line)
            else:
                parts = line.split(',', 1)
                line = parts[0] + f' group-title="{group}",' + parts[1]

            # Update tvg-id and tvg-logo
            line = update_extinf(line, tv_ids, logos)

            stream_url = unwrap_url(lines[i + 1].strip())
            result.append(line)
            result.append(stream_url)
            i += 2
        else:
            i += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))


if __name__ == '__main__':
    main()
