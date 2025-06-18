import requests
import asyncio
from playwright.async_api import async_playwright, Page, Request
import os

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

FORCED_HEADERS = [
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
]

CHANNELS_TO_PROCESS = {
    "NBC10 Philadelphia": "277", "TNT Sports 1 UK": "31", "Discovery Channel": "313",
    "Discovery Life Channel": "311", "Disney Channel": "312", "Disney XD": "314",
    "E! Entertainment": "315", "ESPN Deportes": "375", "ESPN USA": "44",
    "ESPN2 USA": "45", "ESPNews": "288", "ESPNU USA": "316", "Fox Business": "297",
    "Fox News": "347", "Fox Sports 1": "39", "FOX USA": "54", "Freeform": "301",
    "FUSE TV USA": "279", "FX Movie Channel": "381", "FX USA": "317",
    "FXX USA": "298", "Game Show Network": "319", "GOLF Channel USA": "318",
    "Hallmark Movies & Mysteries": "296", "HBO USA": "321", "Headline News": "323",
    "HGTV": "382", "History USA": "322", "Investigation Discovery (ID USA)": "324",
    "ION USA": "325", "Law & Crime Network": "278", "HFTN": "531", # Added HFTN as an example for another channel
    "Lifetime Movies Network": "389", "Lifetime Network": "326", "Magnolia Network": "299",
    "MSNBC": "327", "MTV USA": "371", "National Geographic (NGC)": "328",
    "NBC Sports Philadelphia": "777", "NBC USA": "53", "NewsNation USA": "292",
    "NICK": "330", "NICK JR": "329", "Oprah Winfrey Network (OWN)": "331",
    "Oxygen True Crime": "332", "Pac-12 Network USA": "287",
    "Paramount Network": "334", "Reelz Channel": "293", "Science Channel": "294",
    "SEC Network USA": "385",
}

