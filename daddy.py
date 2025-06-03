import requests
import re
import urllib.parse
import os
 
# Countries to keep and their group titles
ALLOWED_COUNTRIES = {
    'UNITED STATES': 'DaddyLive USA',
    'UNITED KINGDOM': 'DaddyLive UK',
    'CANADA': 'DaddyLive CA',
    'AUSTRALIA': 'DaddyLive AU',
    'NEW ZEALAND': 'DaddyLive NZ'
}
 
SOURCE_URL = 'https://drewski2423-dproxy.hf.space/playlist/channels'
OUTPUT_FILE = 'DaddyLive.m3u8'
 
# Base directory where this script is located, so relative files load correctly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TVIDS_FILE = os.path.join(BASE_DIR, 'tvids.txt')
LOGOS_FILE = os.path.join(BASE_DIR, 'logos.txt')
 
 
def load_mapping(file_path):
    mapping = {}
    if not os.path.exists(file_path):
        print(f"[WARNING] Mapping file not found: {file_path}")
        return mapping
 
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '|' in line:
                name, val = line.strip().split('|', 1)
                mapping[name.strip().lower()] = val.strip()
    print(f"[INFO] Loaded {len(mapping)} entries from {file_path}")
    return mapping
 
 
def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    return query_params.get('url', [url])[0]
 
 
def get_group_title(line, tv_ids):
    # First try to match country names in line
    for country, group in ALLOWED_COUNTRIES.items():
        if country.lower() in line.lower():
            print(f"[DEBUG] Country '{country}' matched in line.")
            return group
 
    # If no country matched, check if display name is in tv_ids => assign USA
    if ',' in line:
        display_name = line.split(',', 1)[1].strip().lower()
        if display_name in tv_ids:
            print(f"[DEBUG] Display name '{display_name}' found in tv_ids; assigning USA group.")
            return ALLOWED_COUNTRIES['UNITED STATES']
 
    # No group matched
    print(f"[DEBUG] No group matched for line: {line}")
    return None
 
 
def update_extinf(line, tv_ids, logos):
    if ',' not in line:
        return line
    prefix, display_name = line.split(',', 1)
    key = display_name.strip().lower()
 
    # Update or add tvg-id
    if key in tv_ids:
        if 'tvg-id="' in prefix:
            prefix = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{tv_ids[key]}"', prefix)
        else:
            prefix += f' tvg-id="{tv_ids[key]}"'
 
    # Update or add tvg-logo
    if key in logos:
        if 'tvg-logo="' in prefix:
            prefix = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logos[key]}"', prefix)
        else:
            prefix += f' tvg-logo="{logos[key]}"'
 
    return f'{prefix},{display_name}'
 
 
def main():
    tv_ids = load_mapping(TVIDS_FILE)
    logos = load_mapping(LOGOS_FILE)
 
    print(f"[INFO] Fetching playlist from {SOURCE_URL} ...")
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()
 
    result = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    i = 0
    channels_processed = 0
 
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            group = get_group_title(line, tv_ids)
            if not group:
                print(f"[DEBUG] Skipping channel at line {i} - no allowed group found.")
                i += 2
                continue
 
            # Update or add group-title attribute
            if 'group-title="' in line:
                line = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', line)
            else:
                parts = line.split(',', 1)
                line = parts[0] + f' group-title="{group}",' + parts[1]
 
            # Update tvg-id and tvg-logo from your mappings
            line = update_extinf(line, tv_ids, logos)
 
            # Unwrap URL if it's wrapped
            stream_url = unwrap_url(lines[i + 1].strip())
 
            result.append(line)
            result.append(stream_url)
 
            channels_processed += 1
            i += 2
        else:
            i += 1
 
    # Write the output playlist file
    output_path = os.path.join(BASE_DIR, OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))
 
    print(f"[INFO] Done. {channels_processed} channels written to {output_path}")
 
 
if __name__ == '__main__':
    main()
