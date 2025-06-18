import requests
import asyncio
from playwright.async_api import async_playwright, Page, Request

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

# Shared headers to inject into the M3U8 playlist for the locked channels
FORCED_HEADERS = [
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
]

# This dictionary now maps Channel Name to its DaddyLive numerical ID.
# This will be used by Playwright to construct the stream page URL.
# You have correctly populated these with your findings.
CHANNELS_TO_PROCESS = {
    "NBC10 Philadelphia": "277",
    "TNT Sports 1 UK": "31",
    "Discovery Channel": "313",
    "Discovery Life Channel": "311",
    "Disney Channel": "312",
    "Disney XD": "314",
    "E! Entertainment": "315",
    "ESPN Deportes": "375",
    "ESPN USA": "44",
    "ESPN2 USA": "45",
    "ESPNews": "288",
    "ESPNU USA": "316",
    "Fox Business": "297",
    "Fox News": "347",
    "Fox Sports 1": "39",
    "FOX USA": "54",
    "Freeform": "301",
    # You had FOX USA listed twice. Assuming the second one meant to be something else,
    # but keeping it as is for now based on your input.
    # If the second "FOX USA" with ID 54 was meant to be another channel like "FUSE",
    # you'd correct it here with its proper ID.
    "FUSE TV USA": "279",
    "FX Movie Channel": "381",
    "FX USA": "317",
    "FXX USA": "298",
    "Game Show Network": "319",
    "GOLF Channel USA": "318",
    "Hallmark Movies & Mysteries": "296",
    "HBO USA": "321",
    "Headline News": "323",
    "HGTV": "382",
    "History USA": "322",
    "Investigation Discovery (ID USA)": "324",
    "ION USA": "325",
    "Law & Crime Network": "278",
    "Lifetime Movies Network": "389",
    "Lifetime Network": "326",
    "Magnolia Network": "299",
    "MSNBC": "327",
    "MTV USA": "371",
    "National Geographic (NGC)": "328",
    "NBC Sports Philadelphia": "777",
    "NBC USA": "53",
    "NewsNation USA": "292",
    "NICK": "330",
    "NICK JR": "329",
    "Oprah Winfrey Network (OWN)": "331",
    "Oxygen True Crime": "332",
    "Pac-12 Network USA": "287",
    "Paramount Network": "334",
    "Reelz Channel": "293",
    "Science Channel": "294",
    "SEC Network USA": "385",
}

