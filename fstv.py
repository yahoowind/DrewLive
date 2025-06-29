from bs4 import BeautifulSoup
import re

def update_playlist_with_logos_and_urls():
    with open("FSTV_PAGE_SOURCE.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Extract info per channel div
    channels = []
    for div in soup.find_all("div", class_="item-channel"):
        url = div.get("data-link")
        logo = div.get("data-logo")
        name = div.get("title")  # channel name from html (optional)
        channels.append({"url": url, "logo": logo, "name": name})

    with open("FSTV.m3u8", "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    channel_index = 0

    extinf_pattern = re.compile(r'(#EXTINF:[^\n]*)(?:tvg-logo="[^"]*")?([^\n]*),(.+)')
    # This pattern matches #EXTINF lines and captures parts before tvg-logo, any trailing text, and channel name.

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("#EXTINF"):
            match = extinf_pattern.match(line)
            if match and channel_index < len(channels):
                prefix = match.group(1)  # e.g. '#EXTINF:-1 '
                suffix = match.group(2)  # any other attributes besides tvg-logo
                channel_name = match.group(3).strip()

                # Get new logo url
                new_logo = channels[channel_index]["logo"]

                # Build new EXTINF line preserving tvg-id and other attrs, only replacing tvg-logo
                new_extinf = f'{prefix}tvg-logo="{new_logo}"{suffix},{channel_name}\n'
                updated_lines.append(new_extinf)

                # Next line should be URL, replace with new one from HTML
                i += 1
                new_url = channels[channel_index]["url"] + "\n"
                updated_lines.append(new_url)

                channel_index += 1
            else:
                # No match or no channel left, just copy line and next line
                updated_lines.append(line)
                i += 1
                if i < len(lines):
                    updated_lines.append(lines[i])
        else:
            updated_lines.append(line)
        i += 1

    with open("FSTV24.m3u8", "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print(f"🎯 Updated {channel_index} channels in FSTV24.m3u8")
