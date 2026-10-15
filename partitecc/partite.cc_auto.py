import asyncio
import hashlib
import os
import re
import socket
import sys
import traceback
from datetime import datetime
from playwright.async_api import async_playwright
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ═══════════════════════════════════════════════════════════════
#  CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════
EMAIL        = 'erciciola@yahoo.it'
PASSWORD     = 'franchino'

OUTPUT_FILE  = 'partite.cc_italy.m3u'

# Google Drive
DRIVE_FILE_ID = '1H1dE3rnPqyVAVxgpm9qJ7mESqGXkYriC'
TOKEN_FILE    = 'token.json'
CLIENT_SECRET = 'client_secret.json'

# Scraper
PARALLEL     = 6
WAIT_SEC     = 8
HARD_TIMEOUT = 15
DELAY_SEC    = 0.2
PAGE_TIMEOUT = 12000
HEADLESS     = True

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
      'AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/120.0.0.0 Safari/537.36')

HOST = 'www.partite.cc'
BASE = f'https://{HOST}'

ITALY_PATTERN = re.compile(r'-(ita|italia)(?:[/?#]|$)', re.IGNORECASE)
# ═══════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
#  RISOLUZIONE IPv4
# ═══════════════════════════════════════════════════════════════
DNS_BLACKLIST = {'1.1.1.1', '1.0.0.1', '8.8.8.8', '8.8.4.4',
                 '9.9.9.9', '208.67.222.222', '208.67.220.220',
                 '127.0.0.1', '0.0.0.0'}

def is_valid_site_ip(ip):
    if ip in DNS_BLACKLIST:
        return False
    if ip.startswith('127.') or ip.startswith('0.'):
        return False
    if ip.startswith('10.') or ip.startswith('192.168.'):
        return False
    if ip.startswith('172.'):
        try:
            if 16 <= int(ip.split('.')[1]) <= 31:
                return False
        except Exception:
            pass
    return True


def resolve_ipv4(host):
    ips = []
    try:
        import subprocess
        for dns in ('1.1.1.1', '8.8.8.8'):
            try:
                out = subprocess.check_output(
                    ['nslookup', '-type=A', host, dns],
                    stderr=subprocess.DEVNULL, timeout=4,
                ).decode('utf-8', errors='ignore')
                for m in re.finditer(r'Addresses?:\s+((?:\d{1,3}\.){3}\d{1,3})', out):
                    ip = m.group(1)
                    if is_valid_site_ip(ip) and ip not in ips:
                        ips.append(ip)
                for m in re.finditer(r'^Address:\s+((?:\d{1,3}\.){3}\d{1,3})', out, re.M):
                    ip = m.group(1)
                    if is_valid_site_ip(ip) and ip not in ips:
                        ips.append(ip)
                if ips:
                    break
            except Exception:
                continue
    except Exception:
        pass

    if not ips:
        try:
            infos = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
            for _, _, _, _, addr in infos:
                if is_valid_site_ip(addr[0]) and addr[0] not in ips:
                    ips.append(addr[0])
        except Exception:
            pass
    return ips


RESOLVED_IPS = resolve_ipv4(HOST)


# ═══════════════════════════════════════════════════════════════
#  FIX REGIONE
# ═══════════════════════════════════════════════════════════════
def fix_url_region(url):
    m = re.search(r'[?&]ark_r=([^&]+)', url)
    if not m:
        return url
    region = m.group(1)
    return re.sub(
        r'^https?://[^.]+\.streamhostingcdn\.top',
        f'https://{region}.streamhostingcdn.top',
        url,
    )


