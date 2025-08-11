import requests
import re
import time
import subprocess
import os
from datetime import datetime

UPSTREAM_URL = "https://pigscanflyyy-scraper.vercel.app/tims"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"
FORCED_TVG_ID = "24.7.Dummy.us"

def fetch_url(url, retries=5, delay=5):
    headers = {"User-Agent": "Mozilla/5.0 (GitHubActions; Python Requests)"}
    for attempt in range(1, retries + 1):
        try:
            print(f"Fetching {url} (Attempt {attempt}/{retries})...")
            r = requests.get(url, headers=headers, timeout=30)
            print(f"Status: {r.status_code}")
            if r.status_code != 200:
                time.sleep(delay)
                continue
            return r.text
        except Exception as e:
            print(f"Error: {e}, retrying in {delay}s...")
            time.sleep(delay)
    return None

def modify_playlist(playlist_text):
    def repl(match):
        duration = match.group(1)
        attrs_str = match.group(2) or ""
        channel_name = match.group(3)

        # Remove existing tvg-id and group-title attrs only
        attrs_str = re.sub(r'tvg-id="[^"]*"', '', attrs_str)
        attrs_str = re.sub(r'group-title="[^"]*"', '', attrs_str)

        # Clean extra whitespace
        attrs_str = ' '.join(attrs_str.split())

        # Append forced attributes
        forced_attrs = f'tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}"'
        new_attrs = f"{attrs_str} {forced_attrs}".strip()

        return f"#EXTINF:{duration} {new_attrs},{channel_name}"

    pattern = re.compile(r'#EXTINF:([-\d\.]+)\s*([^,]*),(.*)')
    return pattern.sub(repl, playlist_text)

def file_content(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def git_commit_push(filename):
    print("Checking git status...")
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)

    subprocess.run(["git", "add", filename], check=True)

    # Check if there are any changes staged
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        print("✅ No changes to commit.")
        return

    commit_message = f"🔁 Update playlist {datetime.utcnow().strftime('%a %b %d %T UTC %Y')}"
    print(f"Committing: {commit_message}")
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # Push with retry on rejection
    for attempt in range(2):
        push_result = subprocess.run(["git", "push", "origin", "main"])
        if push_result.returncode == 0:
            print("✅ Push succeeded.")
            return
        else:
            print("⚠️ Push failed. Attempting git pull --rebase and retry...")
            pull_result = subprocess.run(["git", "pull", "--rebase", "origin", "main"])
            if pull_result.returncode != 0:
                print("❌ Rebase failed, aborting push.")
                return
    print("❌ Push failed after retries.")

def main():
    playlist = fetch_url(UPSTREAM_URL)
    if playlist is None:
        print("Failed to fetch upstream playlist. Exiting.")
        return

    modified_playlist = modify_playlist(playlist)

    existing_content = file_content(OUTPUT_FILE)
    if existing_content == modified_playlist:
        print("Playlist unchanged. No update needed.")
        return

    print("Saving updated playlist...")
    write_file(OUTPUT_FILE, modified_playlist)

    git_commit_push(OUTPUT_FILE)

if __name__ == "__main__":
    main()
