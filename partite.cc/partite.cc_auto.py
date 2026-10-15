import asyncio
import os
import re
import socket
import sys
import traceback
from datetime import datetime
from playwright.async_api import async_playwright

# ═══════════════════════════════════════════════════════════════
#  CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════
EMAIL        = 'erciciola@yahoo.it'
PASSWORD     = 'franchino'

# ── NOMI FILE OUTPUT ──
OUTPUT_ITALY = 'partite.cc_italy.m3u'
OUTPUT_FULL  = 'partite.cc_full.m3u'

# ── VELOCITÀ ──
PARALLEL     = 6
WAIT_SEC     = 8
HARD_TIMEOUT = 15
DELAY_SEC    = 0.2
PAGE_TIMEOUT = 12000
HEADLESS     = True

# ── UA COMPLETO ──
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
      'AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/120.0.0.0 Safari/537.36')

HOST = 'www.partite.cc'
BASE = f'https://{HOST}'

# ── FILTRO ITALIA ──
ITALY_PATTERN = re.compile(r'-(ita|italia)(?:[/?#]|$)', re.IGNORECASE)
# ═══════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════════
def show_menu():
    os.system('cls' if os.name == 'nt' else 'clear')
    print()
    print("═══════════════════════════════")
    print("  A  Genera playlist Partite.cc ITALY")
    print("  B  Genera playlist Partite.cc FULL")
    print("  C  Esci")
    print("═══════════════════════════════")

    while True:
        scelta = input("Scelta: ").strip().lower()
        if scelta in ('a', 'b', 'c'):
            return scelta
        print("Inserisci A, B o C.")


def ask_return_to_menu():
    print()
    try:
        risposta = input("Premi INVIO per uscire, oppure 's' per tornare al menu: ").strip().lower()
    except EOFError:
        return False
    return risposta == 's'


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
#  LOGIN
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


# ═══════════════════════════════════════════════════════════════
#  ELENCO CANALI
# ═══════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════
#  ESTRAZIONE
# ═══════════════════════════════════════════════════════════════
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
            print(f"  ✅ [{n:02d}/{progress['total']}] {name}")
        else:
            async with lock:
                progress['ko'] += 1
                n = progress['ok'] + progress['ko']
            print(f"  ❌ [{n:02d}/{progress['total']}] {name}")

    except Exception as e:
        async with lock:
            progress['ko'] += 1
            n = progress['ok'] + progress['ko']
        print(f"  ⚠️  [{n:02d}/{progress['total']}] {name} ({type(e).__name__})")
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
        print(f"  ⏱️  [{n:02d}/{progress['total']}] {ch['name']} (timeout)")


# ═══════════════════════════════════════════════════════════════
#  RUN PLAYLIST
# ═══════════════════════════════════════════════════════════════
async def run_playlist(mode):
    """mode = 'italy' | 'full'"""
    output_file = OUTPUT_ITALY if mode == 'italy' else OUTPUT_FULL

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
        print(f"{'✅ Login OK' if ok else '⚠️  Login dubbio'}")

        channels_all = await get_channels(context)

        if mode == 'italy':
            channels = [c for c in channels_all if ITALY_PATTERN.search(c['url'])]
            print(f"🇮🇹 Canali italiani: {len(channels)} / {len(channels_all)} totali")
        else:
            channels = channels_all
            print(f"🌍 Canali totali: {len(channels)}")

        progress['total'] = len(channels)

        if not channels:
            print("❌ Nessun canale da elaborare.")
            await browser.close()
            return

        print(f"⚡ {PARALLEL} in parallelo, wait {WAIT_SEC}s, timeout {HARD_TIMEOUT}s\n")

        sem = asyncio.Semaphore(PARALLEL)

        async def worker(ch):
            async with sem:
                await extract_with_timeout(context, ch, results, lock, progress)
                if DELAY_SEC > 0:
                    await asyncio.sleep(DELAY_SEC)

        t0 = datetime.now()
        await asyncio.gather(*[worker(ch) for ch in channels])
        elapsed = (datetime.now() - t0).total_seconds()
        await browser.close()

    # ── SALVATAGGIO ──
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for name, url in results:
            f.write(f'#EXTINF:-1 group-title="Partitecc", {name}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={UA}\n')
            f.write(f'{url}\n')

    print(f"\n{'═'*55}")
    print(f"✨ Salvati {len(results)}/{progress['total']} stream in {elapsed:.1f}s")
    print(f"   OK: {progress['ok']}   KO: {progress['ko']}")
    print(f"   File: {os.path.abspath(output_file)}")
    print(f"{'═'*55}")


def safe_run(mode):
    try:
        asyncio.run(run_playlist(mode))
    except Exception:
        print("\n❌ ECCEZIONE FATALE:\n")
        print(traceback.format_exc())


# ═══════════════════════════════════════════════════════════════
#  AVVIO CON MENU IN LOOP
# ═══════════════════════════════════════════════════════════════
def main():
    if not RESOLVED_IPS:
        print(f"⚠️  Nessun IP IPv4 valido trovato per {HOST}")
        print("    Controlla la connessione e riprova.")
        return

    while True:
        scelta = show_menu()

        if scelta == 'a':
            print("\n🇮🇹  Generazione playlist ITALY...\n")
            safe_run('italy')
        elif scelta == 'b':
            print("\n🌍  Generazione playlist FULL...\n")
            safe_run('full')
        else:  # 'c'
            print("\n👋  Arrivederci!")
            return

        if not ask_return_to_menu():
            print("\n👋  Arrivederci!")
            return


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrotto dall'utente.")
    except Exception:
        print(traceback.format_exc())
