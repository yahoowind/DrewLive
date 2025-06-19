import asyncio
from playwright.async_api import async_playwright, Request
import random
import re

INPUT_FILE = "DaddyLive.m3u8"
OUTPUT_FILE = "DaddyLive.m3u8"

CHANNELS_TO_PROCESS = {
"ABC USA": "51", "A&E USA": "302", "AMC USA": "303", "Animal Planet": "304", "ACC Network USA": "664", "Astro SuperSport 1": "123", "Astro SuperSport 2": "124", "Astro SuperSport 3": "125", "Astro SuperSport 4": "126", "Arena Sport 1 Premium": "134", "Arena Sport 2 Premium": "135", "Arena Sport 3 Premium": "139", "Arena Sport 1 Serbia": "429", "Arena Sport 2 Serbia": "430", "Arena Sport 3 Serbia": "431", "Arena Sport 4 Serbia": "581", "Arena Sport 1 Croatia": "432", "Arena Sport 2 Croatia": "433", "Arena Sport 3 Croatia": "434", "Arena Sport 4 Croatia": "580", "Alkass One": "781", "Alkass Two": "782", "Alkass Three": "783", "Alkass Four": "784", "ABS-CBN": "785", "Arena Sport 1 BiH": "579", "Abu Dhabi Sports 1 UAE": "600", "Abu Dhabi Sports 2 UAE": "601", "Abu Dhabi Sports 1 Premium": "609", "Abu Dhabi Sports 2 Premium": "610", "Astro Cricket": "370", "Antena 3 Spain": "531", "Adult Swim": "295", "AXN Movies Portugal": "717", "Arte DE": "725", "AXS TV USA": "742", "ABCNY USA": "766", "beIN Sports MENA English 1": "61", "beIN Sports MENA English 2": "90", "beIN Sports MENA English 3": "46", "beIN Sports MENA 1": "91", "beIN Sports MENA 2": "92", "beIN Sports MENA 3": "93", "beIN Sports MENA 4": "94", "beIN Sports MENA 5": "95", "beIN Sports MENA 6": "96", "beIN Sports MENA 7": "97", "beIN Sports MENA Premium 1": "98", "beIN Sports MENA Premium 2": "99", "beIN Sports MENA Premium 3": "100", "beIN Sports MAX 4 France": "494", "beIN Sports MAX 5 France": "495", "beIN Sports MAX 6 France": "496", "beIN Sports MAX 7 France": "497", "beIN Sports MAX 8 France": "498", "beIN Sports MAX 9 France": "499", "beIN Sports MAX 10 France": "500", "beIN SPORTS 1 France": "116", "beIN SPORTS 2 France": "117", "beIN SPORTS 3 France": "118", "beIN SPORTS 1 Turkey": "62", "beIN SPORTS 2 Turkey": "63", "beIN SPORTS 3 Turkey": "64", "beIN SPORTS 4 Turkey": "67", "BeIN Sports HD Qatar": "578", "BeIN SPORTS USA": "425", "beIN SPORTS en Espa単ol": "372", "beIN SPORTS Australia 1": "491", "beIN SPORTS Australia 2": "492", "beIN SPORTS Australia 3": "493", "Barca TV Spain": "522", "Benfica TV PT": "380", "Boomerang": "648", "BNT 1 Bulgaria": "476", "BNT 2 Bulgaria": "477", "BNT 3 Bulgaria": "478", "BR Fernsehen DE": "737", "bTV Bulgaria": "479", "bTV Action Bulgaria": "481", "bTV Lady Bulgaria": "484", "BBC America (BBCA)": "305", "BET USA": "306", "Bravo USA": "307", "BBC News Channel HD": "349", "BBC One UK": "356", "BBC Two UK": "357", "BBC Three UK": "358", "BBC Four UK": "359", "BIG TEN Network (BTN USA)": "397", "Cuatro Spain": "535", "Channel 4 UK": "354", "Channel 5 UK": "355", "CBS Sports Network (CBSSN)": "308", "Canal+ France": "121", "Canal+ Sport France": "122", "Canal+ Foot France": "463", "Canal+ Sport360": "464", "Canal 11 Portugal": "540", "Canal+ Sport Poland": "48", "Canal+ Sport 2 Poland": "73", "CANAL+ SPORT 5 Poland": "75", "Canal+ Premium Poland": "566", "Canal+ Family Poland": "567", "Canal+ Seriale Poland": "570", "Canal+ Sport 1 Afrique": "486", "Canal+ Sport 2 Afrique": "487", "Canal+ Sport 3 Afrique": "488", "Canal+ Sport 4 Afrique": "489", "Canal+ Sport 5 Afrique": "490", "CANAL9 Denmark": "805", "Combate Brasil": "89", "C More Football Sweden": "747", "Cosmote Sport 1 HD": "622", "Cosmote Sport 2 HD": "623", "Cosmote Sport 3 HD": "624", "Cosmote Sport 4 HD": "625", "Cosmote Sport 5 HD": "626", "Cosmote Sport 6 HD": "627", "Cosmote Sport 7 HD": "628", "Cosmote Sport 8 HD": "629", "Cosmote Sport 9 HD": "630", "Channel 9 Israel": "546", "Channel 10 Israe": "547", "Channel 11 Israel": "548", "Channel 12 Israel": "549", "Channel 13 Israel": "551", "Channel 14 Israel": "552", "C More Stars Sweden": "8111", "C More First Sweden": "812", "C More Hits Sweden": "813", "C More Series Sweden": "814", "COZI TV USA": "748", "CMT USA": "647", "CBS USA": "52", "CW USA": "300", "CNBC USA": "309", "Comedy Central": "310", "Cartoon Network": "339", "CNN USA": "345", "Cinemax USA": "374", "CTV Canada": "602", "CTV 2 Canada": "838", "Crime+ Investigation USA": "669", "Comet USA": "696", "Cooking Channel USA": "697", "Cleo TV": "715", "C SPAN 1": "750", "CBSNY USA": "767", "Citytv": "831", "CBC CA": "699", "DAZN 1 Bar DE": "426", "DAZN 2 Bar DE": "427", "DAZN 1 Spain": "445", "DAZN 2 Spain": "446", "DAZN 3 Spain": "447", "DAZN 4 Spain": "448", "DAZN F1 ES": "537", "DAZN LaLiga": "538", "DAZN LaLiga 2": "43", "DR1 Denmark": "801", "DR2 Denmark": "802", "Digi Sport 1 Romania": "400", "Digi Sport 2 Romania": "401", "Digi Sport 3 Romania": "402", "Digi Sport 4 Romania": "403", "Diema Sport Bulgaria": "465", "Diema Sport 2 Bulgaria": "466", "Diema Sport 3 Bulgaria": "467", "Diema Bulgaria": "482", "Diema Family Bulgaria": "485", "Dubai Sports 1 UAE": "604", "Dubai Sports 2 UAE": "605", "Dubai Sports 3 UAE": "606", "Dubai Racing 1 UAE": "607", "Dubai Racing 2 UAE": "608", "DSTV Mzansi Magic": "786", "DSTV M-Net": "827", "DSTV kykNET & kie": "828", "Discovery Life Channel": "311", "Disney Channel": "312", "Discovery Channel": "313", "Discovery Family": "657", "Disney XD": "314", "Destination America": "651", "Disney JR": "652", "Dave": "348", "ESPN USA": "44", "ESPN2 USA": "45", "ESPNU USA": "316", "ESPN 1 NL": "379", "ESPN 2 NL": "386", "Eleven Sports 1 Poland": "71", "Eleven Sports 2 Poland": "72", "Eleven Sports 3 Poland": "428", "Eleven Sports 1 Portugal": "455", "Eleven Sports 2 Portugal": "456", "Eleven Sports 3 Portugal": "457", "Eleven Sports 4 Portugal": "458", "Eleven Sports 5 Portugal": "459", "EuroSport 1 UK": "41", "EuroSport 2 UK": "42", "EuroSport 1 Poland": "57", "EuroSport 2 Poland": "58", "EuroSport 1 Spain": "524", "EuroSport 2 Spain": "525", "EuroSport 1 Italy": "878", "EuroSport 2 Italy": "879", "Eurosport 1 Bulgaria": "469", "Eurosport 2 Bulgaria": "470", "ESPN Premium Argentina": "387", "ESPN Brasil": "81", "ESPN2 Brasil": "82", "ESPN3 Brasil": "83", "ESPN4 Brasil": "85", "ESPN SUR": "149", "ESPN2 SUR": "150", "ESPN Deportes": "375", "ESPNews": "288", "E! Entertainment Television": "315", "E4 Channel": "363", "Fox Sports 1 USA": "39", "Fox Sports 2 USA": "758", "FOX Soccer Plus": "756", "Fox Cricket": "369", "FOX Deportes USA": "643", "FOX Sports 502 AU": "820", "FOX Sports 503 AU": "821", "FOX Sports 504 AU": "822", "FOX Sports 505 AU": "823", "FOX Sports 506 AU": "824", "FOX Sports 507 AU": "825", "Fox Sports Argentina": "767", "Fox Sports 2 Argentina": "788", "Fox Sports 3 Argentina": "789", "Fox Sports Premium MX": "830", "FilmBox Premium Poland": "568", "Fight Network": "757", "Fox Business": "297", "FOX HD Bulgaria": "483", "FOX USA": "54", "FX USA": "317", "FXX USA": "298", "Freeform": "301", "Fox News": "347", "FX Movie Channel": "381", "FYI": "665", "Film4 UK": "688", "Fashion TV": "744", "FETV - Family Entertainment Television": "751", "FOXNY USA": "768", "Fox Weather Channel": "775", "GOL PLAY Spain": "530", "GOLF Channel USA": "318", "Game Show Network": "319", "Gol Mundial 1": "292", "Gold UK": "687", "Galavisi贸n USA": "743", "Grit Channel": "752", "Globo SP": "760", "Globo RIO": "761", "Global CA": "836", "The Hallmark Channel": "320", "Hallmark Movies & Mysterie": "296", "HBO USA": "321", "HBO2 USA": "689", "HBO Comedy USA": "690", "HBO Family USA": "691", "HBO Latino USA": "692", "HBO Signature USA": "693", "HBO Zone USA": "694", "HBO Poland": "569", "History USA": "322", "Headline News": "323", "HGTV": "382", "HOT3 Israel": "553", "HR Fernsehen DE": "740", "ITV 1 UK": "350", "ITV 2 UK": "351", "ITV 3 UK": "352", "ITV 4 UK": "353", "Italia 1 Italy": "854", "Investigation Discovery (ID USA)": "324", "ION USA": "325", "IFC TV USA": "656", "Kanal 4 Denmark": "803", "Kanal 5 Denmark": "804", "Kabel Eins (Kabel 1) DE": "731", "LaLiga SmartBank TV": "539", "L'Equipe France": "645", "La Sexta Spain": "534", "Liverpool TV (LFC TV)": "826", "Lifetime Network": "326", "Lifetime Movies Network": "389", "Longhorn Network USA": "667", "La7 Italy": "855", "LA7d HD+ Italy": "856", "Match Football 1 Russia": "136", "Match Football 2 Russia": "137", "Match Football 3 Russia": "138", "Match Premier Russia": "573", "Match TV Russia": "127", "МАТЧ! БОЕЦ Russia": "395", "Movistar Laliga": "84", "Movistar Liga de Campeones": "435", "Movistar Deportes Spain": "436", "Movistar Deportes 2 Spain": "438", "Movistar Deportes 3 Spain": "526", "Movistar Deportes 4 Spain": "527", "Movistar Golf Spain": "528", "Motowizja Poland": "563", "MSG USA": "765", "MSNBC": "327", "Magnolia Network": "299", "MTV UK": "367", "MTV USA": "371", "MUTV UK": "377", "MAVTV USA": "646", "Max Sport 1 Croatia": "779", "Max Sport 2 Croatia": "780", "Marquee Sports Network": "770", "Max Sport 1 Bulgaria": "472", "Max Sport 2 Bulgaria": "473", "Max Sport 3 Bulgaria": "474", "Max Sport 4 Bulgaria": "475", "MLB Network USA": "399", "MASN USA": "829", "MY9TV USA": "654", "Motor Trend": "661", "METV USA": "662", "MDR DE": "733", "Mundotoro TV Spain": "749", "MTV Denmark": "806", "NHL Network USA": "663", "Nova Sport Bulgaria": "468", "Nova Sport Serbia": "582", "Nova Sports 1 Greece": "631", "Nova Sports 2 Greece": "632", "Nova Sports 3 Greece": "633", "Nova Sports 4 Greece": "634", "Nova Sports 5 Greece": "635", "Nova Sports 6 Greece": "636", "Nova Sports Premier League Greece": "599", "Nova Sports Start Greece": "637", "Nova Sports Prime Greece": "638", "Nova Sports News Greece": "639", "NESN USA": "762", "NBC USA": "53", "NBA TV USA": "404", "NBC Sports Chicago": "776", "NBC Sports Philadelphia": "777", "NBC Sports Washington": "778", "NFL Network": "405", "NBC Sports Bay Area": "753", "NBC Sports Boston": "754", "NBC Sports California": "755", "NBCNY USA": "769", "Nova TV Bulgaria": "480", "National Geographic (NGC)": "328", "NICK JR": "329", "NICK": "330", "Nick Music": "666", "Nicktoons": "649", "NDR DE": "736", "NewsNation USA": "292", "Newsmax USA": "613", "Nat Geo Wild USA": "745", "Noovo CA": "835", "New! CWPIX 11": "771", "OnTime Sports": "611", "OnTime Sports 2": "612", "ONE 1 HD Israel": "541", "ONE 2 HD Israel": "542", "Orange Sport 1 Romania": "439", "Orange Sport 2 Romania": "440", "Orange Sport 3 Romania": "441", "Orange Sport 4 Romania": "442", "Oprah Winfrey Network (OWN)": "331", "Oxygen True Crime": "332", "Polsat Poland": "562", "Polsat Sport Poland": "47", "Polsat Sport Extra Poland": "50", "Polsat Sport News Poland": "129", "Polsat News Poland": "443", "Polsat Film Poland": "564", "Porto Canal Portugal": "718", "ProSieben (PRO7) DE": "730", "PTV Sports": "450", "Premier Brasil": "88", "Prima Sport 1": "583", "Prima Sport 2": "584", "Prima Sport 3": "585", "Prima Sport 4": "586", "Paramount Network": "334", "POP TV USA": "653", "RTE 1": "364", "RTE 2": "365", "RMC Sport 1 France": "119", "RMC Sport 2 France": "120", "RTP 1 Portugal": "719", "RTP 2 Portugal": "720", "RTP 3 Portugal": "721", "Rai 1 Italy": "850", "Rai 2 Italy": "851", "Rai 3 Italy": "853", "Rai Sport Italy": "882", "Rai Premium Italy": "858", "Real Madrid TV Spain": "523", "RDS CA": "839", "RDS 2 CA": "840", "RDS Info CA": "841", "Ring Bulgaria": "471", "RTL7 Netherland": "390", "Racing Tv UK": "555", "Reelz Channel": "293", "Sky Sports Football UK": "35", "Sky Sports Arena UK": "36", "Sky Sports Action UK": "37", "Sky Sports Main Event": "38", "Sky sports Premier League": "130", "Sky Sports F1 UK": "60", "Sky Sports Cricket": "65", "Sky Sports Golf UK": "70", "Sky Sports Golf Italy": "574", "Sky Sport MotoGP Italy": "575", "Sky Sport Tennis Italy": "576", "Sky Sport F1 Italy": "577", "Sky Sports News UK": "366", "Sky Sports MIX UK": "449", "Sky Sport Top Event DE": "556", "Sky Sport Mix DE": "557", "Sky Sport Bundesliga 1 HD": "558", "Sky Sport Austria 1 HD": "559", "SportsNet New York (SNY)": "759", "Sky Sport Football Italy": "460", "Sky Sport UNO Italy": "461", "Sky Sport Arena Italy": "462", "Sky Sports Racing UK": "554", "Sky UNO Italy": "881", "Sky Sport 1 NZ": "588", "Sky Sport 2 NZ": "589", "Sky Sport 3 NZ": "590", "Sky Sport 4 NZ": "591", "Sky Sport 5 NZ": "592", "Sky Sport 6 NZ": "593", "Sky Sport 7 NZ": "594", "Sky Sport 8 NZ": "595", "Sky Sport 9 NZ": "596", "Sky Sport Select NZ": "587", "Sport TV1 Portugal": "49", "Sport TV2 Portugal": "74", "Sport TV4 Portugal": "289", "Sport TV3 Portugal": "454", "Sport TV5 Portugal": "290", "Sport TV6 Portugal": "291", "SIC Portugal": "722", "SEC Network USA": "385", "SporTV Brasil": "78", "SporTV2 Brasil": "79", "SporTV3 Brasil": "80", "Sport Klub 1 Serbia": "101", "Sport Klub 2 Serbia": "102", "Sport Klub 3 Serbia": "103", "Sport Klub 4 Serbia": "104", "Sport Klub HD Serbia": "453", "Sportsnet Ontario": "406", "Sportsnet One": "411", "Sportsnet West": "407", "Sportsnet East": "408", "Sportsnet 360": "409", "Sportsnet World": "410", "SuperSport Grandstand": "412", "SuperSport PSL": "413", "SuperSport Premier league": "414", "SuperSport LaLiga": "415", "SuperSport Variety 1": "416", "SuperSport Variety 2": "417", "SuperSport Variety 3": "418", "SuperSport Variety 4": "419", "SuperSport Action": "420", "SuperSport Rugby": "421", "SuperSport Golf": "422", "SuperSport Tennis": "423", "SuperSport Motorsport": "424", "Supersport Football": "56", "SuperSport Cricket": "368", "SuperSport MaXimo 1": "572", "Sporting TV Portugal": "716", "SportDigital Fussball": "571", "Spectrum Sportsnet LA": "764", "Sport1+ Germany": "640", "Sport1 Germany": "641", "S4C UK": "670", "SAT.1 DE": "729", "Sky Cinema Premiere UK": "671", "Sky Cinema Select UK": "672", "Sky Cinema Hits UK": "673", "Sky Cinema Greats UK": "674", "Sky Cinema Animation UK": "675", "Sky Cinema Family UK": "676", "Sky Cinema Action UK": "677", "The Hallmark": "680", "Sky Cinema Thriller UK": "679", "Sky Cinema Sci-Fi Horror UK": "681", "Sky Cinema Collection Italy": "859", "Sky Cinema Uno Italy": "860", "Sky Cinema Action Italy": "861", "8Sky Cinema Comedy Italy": "862", "Sky Cinema Uno +24 Italy": "863", "Sky Cinema Romance Italy": "864", "Sky Cinema Family Italy": "865", "Sky Cinema Due +24 Italy": "866", "Sky Cinema Drama Italy": "867", "8Sky Cinema Suspense Italy": "868", "Sky Sport 24 Italy": "869", "Sky Sport Calcio Italy": "870", "Sky Calcio 1 (251) Italy": "871", "Sky Calcio 2 (252) Italy": "872", "Sky Calcio 3 (253) Italy": "873", "Sky Calcio 4 (254) Italy": "874", "Sky Calcio 5 (255) Italy": "875", "Sky Calcio 6 (256) Italy": "876", "Sky Calcio 7 (257) Italy": "877", "Sky Serie Italy": "880", "StarzPlay CricLife 1 HD": "284", "StarzPlay CricLife 2 HD": "283", "StarzPlay CricLife 3 HD": "282", "Sky Showcase UK": "682", "Sky Arts UK": "683", "Sky Comedy UK": "684", "Sky Crime": "685", "Sky History": "686", "SSC Sport 1": "614", "SSC Sport 2": "615", "SSC Sport 3": "616", "SSC Sport 4": "617", "SSC Sport 5": "618", "SSC Sport Extra 1": "619", "SSC Sport Extra 2": "620", "SSC Sport Extra 3": "621", "Sport 1 Israel": "140", "Sport 2 Israel": "141", "Sport 3 Israel": "142", "Sport 4 Israel": "143", "Sport 5 Israel": "144", "Sport 5 PLUS Israel": "145", "Sport 5 Live Israel": "146", "Sport 5 Star Israel": "147", "Sport 5 Gold Israel": "148", "Science Channel": "294", "Showtime USA": "333", "Showtime SHOxBET USA": "685", "Starz": "335", "Sky Witness HD": "361", "Sixx DE": "732", "Sky Atlantic": "362", "SYFY USA": "373", "Sundance TV": "658", "SWR DE": "735", "SUPER RTL DE": "738", "SR Fernsehen DE": "739", "Smithsonian Channel": "603", "TNT Sports 1 UK": "31", "TNT Sports 2 UK": "32", "TNT Sports 3 UK": "33", "TNT Sports 4 UK": "34", "TSN1": "111", "TSN2": "112", "TSN3": "113", "TSN4": "114", "TSN5": "115", "TVN HD Poland": "565", "TVN24 Poland": "444", "TVP1 Poland": "560", "TVP2 Poland": "561", "Telecinco Spain": "532", "TVE La 1 Spain": "533", "TVE La 2 Spain": "536", "TVI Portugal": "723", "TVI Reality Portugal": "724", "Teledeporte Spain (TDP)": "529", "TYC Sports Argentina": "746", "TVP Sport Poland": "128", "TNT Brasil": "87", "TNT Sports Argentina": "388", "TNT Sports HD Chile": "642", "Tennis Channel": "40", "Ten Sports PK": "741", "TUDN USA": "66", "Telemundo": "131", "TBS USA": "336", "TLC": "337", "TNT USA": "338", "TVA Sports": "833", "TVA Sports 2": "834", "Travel Channel": "340", "TruTV USA": "341", "TVLAND": "342", "TCM USA": "644", "TMC Channel USA": "698", "The Food Network": "384", "The Weather Channel": "394", "TVP INFO": "452", "TeenNick": "650", "TV ONE USA": "660", "TV2 Bornholm Denmark": "807", "TV2 Sport X Denmark": "808", "TV3 Sport Denmark": "809", "TV2 Sport Denmark": "810", "TV2 Denmark": "817", "TV2 Zulu": "818", "TV3+ Denmark": "819", "TVO CA": "842", "Tennis+ 1": "700", "Tennis+ 2": "701", "Tennis+ 3": "702", "Tennis+ 4": "703", "Tennis+ 5": "704", "Tennis+ 6": "705", "Tennis+ 7": "706", "Tennis+ 8": "707", "Tennis+ 9": "708", "Tennis+ 10": "709", "Tennis+ 11": "710", "Tennis+ 12": "711", "Tennis+ 13": "712", "Tennis+ 14": "713", "Tennis+ 15": "714", "USA Network": "343", "Universal Kids USA": "668", "Univision": "132", "Unimas": "133", "Viaplay Sports 1 UK": "451", "Viaplay Sports 2 UK": "550", "Viaplay Xtra UK": "597", "#Vamos Spain": "521", "V Film Premiere": "815", "V Film Family": "816", "VH1 USA": "344", "Veronica NL Netherland": "378", "VTV+ Uruguay": "391", "VICE TV": "659", "Willow Cricket": "346", "Willow XTRA": "598", "WWE Network": "376", "Win Sports+ Columbia": "392", "WETV USA": "655", "WDR DE": "734", "YES Network USA": "763", "Yes Movies Action Israel": "543", "Yes Movies Kids Israel": "544", "Yes Movies Comedy Israel": "545", "Yas TV UAE": "609", "Yes TV CA": "837", "Ziggo Sport Docu NL": "383", "Ziggo Sport Select NL": "393", "Ziggo Sport Racing NL": "396", "Ziggo Sport Voetbal NL": "398", "BBC 1 DE": "727", "ZDF Info DE": "728", "20 Mediaset Italy": "857", "6'eren Denmark": "800", "#0 Spain": "437", "5 USA": "360", "3sat DE": "726", "18+ (Player-01)": "501", "18+ (Player-02)": "502", "18+ (Player-03)": "503", "18+ (Player-04)": "504", "18+ (Player-05)": "505", "18+ (Player-06)": "506", "18+ (Player-07)": "507", "18+ (Player-08)": "508", "18+ (Player-09)": "509", "18+ (Player-10)": "510", "18+ (Player-11)": "511", "18+ (Player-12)": "512", "18+ (Player-13)": "513", "18+ (Player-14)": "514", "18+ (Player-15)": "515", "18+ (Player-16)": "516", "18+ (Player-17)": "517", "18+ (Player-18)": "518", "18+ (Player-19)": "519", "18+ (Player-20)": "520", "Altitude Sports": "923", "Azteca 7 MX": "844", "A Sport PK": "269", "beIN Sports MENA 8": "98", "beIN Sports MENA 9": "99", "beIN SPORTS XTRA 1": "100", "beIN SPORTS XTRA 2": "43", "beIN SPORTS en Español": "372", "Bally Sports Arizona": "890", "Bally Sports Detroit": "891", "Bally Sports Florida": "892", "Bally Sports Great Lakes": "893", "Bally Sports Indiana": "894", "Bally Sports Kansas City": "895", "Bally Sports Midwest": "896", "Bally Sports New Orleans": "897", "Bally Sports North": "898", "Bally Sports Ohio": "899", "Bally Sports Oklahoma": "900", "Bally Sports San Diego": "901", "Bally Sports SoCal": "902", "Bally Sports South": "903", "Bally Sports Southeast": "904", "Bally Sports Sun": "905", "Bally Sports West": "906", "Bally Sports Wisconsin": "907", "Bandsports Brasil": "275", "CANAL+ MotoGP France": "271", "Canal+ Formula 1": "273", "CW PIX 11 USA": "280", "CBS Sports Golazo": "910", "CMTV Portugal": "790", "Cytavision Sports 1 Cyprus": "911", "Cytavision Sports 2 Cyprus": "912", "Cytavision Sports 3 Cyprus": "913", "Cytavision Sports 4 Cyprus": "914", "Cytavision Sports 5 Cyprus": "915", "Cytavision Sports 6 Cyprus": "916", "Cytavision Sports 7 Cyprus": "917", "Court TV USA": "281", "DAZN 1 UK": "230", "Discovery Velocity CA": "285", "ERT 1 Greece": "774", "Eurosport 1 France": "772", "Eurosport 2 France": "773", "ESPN Extra Argentina": "798", "FUSE TV USA": "279", "Galavisión USA": "743", "LaLigaTV UK": "276", "LALIGA TV Hypermotion": "539", "Law & Crime Network": "278", "Monumental Sports Network": "924", "M6 France": "470", "MGM+ USA / Epix": "791", "Movistar Supercopa de Espa�a": "437", "NBC10 Philadelphia": "277", "Premier Sports Ireland 1": "771", "Premier Sports Ireland 2": "799", "Prima TV RO": "843", "Pac-12 Network USA": "287", "PBS USA USA": "210", "PDC TV": "43", "Rally Tv": "607", "RTL DE": "740", "Root Sports Northwest": "920", "Sky Sports F1 DE": "274", "Sky Sports Tennis UK": "46", "Sky Sports Tennis DE": "884", "SBS6 NL": "883", "SEE Denmark": "811", "Star Sports 1 IN": "267", "Star Sports Hindi IN": "268", "Sky Cinema Comedy UK": "678", "Sky Cinema Drama UK": "680", "Showtime 2 USA (SHO2) USA": "792", "Showtime Showcase USA": "793", "Showtime Extreme USA": "794", "Showtime Family Zone (SHO Family Zone) USA": "795", "Showtime Next (SHO Next) USA": "796", "Showtime Women USA": "797", "Space City Home Network": "921", "SportsNet Pittsburgh": "922", "TF1 France": "469", "TV3 Max Denmark": "223", "T Sports BD": "270", "Vodafone Sport": "260", "V Sport Motor Sweden": "272", "YTV CA": "296",
}

