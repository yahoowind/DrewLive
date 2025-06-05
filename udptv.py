import requests
from collections import OrderedDict
import re
from urllib.parse import urlparse, quote
from datetime import datetime
import subprocess
import sys

# Config
GIT_RAW_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u"
UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP_TITLE = "UDPTV Live Streams"
MY_DOMAIN = "http://drewlive24.duckdns.org:3000"
GIT_COMMIT_MSG_PREFIX = "Auto update playlist"

def fetch_m3u(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def clean_lines(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U") or "url-tvg=" in line:
            continue
        cleaned.append(line)
    return cleaned

def get_channel_key(extinf):
    return extinf.split(",")[-1].strip().lower()

def parse_m3u(lines):
    result = OrderedDict()
    last_extinf = None
    for line in lines:
        if line.startswith("#EXTINF"):
            last_extinf = line
        elif last_extinf:
            key = get_channel_key(last_extinf)
            result[key] = (last_extinf, line)
            last_extinf = None
    return result

def force_group_title(meta, forced_group=FORCED_GROUP_TITLE):
    if 'group-title="' in meta:
        meta = re.sub(r'group-title="[^"]*"', f'group-title="{forced_group}"', meta)
    else:
        meta = re.sub(r'(#EXTINF:[^,]+,)', r'\1 group-title="' + forced_group + '",', meta, count=1)
    return meta

def replace_domain(url):
    try:
        encoded_url = quote(url, safe='')
        return f"{MY_DOMAIN}/stream?url={encoded_url}"
    except Exception:
        return url

def merge_playlists(git_dict, upstream_dict):
    merged_dict = {}

    for key, (meta, _) in git_dict.items():
        upstream_url = upstream_dict.get(key, (None, None))[1]
        url_to_use = upstream_url if upstream_url else git_dict[key][1]
        proxied_url = replace_domain(url_to_use)
        merged_dict[key] = (force_group_title(meta), proxied_url)

    for key, (meta, url) in upstream_dict.items():
        if key not in merged_dict:
            proxied_url = replace_domain(url)
            merged_dict[key] = (force_group_title(meta), proxied_url)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    merged = [f'#EXTM3U url-tvg="{EPG_URL}"', f'# Updated: {timestamp}']

    for key in sorted(merged_dict.keys()):
        meta, url = merged_dict[key]
        merged.append(meta)
        merged.append(url)

    return merged

def git_commit_push(filename, commit_msg):
    try:
        subprocess.run(["git", "add", filename], check=True)
        # Check if there is anything to commit
        diff_check = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if diff_check.returncode == 0:
            print("No changes to commit.")
            return False

        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Changes committed and pushed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        return False

def main():
    print("Fetching playlists...")
    git_lines = clean_lines(fetch_m3u(GIT_RAW_URL))
    upstream_lines = clean_lines(fetch_m3u(UPSTREAM_URL))

    print("Parsing playlists...")
    git_dict = parse_m3u(git_lines)
    upstream_dict = parse_m3u(upstream_lines)

    print("Merging playlists...")
    merged_playlist = merge_playlists(git_dict, upstream_dict)

    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged_playlist) + "\n")

    commit_msg = f"{GIT_COMMIT_MSG_PREFIX} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    print("Running git add, commit, and push...")
    committed = git_commit_push(OUTPUT_FILE, commit_msg)
    if not committed:
        print("No changes detected or git push failed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
