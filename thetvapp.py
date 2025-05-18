import requests
import os

URL = "http://75.163.131.149:8090/tvpass/playlist?quality=all"
FILENAME = "TheTVApp.m3u8"

def fetch_playlist(url):
    print("Fetching playlist...")
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def save_if_changed(new_data, filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            current_data = f.read()
        if current_data == new_data:
            print("No changes detected.")
            return False
    with open(filename, "w", encoding="utf-8") as f:
        f.write(new_data)
    print(f"Saved updated playlist to {filename}")
    return True

if __name__ == "__main__":
    try:
        data = fetch_playlist(URL)
        save_if_changed(data, FILENAME)
    except Exception as e:
        print(f"Error: {e}")