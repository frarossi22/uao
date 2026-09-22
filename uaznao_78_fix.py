"""
Scraper Uaznao - Universale (Windows + Android)
- RAI, MEDIASET, SKY (Cinema, Sport, Intrattenimento), DAZN, BLU SPORT + SERIE B
- Carica skympd.m3u su Google Drive (sovrascrive)
- Nessun lettore, solo scraping + upload
"""

import base64
import re
import json
import requests
import time
import sys
import os
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
# CHANNEL MAP – Rai, Mediaset, Sky Cinema, Sky Sport, INTRATTENIMENTO
# ============================================================
CHANNEL_MAP = {
    # RAI
    "rai1": {"name": "Rai 1", "group": "Rai", "directUrl": "https://raiuno3-live.akamaized.net/hls/live/2017910/raiuno3/raiuno3/playlist.m3u8"},
    "rai2": {"name": "Rai 2", "group": "Rai", "directUrl": "https://raidue3-live.akamaized.net/hls/live/2017983/raidue3/raidue3/playlist.m3u8"},
    "rai3": {"name": "Rai 3", "group": "Rai", "directUrl": "https://raitre3-live.akamaized.net/hls/live/2018002/raitre3/raitre3/playlist.m3u8"},

    # MEDIASET
    "rete4": {"name": "Rete 4", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-r4/r4-clr.isml/manifest.mpd"},
    "canale5": {"name": "Canale 5", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-c5/c5-clr.isml/manifest.mpd"},
    "italia1": {"name": "Italia 1", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-i1/i1-clr.isml/manifest.mpd"},
    "grandefratello": {"name": "Grande Fratello", "group": "Mediaset", "directUrl": "https://live02-col.msf.cdn.mediaset.net/live/ch-b7/b7-clr.isml/index.m3u8"},

    # SKY CINEMA (9 canali)
    "cinema1": {"name": "Sky Cinema Uno", "group": "Sky Cinema"},
    "cinemastories": {"name": "Sky Cinema Stories", "group": "Sky Cinema"},
    "cinemafamily": {"name": "Sky Cinema Family", "group": "Sky Cinema"},
    "cinemacomedy": {"name": "Sky Cinema Comedy", "group": "Sky Cinema"},
    "cinemaaction": {"name": "Sky Cinema Action", "group": "Sky Cinema"},
    "cinemasuspense": {"name": "Sky Cinema Suspense", "group": "Sky Cinema"},
    "cinemaromance": {"name": "Sky Cinema Romance", "group": "Sky Cinema"},
    "cinemacollection": {"name": "Sky Cinema Collection", "group": "Sky Cinema"},
    "cinemadrama": {"name": "Sky Cinema Drama", "group": "Sky Cinema"},

    # SKY SPORT (22 canali)
    "sport24": {"name": "Sky Sport 24", "group": "Sky Sport"},
    "sportuno": {"name": "Sky Sport Uno", "group": "Sky Sport"},
    "calcio": {"name": "Sky Sport Calcio", "group": "Sky Sport"},
    "sport251": {"name": "Sky Sport 251", "group": "Sky Sport"},
    "sport252": {"name": "Sky Sport 252", "group": "Sky Sport"},
    "sport253": {"name": "Sky Sport 253", "group": "Sky Sport"},
    "sport254": {"name": "Sky Sport 254", "group": "Sky Sport"},
    "sport255": {"name": "Sky Sport 255", "group": "Sky Sport"},
    "sport256": {"name": "Sky Sport 256", "group": "Sky Sport"},
    "sport257": {"name": "Sky Sport 257", "group": "Sky Sport"},
    "sport258": {"name": "Sky Sport 258", "group": "Sky Sport"},
    "sport259": {"name": "Sky Sport 259", "group": "Sky Sport"},
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

    # INTRATTENIMENTO (16 canali)
    "uno": {"name": "Sky Uno", "group": "INTRATTENIMENTO"},
    "unoplus": {"name": "Sky Uno Plus", "group": "INTRATTENIMENTO"},
    "atlantic": {"name": "Sky Atlantic", "group": "INTRATTENIMENTO"},
    "serie": {"name": "Sky Serie", "group": "INTRATTENIMENTO"},
    "investigation": {"name": "Sky Investigation", "group": "INTRATTENIMENTO"},
    "crime": {"name": "Sky Crime", "group": "INTRATTENIMENTO"},
    "adventure": {"name": "Sky Adventure", "group": "INTRATTENIMENTO"},
    "nature": {"name": "Sky Nature", "group": "INTRATTENIMENTO"},
    "arte": {"name": "Sky Arte", "group": "INTRATTENIMENTO"},
    "documentaries": {"name": "Sky Documentaries", "group": "INTRATTENIMENTO"},
    "comedycentral": {"name": "Comedy Central", "group": "INTRATTENIMENTO"},
    "deakids": {"name": "DeAKids", "group": "INTRATTENIMENTO"},
    "nickjunior": {"name": "Nick Jr", "group": "INTRATTENIMENTO"},
    "nickeleodeon": {"name": "Nickelodeon", "group": "INTRATTENIMENTO"},
    "cartoonnetwork": {"name": "Cartoon Network", "group": "INTRATTENIMENTO"},
    "boomerang": {"name": "Boomerang", "group": "INTRATTENIMENTO"},
}

# ============================================================
# CANALI A EVENTI (DAZN CH, BluSport, SerieB)
# ============================================================
EVENT_FOLDERS = {
    "DAZN CH": {"folder": "daznch", "count": 10, "prefix": "DAZN"},
    "BluSport": {"folder": "blusport", "count": 10, "prefix": "Blu Sport"},
}

SERIEB_CHANNELS = [
    {"path": "serieb/player_serieb.php?event=1", "name": "Serie B 1", "group": "SerieB"},
    {"path": "serieb/player_serieb.php?event=2", "name": "Serie B 2", "group": "SerieB"},
    {"path": "serieb/player_serieb.php?event=3", "name": "Serie B 3", "group": "SerieB"},
    {"path": "serieb/player_serieb.php?event=4", "name": "Serie B 4", "group": "SerieB"},
]

# ============================================================
# FUNZIONI
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
        return base64.b64decode(ck + pad).decode("utf-8")
    except Exception:
        return None

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

    if isinstance(parsed, str):
        if ":" in parsed:
            parts = parsed.split(":", 1)
            return parts[0].strip().lower(), parts[1].strip().lower()
        return None, None

    if isinstance(parsed, list):
        if len(parsed) == 0:
            return None, None
        first = parsed[0]
        if isinstance(first, str) and ":" in first:
            parts = first.split(":", 1)
            return parts[0].strip().lower(), parts[1].strip().lower()
        if isinstance(first, dict):
            kid = first.get("kid")
            key = first.get("key")
            if kid and key:
                return str(kid).strip().lower(), str(key).strip().lower()
        return None, None

    if isinstance(parsed, dict):
        if "kid" in parsed and "key" in parsed:
            return str(parsed["kid"]).strip().lower(), str(parsed["key"]).strip().lower()
        if len(parsed) > 0:
            kid, key = next(iter(parsed.items()))
            return str(kid).strip().lower(), str(key).strip().lower()
        return None, None

    return None, None

def extract_event_channel(url, name, group):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            log(f"  ❌ HTTP {res.status_code}")
            return None

        html = res.text

        mpd_match = re.search(r'STREAM_URL\s*=\s*["\']([^"\']*)["\']', html, re.IGNORECASE)
        if not mpd_match:
            log("  ⚠️ STREAM_URL non trovato")
            return None

        mpd_url = mpd_match.group(1).replace(r"\/", "/").strip()
        if not mpd_url:
            log("  ⏳ STREAM_URL vuoto (in attesa)")
            return None

        keys_match = re.search(r'STREAM_CLEAR_KEYS\s*=\s*(.+?);', html, re.IGNORECASE | re.DOTALL)
        if not keys_match:
            log("  ⚠️ STREAM_CLEAR_KEYS non trovato")
            return None

        kid, key = parse_clear_keys(keys_match.group(1))
        if not kid or not key:
            log("  ⚠️ ClearKey non valida")
            return None

        log("  ✅ OK")
        return {
            "name": name,
            "group": group,
            "kid": kid,
            "key": key,
            "mpd": mpd_url,
        }
    except Exception as e:
        log(f"  ❌ ERRORE: {e}")
        return None

def get_event_channels(folder_name, group_name, prefix, count=10):
    channels = []
    for i in range(1, count + 1):
        log(f"📺 {prefix} {i}...")
        url = f"{BASE_URL}{folder_name}/player_event.php?event={i}"
        ch = extract_event_channel(url, f"{prefix} {i}", group_name)
        if ch:
            channels.append(ch)
        time.sleep(1)
    return channels

def get_serieb_channels():
    channels = []
    for item in SERIEB_CHANNELS:
        log(f"📺 {item['name']}...")
        url = f"{BASE_URL}{item['path']}"
        ch = extract_event_channel(url, item["name"], item["group"])
        if ch:
            channels.append(ch)
        time.sleep(1)
    return channels

def scrape_channels():
    channels = []
    total = len(CHANNEL_MAP)

    log(f"📡 Scraping di {total} canali standard (Rai, Mediaset, Sky)...")

    for i, (path, meta) in enumerate(CHANNEL_MAP.items(), 1):
        try:
            name = meta["name"]
            group = meta["group"]

            # Se il canale ha un URL diretto (Rai / Mediaset)
            if "directUrl" in meta:
                log(f"[{i}/{total}] 📡 {name} (Diretto)...")
                channels.append({
                    "name": name,
                    "group": group,
                    "url": meta["directUrl"]
                })
                log(f"  ✅ OK")
                continue

            page_url = f"{BASE_URL}{path}.php"
            log(f"[{i}/{total}] 📡 {name}...")

            res = requests.get(page_url, headers=HEADERS, timeout=10)

            if res.status_code == 200:
                match = re.search(r'const\s+STREAM_URL\s*=\s*"([^"]+)"', res.text)
                if match:
                    raw_stream = match.group(1).replace(r"\/", "/")
                    clean_url = raw_stream.split("?")[0]

                    ck_match = re.search(r"ck=([^&]+)", raw_stream)
                    clear_key = decode_ck(ck_match.group(1)) if ck_match else None

                    kid = None
                    key = None

                    if not clear_key:
                        keys_match = re.search(
                            r'STREAM_CLEAR_KEYS\s*=\s*(.+?);',
                            res.text, re.IGNORECASE | re.DOTALL
                        )
                        if keys_match:
                            kid, key = parse_clear_keys(keys_match.group(1))

                    ch_dict = {
                        "name": name,
                        "group": group,
                        "url": clean_url,
                    }
                    if clear_key:
                        ch_dict["clear_key"] = clear_key
                    if kid and key:
                        ch_dict["kid"] = kid
                        ch_dict["key"] = key

                    channels.append(ch_dict)
                    log(f"  ✅ OK")
                else:
                    log(f"  ⚠️ Nessun flusso")
            else:
                log(f"  ❌ HTTP {res.status_code}")

        except Exception as e:
            log(f"  ❌ Errore: {e}")

        time.sleep(0.3)

    return channels

def generate_m3u(standard_channels, event_channels_dict):
    content = (
        "#EXTM3U"
        ' url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"\n'
    )

    group_map = {
        "Rai": "Rai",
        "Mediaset": "Mediaset",
        "Sky Sport": "SkySport",
        "Sky Cinema": "Film - Serie TV",
        "INTRATTENIMENTO": "SkyEntertainment",
        "DAZN CH": "DAZN",
        "BluSport": "BLU SPORT",
        "SerieB": "SerieB",
    }

    group_order = ["Rai", "Mediaset", "Film - Serie TV", "SkySport", "SkyEntertainment", "DAZN", "BLU SPORT", "SerieB"]

    by_group = {}
    for ch in standard_channels:
        grp = group_map.get(ch["group"], ch["group"])
        if grp not in by_group:
            by_group[grp] = []
        by_group[grp].append(ch)

    for grp_key, ch_list in event_channels_dict.items():
        mapped_grp = group_map.get(grp_key, grp_key)
        if mapped_grp not in by_group:
            by_group[mapped_grp] = []
        by_group[mapped_grp].extend(ch_list)

    for grp in group_order:
        if grp not in by_group:
            continue
        for ch in by_group[grp]:
            tvg_name = ch.get("name", "Canale")

            content += f'#EXTINF:-1 group-title="{grp}" tvg-id="{tvg_name}",{tvg_name}\n'

            if "clear_key" in ch and ch["clear_key"]:
                content += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
                content += f'#KODIPROP:inputstream.adaptive.license_key={ch["clear_key"]}\n'
            elif "kid" in ch and "key" in ch:
                content += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
                content += f'#KODIPROP:inputstream.adaptive.license_key={ch["kid"]}:{ch["key"]}\n'

            url = ch.get("url") or ch.get("mpd")
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
            log("✅ skympd.m3u caricato su Google Drive!")
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
    print("📺 Uaznao Scraper - Rai, Mediaset, Sky, DAZN, BluSport & Serie B")
    print("=" * 50)
    log("Avvio...")

    standard_channels = scrape_channels()

    event_dict = {}

    for group_name, cfg in EVENT_FOLDERS.items():
        log(f"\n📡 Estrazione {group_name} 1-{cfg['count']}...")
        event_dict[group_name] = get_event_channels(
            cfg["folder"], group_name, cfg["prefix"], cfg["count"]
        )

    log("\n📡 Estrazione SerieB 1-4...")
    event_dict["SerieB"] = get_serieb_channels()

    if not standard_channels and not any(event_dict.values()):
        log("\n❌ Nessun canale trovato!")
        sys.exit(1)

    log(f"\n✅ Standard (Rai/Mediaset/Sky): {len(standard_channels)} canali")
    for group_name, chs in event_dict.items():
        log(f"✅ {group_name}: {len(chs)} canali")

    log("\n📝 Generazione skympd.m3u...")
    m3u_content = generate_m3u(standard_channels, event_dict)

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