VLC_OPT_LINES = [
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0'
]

def parse_m3u_playlist(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    entries = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTM3U"):
            entries.append({"meta": '#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"', "headers": [], "url": None})
            i += 1
        elif line.startswith("#EXTINF:"):
            meta = line
            headers = []
            i += 1
            while i < len(lines) and lines[i].startswith("#EXTVLCOPT"):
                headers.append(lines[i])
                i += 1
            url = lines[i] if i < len(lines) else ""
            entries.append({"meta": meta, "headers": headers, "url": url})
            i += 1
        else:
            i += 1
    return entries

def extract_channel_name(meta_line):
    match = re.search(r",(.+)$", meta_line)
    return match.group(1).strip() if match else None

async def fetch_updated_urls():
    urls = {}
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for name, cid in CHANNELS_TO_PROCESS.items():
            stream_urls = []

            def capture_m3u8(request: Request):
                if ".m3u8" in request.url.lower():
                    print(f"🔍 Found stream for {name}: {request.url}")
                    stream_urls.append(request.url)

            page.on("request", capture_m3u8)

            try:
                print(f"\n🔄 Scraping {name}...")
                await page.goto(f"https://thedaddy.click/stream/stream-{cid}.php", timeout=60000)
                tries = 0
                while not stream_urls and tries < 3:
                    await asyncio.sleep(5)
                    tries += 1
                    print(f"⏳ Waiting for {name}... ({tries})")
            except Exception as e:
                print(f"❌ Failed for {name}: {e}")

            page.remove_listener("request", capture_m3u8)

            if stream_urls:
                urls[name] = random.choice(stream_urls)
                print(f"✅ Final stream for {name}")
            else:
                print(f"⚠️ No streams found for {name}")

        await browser.close()
    return urls

def update_playlist(entries, new_urls):
    updated_entries = []

    for entry in entries:
        if entry["meta"].startswith("#EXTM3U"):
            updated_entries.append(entry)
            continue

        name = extract_channel_name(entry["meta"])

        # Always apply or append the VLC headers
        existing_headers = entry.get("headers", [])
        combined_headers = existing_headers[:]
        for vlc_line in VLC_OPT_LINES:
            if vlc_line not in combined_headers:
                combined_headers.append(vlc_line)

        updated_entries.append({
            "meta": entry["meta"],
            "headers": combined_headers,
            "url": new_urls.get(name, entry["url"])  # Use updated URL if available
        })

    return updated_entries

def save_playlist(entries, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for entry in entries:
            if entry["meta"]:
                f.write(entry["meta"] + "\n")
            if "headers" in entry:
                for h in entry["headers"]:
                    f.write(h + "\n")
            if entry["url"]:
                f.write(entry["url"] + "\n")
    print(f"\n✅ Saved updated playlist to {filepath}")

async def main():
    print("📥 Loading playlist...")
    entries = parse_m3u_playlist(INPUT_FILE)

    print("\n🌐 Scraping updated stream URLs...")
    new_urls = await fetch_updated_urls()

    print("\n🛠️ Rebuilding playlist with fresh streams and headers...")
    updated_entries = update_playlist(entries, new_urls)

    save_playlist(updated_entries, OUTPUT_FILE)

if __name__ == "__main__":
    asyncio.run(main())
