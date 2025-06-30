from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright
import re

# Directly embedded mapping (corrected and structured)
CHANNEL_MAPPINGS = {
    "usanetwork": {"name": "USA Network", "tv-id": "USA.Network.-.East.Feed.us"},
    "VE-usa-cbssport (sv3)": {"name": "CBS Sports", "tv-id": "CBS.Sports.Network.USA.us"},
    "VE-usa-cbs los angeles": {"name": "CBS Los Angeles", "tv-id": "CBS.(KCBS).Los.Angeles,.CA.us"},
    "VE-usa-CBS GOLAZO CDN SV2": {"name": "CBS Sports Golazo!", "tv-id": "plex.tv.CBS.Sports.Golazo.Network.plex"},
    "VE-us-espn": {"name": "ESPN", "tv-id": "ESPN.us"},
    "VE-us-espn2": {"name": "ESPN2", "tv-id": "ESPN2.us"},
    "VE-usa-espn sec network": {"name": "SEC Network", "tv-id": "SEC.Network.us"},
    "VE-us-espnnews": {"name": "ESPNews", "tv-id": "ESPN.News.us"},
    "VE-cdn - us-uespn": {"name": "ESPNU", "tv-id": "ESPN.U.us"},
    "VE-us-espndeportes": {"name": "ESPN Deportes", "tv-id": "ESPN.Deportes.us"},
    "VE-usa-fs1 (sv2)": {"name": "FS1", "tv-id": "Fox.Sports.1.us"},
    "VE-usa-golf": {"name": "Golf Channel", "tv-id": "Golf.Channel.USA.us"},
    "VE-usa-fs2 (sv2)": {"name": "FS2", "tv-id": "Fox.Sports.2.us"},
    "VE-cdn - us-tennistv": {"name": "Tennis Channel", "tv-id": "The.Tennis.Channel.us"},
    "VE-cdn-us-tennistv2": {"name": "Tennis Channel 2", "tv-id": "The.Tennis.Channel.us"},
    "VE-us-nbc": {"name": "NBC", "tv-id": "NBC.(WNBC).New.York,.NY.us"},
    "VE-usa-cnbc": {"name": "CNBC", "tv-id": "CNBC.USA.us"},
    "VE-USa-UNIVERSO": {"name": "NBC Universo", "tv-id": "NBC.Universo.-.Eastern.feed.us"},
    "VE-us-msnbc": {"name": "MSNBC", "tv-id": "MSNBC.USA.us"},
    "ve-tnt1": {"name": "TNT Sports 1", "tv-id": "TNT.Sports.1.HD.uk"},
    "VE-TNT USA": {"name": "TNT", "tv-id": "TNT.-.Eastern.Feed.us"},
    "ve-fanduel sport": {"name": "FanDuel Sports Network", "tv-id": "FanDuel.Sports.Network.us"},
    "VE-usa-billiard tv": {"name": "Billiard TV", "tv-id": "plex.tv.Billiard.TV.plex"},
    "ve-ori-axstv": {"name": "AXS TV", "tv-id": "AXS.TV.USA.HD.us"},
    "VE-uk-bbcone (sv3)": {"name": "BBC One UK", "tv-id": "BBC.One.EastHD.uk"},
    "VE-uk-bbctwo": {"name": "BBC Two UK", "tv-id": "BBC.Two.HD.uk"},
    "VE-uk-bbcnews": {"name": "BBC News UK", "tv-id": "BBC.NEWS.HD.uk"},
    "VE-fox deportes": {"name": "Fox Deportes", "tv-id": "Fox.Deportes.us"},
    "VE-CA-One soccer": {"name": "OneSoccer Canada", "tv-id": "One.Soccer.ca"},
    "VE-Paramount Network": {"name": "Paramount Network", "tv-id": "Paramount.Network.USA.-.Eastern.Feed.us"},
    "VE-uk-skycinemafamily": {"name": "Sky Cinema Family UK", "tv-id": "Sky.Cinema.Family.HD.at"},
    "VE-zeeuk-skycinemacomedy": {"name": "Sky Cinema Comedy UK", "tv-id": "Sky.Cinema.Comedy.it"},
    "VE-DE - DAZN 1 (sv3)": {"name": "DAZN 1 Germany", "tv-id": "DAZN.1.de"},
    "VE-de-skyde top event": {"name": "Sky DE Top Event", "tv-id": "Sky.Sport.Top.Event.de"},
    "VE-DE - DAZN 2 (sv3)": {"name": "DAZN 2 Germany", "tv-id": "DAZN.2.de"},
    "VE-de-skyde news": {"name": "Sky Sport News DE", "tv-id": "Sky.Sport.News.de"},
    "VE-de-sportdigital (sv3-CDN)": {"name": "SportDigital Germany", "tv-id": "sportdigital.Fussball.de"},
    "VE-de-sky premier league": {"name": "Sky Sport Premier League DE", "tv-id": "Sky.Sport.Premier.League.de"},
    "VE-de-skyde mix": {"name": "Sky Mix DE", "tv-id": "Sky.Sport.Mix.de"},
    "VE-de-bundesliga1 (sv3-CDN)": {"name": "Bundesliga 1 Germany", "tv-id": "Sky.Sport.Bundesliga.1.de"},
    "VE-fox 502": {"name": "Fox Sports 502 AU", "tv-id": "FoxCricket.au"},
    "VE-zent-discovery": {"name": "Discovery Channel", "tv-id": "Discovery.Channel.(US).-.Eastern.Feed.us"},
    "VE-zent-cinemax": {"name": "Cinemax", "tv-id": "Cinemax.-.Eastern.Feed.us"},
    "VE-usa-hbo2": {"name": "HBO 2", "tv-id": "HBO.2.-.Eastern.Feed.us"},
    "VE-zent-hbo": {"name": "HBO", "tv-id": "HBO.-.Eastern.Feed.us"},
    "VE-TBS": {"name": "TBS", "tv-id": "TBS.-.East.us"},
    "VE-PT - Sporttv 1 (sv3)": {"name": "Sport TV1 Portugal", "tv-id": "SPORT.TV1.HD.pt"},
    "VE-GOL TV": {"name": "GOL TV", "tv-id": "Gol.TV.USA.us"},
    "VE-TSN 1": {"name": "TSN 1", "tv-id": "TSN1.ca"},
    "VE-TSN 2": {"name": "TSN 2", "tv-id": "TSN2.ca"},
    "VE-TSN 3": {"name": "TSN 3", "tv-id": "TSN3.ca"},
    "VE-TSN 4": {"name": "TSN 4", "tv-id": "TSN4.ca"},
    "VE-TSN 5": {"name": "TSN 5", "tv-id": "TSN5.ca"}
}

