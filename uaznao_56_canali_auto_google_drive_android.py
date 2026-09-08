"""
Scraper Uaznao - Universale (Windows + Android)
- 9 CINEMA + 21 SPORT + 16 INTRATTENIMENTO + 10 DAZN = 56 canali
- Carica skympd.m3u su Google Drive (sovrascrive)
- Nessun lettore, solo scraping + upload
- Funziona su Windows, Android, Linux, macOS
"""

import base64
import re
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
# CANALI AGGIORNATI (56 canali - con sport254-259)
# ============================================================
CHANNEL_MAP = {
    # CINEMA (9 canali)
    "cinema1": {"name": "Sky Cinema Uno", "group": "CINEMA"},
    "cinemastories": {"name": "Sky Cinema Stories", "group": "CINEMA"},
    "cinemafamily": {"name": "Sky Cinema Family", "group": "CINEMA"},
    "cinemacomedy": {"name": "Sky Cinema Comedy", "group": "CINEMA"},
    "cinemaaction": {"name": "Sky Cinema Action", "group": "CINEMA"},
    "cinemasuspense": {"name": "Sky Cinema Suspense", "group": "CINEMA"},
    "cinemaromance": {"name": "Sky Cinema Romance", "group": "CINEMA"},
    "cinemacollection": {"name": "Sky Cinema Collection", "group": "CINEMA"},
    "cinemadrama": {"name": "Sky Cinema Drama", "group": "CINEMA"},
    
    # SPORT (21 canali - con sport254-259)
    "sport24": {"name": "Sky Sport 24", "group": "SPORT"},
    "sportuno": {"name": "Sky Sport Uno", "group": "SPORT"},
    "calcio": {"name": "Sky Sport Calcio", "group": "SPORT"},
    "sport251": {"name": "Sky Sport 251", "group": "SPORT"},
    "sport252": {"name": "Sky Sport 252", "group": "SPORT"},
    "sport253": {"name": "Sky Sport 253", "group": "SPORT"},
    "sport254": {"name": "Sky Sport 254", "group": "SPORT"},
    "sport255": {"name": "Sky Sport 255", "group": "SPORT"},
    "sport256": {"name": "Sky Sport 256", "group": "SPORT"},
    "sport257": {"name": "Sky Sport 257", "group": "SPORT"},
    "sport258": {"name": "Sky Sport 258", "group": "SPORT"},
    "sport259": {"name": "Sky Sport 259", "group": "SPORT"},
    "arena": {"name": "Sky Sport Arena", "group": "SPORT"},
    "sportmax": {"name": "Sky Sport Max", "group": "SPORT"},
    "sportmix": {"name": "Sky Sport Mix", "group": "SPORT"},
    "legend": {"name": "Sky Sport Legend", "group": "SPORT"},
    "f1": {"name": "Sky Sport F1", "group": "SPORT"},
    "motogp": {"name": "Sky Sport MotoGP", "group": "SPORT"},
    "tennis": {"name": "Sky Sport Tennis", "group": "SPORT"},
    "basket": {"name": "Sky Sport Basket", "group": "SPORT"},
    "golf": {"name": "Sky Sport Golf", "group": "SPORT"},
    
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
# FUNZIONI
# ============================================================

def log(msg):
    """Stampa con timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def refresh_access_token():
    """Rinnova il token di accesso Google Drive"""
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
    """Decodifica la chiave CK per i canali Sky"""
    try:
        pad = "=" * (4 - len(ck) % 4) if len(ck) % 4 else ""
        return base64.b64decode(ck + pad).decode("utf-8")
    except Exception:
        return None

def get_dazn_channels():
    """Estrae STREAM_URL e STREAM_CLEAR_KEYS per DAZN 1-10"""
    channels = []
    
    for i in range(1, 11):
        try:
            log(f"📺 DAZN {i}...")
            
            url = f"{BASE_URL}daznch/player_event.php?event={i}"
            res = requests.get(url, headers=HEADERS, timeout=15)
            
            if res.status_code != 200:
                log(f"  ❌ HTTP {res.status_code}")
                continue
            
            html = res.text
            
            # Cerca STREAM_URL
            mpd_match = re.search(r'STREAM_URL\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not mpd_match:
                log("  ❌ STREAM_URL non trovato")
                continue
            
            # Cerca STREAM_CLEAR_KEYS
            keys_match = re.search(r'STREAM_CLEAR_KEYS\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not keys_match:
                log("  ❌ STREAM_CLEAR_KEYS non trovato")
                continue
            
            mpd_url = mpd_match.group(1)
            clear_keys = keys_match.group(1)
            
            if ':' not in clear_keys:
                log("  ❌ Formato KEY non valido")
                continue
            
            kid, key = clear_keys.split(':')
            
            log(f"  ✅ OK")
            
            channels.append({
                "name": f"DAZN {i}",
                "kid": kid.lower(),
                "key": key.lower(),
                "mpd": mpd_url
            })
            
        except Exception as e:
            log(f"  ❌ ERRORE: {e}")
            continue
        
        time.sleep(1)
    
    return channels

def scrape_sky_channels():
    """Scraping dei canali Sky"""
    channels = []
    total = len(CHANNEL_MAP)
    
    log(f"📡 Scraping {total} canali Sky...")
    
    for i, (path, meta) in enumerate(CHANNEL_MAP.items(), 1):
        try:
            page_url = f"{BASE_URL}{path}.php"
            log(f"[{i}/{total}] 📡 {meta['name']}...")
            
            res = requests.get(page_url, headers=HEADERS, timeout=10)
            
            if res.status_code == 200:
                match = re.search(r'const\s+STREAM_URL\s*=\s*"([^"]+)"', res.text)
                if match:
                    raw_stream = match.group(1).replace(r"\/", "/")
                    clean_url = raw_stream.split("?")[0]
                    ck_match = re.search(r"ck=([^&]+)", raw_stream)
                    clear_key = decode_ck(ck_match.group(1)) if ck_match else None
                    
                    channels.append({
                        "name": meta["name"],
                        "group": meta["group"],
                        "url": clean_url,
                        "clear_key": clear_key,
                    })
                    log(f"  ✅ OK")
                else:
                    log(f"  ⚠️ Nessun flusso")
            else:
                log(f"  ❌ HTTP {res.status_code}")
                
        except Exception as e:
            log(f"  ❌ Errore: {e}")
        
        time.sleep(0.3)
    
    return channels

def generate_m3u(sky_channels, dazn_channels):
    """Genera il file M3U"""
    content = (
        "#EXTM3U"
        ' url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"\n'
    )
    
    group_map = {
        "SPORT": "SkySport",
        "CINEMA": "Film - Serie TV",
        "INTRATTENIMENTO": "SkyEntertainment",
        "DAZN": "DAZN",
    }
    
    # Ordine dei gruppi
    group_order = ["Film - Serie TV", "SkySport", "SkyEntertainment", "DAZN"]
    
    # Raggruppa i canali per gruppo
    by_group = {}
    for ch in sky_channels:
        grp = group_map.get(ch["group"], ch["group"])
        if grp not in by_group:
            by_group[grp] = []
        by_group[grp].append(ch)
    
    # Aggiungi DAZN
    if dazn_channels:
        if "DAZN" not in by_group:
            by_group["DAZN"] = []
        by_group["DAZN"].extend(dazn_channels)
    
    # Genera M3U seguendo l'ordine
    for grp in group_order:
        if grp not in by_group:
            continue
        for ch in by_group[grp]:
            # Determina il nome per tvg-id
            tvg_name = ch.get("name", "Canale")
            
            content += f'#EXTINF:-1 group-title="{grp}" tvg-id="{tvg_name}",{tvg_name}\n'
            
            # Gestione DRM per Sky
            if "clear_key" in ch and ch["clear_key"]:
                content += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
                content += f'#KODIPROP:inputstream.adaptive.license_key={ch["clear_key"]}\n'
            
            # Gestione DRM per DAZN
            if "kid" in ch and "key" in ch:
                content += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
                content += f'#KODIPROP:inputstream.adaptive.license_key={ch["kid"]}:{ch["key"]}\n'
            
            # URL dello stream
            url = ch.get("url") or ch.get("mpd")
            if url:
                content += f'{url}\n'
    
    return content

def upload_to_drive(content):
    """Carica il file su Google Drive (sovrascrive)"""
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
            log(f"📄 Risposta: {res.text[:200]}")
            return False
            
    except Exception as e:
        log(f"❌ Errore upload: {e}")
        return False

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 50)
    print("📺 Uaznao Scraper - 56 canali (9 Cinema + 21 Sport + 16 Intrattenimento + 10 DAZN)")
    print("=" * 50)
    log("Avvio...")
    
    # 1. Scraping Sky
    sky_channels = scrape_sky_channels()
    
    # 2. Scraping DAZN
    log("\n📡 Estrazione DAZN 1-10...")
    dazn_channels = get_dazn_channels()
    
    if not sky_channels and not dazn_channels:
        log("\n❌ Nessun canale trovato!")
        sys.exit(1)
    
    log(f"\n✅ SKY: {len(sky_channels)} canali")
    log(f"✅ DAZN: {len(dazn_channels)} canali")
    
    # 3. Genera M3U
    log("\n📝 Generazione skympd.m3u...")
    m3u_content = generate_m3u(sky_channels, dazn_channels)
    
    # 4. Salva localmente
    with open("skympd.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    log("📁 skympd.m3u salvato localmente")
    
    # 5. Upload su Drive
    log("\n☁️ Connessione a Google Drive...")
    if upload_to_drive(m3u_content):
        log("\n🎉 Operazione completata con successo!")
    else:
        log("\n❌ Operazione fallita!")
        sys.exit(1)

if __name__ == "__main__":
    main()