async def get_fresh_locked_channel_urls_async():
    """
    Uses Playwright to navigate to each channel's stream page,
    reload it, and intercept the fresh M3U8 URL.
    Returns a dictionary of {channel_name: fresh_m3u8_url}.
    """
    fresh_urls = {}
    print("🔄 Launching browser to fetch fresh locked channel URLs...")

    async with async_playwright() as p:
        # Set headless=False for debugging to see the browser actions
        # Set headless=True for production to run in background
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        page.set_default_timeout(60000) # Default timeout for Playwright operations (60 seconds)

        try:
            for channel_name, channel_id in CHANNELS_TO_PROCESS.items():
                stream_page_url = f"https://daddylive.top/stream/stream-{channel_id}.php"
                print(f"\n⚡️ Processing {channel_name} (ID: {channel_id}) from {stream_page_url}")

                # 1. Navigate to the specific stream page
                try:
                    await page.goto(stream_page_url, wait_until="domcontentloaded")
                    print(f"  Navigated to {stream_page_url}")
                    # Give the page a moment to load elements and execute initial JS
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    print(f"  ❌ Error navigating to {stream_page_url}: {e}")
                    continue # Skip to next channel

                # --- IMPORTANT: Handle any pop-ups/overlays on this stream page ---
                # Based on your manual observation (F12 Developer Tools):
                # If there's a "Play" button or an ad overlay that needs to be clicked
                # before the video loads, you MUST uncomment and fill in this section.
                # Example:
                # try:
                #     # This selector needs to be highly accurate for the play button/overlay
                #     play_button_selector = "a.play-btn" # REPLACE WITH ACTUAL SELECTOR, e.g., 'div.video-overlay', 'button#playVideo'
                #     if await page.locator(play_button_selector).is_visible(timeout=5000):
                #         print(f"  Attempting to click play button/overlay at: {play_button_selector}")
                #         await page.locator(play_button_selector).click()
                #         await page.wait_for_timeout(2000) # Give time for click action to register
                #     else:
                #         print("  No visible play button/overlay found.")
                # except Exception as e:
                #     print(f"  Error handling play button/overlay: {e}")
                #     pass # Proceed even if no play button is found or clicked

                # The core of your manual process: "pressed refresh, typed .m3u8"
                # We'll use page.wait_for_request to capture the M3U8 after reload.
                
                target_m3u8_url = None
                
                # Define the predicate (a function to filter network requests)
                # This filter should match the exact master.m3u8 URL you see in F12
                def is_specific_stream_m3u8(request_obj: Request):
                    return (
                        "nice-flower.store" in request_obj.url and # Check the domain
                        "master.m3u8" in request_obj.url and      # Ensure it's the master playlist
                        (request_obj.url.endswith(".m3u8") or ".m3u8?" in request_obj.url) # Ensure it ends in .m3u8 or has .m3u8?
                        # Add more specificity if needed, e.g., and "v3/director" in request_obj.url
                    )

                try:
                    # Start waiting for the specific M3U8 request. This sets up the listener.
                    request_promise = page.wait_for_request(is_specific_stream_m3u8, timeout=30000) # 30s timeout to find the M3U8

                    # Now, perform the action that triggers the request: reload the page
                    print("  Reloading page to trigger M3U8 request...")
                    # 'networkidle' waits until there are no more than 0 network connections for 500 ms
                    # This is generally more reliable for dynamic content than 'domcontentloaded' or 'load'.
                    await page.reload(wait_until="networkidle")
                    await page.wait_for_timeout(1000) # Small pause after reload for stability

                    # Await the request promise. This will block until a matching request is made or timeout occurs.
                    m3u8_request = await request_promise
                    target_m3u8_url = m3u8_request.url
                    fresh_urls[channel_name] = target_m3u8_url
                    print(f"  ✅ Captured M3U8 URL for {channel_name}: {target_m3u8_url}")

                except Exception as e:
                    print(f"  ❌ Failed to capture M3U8 URL for {channel_name} after reload: {e}")
                    # This channel will not be added to fresh_urls, and thus won't be updated in the playlist.
                
        except Exception as e:
            print(f"❌ An unexpected error occurred during browser automation: {e}")
        finally:
            await browser.close()
            print("Browser closed.")

    if not fresh_urls:
        print("🛑 No fresh URLs were obtained during the browser automation. Check your IDs and selectors.")
    return fresh_urls

def update_playlist():
    global LOCKED_CHANNELS # Not using this global anymore, but keeping for reference if needed
    
    # Call the async function to get the fresh URLs
    # This dictionary will now hold the actual, up-to-date M3U8 URLs
    freshly_fetched_locked_channels = asyncio.run(get_fresh_locked_channel_urls_async())

    if not freshly_fetched_locked_channels:
        print("🛑 No fresh locked channel URLs obtained. Aborting playlist update.")
        return

    try:
        # Fetch the UPSTREAM_URL template M3U8
        response = requests.get(UPSTREAM_URL, timeout=20)
        response.raise_for_status()
        lines = response.text.splitlines()
        output = []
        i = 0

        # Iterate through the lines of the UPSTREAM_URL playlist
        while i < len(lines):
            line = lines[i]

            matched_channel_name = None
            # Check if this line corresponds to one of our "locked" channels
            for channel_name in freshly_fetched_locked_channels:
                if line.startswith("#EXTINF") and channel_name in line:
                    matched_channel_name = channel_name
                    break

            if matched_channel_name:
                output.append(line) # Keep the #EXTINF line
                i += 1

                # Skip any existing EXTVLCOPT headers or old URLs from the upstream playlist
                while i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                    i += 1
                
                # Insert our forced headers
                output.extend(FORCED_HEADERS)

                # Insert the freshly fetched, working M3U8 URL for this channel
                output.append(freshly_fetched_locked_channels[matched_channel_name])

                # Ensure we skip the original URL line from the upstream playlist if it exists
                if i < len(lines) and not lines[i].startswith("#"):
                    i += 1
            else:
                # If it's not a locked channel, just append the line as is
                output.append(line)
                i += 1

        # Write the modified playlist to the output file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output) + "\n")

        print("✅ Playlist updated with locked streams and forced headers.")

    except Exception as e:
        print(f"❌ Error updating playlist: {e}")

if __name__ == "__main__":
    update_playlist()