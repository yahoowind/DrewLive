import requests
import re

SOURCE_URL = 'http://drewski2423-dproxy.hf.space/playlist/events'
OUTPUT_FILE = 'DaddyLiveEvents.m3u8'
EPG_URL = 'https://raw.githubusercontent.com/pigzillaaaaa/daddylive/refs/heads/main/epgs/daddylive-events-epg.xml'

BLOCKED_GROUPS = {
    group.lower() for group in [
        "ATHLETICS", "CRICKET", "DARTS", "FENCING", "FUTSAL",
        "HANDBALL", "HORSE RACING", "SNOOKER", "TENNIS",
        "TV SHOWS", "WATER SPORTS","VOLLYBALL","RUGBY UNION",
        "GYMNASTICS","CYCLING","BADMINTON","VOLLEYBALL",
        "AUSSIE RULES","EQUESTRIAN","RUGBY LEAGUE","NETBALL",
    ]
}

def extract_group_title(extinf_line):
    match = re.search(r'group-title="([^"]+)"', extinf_line, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return ""

def extract_channel_name(extinf_line):
    # Extract the channel display name after the comma in #EXTINF line
    # Example: #EXTINF:-1 group-title="News",CNN HD  -> returns "CNN HD"
    parts = extinf_line.split(',', 1)
    if len(parts) > 1:
        return parts[1].strip().lower()
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

    # Collect filtered channels as (extinf_line, url_line) tuples
    channels = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            group = extract_group_title(line)
            if group not in BLOCKED_GROUPS:
                if i + 1 < len(lines):
                    url_line = lines[i + 1]
                    channels.append((line, url_line))
            i += 2
        else:
            i += 1

    # Sort channels alphabetically by channel display name
    channels.sort(key=lambda ch: extract_channel_name(ch[0]))

    # Prepare output lines with EPG header
    filtered = [f'#EXTM3U url-tvg="{EPG_URL}"']
    for extinf_line, url_line in channels:
        filtered.append(extinf_line)
        filtered.append(url_line)

    print(f"[*] Writing filtered and sorted playlist to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered))

if __name__ == '__main__':
    main()
