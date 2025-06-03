import requests
import re
import urllib.parse
import os

SOURCE_URL = 'https://drewski2423-dproxy.hf.space/playlist/channels'
OUTPUT_FILE = 'DaddyLive.m3u8'
LOGOS_FILE = r'C:\Users\andre\Desktop\IPTV\Scripts\logos.txt'
TVIDS_FILE = r'C:\Users\andre\Desktop\IPTV\Scripts\tv-ids.txt'

ALLOWED_COUNTRIES = {
    'UNITED STATES': 'DaddyLive USA',
    'UNITED KINGDOM': 'DaddyLive UK',
    'CANADA': 'DaddyLive CA',
    'AUSTRALIA': 'DaddyLive AU',
    'NEW ZEALAND': 'DaddyLive NZ'
}

def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    return query_params['url'][0] if 'url' in query_params else url

def load_mapping(file_path):
    mapping = {}
    if os.path.exists(file_path):
        with open(file_path, encoding='utf-8') as f:
            for line in f:
                if '|' in line:
                    name, value = line.strip().split('|', 1)
                    mapping[name.strip().lower()] = value.strip()
    return mapping

def normalize_name(extinf_line):
    return extinf_line.split(',', 1)[-1].strip().lower() if ',' in extinf_line else extinf_line.lower()

def update_extinf_line(line, group_title, tvg_id, logo_url):
    # Replace or insert group-title
    if 'group-title="' in line:
        line = re.sub(r'group-title="[^"]*"', f'group-title="{group_title}"', line)
    else:
        line = re.sub(r'#EXTINF:-?\d+', f'\\g<0> group-title="{group_title}"', line)

    # Replace or insert tvg-id
    if tvg_id:
        if 'tvg-id="' in line:
            line = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{tvg_id}"', line)
        else:
            line = re.sub(r'#EXTINF:-?\d+', f'\\g<0> tvg-id="{tvg_id}"', line)

    # Replace or insert tvg-logo
    if logo_url:
        if 'tvg-logo="' in line:
            line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logo_url}"', line)
        else:
            line = re.sub(r'#EXTINF:-?\d+', f'\\g<0> tvg-logo="{logo_url}"', line)

    return line

def main():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    logos = load_mapping(LOGOS_FILE)
    tv_ids = load_mapping(TVIDS_FILE)

    channels = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            raw_url = lines[i + 1] if i + 1 < len(lines) else ''
            url = unwrap_url(raw_url.strip())
            name_key = normalize_name(line)

            # Determine if this channel is from an allowed country
            group_title = None
            for country, title in ALLOWED_COUNTRIES.items():
                if country.lower() in line.lower():
                    group_title = title
                    break

            if group_title:
                updated_line = update_extinf_line(
                    line,
                    group_title,
                    tv_ids.get(name_key),
                    logos.get(name_key)
                )
                channels.append((updated_line, url))
            i += 2
        else:
            i += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"\n')
        for extinf, url in channels:
            f.write(extinf + '\n')
            f.write(url + '\n')

if __name__ == '__main__':
    main()