async def get_fresh_locked_channel_urls_async():
    fresh_urls = {}
    print("🔄 Launching browser to fetch fresh locked channel URLs...")

    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Listen for new pages (e.g., pop-up ads) and close them
        context.on('page', lambda page: asyncio.create_task(close_new_page(page)))
        
        page = await context.new_page()
        page.set_default_timeout(90000)

        try:
            for channel_name, channel_id in CHANNELS_TO_PROCESS.items():
                stream_page_url = f"https://thedaddy.click/stream/stream-{channel_id}.php"
                print(f"\n⚡️ Attempting to navigate to: {channel_name} ({stream_page_url})")

                try:
                    # Navigate and wait for the network to be idle
                    await page.goto(stream_page_url, wait_until="networkidle", timeout=60000)
                    print(f"  Successfully navigated to {page.url} (Network Idle achieved)")
                    
                    screenshot_path_idle = f"screenshots/{channel_name.replace(' ', '_')}_network_idle.png"
                    await page.screenshot(path=screenshot_path_idle)
                    print(f"  Network idle screenshot taken: {screenshot_path_idle}")

                    # Check for redirects or explicit error pages
                    if "404" in page.url or "error" in page.url.lower() or "blocked" in page.url.lower():
                        print(f"  ⚠️ Warning: Page navigated to an error/blocked URL: {page.url}")
                        continue

                    await page.wait_for_timeout(3000) # Give extra time for JS to run

                    # --- CRITICAL: Handle "Play" buttons / Overlays / Ads ---
                    # You MUST observe what element needs clicking and get its CSS selector.
                    # Add multiple selectors if different types of pop-ups appear.
                    possible_click_selectors = [
                        "button.play-button",      # Generic play button
                        "div.video-overlay button",# Play button within an overlay
                        "a.play-btn",              # Anchor tag acting as play button
                        "div#player-overlay button", # Specific player overlay button
                        "button[aria-label='Play']", # ARIA labeled play button
                        "div[onclick*='playVideo']", # Div with inline click handler
                        "div.ad-close-button",     # Common ad close button
                        "button.skip-ad",          # Skip ad button
                        "button#player-play-btn",  # Another common id
                        "div.vjs-big-play-button"  # Video.js default play button
                    ]

                    clicked_something = False
                    for selector in possible_click_selectors:
                        try:
                            # Use locator to check visibility and click if present
                            locator = page.locator(selector)
                            if await locator.is_visible(timeout=2000): # Check if element is visible
                                print(f"  Attempting to click: {selector}")
                                await locator.click(timeout=5000) # Click with a timeout
                                await page.wait_for_timeout(2000) # Wait for effect of click
                                clicked_something = True
                                print(f"  Successfully clicked: {selector}")
                                break # Stop after first successful click
                            # else:
                            #     print(f"  {selector} not visible.")
                        except Exception as e:
                            # print(f"  Error trying to click {selector}: {e}")
                            pass # Element not found or clickable, try next selector

                    if not clicked_something:
                        print("  No common play button/overlay clicked. Proceeding assuming none needed or missed.")
                    else:
                         # Take another screenshot after attempted clicks
                        screenshot_path_after_click = f"screenshots/{channel_name.replace(' ', '_')}_after_click.png"
                        await page.screenshot(path=screenshot_path_after_click)
                        print(f"  Screenshot after potential click: {screenshot_path_after_click}")


                    # The core of your manual process: "pressed refresh, typed .m3u8"
                    target_m3u8_url = None
                    
                    def is_specific_stream_m3u8(request_obj: Request):
                        # Ensure this filter is precise based on your F12 observations
                        return (
                            "nice-flower.store" in request_obj.url and
                            "master.m3u8" in request_obj.url and
                            (request_obj.url.endswith(".m3u8") or ".m3u8?" in request_obj.url)
                            # Consider adding: and request_obj.resource_type == "media" for more specificity
                        )

                    try:
                        request_promise = page.wait_for_request(is_specific_stream_m3u8, timeout=40000) # 40s to find the M3U8

                        print("  Reloading page to trigger M3U8 request...")
                        await page.reload(wait_until="networkidle", timeout=60000)
                        await page.wait_for_timeout(2000)

                        m3u8_request = await request_promise
                        target_m3u8_url = m3u8_request.url
                        fresh_urls[channel_name] = target_m3u8_url
                        print(f"  ✅ Captured M3U8 URL for {channel_name}: {target_m3u8_url}")

                    except Exception as e:
                        print(f"  ❌ Failed to capture M3U8 URL for {channel_name} after reload: {e}")
                    
                except Exception as e:
                    print(f"  ❌ Navigation to {stream_page_url} completely failed or timed out: {e}")
                    screenshot_path_fail = f"screenshots/{channel_name.replace(' ', '_')}_navigation_fatal_fail.png"
                    await page.screenshot(path=screenshot_path_fail)
                    print(f"  FATAL navigation failure screenshot: {screenshot_path_fail}")
                    continue

        except Exception as e:
            print(f"❌ An unexpected error occurred during browser automation loop: {e}")
        finally:
            await browser.close()
            print("Browser closed.")

    if not fresh_urls:
        print("🛑 No fresh URLs were obtained. This indicates navigation, interaction, or M3U8 filtering issues.")
    return fresh_urls

async def close_new_page(page: Page):
    """Closes any newly opened pages (often pop-up ads) automatically."""
    print(f"  [AUTO-CLOSE] New page opened: {page.url}. Closing it.")
    try:
        await page.close()
    except Exception as e:
        print(f"  [AUTO-CLOSE ERROR] Could not close new page: {e}")

def update_playlist():
    freshly_fetched_locked_channels = asyncio.run(get_fresh_locked_channel_urls_async())

    if not freshly_fetched_locked_channels:
        print("🛑 No fresh locked channel URLs obtained. Aborting playlist update.")
        return

    try:
        response = requests.get(UPSTREAM_URL, timeout=20)
        response.raise_for_status()
        lines = response.text.splitlines()
        output = []
        i = 0

        while i < len(lines):
            line = lines[i]

            matched_channel_name = None
            for channel_name in freshly_fetched_locked_channels:
                if line.startswith("#EXTINF") and channel_name in line:
                    matched_channel_name = channel_name
                    break

            if matched_channel_name:
                output.append(line)
                i += 1

                while i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                    i += 1
                
                output.extend(FORCED_HEADERS)
                output.append(freshly_fetched_locked_channels[matched_channel_name])

                if i < len(lines) and not lines[i].startswith("#"):
                    i += 1
            else:
                output.append(line)
                i += 1

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output) + "\n")

        print("✅ Playlist updated with locked streams and forced headers.")

    except Exception as e:
        print(f"❌ Error updating playlist: {e}")

if __name__ == "__main__":
    update_playlist()