def normalize_channel_name(name: str) -> str:
    return re.sub(r'\s+', ' ', name.strip().lower())

def load_name_mappings():
    normalized_map = {}
    for k, v in CHANNEL_MAPPINGS.items():
        norm_key = re.sub(r'\s+', ' ', k.strip().lower())
        normalized_map[norm_key] = v["name"].strip()
    return normalized_map

async def fetch_fstv_html():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("\U0001f310 Visiting FSTV...")
        await page.goto("https://fstv.us/live-tv.html?timezone=America%2FDenver", timeout=60000)
        await page.wait_for_load_state("networkidle")

        html = await page.content()
        await browser.close()
        return html

def build_playlist_from_html(html, name_map):
    soup = BeautifulSoup(html, "html.parser")
    channels = []

    for div in soup.find_all("div", class_="item-channel"):
        url = div.get("data-link")
        logo = div.get("data-logo")
        name = div.get("title")

        if not (url and name):
            continue

        normalized_name = normalize_channel_name(name)
        new_name = name_map.get(normalized_name, name.strip())

        channels.append({"url": url, "logo": logo, "name": new_name})

    playlist_lines = ['#EXTM3U\n']
    for ch in channels:
        playlist_lines.append(
            f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="FSTV",{ch["name"]}\n'
        )
        playlist_lines.append(ch["url"] + "\n")

    return playlist_lines

async def main():
    name_map = load_name_mappings()
    html = await fetch_fstv_html()
    playlist_lines = build_playlist_from_html(html, name_map)

    with open("FSTV24.m3u8", "w", encoding="utf-8") as f:
        f.writelines(playlist_lines)

    print(f"\u2705 Generated playlist with {len(playlist_lines)//2} channels in FSTV24.m3u8")

if __name__ == "__main__":
    asyncio.run(main())
