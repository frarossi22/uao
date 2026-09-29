import base64
import re
import json
import requests
import time
import sys
from datetime import datetime

# ============================================================
# CREDENZIALI GOOGLE DRIVE
# ============================================================
CLIENT_ID = "360991432021-p5qnc2i8jg8vcnv12o33n74cnjl4bk5q.apps.googleusercontent.com"
CLIENT_SECRET = "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"
DRIVE_FILE_ID = "1w6LgRLFOmEYD88fXYlwwhzbBFZ210JG_"
REFRESH_TOKEN = "1//04SFIkmoK5XT4CgYIARAAGAQSNwF-L9IrfgX8z4LgUKT_jsT1BSaCVZ2DO8k2AqpaLcYMZ_MqQvg5SRj6cSmWE0uG3AtU1Egv1kA"

ACCESS_TOKEN = ""
BASE_URL = "https://uaznao.com/premium/canalitv/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ============================================================
# ORDINE E MAPPA COMPLETA DEI CANALI
# ============================================================
GROUP_ORDER = [
    "Rai",
    "Mediaset",
    "Sky Cinema",
    "Sky Sport",
    "Serie B",
    "DAZN CH",
    "DAZN PT",
    "Sportv PT",
    "Premier Sport",
    "ESPN",
    "BluSport",
    "Intrattenimento"
]