# ═══════════════════════════════════════════════════════════════
#  SCRAPER
# ═══════════════════════════════════════════════════════════════
async def do_login(context):
    page = await context.new_page()
    try:
        await page.goto(f'{BASE}/login', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(1200)

        for sel in ['input[name="username"]', 'input[name="email"]', 'input[type="text"]']:
            try:
                await page.fill(sel, EMAIL, timeout=3000)
                break
            except Exception:
                continue

        for sel in ['input[name="password"]', 'input[type="password"]']:
            try:
                await page.fill(sel, PASSWORD, timeout=3000)
                break
            except Exception:
                continue

        clicked = False
        for sel in ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Accedi")']:
            try:
                await page.click(sel, timeout=3000)
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            await page.keyboard.press('Enter')

        await page.wait_for_timeout(2200)
        cookies = await context.cookies()
        names = [c['name'] for c in cookies]
        return any('ark' in n or 'session' in n or 'token' in n for n in names)
    finally:
        await page.close()


async def get_channels(context):
    page = await context.new_page()
    try:
        await page.goto(f'{BASE}/channels', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(1800)
        channels = await page.evaluate('''() => {
            const out = [];
            document.querySelectorAll('.chp-card').forEach(c => {
                const a = c.querySelector('.chp-b');
                const n = c.querySelector('.chp-n');
                if (a && n) out.push({url: a.href, name: n.textContent.trim()});
            });
            return out;
        }''')
        return channels
    finally:
        await page.close()


async def extract_one(context, ch, results, lock, progress):
    name = ch['name']
    url  = ch['url']

    page = await context.new_page()

    captured    = []
    response_ok = []

    def on_request(req):
        try:
            u = req.url
            if '.m3u8' in u and 'token=' in u:
                m = re.search(r'token=([^&]*)', u)
                if m and m.group(1) and u not in captured:
                    captured.append(u)
        except Exception:
            pass

    def on_response(resp):
        try:
            u = resp.url
            if '.m3u8' in u and 'token=' in u and resp.status == 200:
                m = re.search(r'token=([^&]*)', u)
                if m and m.group(1) and u not in response_ok:
                    response_ok.append(u)
        except Exception:
            pass

    page.on('request', on_request)
    page.on('response', on_response)

    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=PAGE_TIMEOUT)

        waited_ms = 0
        while waited_ms < WAIT_SEC * 1000:
            if response_ok:
                break
            if captured:
                await page.wait_for_timeout(400)
                break
            await page.wait_for_timeout(200)
            waited_ms += 200

        chosen = response_ok[0] if response_ok else (captured[0] if captured else None)

        if chosen:
            fixed = fix_url_region(chosen)
            async with lock:
                results.append((name, fixed))
                progress['ok'] += 1
                n = progress['ok'] + progress['ko']
            print(f"  OK  [{n:02d}/{progress['total']}] {name}")
        else:
            async with lock:
                progress['ko'] += 1
                n = progress['ok'] + progress['ko']
            print(f"  XX  [{n:02d}/{progress['total']}] {name}")

    except Exception as e:
        async with lock:
            progress['ko'] += 1
            n = progress['ok'] + progress['ko']
        print(f"  !!  [{n:02d}/{progress['total']}] {name} ({type(e).__name__})")
    finally:
        try:
            await page.close()
        except Exception:
            pass


async def extract_with_timeout(context, ch, results, lock, progress):
    try:
        await asyncio.wait_for(
            extract_one(context, ch, results, lock, progress),
            timeout=HARD_TIMEOUT
        )
    except asyncio.TimeoutError:
        async with lock:
            progress['ko'] += 1
            n = progress['ok'] + progress['ko']
        print(f"  T!  [{n:02d}/{progress['total']}] {ch['name']} (timeout)")


async def run_scraper():
    results  = []
    lock     = asyncio.Lock()
    progress = {'ok': 0, 'ko': 0, 'total': 0}

    async with async_playwright() as p:
        host_rules = ','.join(f'MAP {HOST} {ip}' for ip in RESOLVED_IPS)
        launch_args = [
            '--disable-ipv6',
            '--disable-features=UseDnsHttpsSvcb',
            f'--host-resolver-rules={host_rules}',
        ]

        browser = await p.chromium.launch(headless=HEADLESS, args=launch_args)
        context = await browser.new_context(
            user_agent=UA,
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True,
        )

        ok = await do_login(context)
        print(f"{'Login OK' if ok else 'Login DUBBIO'}")

        channels_all = await get_channels(context)
        channels = [c for c in channels_all if ITALY_PATTERN.search(c['url'])]
        print(f"Canali italiani: {len(channels)} / {len(channels_all)} totali")

        progress['total'] = len(channels)

        if not channels:
            print("Nessun canale da elaborare.")
            await browser.close()
            return []

        sem = asyncio.Semaphore(PARALLEL)

        async def worker(ch):
            async with sem:
                await extract_with_timeout(context, ch, results, lock, progress)
                if DELAY_SEC > 0:
                    await asyncio.sleep(DELAY_SEC)

        await asyncio.gather(*[worker(ch) for ch in channels])
        await browser.close()

    return results


# ═══════════════════════════════════════════════════════════════
#  SALVATAGGIO M3U
# ═══════════════════════════════════════════════════════════════
def save_m3u(results, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for name, url in results:
            f.write(f'#EXTINF:-1 group-title="Partitecc", {name}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={UA}\n')
            f.write(f'{url}\n')


def file_hash(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


# ═══════════════════════════════════════════════════════════════
#  GOOGLE DRIVE
# ═══════════════════════════════════════════════════════════════
def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


def drive_file_hash(service, file_id):
    """Scarica il file da Drive e ne calcola l'hash SHA256."""
    try:
        request = service.files().get_media(fileId=file_id)
        content = request.execute()
        return hashlib.sha256(content).hexdigest()
    except Exception as e:
        print(f"  (impossibile leggere da Drive: {e})")
        return None


def upload_to_drive(service, file_id, local_path):
    media = MediaFileUpload(local_path, mimetype='audio/x-mpegurl', resumable=False)
    service.files().update(fileId=file_id, media_body=media).execute()


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════
async def main():
    print("=" * 50)
    print(f" Partite.cc scraper - ITALY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    if not RESOLVED_IPS:
        print("Nessun IP IPv4 valido trovato.")
        return

    # ── 1. Scraper ──
    results = await run_scraper()

    if not results:
        print("Nessun risultato. Stop.")
        return

    # ── 2. Salva M3U locale ──
    save_m3u(results, OUTPUT_FILE)
    local_hash = file_hash(OUTPUT_FILE)
    print(f"\nFile salvato: {OUTPUT_FILE} ({len(results)} canali)")
    print(f"Hash locale:  {local_hash[:16]}...")

    # ── 3. Confronta con la versione su Drive ──
    print("\nControllo se il file su Drive e' cambiato...")
    service = get_drive_service()
    remote_hash = drive_file_hash(service, DRIVE_FILE_ID)

    if remote_hash and remote_hash == local_hash:
        print("Contenuto IDENTICO. Nessun upload necessario.")
        return

    print("Contenuto DIVERSO (o file assente). Carico su Drive...")

    # ── 4. Upload ──
    upload_to_drive(service, DRIVE_FILE_ID, OUTPUT_FILE)
    print("Upload completato!")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception:
        print("\nERRORE FATALE:\n")
        print(traceback.format_exc())
    input("\nPremi INVIO per uscire...")
