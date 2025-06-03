import requests
import re

SOURCE_URL = 'http://drewlive24.duckdns.org:7860/playlist/events'
OUTPUT_FILE = 'DaddyLiveEvents.m3u8'
EPG_URL = 'https://raw.githubusercontent.com/pigzillaaaaa/daddylive/refs/heads/main/epgs/daddylive-events-epg.xml'

BLOCKED_GROUPS = {
    group.lower() for group in [
        "ATHLETICS", "CRICKET", "DARTS", "FENCING", "FUTSAL",
        "HANDBALL", "HORSE RACING", "SNOOKER", "TENNIS",
        "TV SHOWS", "WATER SPORTS"
    ]
}

def extract_group_title(extinf_line):
    match = re.search(r'group-title="([^"]+)"', extinf_line, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return ""

def main():
    print("[*] Fetching event playlist...")
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
    except Exception as e:
        print(f"[!] Error fetching source: {e}")
        return

    lines = response.text.splitlines()
    filtered = [f'#EXTM3U url-tvg="{EPG_URL}"']

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            group = extract_group_title(line)
            if group not in BLOCKED_GROUPS:
                filtered.append(line)
                if i + 1 < len(lines):
                    filtered.append(lines[i + 1])
            i += 2
        else:
            i += 1

    print(f"[*] Writing filtered playlist to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered))

if __name__ == '__main__':
    main()