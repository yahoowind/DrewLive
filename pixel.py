import requests
import re

URL = "https://iptv-scraper-re.vercel.app/pixelsport"
OUTPUT_FILE = "PixelSports.m3u"
FORCED_GROUP = "PixelSports"
FORCED_TVG_ID = "Sports.Dummy.us"
CUSTOM_EPG = "https://tinyurl.com/dummy2423-epg"

def fetch_playlist(url):
    """
    Fetches the raw M3U playlist content from the given URL.
    Raises an HTTPError for bad responses (4xx or 5xx).
    """
    try:
        resp = requests.get(url, timeout=10) # Added a timeout for robustness
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException as e:
        # Catch specific request exceptions for better error messages
        raise ConnectionError(f"Failed to fetch URL {url}: {e}") from e

def force_metadata(extinf_line):
    """
    Modifies an #EXTINF line to force specific tvg-id and group-title attributes.
    """
    # Use re.split to handle potential spaces around the comma in #EXTINF lines
    parts = re.split(r',', extinf_line, 1)
    metadata_part = parts[0]
    title_part = parts[1].strip() if len(parts) > 1 else ""

    # Force or replace tvg-id
    if 'tvg-id="' in metadata_part:
        metadata_part = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{FORCED_TVG_ID}"', metadata_part)
    else:
        # Insert tvg-id after #EXTINF or a preceding attribute for cleaner output
        match = re.match(r'(#EXTINF:[^ ]*) ?(.*)', metadata_part)
        if match:
            # If there are existing attributes, insert after them, otherwise after #EXTINF:
            existing_attrs = match.group(2).strip()
            if existing_attrs:
                metadata_part = f"{match.group(1)} tvg-id=\"{FORCED_TVG_ID}\" {existing_attrs}"
            else:
                metadata_part = f"{match.group(1)} tvg-id=\"{FORCED_TVG_ID}\""
        else: # Fallback if regex fails, just append
            metadata_part += f' tvg-id="{FORCED_TVG_ID}"'


    # Force or replace group-title
    if 'group-title="' in metadata_part:
        metadata_part = re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP}"', metadata_part)
    else:
        # Similar insertion logic for group-title
        match = re.match(r'(#EXTINF:[^ ]*) ?(.*)', metadata_part)
        if match:
            existing_attrs = match.group(2).strip()
            if existing_attrs:
                metadata_part = f"{match.group(1)} group-title=\"{FORCED_GROUP}\" {existing_attrs}"
            else:
                metadata_part = f"{match.group(1)} group-title=\"{FORCED_GROUP}\""
        else: # Fallback if regex fails, just append
            metadata_part += f' group-title="{FORCED_GROUP}"'

    return f"{metadata_part},{title_part}"

def build_playlist(raw_content):
    """
    Parses raw M3U content and rebuilds it with forced metadata and
    proper M3U header and EPG URL.
    """
    lines = raw_content.splitlines()
    output_lines = []

    # Always start with #EXTM3U and the custom EPG URL
    output_lines.append(f'#EXTM3U url-tvg="{CUSTOM_EPG}"')

    # Skip any original #EXTM3U line if present in the raw input,
    # as we've already added our custom one.
    start_index = 0
    if lines and lines[0].strip().startswith("#EXTM3U"):
        start_index = 1

    i = start_index
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF:"):
            # Force metadata line
            output_lines.append(force_metadata(line))
            i += 1

            # Collect any optional M3U tags specific to the channel
            # These are typically #EXTVLCOPT or other #EXT- tags before the URL
            while i < len(lines) and lines[i].strip().startswith("#") and not lines[i].strip().startswith("#EXTINF"):
                output_lines.append(lines[i].strip())
                i += 1

            # Add the actual stream URL
            # Ensure it's not another #EXTINF or an empty line.
            if i < len(lines) and not lines[i].strip().startswith("#") and lines[i].strip():
                output_lines.append(lines[i].strip())
                i += 1
            else:
                # Handle cases where #EXTINF is not followed by a URL (e.g., malformed)
                # It's better to log this or decide how to handle incomplete entries.
                # For now, we just move on, effectively skipping the URL.
                print(f"Warning: #EXTINF at line {i-1} not followed by a valid stream URL.")
                # We don't increment i here because the next iteration of the while loop
                # will pick up the current line if it's not a URL, or the next if it is.
                # This prevents skipping valid subsequent EXTINF entries.
                pass # The outer loop will handle incrementing 'i' if the line wasn't consumed.

        elif line.strip() == "":
            # Pass through empty lines cleanly
            output_lines.append("")
            i += 1
        elif line.startswith("#"):
            # Pass through any other unrecognized M3U headers (e.g., #EXTGRP, #EXTART)
            # but ensure we don't duplicate #EXTM3U if it was handled at the start
            if not line.startswith("#EXTM3U"):
                output_lines.append(line)
            i += 1
        else:
            # If it's not an EXTINF and not a recognized # tag or empty,
            # it might be an orphaned URL or something unexpected.
            # You might want to log this for debugging.
            print(f"Warning: Unrecognized line skipped: '{line}'")
            i += 1

    return "\n".join(output_lines) + "\n"

def main():
    print(f"Attempting to update PixelSports playlist from {URL}...")
    try:
        raw_content = fetch_playlist(URL)
        final_playlist = build_playlist(raw_content)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(final_playlist)

        print(f"✅ Successfully generated and saved '{OUTPUT_FILE}'.")
        print(f"Total lines in output: {len(final_playlist.splitlines())}")

    except ConnectionError as e:
        print(f"❌ Network/Fetch Error: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
