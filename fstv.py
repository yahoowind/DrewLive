from bs4 import BeautifulSoup
import os

# Load your current playlist (FSTV.m3u8)
with open("FSTV.m3u8", "r", encoding="utf-8") as f:
    playlist_lines = f.readlines()

# Load the HTML file (FSTV_PAGE_SOURCE.html)
with open("FSTV_PAGE_SOURCE.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Extract URLs from HTML
html_urls = []
for div in soup.find_all("div", class_="item-channel"):
    url = div.get("data-link")
    if url:
        html_urls.append(url)

# Update playlist URLs while preserving channel names
updated_lines = []
url_index = 0

for line in playlist_lines:
    if line.startswith("http") or line.startswith("https"):
        if url_index < len(html_urls):
            new_url = html_urls[url_index]
            updated_lines.append(new_url + "\n")
            url_index += 1
        else:
            updated_lines.append(line)
    else:
        updated_lines.append(line)

# Prepare the new content as a string
new_content = "".join(updated_lines)

# Check if file exists and content is different before writing
file_path = "FSTV24.m3u8"
write_file = True
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        old_content = f.read()
    if old_content == new_content:
        write_file = False

if write_file:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated {url_index} URLs in playlist and wrote changes.")
else:
    print(f"Updated {url_index} URLs but no changes detected, no file written.")
