import base64
import re
import requests
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options

# Credenziali Google Drive
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
# CANALI SKY
# ============================================================
CHANNEL_MAP = {
    # SKY CINEMA
    "cinemaaction": {"name": "Sky Cinema Action", "group": "CINEMA"},
    "cinemacollection": {"name": "Sky Cinema Collection", "group": "CINEMA"},
    "cinemacomedy": {"name": "Sky Cinema Comedy", "group": "CINEMA"},
    "cinemadrama": {"name": "Sky Cinema Drama", "group": "CINEMA"},
    "cinemaromance": {"name": "Sky Cinema Romance", "group": "CINEMA"},
    "cinemastories": {"name": "Sky Cinema Stories", "group": "CINEMA"},
    "cinemasuspense": {"name": "Sky Cinema Suspense", "group": "CINEMA"},
    "cinema1": {"name": "Sky Cinema Uno", "group": "CINEMA"},
    "cinemafamily": {"name": "Sky Cinema Family", "group": "CINEMA"},
    # SKY SPORT
    "sport24": {"name": "Sky Sport 24", "group": "SPORT"},
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
    "basket": {"name": "Sky Sport Basket", "group": "SPORT"},
    "calcio": {"name": "Sky Sport Calcio", "group": "SPORT"},
    "f1": {"name": "Sky Sport F1", "group": "SPORT"},
    "golf": {"name": "Sky Sport Golf", "group": "SPORT"},
    "legend": {"name": "Sky Sport Legend", "group": "SPORT"},
    "sportmax": {"name": "Sky Sport Max", "group": "SPORT"},
    "sportmix": {"name": "Sky Sport Mix", "group": "SPORT"},
    "motogp": {"name": "Sky Sport MotoGP", "group": "SPORT"},
    "tennis": {"name": "Sky Sport Tennis", "group": "SPORT"},
    "sportuno": {"name": "Sky Sport Uno", "group": "SPORT"},
    # INTRATTENIMENTO
    "boomerang": {"name": "Boomerang", "group": "INTRATTENIMENTO"},
    "cartoonnetwork": {"name": "Cartoon Network", "group": "INTRATTENIMENTO"},
    "comedycentral": {"name": "Comedy Central", "group": "INTRATTENIMENTO"},
    "deakids": {"name": "DeAKids", "group": "INTRATTENIMENTO"},
    "nickeleodeon": {"name": "Nickelodeon", "group": "INTRATTENIMENTO"},
    "nickjunior": {"name": "Nick Jr", "group": "INTRATTENIMENTO"},
    "adventure": {"name": "Sky Adventure", "group": "INTRATTENIMENTO"},
    "arte": {"name": "Sky Arte", "group": "INTRATTENIMENTO"},
    "atlantic": {"name": "Sky Atlantic", "group": "INTRATTENIMENTO"},
    "crime": {"name": "Sky Crime", "group": "INTRATTENIMENTO"},
    "documentaries": {"name": "Sky Documentaries", "group": "INTRATTENIMENTO"},
    "nature": {"name": "Sky Nature", "group": "INTRATTENIMENTO"},
    "serie": {"name": "Sky Serie", "group": "INTRATTENIMENTO"},
    "uno": {"name": "Sky Uno", "group": "INTRATTENIMENTO"},
    "unoplus": {"name": "Sky Uno Plus", "group": "INTRATTENIMENTO"},
    "investigation": {"name": "Sky Investigation", "group": "INTRATTENIMENTO"},
}

# ============================================================
# DAZN 1-10 - ESTRAZIONE VOCI CON SELENIUM
# ============================================================

