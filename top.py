import requests
import json
import asyncio
import re
from playwright.async_api import async_playwright
from tqdm.asyncio import tqdm

CONCURRENT_WORKERS = 4 

async def get_m3u8_from_page(context, url):
    """
    Asynchronously processes a single URL to find an M3U8 link.
    """
    m3u8_future = asyncio.Future()

    async def handle_request(request):
        if ".m3u8" in request.url and not m3u8_future.done():
            m3u8_future.set_result(request.url)

    page = await context.new_page()
    page.on("request", handle_request)
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        try:
            await page.locator('.vjs-big-play-button').first.click(timeout=3000)
        except Exception:
            pass 

        m3u8_link = await asyncio.wait_for(m3u8_future, timeout=7)
        return m3u8_link
    except Exception:
        return None
    finally:
        await page.close()

async def main():
    api_url = "https://topembed.pw/api.php?format=json"
    playlist_filename = "topembed_playlist.m3u8"
    
    print(f"📡 Fetching channel list from API: {api_url}")
    try:
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        api_data = response.json()
        
        urls_to_process = []
        unique_urls = set()
        events_by_date = api_data.get("events", {})
        for daily_events in events_by_date.values():
            for event in daily_events:
                match_name = event.get("match", "Unknown Match")
                sport_group = event.get("sport", "General")
                for channel_url in event.get("channels", []):
                    if isinstance(channel_url, str) and channel_url not in unique_urls:
                        unique_urls.add(channel_url)
                        channel_id = channel_url.split('/channel/')[1] if '/channel/' in channel_url else channel_url
                        
                        urls_to_process.append({
                            'url': channel_url.strip(),
                            'sport': sport_group,
                            'match_name': match_name, 
                            'channel_id': channel_id 
                        })
        
        if not urls_to_process:
            print("❌ No channel URLs found.")
            return
            
        print(f"✅ Found {len(urls_to_process)} unique channel streams to process.")

    except Exception as e:
        print(f"❌ ERROR: Could not get data from the API. Error: {e}")
        return

    async with async_playwright() as p:
        print(f"\n🚀 Launching browser with a limit of {CONCURRENT_WORKERS} parallel workers...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            extra_http_headers={"Referer": "https://topembed.pw/"}
        )
        await context.route(re.compile(r"\.(jpg|jpeg|png|gif|css|woff|woff2)$"), lambda route: route.abort())

        semaphore = asyncio.Semaphore(CONCURRENT_WORKERS)
        
        async def process_with_semaphore(item):
            async with semaphore:
                link = await get_m3u8_from_page(context, item['url'])
                return item, link

        tasks = [process_with_semaphore(item) for item in urls_to_process]
        
        playlist_content = "#EXTM3U\n"
        stream_count = 0
        
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Scraping M3U8 Links"):
            item, m3u8_link = await future
            
            log_name = f"{item['match_name']} ({item['channel_id']})"
            
            if m3u8_link:
                tqdm.write(f"  ✅ Success: {log_name}")
                
                playlist_content += f'#EXTINF:-1 group-title="{item["sport"]}" tvg-name="{item["channel_id"]}",{log_name}\n'
                playlist_content += f'#EXTVLCOPT:http-origin=https://jxoxkplay.xyz\n'
                playlist_content += f'#EXTVLCOPT:http-referer=https://jxoxkplay.xyz/\n'
                playlist_content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0\n'
                playlist_content += f'{m3u8_link}\n\n'
                stream_count += 1
            else:
                tqdm.write(f"  ❌ Failed:  {log_name}")

        await browser.close()

    if stream_count > 0:
        with open(playlist_filename, 'w', encoding='utf-8') as f:
            f.write(playlist_content)
        print(f"\n🎉 Finished! Playlist with {stream_count} streams saved to '{playlist_filename}'")
    else:
        print("\nCould not find any playable M3U8 streams.")

if __name__ == "__main__":
    asyncio.run(main())
