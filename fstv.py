from bs4 import BeautifulSoup

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

# Now update playlist URLs while preserving channel names
updated_lines = []
url_index = 0

for line in playlist_lines:
    if line.startswith("http") or line.startswith("https"):
        # Replace URL with the new one from HTML in order
        if url_index < len(html_urls):
            new_url = html_urls[url_index]
            updated_lines.append(new_url + "\n")
            url_index += 1
        else:
            # No new URL? Keep old URL
            updated_lines.append(line)
    else:
        # Not a URL line, keep as is (this keeps your custom channel names intact)
        updated_lines.append(line)

# Save the updated playlist
with open("FSTV24.m3u8", "w", encoding="utf-8") as f:
    f.writelines(updated_lines)

print(f"Updated {url_index} URLs in playlist.")