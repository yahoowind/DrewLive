import requests
import re

SOURCE_URL = 'http://drewski2423-dproxy.hf.space/playlist/events'
OUTPUT_FILE = 'DaddyLiveEvents.m3u8'
EPG_URL = 'https://tinyurl.com/dummy2423-epg'  # forced new EPG URL

BLOCKED_GROUPS = {
    group.lower() for group in [
        "ATHLETICS", "CRICKET", "DARTS", "FENCING", "FUTSAL",
        "HANDBALL", "HORSE RACING", "SNOOKER", "TENNIS",
        "TV SHOWS", "WATER SPORTS","VOLLYBALL","RUGBY UNION",
        "GYMNASTICS", "CYCLING","BADMINTON", "VOLLEYBALL",
        "AUSSIE RULES", "EQUESTRIAN", "RUGBY LEAGUE", "NETBALL",
        "BOWLING", "CLIMBING", "FLOOR-BALL", "FRISBEE", "GAA",
        "LACROSSE", "SAILING / BOATING", "SQUASH", "FLOORBALL",
        "WATER POLO", "BEACH SOCCER", "FIELD HOCKEY",
        "WEIGHTLIFTING", "TRIATHLON",
    ]
}

def extract_group_title(extinf_line):
    match = re.search(r'group-title="([^"]+)"', extinf_line, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return ""

def extract_channel_name(extinf_line):
    parts = extinf_line.split(',', 1)
    if len(parts) > 1:
        return parts[1].strip().lower()
    return ""

def force_tvg_id(extinf_line):
    # Remove any existing tvg-id attribute
    extinf_line = re.sub(r'tvg-id="[^"]*"', '', extinf_line)
    # Insert forced tvg-id after #EXTINF:-1 (or after group-title if present)
    if 'group-title=' in extinf_line:
        extinf_line = re.sub(r'(#EXTINF:-1\s*)(group-title="[^"]+")',
                            r'\1\2 tvg-id="Sports.Dummy.us"', extinf_line)
    else:
        extinf_line = re.sub(r'(#EXTINF:-1)',
                            r'\1 tvg-id="Sports.Dummy.us"', extinf_line)
    return extinf_line

def main():
    print("[*] Fetching event playlist...")
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
    except Exception as e:
        print(f"[!] Error fetching source: {e}")
        return

    lines = response.text.splitlines()

    channels = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            group = extract_group_title(line)
            if group not in BLOCKED_GROUPS:
                if i + 1 < len(lines):
                    url_line = lines[i + 1]
                    forced_extinf = force_tvg_id(line)
                    channels.append((forced_extinf, url_line))
            i += 2
        else:
            i += 1

    channels.sort(key=lambda ch: extract_channel_name(ch[0]))

    filtered = [f'#EXTM3U url-tvg="{EPG_URL}"']
    for extinf_line, url_line in channels:
        filtered.append(extinf_line)
        filtered.append(url_line)

    print(f"[*] Writing filtered and sorted playlist to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered))

if __name__ == '__main__':
    main()
