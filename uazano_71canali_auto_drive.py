import time
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# ============================================================
# CREDENZIALI GOOGLE DRIVE
# ============================================================
CLIENT_ID = "360991432021-p5qnc2i8jg8vcnv12o33n74cnjl4bk5q.apps.googleusercontent.com"
CLIENT_SECRET = "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"
DRIVE_FILE_ID = "1w6LgRLFOmEYD88fXYlwwhzbBFZ210JG_"
REFRESH_TOKEN = "1//04SFIkmoK5XT4CgYIARAAGAQSNwF-L9IrfgX8z4LgUKT_jsT1BSaCVZ2DO8k2AqpaLcYMZ_MqQvg5SRj6cSmWE0uG3AtU1Egv1kA"

# ============================================================
# CONFIGURAZIONE CANALI (78 Canali Completi)[cite: 2]
# ============================================================
BASE_URL = 'https://uaznao.com/premium/canalitv/'

CHANNEL_MAP = {
    # Rai
    "rai1": {"name": "Rai 1", "group": "Rai", "directUrl": "https://raiuno3-live.akamaized.net/hls/live/2017910/raiuno3/raiuno3/playlist.m3u8"},
    "rai2": {"name": "Rai 2", "group": "Rai", "directUrl": "https://raidue3-live.akamaized.net/hls/live/2017983/raidue3/raidue3/playlist.m3u8"},
    "rai3": {"name": "Rai 3", "group": "Rai", "directUrl": "https://raitre3-live.akamaized.net/hls/live/2018002/raitre3/raitre3/playlist.m3u8"},

    # Mediaset
    "rete4": {"name": "Rete 4", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-r4/r4-clr.isml/manifest.mpd"},
    "canale5": {"name": "Canale 5", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-c5/c5-clr.isml/manifest.mpd"},
    "italia1": {"name": "Italia 1", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-i1/i1-clr.isml/manifest.mpd"},
    "grandefratello": {"name": "Grande Fratello", "group": "Mediaset", "directUrl": "https://live02-col.msf.cdn.mediaset.net/live/ch-b7/b7-clr.isml/index.m3u8"},

    # Sky Cinema
    "cinema1": {"name": "Sky Cinema Uno", "group": "Sky Cinema"},
    "cinemastories": {"name": "Sky Cinema Stories", "group": "Sky Cinema"},
    "cinemafamily": {"name": "Sky Cinema Family", "group": "Sky Cinema"},
    "cinemacomedy": {"name": "Sky Cinema Comedy", "group": "Sky Cinema"},
    "cinemaaction": {"name": "Sky Cinema Action", "group": "Sky Cinema"},
    "cinemasuspense": {"name": "Sky Cinema Suspense", "group": "Sky Cinema"},
    "cinemaromance": {"name": "Sky Cinema Romance", "group": "Sky Cinema"},
    "cinemacollection": {"name": "Sky Cinema Collection", "group": "Sky Cinema"},
    "cinemadrama": {"name": "Sky Cinema Drama", "group": "Sky Cinema"},

    # Sky Sport
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

    # Intrattenimento
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

    # DAZN CH
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

    # BluSport
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

    # Serie B
    "serieb/player_serieb.php?event=1": {"name": "Serie B 1", "group": "Serie B"},
    "serieb/player_serieb.php?event=2": {"name": "Serie B 2", "group": "Serie B"},
    "serieb/player_serieb.php?event=3": {"name": "Serie B 3", "group": "Serie B"},
    "serieb/player_serieb.php?event=4": {"name": "Serie B 4", "group": "Serie B"}
}

import base64
import re
import json

def decode_ck(ck):
    try:
        pad = '=' * (4 - len(ck) % 4) if len(ck) % 4 else ''
        decoded = base64.b64decode(ck + pad).decode('utf-8', errors='ignore')
        match = re.search(r'([0-9a-fA-F]+):([0-9a-fA-F]+)', decoded)
        if match:
            return {"kid": match.group(1), "key": match.group(2)}
        return None
    except Exception:
        return None

def extract_ck_from_url(raw_url):
    try:
        from urllib.parse import urlparse, parse_qs, urlunparse
        parsed = urlparse(raw_url)
        qs = parse_qs(parsed.query)
        ck = qs.get('ck', [None])[0]
        
        # Rimuove 'ck' dai parametri
        if 'ck' in qs:
            del qs['ck']
        
        from urllib.parse import urlencode
        new_query = urlencode(qs, doseq=True)
        clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        clear_key = decode_ck(ck) if ck else None
        return {"cleanUrl": cleanUrl, "clearKey": clear_key}
    except Exception:
        return {"cleanUrl": raw_url, "clearKey": None}

def fetch_channel_page(slug, meta):
    if meta and "directUrl" in meta:
        return {"cleanUrl": meta["directUrl"], "clearKey": None}

    if "player_event.php" in slug or "player.php" in slug or "player_serieb.php" in slug:
        page_url = BASE_URL + slug
    else:
        page_url = BASE_URL + slug + '.php'

    try:
        res = requests.get(page_url, timeout=10)
        if res.status_code != 200:
            return None
        body = res.text

        try:
            data = json.loads(body)
            if "body" in data:
                body = data["body"]
            elif "contents" in data:
                body = data["contents"]
        except Exception:
            pass

        if "player_event.php" in slug or "player.php" in slug or "player_serieb.php" in slug:
            mpd_match = re.search(r'STREAM_URL\s*=\s*(?:["\'])([^"\'&\s]+)(?:["\'])', body, re.IGNORECASE)
            if not mpd_match:
                return None
            clean_url = mpd_match.group(1).replace('\\/', '/')

            clear_key = None
            keys_array_match = re.search(r'STREAM_CLEAR_KEYS\s*=\s*\[([^\]]*)\]', body, re.IGNORECASE)
            if keys_array_match:
                inner = keys_array_match.group(1)
                key_matches = re.findall(r'(?:["\'])([^"\'&\s]+)(?:["\'])', inner)
                if key_matches:
                    joined = ",".join([k.replace('\\/', '/') for k in key_matches])
                    clear_key = decode_ck(joined)
            
            if not clear_key:
                keys_string_match = re.search(r'STREAM_CLEAR_KEYS\s*=\s*(?:["\'])([^"\'&\s]+)(?:["\'])', body, re.IGNORECASE)
                if keys_string_match:
                    clear_key = decode_ck(keys_string_match.group(1).replace('\\/', '/'))

            return {"cleanUrl": clean_url, "clearKey": clear_key}

        match = re.search(r'const\s+STREAM_URL\s*=\s*(?:["\'])([^"\'&\s]+)(?:["\'])', body)
        if not match:
            return None
        raw_stream_url = match.group(1).replace('\\/', '/')
        extracted = extract_ck_from_url(raw_stream_url)
        return {"cleanUrl": extracted["cleanUrl"], "clearKey": extracted["clearKey"]}
    except Exception:
        return None

def generate_m3u(all_channels):
    m3u_content = '#EXTM3U url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"\n'
    for ch in all_channels:
        m3u_content += f'#EXTINF:-1 group-title="{ch["group"]}" tvg-id="{ch["tvgId"]}" tvg-logo="" ,{ch["name"]}\n'
        if ch.get("clearKey") and "kid" in ch["clearKey"] and "key" in ch["clearKey"]:
            m3u_content += '#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
            m3u_content += f'#KODIPROP:inputstream.adaptive.license_key={ch["clearKey"]["kid"]}:{ch["clearKey"]["key"]}\n'
            m3u_content += f'{ch["url"]}\n'
        else:
            m3u_content += f'{ch.get("url") or ""}\n'
    return m3u_content

def upload_to_drive(content):
    print("🔄 Connessione a Google Drive in corso...")
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token"
    )
    
    service = build('drive', 'v3', credentials=creds)
    media = MediaIoBaseUpload(io.BytesIO(content.encode('utf-8')), mimetype='text/plain', resumable=True)
    
    try:
        updated_file = service.files().update(
            fileId=DRIVE_FILE_ID,
            media_body=media
        ).execute()
        print(f"✅ File 'skympd.m3u' inviato con successo a Google Drive! (ID: {updated_file.get('id')})")
    except Exception as e:
        print(f"❌ Errore durante l'invio su Google Drive: {e}")

def main():
    print("🚀 Inizio scraping dei canali...")
    all_channels = []
    slugs = list(CHANNEL_MAP.keys())
    done = 0

    for slug in slugs:
        meta = CHANNEL_MAP[slug]
        done += 1
        print(f"[{done}/{len(slugs)}] Elaborazione: {meta['name']}...")
        is_event_group = meta['group'] in ['Serie B', 'DAZN CH', 'BluSport']

        try:
            result = fetch_channel_page(slug, meta)
            if result and result.get("cleanUrl"):
                ch = {
                    "name": meta["name"],
                    "group": meta["group"],
                    "tvgId": meta["name"],
                    "url": result["cleanUrl"],
                    "clearKey": result.get("clearKey")
                }
                all_channels.append(ch)
            elif is_event_group:
                ch = {
                    "name": meta["name"],
                    "group": meta["group"],
                    "tvgId": meta["name"],
                    "url": None,
                    "clearKey": None
                }
                all_channels.append(ch)
        except Exception:
            if is_event_group:
                ch = {
                    "name": meta["name"],
                    "group": meta["group"],
                    "tvgId": meta["name"],
                    "url": None,
                    "clearKey": None
                }
                all_channels.append(ch)

    print("📄 Generazione contenuto M3U...")
    m3u_content = generate_m3u(all_channels)
    
    # Salvataggio locale opzionale come skympd.m3u
    with open("skympd.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print("💾 Playlist salvata localmente come 'skympd.m3u'")

    # Invio automatico su Google Drive
    upload_to_drive(m3u_content)

if __name__ == "__main__":
    main()
