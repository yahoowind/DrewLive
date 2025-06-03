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

# Load metadata maps
SCRIPT_DIR = r'C:\Users\andre\Desktop\IPTV\Scripts'
TV_ID_FILE = os.path.join(SCRIPT_DIR, 'tvids.txt')
LOGO_FILE = os.path.join(SCRIPT_DIR, 'logos.txt')

def load_metadata(filepath):
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if '|' in line:
                name, value = line.strip().split('|', 1)
                data[name.strip().lower()] = value.strip()
    return data

tv_ids = load_metadata(TV_ID_FILE)
logos = load_metadata(LOGO_FILE)

def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    if 'url' in query_params:
        return query_params['url'][0]
    return url

def get_group_title(extinf_line):
    for country, group_name in ALLOWED_COUNTRIES.items():
        if country.lower() in extinf_line.lower():
            return group_name
    return None

def build_extinf(original_line, channel_name, group_name):
    line = '#EXTINF:-1'

    # Attach tvg-id if available
    tvg_id = tv_ids.get(channel_name.lower())
    if tvg_id:
        line += f' tvg-id="{tvg_id}"'

    # Attach tvg-logo if available
    logo = logos.get(channel_name.lower())
    if logo:
        line += f' tvg-logo="{logo}"'

    # Always overwrite group-title
    line += f' group-title="{group_name}",{channel_name}'
    return line

def main():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    output_lines = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    unmatched_channels = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            clean_url = unwrap_url(next_line.strip())

            # Extract channel name after the comma
            channel_name = line.split(',', 1)[-1].strip()

            group = get_group_title(line)
            if group:
                extinf = build_extinf(line, channel_name, group)
                output_lines.append(extinf)
                output_lines.append(clean_url)
            else:
                unmatched_channels.append(channel_name)
            i += 2
        else:
            i += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(line + '\n')

    # Optional: Save unmatched names to a log
    if unmatched_channels:
        with open(os.path.join(SCRIPT_DIR, 'unmatched_channels.txt'), 'w', encoding='utf-8') as f:
            for ch in sorted(set(unmatched_channels)):
                f.write(ch + '\n')

if __name__ == '__main__':
    main()