def get_dazn_channels():
    """Prende STREAM_URL e STREAM_CLEAR_KEYS per DAZN 1-10 via Selenium"""
    channels = []
    player_url = "https://uaznao.com/premium/canalitv/daznch/player_event.php?event="
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")
    
    driver = None
    
    for i in range(1, 11):
        try:
            print(f"📺 DAZN {i}...", end=" ")
            
            driver = webdriver.Edge(options=options)
            driver.set_page_load_timeout(30)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.get(f"{player_url}{i}")
            time.sleep(5)
            
            html = driver.page_source
            
            mpd_match = re.search(r'STREAM_URL\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not mpd_match:
                print("❌ STREAM_URL non trovato")
                driver.quit()
                continue
            
            keys_match = re.search(r'STREAM_CLEAR_KEYS\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not keys_match:
                print("❌ STREAM_CLEAR_KEYS non trovato")
                driver.quit()
                continue
            
            mpd_url = mpd_match.group(1)
            clear_keys = keys_match.group(1)
            
            if ':' not in clear_keys:
                print("❌ Formato KEY non valido")
                driver.quit()
                continue
            
            kid, key = clear_keys.split(':')
            
            print("✅ OK")
            
            channels.append({
                "name": f"DAZN {i}",
                "kid": kid.lower(),
                "key": key.lower(),
                "mpd": mpd_url
            })
            
            driver.quit()
            
        except Exception as e:
            print(f"❌ ERRORE: {e}")
            if driver:
                driver.quit()
            continue
        
        time.sleep(1)
    
    return channels


def refresh_access_token():
    global ACCESS_TOKEN
    try:
        res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
        )
        data = res.json()
        if "access_token" in data:
            ACCESS_TOKEN = data["access_token"]
            return True
    except Exception:
        pass
    return False


def decode_ck(ck):
    try:
        pad = "=" * (4 - len(ck) % 4) if len(ck) % 4 else ""
        return base64.b64decode(ck + pad).decode("utf-8")
    except Exception:
        return None


def generate_m3u(sky_channels, dazn_channels):
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
    
    # SKY
    for ch in sky_channels:
        grp = group_map.get(ch["group"], ch["group"])
        content += f'#EXTINF:-1 group-title="{grp}" tvg-id="{ch["name"]}",{ch["name"]}\n'
        if ch["clear_key"]:
            content += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
            content += f'#KODIPROP:inputstream.adaptive.license_key={ch["clear_key"]}\n'
        content += f'{ch["url"]}\n'
    
    # DAZN
    for ch in dazn_channels:
        content += f'#EXTINF:-1 group-title="DAZN" tvg-id="{ch["name"]}",{ch["name"]}\n'
        content += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
        content += f'#KODIPROP:inputstream.adaptive.license_key={ch["kid"]}:{ch["key"]}\n'
        content += f'{ch["mpd"]}\n'
    
    return content


def main():
    print("🔄 Avvio operazione...\n")
    
    # 1. Scraping SKY
    sky_channels = []
    print("📡 Scraping canali SKY...\n")
    total = len(CHANNEL_MAP)
    
    for i, (path, meta) in enumerate(CHANNEL_MAP.items(), 1):
        try:
            page_url = f"{BASE_URL}{path}.php"
            print(f"[{i}/{total}] 📡 {meta['name']}")
            
            res = requests.get(page_url, headers=HEADERS, timeout=10)
            
            if res.status_code == 200:
                match = re.search(r'const\s+STREAM_URL\s*=\s*"([^"]+)"', res.text)
                if match:
                    raw_stream = match.group(1).replace(r"\/", "/")
                    clean_url = raw_stream.split("?")[0]
                    ck_match = re.search(r"ck=([^&]+)", raw_stream)
                    clear_key = decode_ck(ck_match.group(1)) if ck_match else None
                    sky_channels.append({
                        "name": meta["name"],
                        "group": meta["group"],
                        "url": clean_url,
                        "clear_key": clear_key,
                    })
                    print(f"  ✅ OK")
                else:
                    print(f"  ⚠️ Nessun flusso")
            else:
                print(f"  ❌ Errore HTTP {res.status_code}")
                
        except Exception as e:
            print(f"  ❌ Errore: {e}")
        
        time.sleep(0.3)
    
    # 2. DAZN con Selenium
    print("\n📡 Estrazione DAZN 1-10 con Selenium...\n")
    dazn_channels = get_dazn_channels()
    
    if not sky_channels and not dazn_channels:
        print("\n❌ Nessun canale trovato!")
        return
    
    print(f"\n✅ SKY: {len(sky_channels)} canali")
    print(f"✅ DAZN: {len(dazn_channels)} canali")
    print("☁️ Connessione a Google Drive in corso...\n")
    
    m3u_content = generate_m3u(sky_channels, dazn_channels)
    
    if refresh_access_token():
        try:
            url = f"https://www.googleapis.com/upload/drive/v3/files/{DRIVE_FILE_ID}?uploadType=media"
            upload_headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "text/plain",
            }
            res = requests.patch(
                url, headers=upload_headers, data=m3u_content.encode("utf-8")
            )
            if res.status_code == 200:
                print("=" * 55)
                print("✅ skympd.m3u inviato con successo su Google Drive!")
                print("=" * 55)
            else:
                print(f"❌ Errore Google Drive: HTTP {res.status_code}")
        except Exception as e:
            print(f"❌ Errore durante l'upload: {e}")
    else:
        print("❌ Errore rinnovo token Google Drive.")


if __name__ == "__main__":
    main()
