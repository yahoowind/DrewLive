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

def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    return query_params.get('url', [url])[0]

def extract_group_title(line):
    match = re.search(r'group-title="([^"]+)"', line)
    return match.group(1).strip().upper() if match else None

def replace_group_title(line, old_group):
    if old_group in ALLOWED_COUNTRIES:
        return re.sub(r'group-title="[^"]+"', f'group-title="{ALLOWED_COUNTRIES[old_group]}"', line)
    return line

def main():
    # Step 1: Pull fresh stream URLs from source
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    remote_lines = response.text.splitlines()

    # Step 2: Build fresh URL list for allowed groups
    fresh_urls = []
    i = 0
    while i < len(remote_lines):
        if remote_lines[i].startswith('#EXTINF') and (i + 1) < len(remote_lines):
            group_title = extract_group_title(remote_lines[i])
            if group_title and group_title in ALLOWED_COUNTRIES:
                fresh_urls.append(unwrap_url(remote_lines[i + 1].strip()))
            i += 2
        else:
            i += 1

    # Step 3: Update existing playlist by replacing only URLs
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        template_lines = f.read().splitlines()

    result = []
    i = 0
    fresh_index = 0
    updated = 0

    while i < len(template_lines):
        line = template_lines[i]

        if line.startswith('#EXTM3U'):
            result.append(line)  # Preserve custom EPG line
            i += 1
        elif line.startswith('#EXTINF') and (i + 1) < len(template_lines):
            group_title = extract_group_title(line)
            fixed_line = replace_group_title(line, group_title) if group_title else line
            result.append(fixed_line)  # Preserve or correct group name

            if group_title and group_title in ALLOWED_COUNTRIES and fresh_index < len(fresh_urls):
                result.append(fresh_urls[fresh_index])  # Replace URL
                fresh_index += 1
                updated += 1
            else:
                result.append(template_lines[i + 1])  # Keep original URL
            i += 2
        else:
            result.append(line)
            i += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))

    print(f"[+] Updated {updated} stream URLs in {OUTPUT_FILE} — metadata untouched.")

if __name__ == '__main__':
    main()
