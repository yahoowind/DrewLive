import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import datetime
from zoneinfo import ZoneInfo

# Timezones
# We will now assume the website's times are in Mountain Time.
MT = ZoneInfo("America/Denver")

async def get_html_content(url):
    print(f"Launching browser to fetch HTML from: {url}")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_selector("div.schedule-playlist", timeout=15000)
            html_content = await page.content()
            print("Successfully fetched HTML content.")
            return html_content
        except Exception as e:
            print(f"Error fetching page content: {e}")
            return None
        finally:
            await browser.close()

def parse_schedule_to_json(html):
    soup = BeautifulSoup(html, "html.parser")
    schedule_div = soup.find("div", class_="schedule-playlist")
    if not schedule_div:
        print("Schedule container 'div.schedule-playlist' not found.")
        return []

    blocks = schedule_div.find_all("div", class_="block")
    if not blocks:
        print("No schedule blocks 'div.block' found within the container.")
        return []

    schedule = []
    for block in blocks:
        block_name_tag = block.find("span", class_="block-name")
        block_name = block_name_tag.text.strip() if block_name_tag else "Unknown Block"

        start_time_tag = block.find("span", class_="block-start-time")
        start_time_text = start_time_tag.text.strip() if start_time_tag else None

        start_time = None
        if start_time_text:
            try:
                parts = start_time_text.split(": ", 1)
                if len(parts) == 2:
                    start_time = parts[1].strip()
            except Exception:
                pass

        items = block.find_all("li", class_="block-item")
        for item in items:
            time_tag = item.find("span", class_="time")
            name_tag = item.find("span", class_="name")
            episode_tag = item.find("span", class_="episode")

            time_val = time_tag.text.strip() if time_tag else None
            name_val = name_tag.text.strip() if name_tag else None
            episode_val = episode_tag.text.strip() if episode_tag else None

            schedule.append({
                "block": block_name,
                "block_start_time": start_time,
                "start_time": time_val,
                "title": name_val,
                "episode": episode_val,
            })
    return schedule

def parse_time_to_datetime_mt(day_time_str, base_date):
    """
    Parses a time string (e.g., "Sun 9:01 PM") and a base date to create a
    timezone-aware datetime object localized directly to Mountain Time (MT).
    """
    try:
        day_str, time_str = day_time_str.split(" ", 1)
        day_map = {"Sun":6, "Mon":0, "Tue":1, "Wed":2, "Thu":3, "Fri":4, "Sat":5}
        day_offset = day_map.get(day_str, 0)
        time_obj = datetime.datetime.strptime(time_str, "%I:%M %p").time()
        
        dt_naive = datetime.datetime.combine(base_date, time_obj)
        
        current_weekday = dt_naive.weekday()
        if day_offset < current_weekday:
            dt_naive += datetime.timedelta(days=(7 - current_weekday + day_offset))
        else:
            dt_naive += datetime.timedelta(days=(day_offset - current_weekday))

        dt_mt = dt_naive.replace(tzinfo=MT)
        return dt_mt
    except Exception as e:
        print(f"Failed to parse datetime from '{day_time_str}': {e}")
        return None

def format_xmltv_time(dt):
    """
    Formats a datetime object into the XMLTV required format, including timezone offset.
    Example: 20250720190100 -0600
    """
    return dt.strftime("%Y%m%d%H%M%S %z")

def convert_to_xmltv(schedule, base_date):
    program_list = []
    for prog in schedule:
        # We now parse directly into Mountain Time
        dt_mt = parse_time_to_datetime_mt(prog["start_time"], base_date)
        if not dt_mt:
            continue

        program_list.append({
            "start_dt_mt": dt_mt,
            "title": prog["title"] or "Unknown",
            "block": prog["block"],
        })

    program_list.sort(key=lambda x: x["start_dt_mt"])

    xmltv = []
    xmltv.append('<?xml version="1.0" encoding="UTF-8"?>')
    xmltv.append('<!DOCTYPE tv SYSTEM "xmltv.dtd">')
    xmltv.append('<tv generator-info-name="Custom Toonami EPG">')
    xmltv.append('  <channel id="toonami">')
    xmltv.append('    <display-name>Toonami Aftermath East</display-name>')
    xmltv.append('  </channel>')

    for i, prog in enumerate(program_list):
        start_dt = prog["start_dt_mt"]
        if i + 1 < len(program_list):
            stop_dt = program_list[i+1]["start_dt_mt"]
            if stop_dt <= start_dt:
                stop_dt = start_dt + datetime.timedelta(minutes=30)
        else:
            stop_dt = start_dt + datetime.timedelta(minutes=30)

        category = "Movie" if "Movie" in prog["block"] or "Feature" in prog["block"] else "Series"

        xmltv.append(f'  <programme channel="toonami" start="{format_xmltv_time(start_dt)}" stop="{format_xmltv_time(stop_dt)}">')
        xmltv.append(f'    <title lang="en">{prog["title"]}</title>')
        xmltv.append(f'    <category lang="en">{category}</category>')
        xmltv.append('  </programme>')

    xmltv.append('</tv>')
    return "\n".join(xmltv).encode("utf-8")

async def main():
    print("Starting script...")
    schedule_url = "https://www.toonamiaftermath.com/schedule"
    html = await get_html_content(schedule_url)

    if html:
        print("HTML successfully retrieved. Attempting to parse schedule...")
        schedule_json = parse_schedule_to_json(html)
        print(f"Parsed {len(schedule_json)} schedule items.")

        if not schedule_json:
            print("No schedule data parsed. XML file will be empty.")
            xmltv_data = convert_to_xmltv(schedule_json, datetime.date.today())
        else:
            today = datetime.date.today()
            days_since_sunday = (today.weekday() + 1) % 7
            base_date = today - datetime.timedelta(days=days_since_sunday)
            print(f"Using dynamic base date for schedule calculations: {base_date}")
            xmltv_data = convert_to_xmltv(schedule_json, base_date)

        with open("toonami24-epg.xml", "wb") as f:
            f.write(xmltv_data)

        print("Saved XMLTV schedule to toonami24-epg.xml")
    else:
        print("Failed to retrieve HTML content. XMLTV file not generated.")

if __name__ == "__main__":
    asyncio.run(main())
