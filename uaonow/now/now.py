#!/usr/bin/env python3
"""
NOW TV Italia — extractor standalone (schema DAZN).

Niente Fire Stick a runtime:
  1) login da accounts.txt (email:password) → oauth + userToken
  2) POST ovp.nowtv.com/video/playouts/live  (SkyOTT HMAC)
  3) WVD locale → POST licenceAcquisitionUrl (challenge raw)
  4) manifests.json (formato SIUM) + now_playlist.m3u (MPD CDN diretto, niente proxy)

Uso:
  python now.py
  python now.py --channel BmyKaByQ78fi0eWcrCJDkr5U
  python now.py --service-key 1234
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote, unquote, urlparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_VENV_SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Lib", "site-packages")
if os.path.isdir(_VENV_SP):
    sys.path.insert(0, _VENV_SP)

def _patch_construct_if_needed() -> None:
    """construct 2.10: Const invertito; String rimosso (pymp4/pywidevine)."""
    import construct as _construct
    import construct.core as _core
    from construct import Const, Int8ub

    if not getattr(_construct, "String", None):
        class _LegacyString(_construct.Adapter):
            def __init__(self, length, encoding=None, padchar=b"\x00", paddir="right", trimdir="right"):
                super().__init__(_construct.Bytes(length))
                self._n = length
                self._enc = encoding
                self._pad = padchar if isinstance(padchar, (bytes, bytearray)) else str(padchar).encode("ascii")
                self._paddir = paddir
                self._trimdir = trimdir

            def _decode(self, obj, context, path):
                pad = self._pad[:1] or b"\x00"
                if self._paddir == "left":
                    obj = obj.lstrip(pad)
                elif self._paddir == "both":
                    obj = obj.strip(pad)
                else:
                    obj = obj.rstrip(pad)
                return obj.decode(self._enc) if self._enc else obj

            def _encode(self, obj, context, path):
                if self._enc and isinstance(obj, str):
                    obj = obj.encode(self._enc)
                if not isinstance(obj, (bytes, bytearray)):
                    obj = bytes(obj)
                n = self._n(context) if callable(self._n) else self._n
                pad = self._pad[:1] or b"\x00"
                if len(obj) > n:
                    obj = obj[:n] if self._trimdir == "right" else obj[-n:]
                extra = n - len(obj)
                if extra > 0:
                    if self._paddir == "left":
                        obj = pad * extra + obj
                    elif self._paddir == "both":
                        left = extra // 2
                        obj = pad * left + obj + pad * (extra - left)
                    else:
                        obj = obj + pad * extra
                return obj

        def _string(length, encoding=None, padchar=b"\x00", paddir="right", trimdir="right"):
            return _LegacyString(length, encoding, padchar, paddir, trimdir)

        _construct.String = _string
        _core.String = _string
        all_names = getattr(_construct, "__all__", None)
        if isinstance(all_names, list) and "String" not in all_names:
            all_names.append("String")

    def _needs_const_swap() -> bool:
        try:
            Const(Int8ub, 2)
            return False
        except TypeError:
            return True

    if _needs_const_swap():
        _orig_const = _construct.Const

        def _const_compat(*args, **kwargs):
            if len(args) >= 2 and hasattr(args[0], "parse") and not hasattr(args[1], "parse"):
                args = (args[1], args[0]) + args[2:]
            return _orig_const(*args, **kwargs)

        _construct.Const = _const_compat
        _core.Const = _const_compat


_patch_construct_if_needed()

try:
    from curl_cffi import requests as rq
    HAS_CFFI = True
except ImportError:
    import requests as rq
    HAS_CFFI = False

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

try:
    from pywidevine import PSSH, Cdm, Device
    HAS_WVD = True
except Exception as e:
    HAS_WVD = False
    PSSH = Cdm = Device = None  # type: ignore
    _WVD_IMPORT_ERR = e

SCRIPT = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(SCRIPT, "now_config.json")
TOK_PATH = os.path.join(SCRIPT, "now_tokens.json")
ACCOUNTS_FILE = os.path.join(SCRIPT, "accounts.txt")
EXTRACT_JSON = os.path.join(SCRIPT, "manifests.json")
PLAYLIST = os.path.join(SCRIPT, "now_playlist.m3u")
# group playlist → (provider, category) come SIUM/manifests.json
GROUP_META = {
    "NOW Sport": ("NOWTV SPORT", "sports"),
    "NOW Cinema": ("NOWTV CINEMA", "cinema"),
    "NOW Kids": ("NOWTV BAMBINI", "kids"),
    "NOW News": ("NOWTV INTRATTENIMENTI", "ENTERTAINMENT"),
    "NOW Intrattenimento": ("NOWTV INTRATTENIMENTI", "ENTERTAINMENT"),
}
MITM = "http://127.0.0.1:8081/flows"
MITM_TOKEN = "netflix"

WV_UUID = "edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"


def load_cfg() -> Dict[str, Any]:
    return json.loads(open(CFG_PATH, encoding="utf-8").read())


def load_tokens() -> Dict[str, Any]:
    if not os.path.exists(TOK_PATH):
        return {}
    return json.loads(open(TOK_PATH, encoding="utf-8").read())


def save_tokens(tok: Dict[str, Any]) -> None:
    tok["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    open(TOK_PATH, "w", encoding="utf-8").write(json.dumps(tok, indent=2) + "\n")


def session():
    if HAS_CFFI:
        return rq.Session(impersonate="chrome99_android")
    return rq.Session()


def skyott_headers(cfg: Dict[str, Any], extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {
        "accept": "application/json",
        "user-agent": (
            "Mozilla/5.0 (Linux; Android 11; Fire TV Stick Build/RQ3A.211001.001; wv) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/105.0.5195.79 "
            "Mobile Safari/537.36"
        ),
        "x-skyott-territory": "IT",
        "x-skyott-activeterritory": "IT",
        "x-skyott-provider": "NOWTV",
        "x-skyott-proposition": "NOWOTT",
        "x-skyott-platform": "ANDROIDTV",
        "x-skyott-device": "TV",
        "x-skyott-language": "it-IT",
        "x-skyott-client-version": "7.9.20",
    }
    h.update(cfg.get("headers") or {})
    if extra:
        h.update(extra)
    return h


def sky_signature(cfg: Dict[str, Any], method: str, url: str, headers: Dict[str, str], payload: str) -> Dict[str, str]:
    timestamp = int(time.time())
    path = urlparse(url).path
    text_headers = ""
    for key in sorted(headers.keys()):
        if key.lower().startswith("x-skyott"):
            text_headers += key.lower() + ": " + headers[key] + "\n"
    headers_md5 = hashlib.md5(text_headers.encode()).hexdigest()
    body = payload.encode("utf-8") if isinstance(payload, str) else payload
    payload_md5 = hashlib.md5(body).hexdigest()
    app_id = cfg.get("app_id") or "IE-NOWTV-ANDROID-v1"
    version = cfg.get("sig_version") or "1.0"
    to_hash = (
        f"{method}\n{path}\n\n{app_id}\n{version}\n{headers_md5}\n"
        f"{timestamp}\n{payload_md5}\n"
    )
    key = base64.b64decode(cfg["signature_key_b64"])
    signature = base64.b64encode(hmac.new(key, to_hash.encode("utf-8"), hashlib.sha1).digest()).decode()
    return {
        "x-sky-signature": (
            f'SkyOTT client="{app_id}",signature="{signature}",'
            f'timestamp="{timestamp}",version="{version}"'
        )
    }


def pkcs7_pad(data: bytes) -> bytes:
    p = padding.PKCS7(128).padder()
    return p.update(data) + p.finalize()


def pkcs7_unpad(data: bytes) -> bytes:
    u = padding.PKCS7(128).unpadder()
    return u.update(data) + u.finalize()


def aes_cbc_enc(key: bytes, iv: bytes, data: bytes) -> bytes:
    c = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return c.update(pkcs7_pad(data)) + c.finalize()


def aes_cbc_dec(key: bytes, iv: bytes, data: bytes) -> bytes:
    c = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    pt = c.update(data) + c.finalize()
    try:
        return pkcs7_unpad(pt)
    except Exception:
        return pt


def fri_wrap(plaintext: bytes, key: bytes, iv: Optional[bytes] = None) -> str:
    if iv is None:
        iv = os.urandom(16)
    ct = aes_cbc_enc(key, iv, plaintext)
    return iv.hex().upper() + quote(base64.b64encode(ct).decode(), safe="")


def fri_unwrap(field: str, key: bytes) -> bytes:
    iv = bytes.fromhex(field[:32])
    rest = unquote(field[32:])
    try:
        raw = base64.b64decode(rest)
    except Exception:
        raw = rest.encode("latin-1")
    return aes_cbc_dec(key, iv, raw)


def parse_mpd(text: str) -> Tuple[List[str], List[str]]:
    kids = [k.replace("-", "").lower() for k in re.findall(r'default_KID="([^"]+)"', text)]
    psshs: List[str] = []
    for m in re.finditer(
        r'schemeIdUri="urn:uuid:%s"[^>]*>.*?<cenc:pssh[^>]*>([^<]+)</cenc:pssh>' % WV_UUID,
        text,
        re.I | re.S,
    ):
        psshs.append(m.group(1).strip())
    if not psshs:
        psshs = [m.group(1).strip() for m in re.finditer(r"<cenc:pssh[^>]*>([^<]+)</cenc:pssh>", text)]
    return kids, psshs


def channel_id_from_mpd(url: str) -> Optional[str]:
    if "/channel(" not in url:
        return None
    return url.split("/channel(", 1)[1].split(")", 1)[0]


def cdn_user_key(url: str) -> List[bytes]:
    out: List[bytes] = []
    m = re.search(r"_u~([0-9a-fA-F]{32,64})", url)
    if m:
        hx = m.group(1)
        raw = bytes.fromhex(hx)
        if len(raw) >= 16:
            out.append(raw[:16])
        if len(raw) >= 32:
            out.append(raw[:32])
    return out


def latest_mpd_from_mitm() -> str:
    try:
        import urllib.request

        data = json.loads(
            urllib.request.urlopen(
                urllib.request.Request(MITM, headers={"Authorization": f"Bearer {MITM_TOKEN}"}),
                timeout=8,
            ).read()
        )
    except Exception:
        return ""
    url = ""
    for f in data:
        r = f.get("request") or {}
        host = r.get("pretty_host") or ""
        path = r.get("path") or ""
        if "master_" in path and ".mpd" in path and "lin-it" in host:
            url = r.get("pretty_url") or f"https://{host}{path}"
    return url


def ensure_device_id(tok: Dict[str, Any]) -> str:
    did = (tok.get("device_id") or "").strip()
    if not did:
        did = uuid.uuid4().hex
        tok["device_id"] = did
        save_tokens(tok)
    return did


def load_accounts(path: Optional[str] = None) -> List[Tuple[str, str]]:
    accounts_path = path or ACCOUNTS_FILE
    if not os.path.isfile(accounts_path):
        return []
    out: List[Tuple[str, str]] = []
    with open(accounts_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            email, password = line.split(":", 1)
            email, password = email.strip(), password.strip()
            if email and password:
                out.append((email, password))
    return out


def _account_label(email: str) -> str:
    return (email or "").split("@")[0] or "account"


def _user_token_fresh(tok: Dict[str, Any]) -> bool:
    if not (tok.get("user_token") or "").strip():
        return False
    exp = (tok.get("token_expiry") or "").strip()
    if not exp:
        return False
    try:
        dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp() > time.time() + 60
    except Exception:
        return False


def _siren_href(data: Dict[str, Any]) -> str:
    props = data.get("properties") or {}
    if props.get("href"):
        return str(props["href"])
    for link in data.get("links") or []:
        href = str(link.get("href") or "")
        if "oauth" in href or "authorize" in href:
            return href
    for link in data.get("links") or []:
        if link.get("href"):
            return str(link["href"])
    return ""


def _oauth_from_payload(data: Any, url: str = "") -> str:
    if isinstance(data, dict):
        props = data.get("properties") or {}
        for key in ("access_token", "accessToken", "token", "authToken"):
            val = props.get(key) or data.get(key)
            if val:
                return str(val)
    parsed = urlparse(url)
    qs = parse_qs(parsed.query) | parse_qs(parsed.fragment)
    for key in ("access_token", "accessToken", "token"):
        if qs.get(key):
            return qs[key][0]
    return ""


def now_rango_login(email: str, password: str) -> Tuple[str, Optional[str], str]:
    """POST Rango signin → oauth access_token. Come scripts/nowtv.py, territorio IT."""
    authorize = (
        "https://rango.id.nowtv.it/oauth/authorize/service/international"
        "?response_type=token&client_id=nowtv_tvclient"
        "&redirect_uri=nowtv://auth&api_id=oauth"
    )
    endpoints = [
        "https://rango.id.nowtv.it/signin/service/international",
        "https://rango.id.nowtv.com/signin/service/international",
    ]
    headers = {
        "accept": "application/vnd.siren+json",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://tv.clients.nowtv.com",
        "referer": "https://tv.clients.nowtv.com/",
        "user-agent": (
            "Mozilla/5.0 (Linux; Android 11; Fire TV Stick Build/RQ3A.211001.001; wv) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/105.0.5195.79 "
            "Mobile Safari/537.36"
        ),
        "x-skyott-territory": "IT",
        "x-skyott-activeterritory": "IT",
        "x-skyott-provider": "NOWTV",
        "x-skyott-proposition": "NOWOTT",
        "x-skyott-platform": "ANDROIDTV",
        "x-skyott-device": "TV",
    }
    payload = {
        "userIdentifier": email,
        "password": password,
        "rememberMe": "true",
    }
    s = session()
    last = "login fallito"
    for url in endpoints:
        try:
            r = s.post(
                url,
                headers=headers,
                params={"continuationUrl": authorize},
                data=payload,
                timeout=25,
            )
        except Exception as e:
            last = str(e)
            continue
        body = r.text or ""
        if r.status_code == 422 or "invalid.credentials" in body:
            return "FAIL", None, "credenziali"
        if r.status_code in (429,) or '"code":"289"' in body or '"code": 289' in body:
            last = f"Shape/F5 {r.status_code}"
            continue
        if not r.ok:
            last = f"HTTP {r.status_code}"
            continue
        try:
            data = r.json()
        except Exception:
            last = "risposta login non JSON"
            continue
        href = _siren_href(data)
        oauth = _oauth_from_payload(data, r.url or "")
        if not oauth and href:
            try:
                hop = s.get(href, headers=headers, timeout=25, allow_redirects=True)
            except Exception as e:
                last = str(e)
                continue
            try:
                hop_data = hop.json()
            except Exception:
                hop_data = {}
            loc = hop.headers.get("Location") or hop.headers.get("location") or ""
            oauth = (
                _oauth_from_payload(hop_data, hop.url or href)
                or _oauth_from_payload({}, loc)
                or _oauth_from_payload({}, href)
            )
        if oauth:
            return "SUCCESS", oauth, "ok"
        last = "oauth assente nella risposta Rango"
    return "BLOCKED", None, last


def oauth_to_usertoken(cfg: Dict[str, Any], tok: Dict[str, Any], oauth: str) -> str:
    did = ensure_device_id(tok)
    urls = [
        cfg.get("tokens_url") or "https://ovp.nowtv.com/auth/throttled/tokens",
        "https://ovp.nowtv.com/auth/tokens",
    ]
    body_obj = {
        "auth": {
            "authScheme": "OAUTH",
            "authToken": oauth,
            "provider": "NOWTV",
            "providerTerritory": "IT",
            "proposition": "NOWOTT",
        },
        "device": {
            "type": "TV",
            "platform": "ANDROIDTV",
            "id": did,
            "drmDeviceId": "UNKNOWN",
        },
    }
    payload = json.dumps(body_obj, separators=(",", ":"))
    s = session()
    for url in urls:
        headers = skyott_headers(
            cfg,
            {
                "accept": "application/vnd.tokens.v1+json",
                "content-type": "application/vnd.tokens.v1+json",
            },
        )
        headers.update(sky_signature(cfg, "POST", url, headers, payload))
        try:
            r = s.post(url, headers=headers, data=payload, timeout=25)
        except Exception as e:
            print("  tokens POST err", e)
            continue
        print(f"  tokens POST {r.status_code} {(r.text or '')[:120]}")
        if not r.ok:
            continue
        try:
            data = r.json()
        except Exception:
            continue
        ut = data.get("userToken") or ""
        if ut:
            tok["user_token"] = ut
            tok["oauth_token"] = oauth
            tok["token_expiry"] = str(data.get("tokenExpiryTime") or "")
            save_tokens(tok)
            print("  userToken ok")
            return ut
    return ""


def login_from_accounts(cfg: Dict[str, Any], tok: Dict[str, Any], accounts_path: Optional[str] = None) -> str:
    accounts_path = accounts_path or ACCOUNTS_FILE
    if not os.path.isfile(accounts_path):
        print(f"manca {accounts_path} — crea il file con righe email:password")
        return ""
    accounts = load_accounts(accounts_path)
    if not accounts:
        print(f"{accounts_path} è vuoto — metti un account NOW per riga (email:password)")
        return ""
    print(f"  login da accounts.txt ({len(accounts)} account)")
    for email, password in accounts:
        label = _account_label(email)
        print(f"  provo {label}...")
        status, oauth, detail = now_rango_login(email, password)
        if status != "SUCCESS" or not oauth:
            print(f"  {label}: {status} {detail}")
            continue
        tok["account"] = email
        ut = oauth_to_usertoken(cfg, tok, oauth)
        if ut:
            print(f"  login ok ({label})")
            return ut
        print(f"  {label}: oauth ok, userToken no")
    print("nessun account in accounts.txt ha prodotto un userToken")
    return ""


def refresh_user_token(cfg: Dict[str, Any], tok: Dict[str, Any], force: bool = False) -> str:
    if not force and _user_token_fresh(tok):
        return (tok.get("user_token") or "").strip()
    oauth = (tok.get("oauth_token") or "").strip()
    if oauth:
        ut = oauth_to_usertoken(cfg, tok, oauth)
        if ut:
            return ut
    return login_from_accounts(cfg, tok)


def playback_body(service_key: Optional[str] = None, provider_variant_id: Optional[str] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "device": {
            "capabilities": [
                {
                    "protection": "WIDEVINE",
                    "container": "ISOBMFF",
                    "transport": "DASH",
                    "acodec": "AAC",
                    "vcodec": "H264",
                }
            ],
            "maxVideoFormat": "HD",
            "model": "AFTMM",
            "hdcpEnabled": True,
            "robustness": "HW_SECURE_ALL",
            "supportedColourSpaces": ["SDR"],
        },
        "client": {"thirdParties": ["FREEWHEEL"], "timeShiftEnabled": "false"},
        "parentalControlPin": "null",
        "personaParentalControlRating": "19",
    }
    if service_key:
        body["serviceKey"] = service_key
    if provider_variant_id:
        body["providerVariantId"] = provider_variant_id
    return body


def request_playout(cfg: Dict[str, Any], tok: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
    url = cfg.get("playout_live") or "https://ovp.nowtv.com/video/playouts/live"
    user = refresh_user_token(cfg, tok)
    payload = json.dumps(body, separators=(",", ":"))
    headers = skyott_headers(
        cfg,
        {
            "accept": "application/vnd.playlive.v1+json",
            "content-type": "application/vnd.playlive.v1+json",
        },
    )
    if user:
        headers["x-skyott-usertoken"] = user
    headers.update(sky_signature(cfg, "POST", url, headers, payload))
    s = session()
    r = s.post(url, headers=headers, data=payload, timeout=25)
    print(f"  playout POST {r.status_code} {str(r.text)[:220]}")
    if (not r.ok) and ("OVP_00006" in (r.text or "") or "Invalid OTT user token" in (r.text or "")):
        user = refresh_user_token(cfg, tok, force=True)
        if user:
            headers["x-skyott-usertoken"] = user
            headers.update(sky_signature(cfg, "POST", url, headers, payload))
            r = s.post(url, headers=headers, data=payload, timeout=25)
            print(f"  playout retry {r.status_code} {str(r.text)[:220]}")
    if not r.ok:
        return {"error": r.text, "status": r.status_code}
    try:
        return r.json()
    except Exception:
        return {"error": r.text}


def collect_mpd_url(cfg: Dict[str, Any], channel: Optional[str]) -> str:
    url = latest_mpd_from_mitm()
    if url and (not channel or channel in url):
        return url
    if os.path.exists(EXTRACT_JSON):
        data = json.loads(open(EXTRACT_JSON, encoding="utf-8").read())
        # formato SIUM: {id: {manifest_url, name, ...}}
        if isinstance(data, dict) and "channels" not in data:
            for cid, ch in data.items():
                if not isinstance(ch, dict):
                    continue
                if channel and cid != channel and ch.get("name") != channel:
                    continue
                if ch.get("manifest_url") or ch.get("manifest"):
                    return ch.get("manifest_url") or ch.get("manifest") or ""
        for ch in data.get("channels") or []:
            if channel and ch.get("id") != channel and ch.get("name") != channel:
                continue
            if ch.get("manifest") or ch.get("manifest_url"):
                return ch.get("manifest") or ch.get("manifest_url") or ""
    return ""


def wrap_keys(cfg: Dict[str, Any], mpd_url: str, tok: Dict[str, Any]) -> List[bytes]:
    keys: List[bytes] = []
    manual = (cfg.get("fri_wrap_key") or "").strip()
    if manual:
        if re.fullmatch(r"[0-9a-fA-F]+", manual) and len(manual) in (32, 64):
            keys.append(bytes.fromhex(manual))
        else:
            keys.append(manual.encode("utf-8")[:16].ljust(16, b"\0"))
    keys.extend(cdn_user_key(mpd_url))
    oauth = (tok.get("oauth_token") or "").strip()
    if re.fullmatch(r"[0-9a-fA-F]{32,64}", oauth):
        raw = bytes.fromhex(oauth)
        keys.append(raw[:16])
        if len(raw) >= 32:
            keys.append(raw[:32])
    seen = set()
    out = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def load_wvd(cfg: Dict[str, Any]) -> str:
    """Risolve il .wvd: config → fallback → primo *.wvd nella cartella dello script."""
    candidates = [
        os.path.join(SCRIPT, cfg.get("wvd") or ""),
        os.path.join(SCRIPT, cfg.get("wvd_fallback") or "WVD.wvd"),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    # auto: qualunque .wvd presente (es. dopo cambio device)
    try:
        found = sorted(
            f
            for f in os.listdir(SCRIPT)
            if f.lower().endswith(".wvd") and os.path.isfile(os.path.join(SCRIPT, f))
        )
    except OSError:
        found = []
    if found:
        return os.path.join(SCRIPT, found[0])
    raise FileNotFoundError(
        f"manca WVD in {SCRIPT} (config={cfg.get('wvd')!r}, nessun *.wvd trovato)"
    )


def keys_from_cdm(cdm: Cdm, sess) -> List[Tuple[str, str]]:
    out = []
    for k in cdm.get_keys(sess):
        if getattr(k, "type", "") in ("SIGNING",):
            continue
        kid = (
            k.kid.hex
            if hasattr(k.kid, "hex") and isinstance(k.kid.hex, str)
            else (k.kid.hex() if hasattr(k.kid, "hex") else str(k.kid).replace("-", ""))
        )
        key = k.key.hex() if callable(getattr(k.key, "hex", None)) else getattr(k.key, "hex", str(k.key))
        out.append((kid.lower().replace("-", ""), key.lower()))
    return out


def get_content_keys(
    cfg: Dict[str, Any],
    pssh_b64: str,
    mpd_url: str,
    tok: Dict[str, Any],
    license_url: Optional[str] = None,
) -> List[Tuple[str, str]]:
    if not HAS_WVD:
        raise RuntimeError(f"pywidevine non importabile: {_WVD_IMPORT_ERR}")
    wvd = load_wvd(cfg)
    device = Device.load(wvd)
    cdm = Cdm.from_device(device)
    sess = cdm.open()
    challenge = cdm.get_license_challenge(sess, PSSH(pssh_b64), privacy_mode=False)
    print(f"  WVD {os.path.basename(wvd)} challenge {len(challenge)} B")

    headers = skyott_headers(cfg)
    # 1) official acquirelicense from playout (come DAZN / SkyOtt Kodi)
    if license_url:
        try:
            raw_h = {
                "user-agent": headers.get("user-agent", ""),
                "accept": "*/*",
                "content-type": "application/octet-stream",
            }
            r = session().post(license_url, headers=raw_h, data=challenge, timeout=25)
            print(f"  acquirelicense POST {r.status_code} {str(r.text)[:140]}")
            if r.ok and r.content and r.content[:1] != b"{":
                cdm.parse_license(sess, r.content)
                found = keys_from_cdm(cdm, sess)
                if found:
                    cdm.close(sess)
                    return found
        except Exception as e:
            print("  acquirelicense err", e)

    la = cfg.get("license_url") or "https://ovp.nowtv.com/fri/v4/a"
    try:
        raw_h = {**headers, "content-type": "application/octet-stream"}
        r = session().post(la, headers=raw_h, data=challenge, timeout=25)
        print(f"  raw FRI POST {r.status_code} {str(r.text)[:120]}")
        if r.ok and r.content and r.content[:1] != b"{":
            cdm.parse_license(sess, r.content)
            found = keys_from_cdm(cdm, sess)
            if found:
                cdm.close(sess)
                return found
    except Exception as e:
        print("  raw POST err", e)

    payload = json.dumps(
        {
            "provider": "NOWTV",
            "territory": "IT",
            "proposition": "NOWOTT",
            "platform": "ANDROIDTV",
            "device": "TV",
            "md": "widevine",
        }
    ).encode()

    for key in wrap_keys(cfg, mpd_url, tok):
        print(f"  FRI wrap key {key.hex()[:32]}… ({len(key) * 8} bit)")
        body = {"a": fri_wrap(challenge, key), "p": fri_wrap(payload, key), "md": "symmetric"}
        try:
            r = session().post(la, headers=headers, json=body, timeout=25)
        except Exception as e:
            print("  FRI err", e)
            continue
        print(f"  FRI POST {r.status_code} {str(r.text)[:160]}")
        if not r.ok:
            continue
        try:
            j = r.json()
        except Exception:
            continue
        if j.get("a") != "Success" or not j.get("b"):
            continue
        try:
            lic = fri_unwrap(j["b"], key)
            print(f"  unwrap license {len(lic)} B")
            cdm.parse_license(sess, lic)
            found = keys_from_cdm(cdm, sess)
            if found:
                cdm.close(sess)
                return found
        except Exception as e:
            print("  unwrap/parse", e)

    cdm.close(sess)
    return []


def extract_entry(
    *,
    name: str,
    channel_id: str,
    manifest: str,
    kid: str = "",
    key: Optional[str] = None,
    service_key: str = "",
    group: str = "",
) -> Dict[str, Any]:
    kid = kid or ""
    key = key or ""
    return {
        "name": name or channel_id,
        "id": channel_id,
        "service_key": service_key,
        "group": group,
        "manifest": manifest,
        "kid": kid,
        "key": key,
        "kid_key": f"{kid}:{key}" if kid and key else "",
    }


def _channel_to_sium_entry(c: Dict[str, Any], updated_at: str) -> Dict[str, Any]:
    """Entry allineata a SIUM/manifests.json (indent 4, stessi campi)."""
    group = c.get("group") or "NOW Intrattenimento"
    provider, category = GROUP_META.get(group, ("NOWTV INTRATTENIMENTI", "ENTERTAINMENT"))
    if c.get("provider"):
        provider = str(c["provider"])
    if c.get("category"):
        category = str(c["category"])
    kid_key = c.get("kid_key") or ""
    if not kid_key and c.get("kid") and c.get("key"):
        kid_key = f"{c['kid']}:{c['key']}"
    keys = list(c.get("keys") or [])
    if kid_key and kid_key not in keys:
        keys = [kid_key] + keys
    manifest = c.get("manifest_url") or c.get("manifest") or c.get("mpd") or ""
    status = c.get("status") or ("ok" if manifest and keys else ("ok" if manifest else "error"))
    return {
        "name": c.get("name") or c.get("id") or "",
        "provider": provider,
        "category": category,
        "serviceKey": str(c.get("serviceKey") or c.get("service_key") or ""),
        "keys": keys,
        "updated_at": updated_at,
        "manifest_url": manifest,
        "status": status,
    }


def write_extract_json(channels: List[Dict[str, Any]], quiet: bool = False) -> None:
    """Scrive manifests.json come SIUM: oggetto {channelId: {...}}, indent=4."""
    updated_at = datetime.now().isoformat()
    out: Dict[str, Any] = {}
    for c in channels:
        cid = str(c.get("id") or "").strip()
        if not cid:
            continue
        out[cid] = _channel_to_sium_entry(c, updated_at)
    open(EXTRACT_JSON, "w", encoding="utf-8").write(
        json.dumps(out, indent=4, ensure_ascii=False) + "\n"
    )
    if not quiet:
        print(f"salvato {EXTRACT_JSON}")


def m3u_channel_lines(
    channel_id: str,
    name: str,
    group: str,
    mpd_url: str,
    kid: str,
    key: Optional[str],
) -> List[str]:
    lines = [
        f'#EXTINF:-1 tvg-id="{channel_id}" group-title="{group}",{name}',
        "#KODIPROP:inputstream=inputstream.adaptive",
        "#KODIPROP:inputstream.adaptive.manifest_type=mpd",
    ]
    if kid and key:
        lines.append("#KODIPROP:inputstream.adaptive.license_type=clearkey")
        lines.append(f"#KODIPROP:inputstream.adaptive.license_key={kid}:{key}")
    lines.append(mpd_url)
    return lines


def write_playlist(channels: List[Dict[str, Any]]) -> None:
    lines = ["#EXTM3U"]
    for c in channels:
        lines.extend(
            m3u_channel_lines(
                str(c.get("id") or ""),
                str(c.get("name") or c.get("id") or ""),
                str(c.get("group") or "NOW Italia"),
                str(c.get("manifest") or c.get("mpd") or ""),
                str(c.get("kid") or ""),
                c.get("key"),
            )
        )
    open(PLAYLIST, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"salvato {PLAYLIST}")


def write_outputs(
    channel_id: str,
    mpd_url: str,
    mpd_text: str,
    kid: str,
    key: Optional[str],
    cfg: Dict[str, Any],
    license_url: Optional[str] = None,
    name: str = "",
    service_key: str = "",
) -> None:
    del mpd_text, license_url, cfg
    entry = extract_entry(
        name=name or channel_id,
        channel_id=channel_id,
        manifest=mpd_url,
        kid=kid,
        key=key,
        service_key=service_key,
    )
    write_extract_json([entry])
    write_playlist([entry])


GUIDE_DISCOVERY_SEGMENTS = (
    "ENTERTAINMENT,HAYU,KIDS,MOVIES,NEWS,SHORTFORM,SPORTS,SPORTS_CORE,"
    "SPORTS_ESSENTIALS,SPORTS_EVENTS,SPORTS_EVENTS_EXCLUSIVE,SSN"
)
GUIDE_PLAYOUT_SEGMENTS = (
    "NEWS,SHORTFORM,SPORTS,SPORTS_BONUS,SPORTS_CORE,SPORTS_ESSENTIALS,"
    "SPORTS_EVENTS,SPORTS_EVENTS_EXCLUSIVE,SSN,SUPERSPORT,"
    "pkgcinema,pkgentertainment,pkgkids,pkgsport"
)
GUIDE_ACCOUNT_SEGMENTS = "DLOAD_USER,DOLBY,HD,NO_ADS,UHD"
SECTION_GROUPS = {
    "SPORTS": "NOW Sport",
    "CINEMA": "NOW Cinema",
    "KIDS": "NOW Kids",
    "NEWS": "NOW News",
    "ENTERTAINMENT": "NOW Intrattenimento",
}


def fetch_epg(cfg: Dict[str, Any], tok: Dict[str, Any]) -> List[Dict[str, Any]]:
    refresh_user_token(cfg, tok)
    start = time.strftime("%Y-%m-%dT%H:00Z", time.gmtime())
    url = "https://web.clients.nowtv.com/bff/channel_guide"
    params = {
        "startTime": start,
        "discovery_content_segments": GUIDE_DISCOVERY_SEGMENTS,
        "playout_content_segments": GUIDE_PLAYOUT_SEGMENTS,
        "account_segments": GUIDE_ACCOUNT_SEGMENTS,
    }
    headers = skyott_headers(cfg, {"accept": "application/json"})
    if tok.get("user_token"):
        headers["x-skyott-usertoken"] = tok["user_token"]
    headers.update(sky_signature(cfg, "GET", url, headers, ""))
    r = session().get(url, headers=headers, params=params, timeout=25)
    if not r.ok:
        print("EPG", r.status_code, str(r.text)[:160])
        return []
    data = r.json()
    out = []
    seen = set()
    for c in data.get("channels") or []:
        if (c.get("tileType") or "linearChannel") not in ("linearChannel", ""):
            continue
        sk = str(c.get("serviceKey") or "")
        if not sk or sk in seen:
            continue
        seen.add(sk)
        section = str(c.get("sectionNavigation") or "ENTERTAINMENT").upper()
        out.append(
            {
                "id": sk,
                "service_key": sk,
                "name": c.get("name") or c.get("channelTitle") or sk,
                "uuid": c.get("id"),
                "group": SECTION_GROUPS.get(section, "NOW Intrattenimento"),
            }
        )
    print(
        "EPG canali",
        len(out),
        " ".join(
            f"{g.split()[-1]}={sum(1 for x in out if x['group']==g)}"
            for g in SECTION_GROUPS.values()
        ),
    )
    return out


def extract_playout_mpd(data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    mpd = ""
    for ep in (data.get("asset") or {}).get("endpoints") or []:
        u = ep.get("url") or ""
        if u and (not mpd or "cmaf" in u.lower() or ".mpd" in u):
            mpd = u
    prot = data.get("protection") or {}
    return mpd, prot.get("licenceAcquisitionUrl")


def load_manifests() -> Dict[str, Any]:
    if not os.path.exists(EXTRACT_JSON):
        return {}
    try:
        data = json.loads(open(EXTRACT_JSON, encoding="utf-8").read())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def save_manifests(data: Dict[str, Any], quiet: bool = False) -> None:
    open(EXTRACT_JSON, "w", encoding="utf-8").write(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n"
    )
    if not quiet:
        print(f"salvato {EXTRACT_JSON} ({len(data)} canali)")


def _ensure_tok(cfg: Dict[str, Any], tok: Dict[str, Any]) -> None:
    if not (tok.get("user_token") or "").strip():
        login_from_accounts(cfg, tok)
        return
    try:
        refresh_user_token(cfg, tok)
    except Exception:
        login_from_accounts(cfg, tok)


def refresh_mpd_from_manifests(cfg: Dict[str, Any], tok: Dict[str, Any]) -> int:
    """Aggiorna solo manifest_url in manifests.json (chiavi intatte)."""
    data = load_manifests()
    if not data:
        print("manifests.json vuoto — niente da aggiornare")
        return 1
    _ensure_tok(cfg, tok)
    ok = fail = 0
    ts = datetime.now().isoformat()
    for cid, entry in list(data.items()):
        if not isinstance(entry, dict):
            continue
        sk = str(entry.get("serviceKey") or entry.get("service_key") or "").strip()
        if not sk:
            fail += 1
            continue
        print(f"— MPD {entry.get('name') or cid} sk={sk}")
        try:
            playout = request_playout(cfg, tok, playback_body(sk, None))
            mpd_url, _lic = extract_playout_mpd(playout)
        except Exception as e:
            print(f"  ERR {e}")
            entry["status"] = "error"
            fail += 1
            continue
        if not mpd_url:
            print("  no mpd")
            entry["status"] = "error"
            fail += 1
            continue
        entry["manifest_url"] = mpd_url
        entry["updated_at"] = ts
        entry["status"] = "ok"
        ok += 1
        data[cid] = entry
    save_manifests(data)
    print(f"refresh-mpd: {ok} ok / {fail} fail / {len(data)} totali")
    return 0 if ok else 1


def refresh_keys_from_manifests(cfg: Dict[str, Any], tok: Dict[str, Any]) -> int:
    """Riestrae chiavi ClearKey (+ MPD) per ogni canale in manifests.json."""
    data = load_manifests()
    if not data:
        print("manifests.json vuoto — niente da aggiornare")
        return 1
    _ensure_tok(cfg, tok)
    ok = fail = 0
    ts = datetime.now().isoformat()
    for cid, entry in list(data.items()):
        if not isinstance(entry, dict):
            continue
        sk = str(entry.get("serviceKey") or entry.get("service_key") or "").strip()
        name = entry.get("name") or cid
        if not sk:
            fail += 1
            continue
        print(f"— KEYS {name} sk={sk}")
        try:
            playout = request_playout(cfg, tok, playback_body(sk, None))
            mpd_url, license_url = extract_playout_mpd(playout)
        except Exception as e:
            print(f"  playout ERR {e}")
            entry["status"] = "error"
            fail += 1
            continue
        if not mpd_url:
            print("  no mpd")
            entry["status"] = "error"
            fail += 1
            continue
        entry["manifest_url"] = mpd_url
        try:
            r = session().get(mpd_url, headers=skyott_headers(cfg), timeout=20)
        except Exception as e:
            print(f"  MPD get ERR {e}")
            entry["status"] = "error"
            fail += 1
            continue
        if not r.ok:
            print(f"  MPD HTTP {r.status_code}")
            entry["status"] = "error"
            fail += 1
            continue
        kids, psshs = parse_mpd(r.text)
        kid = kids[0] if kids else ""
        key = None
        if psshs:
            try:
                found = get_content_keys(cfg, psshs[0], mpd_url, tok, license_url)
            except Exception as e:
                print(f"  license ERR {e}")
                found = []
            if found:
                if kid:
                    for k_id, k_key in found:
                        if k_id == kid:
                            key = k_key
                            break
                if not key:
                    kid, key = found[0]
                print(f"  KEY {kid}:{key}")
        if kid and key:
            entry["keys"] = [f"{kid}:{key}"]
            entry["status"] = "ok"
            ok += 1
        else:
            entry["status"] = "error"
            fail += 1
        entry["updated_at"] = ts
        data[cid] = entry
        save_manifests(data, quiet=True)
    save_manifests(data)
    print(f"refresh-keys: {ok} ok / {fail} fail / {len(data)} totali")
    return 0 if ok else 1


def run_daemon(cfg: Dict[str, Any], tok: Dict[str, Any]) -> int:
    """Servizio: MPD ogni 2h, chiavi ogni 24h."""
    mpd_every = 2 * 3600
    keys_every = 24 * 3600
    state_path = os.path.join(SCRIPT, "now_daemon_state.json")

    def _load_state() -> Dict[str, float]:
        try:
            return json.loads(open(state_path, encoding="utf-8").read())
        except Exception:
            return {}

    def _save_state(st: Dict[str, float]) -> None:
        open(state_path, "w", encoding="utf-8").write(json.dumps(st) + "\n")

    print(f"NOW daemon avviato — MPD ogni {mpd_every // 3600}h, KEYS ogni {keys_every // 3600}h")
    st = _load_state()
    # al boot: se mai fatto, fai subito
    now = time.time()
    if now - float(st.get("last_keys") or 0) >= keys_every:
        print("=== refresh-keys (startup/due) ===")
        try:
            refresh_keys_from_manifests(cfg, tok)
            st["last_keys"] = time.time()
            st["last_mpd"] = st["last_keys"]
            _save_state(st)
        except Exception as e:
            print("refresh-keys ERR", e)
    elif now - float(st.get("last_mpd") or 0) >= mpd_every:
        print("=== refresh-mpd (startup/due) ===")
        try:
            refresh_mpd_from_manifests(cfg, tok)
            st["last_mpd"] = time.time()
            _save_state(st)
        except Exception as e:
            print("refresh-mpd ERR", e)

    while True:
        now = time.time()
        next_mpd = float(st.get("last_mpd") or 0) + mpd_every
        next_keys = float(st.get("last_keys") or 0) + keys_every
        wake = min(next_mpd, next_keys)
        sleep_s = max(30.0, wake - now)
        print(f"sleep {int(sleep_s)}s (next mpd in {int(next_mpd - now)}s, keys in {int(next_keys - now)}s)")
        time.sleep(sleep_s)
        now = time.time()
        tok = load_tokens()
        if now >= float(st.get("last_keys") or 0) + keys_every:
            print("=== refresh-keys ===")
            try:
                refresh_keys_from_manifests(cfg, tok)
                st["last_keys"] = time.time()
                st["last_mpd"] = st["last_keys"]
                _save_state(st)
            except Exception as e:
                print("refresh-keys ERR", e)
            continue
        if now >= float(st.get("last_mpd") or 0) + mpd_every:
            print("=== refresh-mpd ===")
            try:
                refresh_mpd_from_manifests(cfg, tok)
                st["last_mpd"] = time.time()
                _save_state(st)
            except Exception as e:
                print("refresh-mpd ERR", e)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="NOW extractor standalone (no stick)")
    ap.add_argument("--channel", default="", help="channel id CDN opzionale")
    ap.add_argument("--service-key", default="", help="serviceKey live OVP")
    ap.add_argument("--variant", default="", help="providerVariantId")
    ap.add_argument("--all", action="store_true", help="tutti i canali live dall'EPG")
    ap.add_argument("--login", action="store_true", help="solo login da accounts.txt e salva i token")
    ap.add_argument("--manifest-json", action="store_true", help="stampa JSON ManifestUrl per --service-key (compat SIUM)")
    ap.add_argument("--refresh-mpd", action="store_true", help="aggiorna solo MPD da manifests.json")
    ap.add_argument("--refresh-keys", action="store_true", help="riestrae chiavi (+MPD) da manifests.json")
    ap.add_argument("--daemon", action="store_true", help="loop: MPD ogni 2h, chiavi ogni 24h")
    ap.add_argument("--accounts", default="", help="path accounts.txt (email:password)")
    args = ap.parse_args()
    cfg = load_cfg()
    tok = load_tokens()
    if args.daemon:
        print("NOW daemon — token + playout + WVD")
        return run_daemon(cfg, tok)
    if args.refresh_mpd:
        print("NOW refresh-mpd")
        return refresh_mpd_from_manifests(cfg, tok)
    if args.refresh_keys:
        print("NOW refresh-keys")
        return refresh_keys_from_manifests(cfg, tok)
    if args.manifest_json:
        if not args.service_key:
            print(json.dumps({"error": "serviceKey required"}))
            return 2
        tok = load_tokens()
        cfg = load_cfg()
        # silenzioso: niente log su stdout (solo JSON)
        import builtins as _bi
        _real_print = _bi.print
        def _quiet_print(*a, **k):
            if k.get("file") is sys.stderr:
                _real_print(*a, **k)
        _bi.print = _quiet_print
        try:
            if not (tok.get("user_token") or "").strip():
                login_from_accounts(cfg, tok)
            else:
                try:
                    refresh_user_token(cfg, tok)
                except Exception:
                    login_from_accounts(cfg, tok)
            data = request_playout(cfg, tok, playback_body(args.service_key, args.variant or None))
            mpd_url, _lic = extract_playout_mpd(data)
        finally:
            _bi.print = _real_print
        if not mpd_url:
            err = data.get("error") or data.get("description") or "no mpd"
            print(json.dumps({"error": err}))
            return 2
        print(json.dumps({"ManifestUrl": mpd_url}, indent=2))
        return 0
    print("NOW standalone — token + playout + WVD, nessuna stick richiesta")
    if args.login:
        ut = login_from_accounts(cfg, tok, args.accounts or None)
        return 0 if ut else 2

    if args.all or (not args.channel and not args.service_key and not args.variant):
        epg = fetch_epg(cfg, tok)
        catalog = []
        for ch in epg:
            sk = ch["service_key"]
            name = ch["name"]
            group = ch.get("group") or "NOW Intrattenimento"
            print("—", name, "sk", sk, group)
            data = request_playout(cfg, tok, playback_body(sk, None))
            mpd_url, license_url = extract_playout_mpd(data)
            if not mpd_url:
                continue
            r = session().get(mpd_url, headers=skyott_headers(cfg), timeout=20)
            if not r.ok:
                print("  MPD", r.status_code)
                continue
            kids, psshs = parse_mpd(r.text)
            kid = kids[0] if kids else ""
            key = None
            if psshs:
                try:
                    found = get_content_keys(cfg, psshs[0], mpd_url, tok, license_url)
                except Exception as e:
                    print("  license", e)
                    found = []
                if found:
                    if kid:
                        for k_id, k_key in found:
                            if k_id == kid:
                                key = k_key
                                break
                    if not key:
                        kid, key = found[0]
                    print(f"  KEY {kid}:{key}")
            cid = channel_id_from_mpd(mpd_url) or sk
            entry = extract_entry(
                name=name,
                channel_id=cid,
                manifest=mpd_url,
                kid=kid,
                key=key,
                service_key=sk,
                group=group,
            )
            catalog.append(entry)
            write_extract_json(catalog, quiet=True)
        write_extract_json(catalog)
        write_playlist(catalog)
        keyed = sum(1 for c in catalog if c.get("key"))
        print(f"playlist {PLAYLIST}  ({keyed}/{len(catalog)} chiavi, MPD diretto)")
        return 0 if keyed else 2

    license_url = None
    mpd_url = ""
    service_key = args.service_key or None
    variant = args.variant or None
    if not variant and args.channel and args.channel.startswith("R_"):
        variant = args.channel

    if service_key or variant:
        print("playout", service_key or variant)
        data = request_playout(cfg, tok, playback_body(service_key, variant))
        mpd_url, license_url = extract_playout_mpd(data)
    else:
        # prova token refresh comunque (serve dopo, senza stick)
        try:
            refresh_user_token(cfg, tok)
        except Exception as e:
            print("token", e)
        mpd_url = collect_mpd_url(cfg, args.channel or None)

    if not mpd_url:
        print("Nessun MPD. Avvia un live una volta oppure passa --service-key / --variant.")
        return 1

    cid = channel_id_from_mpd(mpd_url) or args.channel or service_key or variant or "live"
    print("canale", cid)
    print("mpd", mpd_url[:140])
    headers = skyott_headers(cfg)
    r = session().get(mpd_url, headers=headers, timeout=20)
    if not r.ok:
        print("MPD HTTP", r.status_code)
        return 1
    text = r.text
    kids, psshs = parse_mpd(text)
    print("KID", kids[:3], "PSSH", len(psshs), "LA", (license_url or "")[:80])
    if not psshs:
        print("nessun PSSH Widevine")
        return 1
    try:
        found = get_content_keys(cfg, psshs[0], mpd_url, tok, license_url)
    except Exception as e:
        print("license err", e)
        found = []
    kid = kids[0] if kids else ""
    key = None
    if found:
        if kid:
            for k_id, k_key in found:
                if k_id == kid:
                    key = k_key
                    break
        if not key:
            kid, key = found[0]
        print(f"KEY {kid}:{key}")
    else:
        print("nessuna content key ancora.")
    write_outputs(
        cid,
        mpd_url,
        text,
        kid,
        key,
        cfg,
        license_url,
        name=cid,
        service_key=service_key or "",
    )
    return 0 if key else 2


if __name__ == "__main__":
    raise SystemExit(main())

