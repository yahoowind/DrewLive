import asyncio
from urllib.parse import unquote, urlparse, parse_qs
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re

TARGET_URL = "https://fstv.us/live-tv.html?timezone=America%2FDenver"

def normalize_channel_name(name: str) -> str:
    # lowercase, strip, collapse spaces for normalization
    return re.sub(r"\s+", " ", name.strip().lower())

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        stream_links = set()
        # stream_map: normalized_name -> {"display_name": original, "urls": set()}
        stream_map = {}

        current_channel_name = None
        found_stream_for_current = False

        async def handle_response(response):
            nonlocal found_stream_for_current
            url = response.url

            if ".m3u8" in url and not found_stream_for_current:
                if "fstv.us/player" in url:
                    # Decode actual .m3u8 link from the `link` param
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query)
                    if "link" in qs:
                        url = unquote(qs["link"][0])
                elif "jwpltx.com" in url or "ping.gif" in url:
                    return  # Skip junk

                found_stream_for_current = True
                if url not in stream_links:
                    stream_links.add(url)
                    name = current_channel_name or "Unknown"
                    norm_name = normalize_channel_name(name)

                    if norm_name not in stream_map:
                        stream_map[norm_name] = {"display_name": name, "urls": set()}
                    stream_map[norm_name]["urls"].add(url)
                    print(f"🎯 {name} -> {url}")

        page.on("response", handle_response)

        print(f"🌐 Navigating to {TARGET_URL}")
        await page.goto(TARGET_URL, timeout=60000)
        await page.wait_for_load_state("networkidle")

        print("🔍 Finding clickable stream elements...")
        elements = await page.query_selector_all("a[href*='player'], div.card, div[class*='channel'], a.card")

        visible_elements = []
        for el in elements:
            try:
                if await el.is_visible():
                    visible_elements.append(el)
            except:
                pass

        print(f"🧩 Found {len(elements)} total elements, {len(visible_elements)} visible")

        for i, el in enumerate(visible_elements):
            default_name = f"Channel_{i + 1}"
            try:
                text = await el.inner_text()
                current_channel_name = " ".join(text.split()).strip() or default_name
            except:
                current_channel_name = default_name

            found_stream_for_current = False

            print(f"\n➡️ Clicking element {i+1}/{len(visible_elements)} - Channel: {current_channel_name}")
            try:
                await el.evaluate("el => el.scrollIntoView({behavior: 'auto', block: 'center'})")
                await el.wait_for_element_state("stable", timeout=5000)

                overlays = await page.query_selector_all("div.overlay, div.modal, div.popup, div[style*='fixed']")
                for overlay in overlays:
                    try:
                        await page.evaluate("(el) => el.style.display = 'none'", overlay)
                    except:
                        pass

                await el.click(timeout=7000, force=True)
                await page.wait_for_timeout(4000)

                if "player?" in page.url:
                    await page.go_back(timeout=10000)
                    await page.wait_for_load_state("networkidle")

            except Exception as e:
                print(f"⚠️ Failed click on {current_channel_name}: {e}")

        with open("FSTV_CLEANED.m3u8", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for data in stream_map.values():
                clean_name = data["display_name"].replace('\n', '').replace('\r', '').strip()
                for url in data["urls"]:
                    f.write(f"#EXTINF:-1,{clean_name}\n{url}\n")

        print(f"\n✅ Done. Collected {len(stream_links)} unique stream links.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())