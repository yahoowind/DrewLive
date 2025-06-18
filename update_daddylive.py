import requests
import asyncio
from playwright.async_api import async_playwright, Page, Request, Response, ConsoleMessage
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
    "ION USA": "325", "Law & Crime Network": "278", "HFTN": "531",
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
    if not os.path.exists("console_logs"):
        os.makedirs("console_logs")
    if not os.path.exists("network_logs"):
        os.makedirs("network_logs")

    async with async_playwright() as p:
        # Try a different browser if Chromium keeps crashing: p.firefox or p.webkit
        browser = await p.chromium.launch(headless=False, args=['--disable-features=HardwareMediaKeyHandling'])
        context = await browser.new_context()

        # Listen for new pages (e.g., pop-up ads) and close them
        context.on('page', lambda page: asyncio.create_task(close_new_page(page)))
        
        page = await context.new_page()

        # Event listener for page crashes
        page.on('crash', lambda: print(f"⚠️ PAGE CRASHED for {page.url}"))

        # --- Enhanced Console & Network Logging ---
        channel_console_messages = []
        network_requests_log = []

        def on_console_message(msg: ConsoleMessage):
            channel_console_messages.append(f"CONSOLE {msg.type.upper()}: {msg.text}")

        def on_request(request: Request):
            url = request.url
            # Log all requests, not just specific ones, to see everything
            network_requests_log.append(f"REQ: {request.method} {url} (Type: {request.resource_type})")

        def on_response(response: Response):
            url = response.url
            status = response.status
            network_requests_log.append(f"RES: {status} {url}")
            # Log response body for M3U8 if it's not too big
            if ".m3u8" in url and status == 200:
                asyncio.create_task(log_response_body(response, url, network_requests_log))

        async def log_response_body(response: Response, url: str, log_list: list):
            try:
                body = await response.text()
                if len(body) < 1000:
                    log_list.append(f"    BODY for {url}:\n{body[:500]}...")
                else:
                    log_list.append(f"    BODY for {url}: (too large to log)")
            except Exception as e:
                log_list.append(f"    Failed to get body for {url}: {e}")

        page.on('console', on_console_message)
        page.on('request', on_request)
        page.on('response', on_response)
        
        page.set_default_timeout(90000)

        try:
            for channel_name, channel_id in CHANNELS_TO_PROCESS.items():
                channel_console_messages.clear()
                network_requests_log.clear()

                stream_page_url = f"https://thedaddy.click/stream/stream-{channel_id}.php"
                print(f"\n⚡️ Attempting to navigate to: {channel_name} ({stream_page_url})")

                try:
                    await page.goto(stream_page_url, wait_until="domcontentloaded", timeout=60000)
                    print(f"  Successfully navigated to {page.url}")
                    
                    screenshot_path_initial = f"screenshots/{channel_name.replace(' ', '_')}_initial_load.png"
                    await page.screenshot(path=screenshot_path_initial)
                    print(f"  Initial load screenshot taken: {screenshot_path_initial}")

                    # --- PAUSE HERE FOR MANUAL INSPECTION AFTER INITIAL LOAD ---
                    print(f"  Script paused after initial load. Inspect browser (F12). Type 'resume' in terminal to continue.")
                    await page.pause() 
                    
                    await page.wait_for_timeout(3000)

                    if "404" in page.url or "error" in page.url.lower() or "blocked" in page.url.lower():
                        print(f"  ⚠️ Warning: Page navigated to an error/blocked URL: {page.url}")
                        continue

                    possible_click_selectors = [
                        "button.vjs-big-play-button", "button[title='Play']", "a.play-btn",
                        "div.play-button", "div.video-player-overlay button",
                        ".ad-close-button", ".ad-skip-button", "button.skip-ad",
                        "div[id*='ad'] button[id*='close']", "div[id*='popup'] button[id*='close']",
                        "#qc-cmp2-ui button", "#onetrust-accept-btn-handler", "button.cookie-consent-button",
                    ]

                    clicked_something = False
                    for selector in possible_click_selectors:
                        try:
                            locator = page.locator(selector)
                            if await locator.is_visible(timeout=1000):
                                print(f"  Attempting to click: '{selector}'")
                                await locator.click(timeout=5000, force=True)
                                await page.wait_for_timeout(2000)
                                clicked_something = True
                                print(f"  Successfully clicked: '{selector}'")
                                screenshot_path_after_click = f"screenshots/{channel_name.replace(' ', '_')}_after_click_{selector.replace('.', '_').replace('#', '_').replace('[', '_').replace(']', '_')}.png"
                                await page.screenshot(path=screenshot_path_after_click)
                                break
                        except Exception:
                            pass

                    if not clicked_something:
                        print("  No common play button/overlay clicked. Assuming none needed or missed.")
                    
                    # --- PAUSE HERE FOR MANUAL INSPECTION AFTER CLICKS ---
                    print(f"  Script paused after click attempts. Inspect browser (F12). Type 'resume' in terminal to continue.")
                    await page.pause() 

                    await page.wait_for_load_state('networkidle', timeout=30000)
                    print(f"  Page loaded (networkidle) after interactions.")
                    screenshot_path_after_interaction = f"screenshots/{channel_name.replace(' ', '_')}_after_interaction.png"
                    await page.screenshot(path=screenshot_path_after_interaction)
                    print(f"  Screenshot after interaction/idle: {screenshot_path_after_interaction}")

                    target_m3u8_url = None
                    
                    def is_specific_stream_m3u8(request_obj: Request):
                        # Filter for the specific M3U8 you need
                        return (
                            "nice-flower.store" in request_obj.url and
                            "master.m3u8" in request_obj.url and
                            (request_obj.url.endswith(".m3u8") or ".m3u8?" in request_obj.url)
                        )

                    try:
                        # Consider if you need a reload here, or if the M3U8 is already in the network log
                        # If the browser is crashing on reload, remove this block and check the earlier logs.
                        request_promise = page.wait_for_request(is_specific_stream_m3u8, timeout=40000)

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
                    print(f"  ❌ Navigation or initial page processing for {stream_page_url} failed: {e}")
                    print(f"     Error details: {e}") # Print the full exception for better understanding
                    screenshot_path_fatal = f"screenshots/{channel_name.replace(' ', '_')}_fatal_failure.png"
                    try:
                        await page.screenshot(path=screenshot_path_fatal)
                        print(f"  FATAL navigation/processing failure screenshot: {screenshot_path_fatal}")
                    except Exception as ss_e:
                        print(f"  Could not take screenshot on fatal failure: {ss_e}")
                finally:
                    # Make sure logs are saved even if an error occurs
                    console_log_path = f"console_logs/{channel_name.replace(' ', '_')}_console.txt"
                    with open(console_log_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(channel_console_messages))
                    print(f"  Console logs saved to: {console_log_path}")

                    network_log_path = f"network_logs/{channel_name.replace(' ', '_')}_network.txt"
                    with open(network_log_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(network_requests_log))
                    print(f"  Network logs saved to: {network_log_path}")

        except Exception as e:
            print(f"❌ An unexpected error occurred during browser automation loop: {e}")
        finally:
            await browser.close()
            print("Browser closed.")

    if not fresh_urls:
        print("🛑 No fresh URLs were obtained. This indicates persistent issues.")
    return fresh_urls

async def close_new_page(page: Page):
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