CHANNEL_MAP = {
    # Rai (3)
    "rai1": {"name": "Rai 1", "group": "Rai", "directUrl": "https://raiuno3-live.akamaized.net/hls/live/2017910/raiuno3/raiuno3/playlist.m3u8"},
    "rai2": {"name": "Rai 2", "group": "Rai", "directUrl": "https://raidue3-live.akamaized.net/hls/live/2017983/raidue3/raidue3/playlist.m3u8"},
    "rai3": {"name": "Rai 3", "group": "Rai", "directUrl": "https://raitre3-live.akamaized.net/hls/live/2018002/raitre3/raitre3/playlist.m3u8"},

    # Mediaset (4)
    "rete4": {"name": "Rete 4", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-r4/r4-clr.isml/manifest.mpd"},
    "canale5": {"name": "Canale 5", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-c5/c5-clr.isml/manifest.mpd"},
    "italia1": {"name": "Italia 1", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-i1/i1-clr.isml/manifest.mpd"},
    "grandefratello": {"name": "Grande Fratello", "group": "Mediaset", "directUrl": "https://live02-col.msf.cdn.mediaset.net/live/ch-b7/b7-clr.isml/index.m3u8"},

    # Sky Cinema (9)
    "cinema1": {"name": "Sky Cinema Uno", "group": "Sky Cinema"},
    "cinemastories": {"name": "Sky Cinema Stories", "group": "Sky Cinema"},
    "cinemafamily": {"name": "Sky Cinema Family", "group": "Sky Cinema"},
    "cinemacomedy": {"name": "Sky Cinema Comedy", "group": "Sky Cinema"},
    "cinemaaction": {"name": "Sky Cinema Action", "group": "Sky Cinema"},
    "cinemasuspense": {"name": "Sky Cinema Suspense", "group": "Sky Cinema"},
    "cinemaromance": {"name": "Sky Cinema Romance", "group": "Sky Cinema"},
    "cinemacollection": {"name": "Sky Cinema Collection", "group": "Sky Cinema"},
    "cinemadrama": {"name": "Sky Cinema Drama", "group": "Sky Cinema"},

    # Sky Sport (22)
    "sport24": {"name": "Sky Sport 24", "group": "Sky Sport"},
    "sportuno": {"name": "Sky Sport Uno", "group": "Sky Sport"},
    "calcio": {"name": "Sky Sport Calcio", "group": "Sky Sport"},
    "arena": {"name": "Sky Sport Arena", "group": "Sky Sport"},
    "sportmax": {"name": "Sky Sport Max", "group": "Sky Sport"},
    "sportmix": {"name": "Sky Sport Mix", "group": "Sky Sport"},
    "legend": {"name": "Sky Sport Legend", "group": "Sky Sport"},
    "f1": {"name": "Sky Sport F1", "group": "Sky Sport"},
    "motogp": {"name": "Sky Sport MotoGP", "group": "Sky Sport"},
    "tennis": {"name": "Sky Sport Tennis", "group": "Sky Sport"},
    "basket": {"name": "Sky Sport Basket", "group": "Sky Sport"},
    "golf": {"name": "Sky Sport Golf", "group": "Sky Sport"},
    "amazonlive": {"name": "Amazon Live", "group": "Sky Sport"},
    "sport251": {"name": "Sky Sport 251", "group": "Sky Sport"},
    "sport252": {"name": "Sky Sport 252", "group": "Sky Sport"},
    "sport253": {"name": "Sky Sport 253", "group": "Sky Sport"},
    "sport254": {"name": "Sky Sport 254", "group": "Sky Sport"},
    "sport255": {"name": "Sky Sport 255", "group": "Sky Sport"},
    "sport256": {"name": "Sky Sport 256", "group": "Sky Sport"},
    "sport257": {"name": "Sky Sport 257", "group": "Sky Sport"},
    "sport258": {"name": "Sky Sport 258", "group": "Sky Sport"},
    "sport259": {"name": "Sky Sport 259", "group": "Sky Sport"},

    # Serie B (4)
    "serieb/player_serieb.php?event=1": {"name": "Serie B 1", "group": "Serie B"},
    "serieb/player_serieb.php?event=2": {"name": "Serie B 2", "group": "Serie B"},
    "serieb/player_serieb.php?event=3": {"name": "Serie B 3", "group": "Serie B"},
    "serieb/player_serieb.php?event=4": {"name": "Serie B 4", "group": "Serie B"},

    # DAZN CH (10)
    "daznch/player_event.php?event=1": {"name": "DAZN 1", "group": "DAZN CH"},
    "daznch/player_event.php?event=2": {"name": "DAZN 2", "group": "DAZN CH"},
    "daznch/player_event.php?event=3": {"name": "DAZN 3", "group": "DAZN CH"},
    "daznch/player_event.php?event=4": {"name": "DAZN 4", "group": "DAZN CH"},
    "daznch/player_event.php?event=5": {"name": "DAZN 5", "group": "DAZN CH"},
    "daznch/player_event.php?event=6": {"name": "DAZN 6", "group": "DAZN CH"},
    "daznch/player_event.php?event=7": {"name": "DAZN 7", "group": "DAZN CH"},
    "daznch/player_event.php?event=8": {"name": "DAZN 8", "group": "DAZN CH"},
    "daznch/player_event.php?event=9": {"name": "DAZN 9", "group": "DAZN CH"},
    "daznch/player_event.php?event=10": {"name": "DAZN 10", "group": "DAZN CH"},

    # DAZN PT (5)
    "dazn1_pt": {"name": "DAZN 1 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$521/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MzliY2JjOTQxOGFhNGQ2MmI5NmI2YTNlYWUyZjZkZjA6YThmOTY4YjZhOGVkN2JmYjE3YmY3ODdiNmM5MzBjN2U="},
    "dazn2_pt": {"name": "DAZN 2 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$522/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MzgwNWNkNTMzYzEzNDFhNzkzNGQxMzYyOWViN2EzNGU6MjU0MjU2NDkyOGNiOGUzZmU0NTk1YWI4ZGNmZDZlNzc="},
    "dazn3_pt": {"name": "DAZN 3 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$523/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=NzIyNGYyYTZhMTRhNGQ4ODg3NGQxMGRkOTUzYzg4ZGM6OTcxOWVhMjM4ZDNkZTY2ZWIwNzNjZTg0MjgxNGY0NjQ="},
    "dazn4_pt": {"name": "DAZN 4 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$524/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MGI2ZTVmZTViMWQxNDBiMDkyZTIyY2M2NjIwODgyNzY6NmJkZDc2YWRiYzViYjI1MDg5OTgzYjI1MDBkZGU3Y2E="},
    "dazn5_pt": {"name": "DAZN 5 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$525/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=ZDkzMWQ2NzE4ODQxNDVkZmIzOTJiZTBjYWRlNTA4OGM6YmVlZTM5NTZiNzY5YzM5ZjAwZmEzY2U4NGEyZWZhYmE="},

    # Sportv PT (7)
    "sportv1_pt": {"name": "Sport TV 1 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$151/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=YzJiYWM5YzM5M2YxNDVmYzkyNGNlNTcyY2E5OTE1NmY6NDVmNjYzN2VlZjgwZWFmYmU3ZTYzMDIzMTEzOWRmNWI="},
    "sportv2_pt": {"name": "Sport TV 2 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$152/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MGQyOGVkZjRmMDU1NDA5YmIxMmQ2ZDAyNjBiMjZiNmI6YmY2OWY4YTMzYzM5YzMxZjVmZjA2YWI1MjAxMmUyN2M="},
    "sportv3_pt": {"name": "Sport TV 3 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$153/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MjA2ZmVjNTZmNWI3NDFlNWFhODExMjQ4OTVkOWI1OTI6MjdiOTE1MDVhYTY5MjZmNTkxOTljODI4YmMyNzc2N2I="},
    "sportv4_pt": {"name": "Sport TV 4 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$10/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=Y2MwYjdhYzMxYjVlNDJmOGJmOTM0Zjk5YWNmNzFhOGE6ZDc2NDI0ZDY0NGEzNjAwNTY1NjdhMjQ4ZDhiODliNmM="},
    "sportv5_pt": {"name": "Sport TV 5 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$112/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=ODFjYTQzNGM5MzFhNDAzZTk1MGRmM2Q4MDhjMjRjNDE6MTg1NDgxOTBjZjNjODI5NDA5NmFmOGEyMTQ2ZTMyYTU="},
    "sportv6_pt": {"name": "Sport TV 6 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$566/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=ZDMxOWFhYjAyYTgzNDIyNDhjY2ViMGZkZjA2MGJjNTQ6YjM2NjY4YTgzNmIxNTA1NWJlMWYwNGI4ZDhhOGNjNzA="},
    "sportv7_pt": {"name": "Sport TV 7 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$597/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=NDAwOTU3YWM2OGQ1NDlmYmJiYmM2NjhkM2E5ZWI3MDk6M2RkMzUxZjE4NzViMGRkNDBhNGUzOTJmMDZhMjliMjk="},

    # Premier Sport (2)
    "premiersports1_uk": {"name": "Premier Sports 1 [UK]", "group": "Premier Sport", "directUrl": "https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/m6sqanvm2m/out/v1/f6beb46c6e9a4132ad739f3ca27df6aa/cenc.mpd?ck=MTQ0NGY0MjM1NTI5ZjE4M2YwYTVhNDg2YmVmZTljZGI6ZTVlM2ZlYzY3YTFiYjM0NzJhMjA4OWM4YTBhMjU1N2Y="},
    "premiersports2_uk": {"name": "Premier Sports 2 [UK]", "group": "Premier Sport", "directUrl": "https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/bcj3iscpd6/out/v1/fcd137b391214f7cb99dd4d7be90ca87/cenc.mpd?ck=MWE1ZGY1MzYwOWViYzk4NTc4OThjNDkwZjQ3MjQ5MTg6NzdmNjI5ODBkNTgyZWM1NDEyODA3OTZhY2Y4YjJkMTk="},

    # ESPN (7)
    "espn1_sur": {"name": "ESPN [SUR]", "group": "ESPN", "directUrl": "https://vcdn.mn10.entel.bo/Content/DASH/Live/Channel(8757cb0a-3584-40cd-901e-8937c7deba83)/master.mpd?ck=Y2IwMDRmYjEwMGJkOTJmMjM3OTM1NjI4OTFlMzIzNmI6YjNlNGU3NGFlMjA4MGIxMzdlNjhiYmQwZWY4YTdlMDU="},
    "espn2_sur": {"name": "ESPN 2 [SUR]", "group": "ESPN", "directUrl": "https://vcdn.mn10.entel.bo/Content/DASH/Live/Channel(62567d5c-295c-4ffd-ac7e-c9749e874884)/master.mpd?ck=YTgxZWU0YTY5NGZlY2Q2YWE4YTY4MmU1MDI0YjMxM2M6NmQxNTU2OGUxZGFiNTllNzIwMmFlMTJlNzE1MDUxODU="},
    "espn3_sur": {"name": "ESPN 3 [SUR]", "group": "ESPN", "directUrl": "https://vcdn.mn10.entel.bo/Content/DASH/Live/Channel(a38d1401-ee01-4802-812a-7cb460c9832c)/master.mpd?ck=OGE2MGQ3ODg5ZmYxMjZlZTE4OTUzMzVlOTIyNTRmOGU6ZGUxYjBjZTE5ZmE4MDRhMWM0NzNlYjhlZjJkNWNmNmQ="},
    "espn4_sur": {"name": "ESPN 4 [SUR]", "group": "ESPN", "directUrl": "https://vcdn.mn10.entel.bo/Content/DASH/Live/Channel(9500bf02-0001-4199-a150-58dc5d692cca)/master.mpd?ck=NTRhMmMxMTA4NWMzMTVlZDZmZjg1YzM0MGE4NjA5NWQ6NWYwZDEwY2Y0YTVjN2UyMmUyODZiN2U4Y2I0ZTc5ZjQ="},
    "espn5_sur": {"name": "ESPN 5 [SUR]", "group": "ESPN", "directUrl": "https://vcdn.mn10.entel.bo/Content/DASH/Live/Channel(80c74968-a2ef-4005-8661-045fe97408a8)/master.mpd?ck=NGUxMjYyOTdmYzdhZjM1YzczNmJkZmZlOThlZWNhYWE6ZmRiMDA5MWNmNjdkOWM1OTZkYmZiMDdjZjZmNGM4ZjU="},
    "espn6_sur": {"name": "ESPN 6 [SUR]", "group": "ESPN", "directUrl": "https://vcdn.mn10.entel.bo/Content/DASH/Live/Channel(b30aa51e-97fa-4354-bb38-871fb360e984)/master.mpd?ck=ZjU4MzYzODI0NTJjZGNhMWUxYzhiZjhiOWE3MTM1MzQ6N2QyNjE5MzBjMzMwOWVkMmIwNmQyYWJiMzRhNjQ0MTA="},
    "espn7_sur": {"name": "ESPN 7 [SUR]", "group": "ESPN", "directUrl": "https://vcdn.mn10.entel.bo/Content/DASH/Live/Channel(5ab5db84-2235-4c10-9066-be9bc2ee087a)/master.mpd?ck=OThlYTFlMzIyMjdhZGNkMzYxOGJhYWMyYmJmMzY4MTQ6NzJhMDNhMDlkMzNlNDEyZjE0YTliZmE0ZWYyNGI1NDI="},

    # BluSport (10)
    "blusport/player_event.php?event=1": {"name": "Blu Sport 1", "group": "BluSport"},
    "blusport/player_event.php?event=2": {"name": "Blu Sport 2", "group": "BluSport"},
    "blusport/player_event.php?event=3": {"name": "Blu Sport 3", "group": "BluSport"},
    "blusport/player_event.php?event=4": {"name": "Blu Sport 4", "group": "BluSport"},
    "blusport/player_event.php?event=5": {"name": "Blu Sport 5", "group": "BluSport"},
    "blusport/player_event.php?event=6": {"name": "Blu Sport 6", "group": "BluSport"},
    "blusport/player_event.php?event=7": {"name": "Blu Sport 7", "group": "BluSport"},
    "blusport/player_event.php?event=8": {"name": "Blu Sport 8", "group": "BluSport"},
    "blusport/player_event.php?event=9": {"name": "Blu Sport 9", "group": "BluSport"},
    "blusport/player_event.php?event=10": {"name": "Blu Sport 10", "group": "BluSport"},

    # Intrattenimento (16)
    "uno": {"name": "Sky Uno", "group": "Intrattenimento"},
    "unoplus": {"name": "Sky Uno Plus", "group": "Intrattenimento"},
    "atlantic": {"name": "Sky Atlantic", "group": "Intrattenimento"},
    "serie": {"name": "Sky Serie", "group": "Intrattenimento"},
    "investigation": {"name": "Sky Investigation", "group": "Intrattenimento"},
    "crime": {"name": "Sky Crime", "group": "Intrattenimento"},
    "adventure": {"name": "Sky Adventure", "group": "Intrattenimento"},
    "nature": {"name": "Sky Nature", "group": "Intrattenimento"},
    "arte": {"name": "Sky Arte", "group": "Intrattenimento"},
    "documentaries": {"name": "Sky Documentaries", "group": "Intrattenimento"},
    "comedycentral": {"name": "Comedy Central", "group": "Intrattenimento"},
    "deakids": {"name": "DeAKids", "group": "Intrattenimento"},
    "nickjunior": {"name": "Nick Jr", "group": "Intrattenimento"},
    "nickeleodeon": {"name": "Nickelodeon", "group": "Intrattenimento"},
    "cartoonnetwork": {"name": "Cartoon Network", "group": "Intrattenimento"},
    "boomerang": {"name": "Boomerang", "group": "Intrattenimento"},
}

# ============================================================
# FUNZIONI DI SUPPORTO
# ============================================================
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def refresh_access_token():
    global ACCESS_TOKEN
    try:
        log("🔄 Rinnovo token Google Drive...")
        res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
            timeout=30
        )
        data = res.json()
        if "access_token" in data:
            ACCESS_TOKEN = data["access_token"]
            log("✅ Token rinnovato!")
            return True
        else:
            log(f"❌ Errore refresh token: {data}")
            return False
    except Exception as e:
        log(f"❌ Errore refresh token: {e}")
        return False

def decode_ck(ck):
    try:
        pad = "=" * (4 - len(ck) % 4) if len(ck) % 4 else ""
        decoded = base64.b64decode(ck + pad).decode("utf-8")
        match = re.search(r"([0-9a-fA-F]+):([0-9a-fA-F]+)", decoded)
        if match:
            return f"{match.group(1).lower()}:{match.group(2).lower()}"
    except Exception:
        pass
    return None

def extract_ck_from_url(raw_url):
    try:
        if "ck=" in raw_url:
            parts = raw_url.split("ck=")
            base_url = parts[0].rstrip("&?")
            ck_val = parts[1].split("&")[0]
            clear_key = decode_ck(ck_val)
            return base_url, clear_key
    except Exception:
        pass
    return raw_url, None

def parse_clear_keys(raw_keys):
    if not raw_keys:
        return None, None
    raw_keys = raw_keys.strip().rstrip(";").strip()
    try:
        parsed = json.loads(raw_keys)
    except (json.JSONDecodeError, ValueError):
        cleaned = raw_keys.strip("\"'").strip()
        if ":" in cleaned:
            parts = cleaned.split(":", 1)
            return parts[0].strip().lower(), parts[1].strip().lower()
        return None, None

    if isinstance(parsed, str) and ":" in parsed:
        parts = parsed.split(":", 1)
        return parts[0].strip().lower(), parts[1].strip().lower()

    if isinstance(parsed, list) and len(parsed) > 0:
        first = parsed[0]
        if isinstance(first, str) and ":" in first:
            parts = first.split(":", 1)
            return parts[0].strip().lower(), parts[1].strip().lower()
        if isinstance(first, dict):
            kid = first.get("kid")
            key = first.get("key")
            if kid and key:
                return str(kid).strip().lower(), str(key).strip().lower()

    if isinstance(parsed, dict):
        if "kid" in parsed and "key" in parsed:
            return str(parsed["kid"]).strip().lower(), str(parsed["key"]).strip().lower()
        if len(parsed) > 0:
            kid, key = next(iter(parsed.items()))
            return str(kid).strip().lower(), str(key).strip().lower()

    return None, None

def scrape_channels():
    channels = []
    total = len(CHANNEL_MAP)
    log(f"📡 Scraping e estrazione di tutti i {total} canali...")

    for i, (path, meta) in enumerate(CHANNEL_MAP.items(), 1):
        try:
            name = meta["name"]
            group = meta["group"]

            if "directUrl" in meta:
                log(f"[{i}/{total}] 📡 {name} (Diretto)...")
                raw_url = meta["directUrl"]
                clean_url, clear_key = extract_ck_from_url(raw_url)

                ch_dict = {"name": name, "group": group, "url": clean_url}
                if clear_key:
                    ch_dict["clear_key"] = clear_key

                channels.append(ch_dict)
                log("  ✅ OK")
                continue

            if "player_event.php" in path or "player_serieb.php" in path or "player.php" in path:
                page_url = f"{BASE_URL}{path}"
            else:
                page_url = f"{BASE_URL}{path}.php"

            log(f"[{i}/{total}] 📡 {name}...")
            res = requests.get(page_url, headers=HEADERS, timeout=10)

            if res.status_code == 200:
                html = res.text

                match = re.search(r'const\s+STREAM_URL\s*=\s*"([^"]+)"', html)
                if not match:
                    match = re.search(r'STREAM_URL\s*=\s*["\']([^"\']*)["\']', html, re.IGNORECASE)

                if match:
                    raw_stream = match.group(1).replace(r"\/", "/")

                    if not raw_stream.strip():
                        log(f"  ⏳ {name} - In attesa dell'url")
                        continue

                    clean_url, clear_key = extract_ck_from_url(raw_stream)

                    kid, key = None, None
                    keys_match = re.search(r'STREAM_CLEAR_KEYS\s*=\s*(.+?);', html, re.IGNORECASE | re.DOTALL)
                    if keys_match:
                        kid, key = parse_clear_keys(keys_match.group(1))

                    ch_dict = {"name": name, "group": group, "url": clean_url}
                    if clear_key:
                        ch_dict["clear_key"] = clear_key
                    elif kid and key:
                        ch_dict["clear_key"] = f"{kid}:{key}"

                    channels.append(ch_dict)
                    log("  ✅ OK")
                else:
                    log(f"  ⏳ {name} - In attesa dell'url")
            else:
                log(f"  ❌ HTTP {res.status_code}")
        except Exception as e:
            log(f"  ❌ Errore: {e}")
        time.sleep(0.1)

    return channels

def generate_m3u(all_channels_collected):
    content = '#EXTM3U url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"\n'

    for grp in GROUP_ORDER:
        for ch in all_channels_collected:
            if ch["group"] == grp:
                tvg_name = ch.get("name", "Canale")
                content += f'#EXTINF:-1 group-title="{grp}" tvg-id="{tvg_name}",{tvg_name}\n'

                if "clear_key" in ch and ch["clear_key"]:
                    content += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
                    content += f'#KODIPROP:inputstream.adaptive.license_key={ch["clear_key"]}\n'

                url = ch.get("url")
                if url:
                    content += f'{url}\n'
    return content

def upload_to_drive(content):
    try:
        log("☁️ Caricamento su Google Drive...")
        if not refresh_access_token():
            log("❌ Impossibile ottenere token")
            return False

        url = f"https://www.googleapis.com/upload/drive/v3/files/{DRIVE_FILE_ID}?uploadType=media"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "text/plain",
        }
        res = requests.patch(url, headers=headers, data=content.encode("utf-8"), timeout=30)

        if res.status_code == 200:
            log("=" * 50)
            log("✅ skympd.m3u caricato su Google Drive con successo!")
            log("=" * 50)
            return True
        else:
            log(f"❌ Errore Google Drive: HTTP {res.status_code}")
            return False
    except Exception as e:
        log(f"❌ Errore upload: {e}")
        return False

def main():
    print("=" * 50)
    print("📺 Uaznao Scraper - Canali Aggiornati")
    print("=" * 50)
    log("Avvio...")

    all_collected = scrape_channels()

    if not all_collected:
        log("\n❌ Nessun canale trovato!")
        sys.exit(1)

    log(f"\n📝 Generazione file m3u con {len(all_collected)} canali...")
    m3u_content = generate_m3u(all_collected)

    with open("skympd.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    log("📁 skympd.m3u salvato localmente")

    log("\n☁️ Connessione a Google Drive...")
    if upload_to_drive(m3u_content):
        log("\n🎉 Operazione completata con successo!")
    else:
        log("\n❌ Operazione fallita!")
        sys.exit(1)

if __name__ == "__main__":
    main()