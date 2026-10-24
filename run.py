import requests as rq
import os
import re
import sys
import time
import base64
import threading
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import mmh3
    HAS_MMH3 = True
except ImportError:
    HAS_MMH3 = False

################################
## Author : Tyr3X             ##
################################

# Please don't remove author name

def get_results_dir():
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Results')
    os.makedirs(results_dir, exist_ok=True)
    return results_dir


def admin():
    output_file = os.path.join(get_results_dir(), 'admin.result.txt')
    page = []
    error = []
    e = input(f"[+] Enter url ( ex : https://google.com ) : ")
    f = open("db/db1.txt", "r")

    b = f.readlines()


    for v in b:
        v = v.replace("\n", "")
        url = e + "/" + v
        req = rq.get(url)
        if req.status_code != 404 and req.status_code != 401:
            if req.content == "Page not Found":
                error.append(url)
                pass
            else:
                page.append(url)
                with open(output_file, "a", encoding="utf-8") as result:
                    result.write(url + "\n")
        else:
            error.append(url)
            pass
        print(end='\r[*] Page Found : %s - Page Not Found : %s'%(
                str(len(page)),
                str(len(error))
              ),
              flush=True
             )    
    print(f"\n\nsaved : {output_file}")
               
def dirs():
    output_file = os.path.join(get_results_dir(), 'dir.result.txt')
    page = []
    error = []
    link = input(f"[+] Enter url ( ex : https://google.com ) : ")
    f = open("db/db2.txt","r")
    f1 = f.readlines()

    for i in f1: 
        i = i.replace("\n", "")
        url = link + "/" + i
        req = rq.get(url)
        if req.status_code != 401 and req.status_code != 404:
            if req.content == "Page not Found":
                error.append(url)
                pass
            else:
                page.append(url)
                with open(output_file, "a", encoding="utf-8") as result:
                    result.write(url + "\n")
        else:
            error.append(url)
            pass          
        print(end='\r[*] Page Found : %s - Page Not Found : %s'%(
                str(len(page)),
                str(len(error))
              ),
              flush=True
             )    
    print(f"\n\nsaved : {output_file}")

def domain():
    output_file = os.path.join(get_results_dir(), 'domain.result.txt')
    page = []
    error = []
    x = input(f"[+] Enter url ( ex : google.com ) : ")
    c = open("db/db3.txt", "r")
    f1 = c.readlines()
    
    for i in f1:
        i = i.replace("\n", "")
        url = i + "." + x
        req = rq.get(url)
        if req.status_code != 404 and req.status_code != 401:
            if req.content == "Page not Found":
                error.append(url)
                pass
            else:
                page.append(url)
                with open(output_file, "a", encoding="utf-8") as result:
                    result.write(url + "\n")
        else:
            error.append(url)
            pass
        print(end='\r[*] Page Found : %s - Page Not Found : %s'%(
                str(len(page)),
                str(len(error))
              ),
              flush=True
             )  
    print(f"\n\nsaved : {output_file}")
        


TIMEOUT     = 10
BATCH_SIZE  = 1_000  # Optimal batch size
MAX_THREADS = 500
RETRY_COUNT = 2

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CMS_OUTPUT_FILES = {
    "wordpress":  "good_wordpress.txt",
    "joomla":     "good_joomla.txt",
    "laravel":    "good_laravel.txt",
    "prestashop": "good_prestashop.txt",
    "drupal":     "good_drupal.txt",
    "magento":    "good_magento.txt",
    "opencart":   "good_opencart.txt",
    "other":      "other.txt",  # Sites with no CMS detected
}

# ── Favicon mmh3 hashes per CMS ────────────────────────────
FAVICON_HASHES = {
    "wordpress": {},
    "joomla": {290818842, -1507021389},
    "laravel": {},
    "prestashop": {1975780388, -1215547960},
    "drupal": {1191453214, -1950415971, 1340275924},
    "magento": {-1073349348, 174241529},
    "opencart": {-1073349348, -1066729021, 2008371659},
}

STRICT_MIN_STRONG = 2
STRICT_MODE = False


_tls = threading.local()

def get_session() -> requests.Session:
    if not hasattr(_tls, "session"):
        s = requests.Session()
        s.verify = False
        s.mount("http://", requests.adapters.HTTPAdapter(
            pool_connections=1, pool_maxsize=1, max_retries=0))
        s.mount("https://", requests.adapters.HTTPAdapter(
            pool_connections=1, pool_maxsize=1, max_retries=0))
        _tls.session = s
    return _tls.session


def normalize_url(raw: str) -> str:
    raw = raw.strip().split("#")[0].strip()
    if not raw:
        return ""
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    try:
        parsed = urlparse(raw)
        if not parsed.netloc:
            return ""
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return ""

def count_lines(filepath: str) -> int:
    try:
        count = 0
        buf = bytearray(1 << 20)
        with open(filepath, "rb") as f:
            while True:
                n = f.readinto(buf)
                if not n:
                    break
                count += buf[:n].count(b'\n')
        return count
    except Exception:
        return 0

def stream_urls(filepath: str):
    seen = set()
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                url = normalize_url(line)
                if url and url not in seen:
                    seen.add(url)
                    yield url
    except Exception as e:
        print(f"\n[!] Error reading file: {e}")
        return

# ── HTTP helpers dengan error handling ─────────────────────
def _get(session, url, allow_redirects=True, stream=False):
    for attempt in range(RETRY_COUNT):
        try:
            return session.get(
                url, headers=HEADERS, timeout=TIMEOUT,
                allow_redirects=allow_redirects, stream=stream,
            )
        except requests.exceptions.Timeout:
            if attempt == RETRY_COUNT - 1:
                return None
            time.sleep(0.5)
        except requests.exceptions.RequestException:
            return None
        except Exception:
            return None
    return None

def _head(session, url, allow_redirects=False):
    try:
        return session.head(
            url, headers=HEADERS, timeout=TIMEOUT,
            allow_redirects=allow_redirects,
        )
    except Exception:
        return None

def _fetch(session, url, max_bytes=200_000):
    r = _get(session, url)
    if r is None:
        return None, b""
    try:
        content = r.content[:max_bytes] if r.content else b""
    except Exception:
        content = b""
    return r, content

# ── Favicon mmh3 hashing ───────────────────────────────────
def compute_favicon_hash(session, base_url):
    if not HAS_MMH3:
        return None, 0
    r = _get(session, base_url + "/favicon.ico")
    if r is None or r.status_code != 200:
        return None, 0
    try:
        content = r.content
        if not content or len(content) < 50:
            return None, 0
        b64 = base64.encodebytes(content)
        h = mmh3.hash(b64)
        return h, len(content)
    except Exception:
        return None, 0

def favicon_match(cms: str, fav_hash):
    if fav_hash is None:
        return False
    hashes = FAVICON_HASHES.get(cms, set())
    return fav_hash in hashes

# ══════════════════════════════════════════════════════════
#  DETEKTOR PER CMS
# ══════════════════════════════════════════════════════════

def detect_wordpress(session, base):
    evidence = []
    strong = 0
    weak = 0
    version = None

    try:
        # 1) wp-json REST API (definitive strong)
        r = _get(session, base + "/wp-json/")
        if r is not None and r.status_code == 200:
            ctype = r.headers.get("Content-Type", "").lower()
            if "json" in ctype:
                try:
                    data = r.json()
                    if isinstance(data, dict) and "namespaces" in data and "name" in data:
                        strong += 1
                        evidence.append("wp-json-api")
                except Exception:
                    pass

        # 2) Link header with api.w.org (strong)
        r2 = _head(session, base + "/")
        if r2 is not None:
            link_hdr = r2.headers.get("Link", "")
            if "api.w.org" in link_hdr or "/wp-json/" in link_hdr:
                strong += 1
                evidence.append("link-header-wp-json")

            # X-Pingback with xmlrpc.php (strong)
            pingback = r2.headers.get("X-Pingback", "").lower()
            if "xmlrpc.php" in pingback:
                strong += 1
                evidence.append("x-pingback-xmlrpc")

        # 3) wp-login.php form (strong)
        r3 = _get(session, base + "/wp-login.php")
        if r3 is not None and r3.status_code == 200:
            body = r3.content[:120_000].lower()
            if b'name="log"' in body and b'name="pwd"' in body and b'wp-submit' in body:
                strong += 1
                evidence.append("wp-login-form")

        # 4) xmlrpc.php endpoint (strong)
        r5 = _head(session, base + "/xmlrpc.php")
        if r5 is not None and r5.status_code == 405:  # Method Not Allowed
            strong += 1
            evidence.append("xmlrpc-405")
        elif r5 is not None and r5.status_code == 200:
            ctype = r5.headers.get("Content-Type", "").lower()
            if "xml" in ctype:
                strong += 1
                evidence.append("xmlrpc-200-xml")

        # 5) HTML body analysis
        r4, html = _fetch(session, base + "/")
        if html:
            # Meta generator (strong)
            m = re.search(rb'<meta[^>]+name=["\']generator["\'][^>]+content=["\']WordPress\s*([0-9.]+)',
                          html, re.I)
            if m:
                version = m.group(1).decode()
                strong += 1
                evidence.append(f"generator-v{version}")

            h = html.lower()

            # wp-content paths (weak - many sites use this naming)
            if b"wp-content/themes/" in h or b"wp-content/plugins/" in h:
                weak += 1
                evidence.append("wp-content-paths")

            # wp-includes (weak)
            if b"wp-includes/" in h:
                weak += 1
                evidence.append("wp-includes-path")

        # 6) Favicon match (strong)
        if HAS_MMH3:
            fh, _ = compute_favicon_hash(session, base)
            if favicon_match("wordpress", fh):
                strong += 1
                evidence.append(f"favicon-mmh3({fh})")
    except Exception:
        pass

    return _finalize(strong, weak, evidence, version)

def detect_joomla(session, base):
    evidence = []
    strong = 0
    weak = 0
    version = None

    try:
        # 1) Joomla manifest file (definitive strong)
        r = _get(session, base + "/administrator/manifests/files/joomla.xml")
        if r is not None and r.status_code == 200:
            body = r.content[:80_000]
            if b"<extension" in body and b"joomla" in body.lower():
                strong += 1
                evidence.append("joomla.xml-manifest")
                m = re.search(rb"<version>([0-9.]+)</version>", body)
                if m:
                    version = m.group(1).decode()

        # 2) Language XML file (strong indicator)
        if strong == 0:
            r2 = _get(session, base + "/language/en-GB/en-GB.xml")
            if r2 is not None and r2.status_code == 200:
                content = r2.content[:5000]
                if b"<metafile" in content and b"joomla" in content.lower():
                    strong += 1
                    evidence.append("language-en-GB-xml")

        # 3) HTML body analysis
        r3, html = _fetch(session, base + "/")
        if html:
            # Meta generator (strong)
            m = re.search(rb'<meta[^>]+name=["\']generator["\'][^>]+content=["\']Joomla!?\s*([0-9.]*)',
                          html, re.I)
            if m:
                strong += 1
                evidence.append("generator")
                if m.group(1):
                    version = m.group(1).decode()

            h = html.lower()

            # /components/com_* (Joomla specific - strong if multiple)
            com_count = h.count(b"/components/com_")
            if com_count >= 2:
                strong += 1
                evidence.append(f"components-com-multiple({com_count})")
            elif com_count == 1:
                weak += 1
                evidence.append("components-com-single")

            # /modules/mod_* (Joomla modules - weak)
            if b"/modules/mod_" in h:
                weak += 1
                evidence.append("modules-mod")

            # Joomla JavaScript framework markers (weak)
            if b"joomla(" in h or b"joomla.JText" in h:
                weak += 1
                evidence.append("joomla-js-framework")

        # 4) Favicon match (strong)
        if HAS_MMH3:
            fh, _ = compute_favicon_hash(session, base)
            if favicon_match("joomla", fh):
                strong += 1
                evidence.append(f"favicon-mmh3({fh})")
    except Exception:
        pass

    return _finalize(strong, weak, evidence, version)

def detect_laravel(session, base):
    evidence = []
    strong = 0
    weak = 0
    version = None

    try:
        # 1) Cookies (strong if both present)
        r, html = _fetch(session, base + "/")

        if r is not None:
            cookie_names = " ".join(r.cookies.keys()).lower()
            set_cookie = r.headers.get("Set-Cookie", "").lower()

            has_laravel_session = "laravel_session" in cookie_names or "laravel_session" in set_cookie
            has_xsrf = "xsrf-token" in cookie_names or "xsrf-token" in set_cookie

            if has_laravel_session:
                strong += 1
                evidence.append("laravel_session-cookie")

            if has_xsrf:
                weak += 1
                evidence.append("xsrf-token-cookie")

        # 2) HTML body analysis
        if html:
            h = html.lower()

            # CSRF meta token (weak - many frameworks use this)
            if b'name="csrf-token"' in h:
                weak += 1
                evidence.append("csrf-meta")

            # /vendor/laravel path (strong)
            if b"/vendor/laravel" in h:
                strong += 1
                evidence.append("vendor/laravel-path")

        # 3) Laravel-specific endpoints
        for probe in ("/_ignition/health-check", "/telescope/requests"):
            rr = _get(session, base + probe)
            if rr is None:
                continue
            body = rr.content[:30_000].lower()
            if rr.status_code in (200, 401, 403, 500):
                if b"laravel" in body and (b"ignition" in body or b"telescope" in body):
                    strong += 1
                    evidence.append(f"laravel-{probe.strip('/').split('/')[0]}")
                    break

        # 4) Favicon match (strong)
        if HAS_MMH3:
            fh, _ = compute_favicon_hash(session, base)
            if favicon_match("laravel", fh):
                strong += 1
                evidence.append(f"favicon-mmh3({fh})")
    except Exception:
        pass

    return _finalize(strong, weak, evidence, version)

def detect_prestashop(session, base):
    evidence = []
    strong = 0
    weak = 0
    version = None

    try:
        # 1) Cookie (strong indicator)
        r, html = _fetch(session, base + "/")

        if r is not None:
            cookie_names = " ".join(r.cookies.keys()).lower()
            set_cookie = r.headers.get("Set-Cookie", "").lower()
            if "prestashop-" in cookie_names or "prestashop-" in set_cookie:
                strong += 1
                evidence.append("prestashop-cookie")

        # 2) HTML body analysis
        if html:
            # Meta generator (strong)
            m = re.search(rb'<meta[^>]+name=["\']generator["\'][^>]+content=["\']PrestaShop\s*([0-9.]*)',
                          html, re.I)
            if m:
                strong += 1
                evidence.append("generator")
                if m.group(1):
                    version = m.group(1).decode()

            h = html.lower()

            # PrestaShop JavaScript var (strong)
            if b"var prestashop = {" in h or b"prestashop = {" in h:
                strong += 1
                evidence.append("prestashop-js-var")

            # /themes/ + /modules/ combo (weak)
            if b"/themes/" in h and b"/modules/" in h:
                weak += 1
                evidence.append("themes-modules-paths")

            # Product page indicators (weak)
            if b"id_product" in h and b"add-to-cart" in h:
                weak += 1
                evidence.append("product-id-cart")

        # 3) Favicon match (strong)
        if HAS_MMH3:
            fh, _ = compute_favicon_hash(session, base)
            if favicon_match("prestashop", fh):
                strong += 1
                evidence.append(f"favicon-mmh3({fh})")
    except Exception:
        pass

    return _finalize(strong, weak, evidence, version)

def detect_drupal(session, base):
    evidence = []
    strong = 0
    weak = 0
    version = None

    try:
        # 1) X-Generator header (definitive)
        r = _head(session, base + "/")
        if r is not None:
            xgen = r.headers.get("X-Generator", "").lower()
            if "drupal" in xgen and ("drupal/" in xgen or re.search(r"\bdrupal\s+\d", xgen)):
                strong += 1
                evidence.append("x-generator")
                m = re.search(r"drupal\s*([0-9.]+)", xgen)
                if m:
                    version = m.group(1)

        # 2) /core/misc/drupal.js (file path unique to Drupal, strong)
        r2 = _head(session, base + "/core/misc/drupal.js")
        if r2 is not None and r2.status_code == 200:
            strong += 1
            evidence.append("core/misc/drupal.js")

        # 3) CHANGELOG.txt + "Drupal" keyword (strong if found)
        if strong == 0:
            r3 = _get(session, base + "/CHANGELOG.txt")
            if r3 is not None and r3.status_code == 200:
                content = r3.content[:20_000]
                if b"Drupal" in content and b"Released" in content:
                    strong += 1
                    evidence.append("CHANGELOG.txt")
                    m = re.search(rb"Drupal\s+([0-9.]+)", content[:5000])
                    if m:
                        version = m.group(1).decode()

        # 4) HTML body analysis
        r4, html = _fetch(session, base + "/")
        if html:
            # Meta generator (strong)
            m = re.search(rb'<meta[^>]+name=["\']generator["\'][^>]+content=["\']Drupal\s*([0-9.]*)',
                          html, re.I)
            if m:
                strong += 1
                evidence.append("generator")
                if m.group(1):
                    version = m.group(1).decode()

            h = html.lower()

            # data-drupal-* attributes (strong - very Drupal specific)
            if b"data-drupal-" in h:
                strong += 1
                evidence.append("data-drupal-attributes")

            # drupal.js + drupal-settings-json (strong combo)
            if b"drupal.settings = {" in h or b"drupalSettings" in h:
                strong += 1
                evidence.append("drupal-settings-object")

            # /sites/default/files/ (weak - could be generic)
            if b"/sites/default/files/" in h:
                weak += 1
                evidence.append("sites-default-files")

            # /sites/all/modules/ (weak but Drupal-ish)
            if b"/sites/all/modules/" in h or b"/sites/all/themes/" in h:
                weak += 1
                evidence.append("sites-all-modules")

            # Generic drupal word in JS (weak - could be name coincidence)
            if b"drupal" in h and (b"drupal = {" in h or b"drupal.behaviors" in h):
                weak += 1
                evidence.append("drupal-js-object")

        # 5) Favicon match (strong)
        if HAS_MMH3:
            fh, _ = compute_favicon_hash(session, base)
            if favicon_match("drupal", fh):
                strong += 1
                evidence.append(f"favicon-mmh3({fh})")
    except Exception:
        pass

    return _finalize(strong, weak, evidence, version)

def detect_magento(session, base):
    evidence = []
    strong = 0
    weak = 0
    version = None

    try:
        # 1) Cookie (strong indicator)
        r, html = _fetch(session, base + "/")

        if r is not None:
            cookie_names = " ".join(r.cookies.keys()).lower()
            set_cookie = r.headers.get("Set-Cookie", "").lower()
            if "frontend=" in cookie_names or "frontend=" in set_cookie:
                strong += 1
                evidence.append("frontend-cookie")

        # 2) HTML body analysis
        if html:
            # Meta generator (strong)
            m = re.search(rb'<meta[^>]+name=["\']generator["\'][^>]+content=["\']Magento\s*([0-9.]*)',
                          html, re.I)
            if m:
                strong += 1
                evidence.append("generator")
                if m.group(1):
                    version = m.group(1).decode()

            h = html.lower()

            # /pub/static/ (strong - Magento 2 specific)
            if b"/pub/static/" in h:
                strong += 1
                evidence.append("pub-static-path")

            # Mage JS init (strong)
            if b"data-mage-init" in h:
                strong += 1
                evidence.append("data-mage-init")

            # /skin/frontend/ (weak - older Magento)
            if b"/skin/frontend/" in h:
                weak += 1
                evidence.append("skin-frontend-path")

        # 3) magento_version endpoint (strong)
        if strong == 0:
            rv = _get(session, base + "/magento_version")
            if rv is not None and rv.status_code == 200:
                if b"magento" in rv.content[:200].lower():
                    strong += 1
                    evidence.append("magento_version-endpoint")

        # 4) Favicon match (strong)
        if HAS_MMH3:
            fh, _ = compute_favicon_hash(session, base)
            if favicon_match("magento", fh):
                strong += 1
                evidence.append(f"favicon-mmh3({fh})")
    except Exception:
        pass

    return _finalize(strong, weak, evidence, version)

def detect_opencart(session, base):
    evidence = []
    strong = 0
    weak = 0
    version = None

    try:
        # 1) Cookie (strong indicator)
        r, html = _fetch(session, base + "/")

        if r is not None:
            cookie_names = " ".join(r.cookies.keys()).lower()
            set_cookie = r.headers.get("Set-Cookie", "").lower()
            if "ocsessid" in cookie_names or "ocsessid" in set_cookie:
                strong += 1
                evidence.append("ocsessid-cookie")

        # 2) HTML body analysis
        if html:
            # Meta generator (strong)
            m = re.search(rb'<meta[^>]+name=["\']generator["\'][^>]+content=["\']OpenCart\s*([0-9.]*)',
                          html, re.I)
            if m:
                strong += 1
                evidence.append("generator")
                if m.group(1):
                    version = m.group(1).decode()

            h = html.lower()

            # index.php?route= (strong - OpenCart URL pattern)
            if b"index.php?route=" in h:
                strong += 1
                evidence.append("route-param")

            # /catalog/view/theme/ (weak)
            if b"/catalog/view/theme/" in h:
                weak += 1
                evidence.append("catalog-view-theme")

            # /catalog/model/ or /catalog/controller/ (weak)
            if b"/catalog/model/" in h or b"/catalog/controller/" in h:
                weak += 1
                evidence.append("catalog-structure")

        # 3) Favicon match (strong)
        if HAS_MMH3:
            fh, _ = compute_favicon_hash(session, base)
            if favicon_match("opencart", fh):
                strong += 1
                evidence.append(f"favicon-mmh3({fh})")
    except Exception:
        pass

    return _finalize(strong, weak, evidence, version)


def _finalize(strong, weak, evidence, version):
    """
    Validasi: WRITE only jika HIGH confidence
    - HIGH: strong >= 2 OR (strong >= 1 AND weak >= 1)
    - MEDIUM: strong >= 1 (tidak di-write)
    - LOW: weak >= 2 only (skip)
    """

    if strong >= 2:
        conf = "high"
        matched = True
    elif strong >= 1 and weak >= 1:
        conf = "high"
        matched = True
    elif strong >= 1:
        conf = "medium"
        matched = False  # Too risky - skip medium confidence
    else:
        conf = "low"
        matched = False

    return {
        "match": matched,
        "version": version,
        "evidence": evidence,
        "confidence": conf,
        "strong": strong,
        "weak": weak,
    }


DETECTORS = {
    "wordpress":  detect_wordpress,
    "joomla":     detect_joomla,
    "laravel":    detect_laravel,
    "prestashop": detect_prestashop,
    "drupal":     detect_drupal,
    "magento":    detect_magento,
    "opencart":   detect_opencart,
}
DETECT_ORDER = ["wordpress", "joomla", "laravel",
                "prestashop", "drupal", "magento", "opencart"]

def detect_all(base_url: str) -> list:
    session = get_session()
    results = []
    for name in DETECT_ORDER:
        try:
            r = DETECTORS[name](session, base_url)
        except Exception:
            continue
        if r["match"]:
            results.append({
                "cms": name,
                "version": r["version"],
                "evidence": r["evidence"],
                "confidence": r["confidence"],
                "strong": r["strong"],
                "weak": r["weak"],
            })
    return results


class OutputWriter:
    def __init__(self, output_dir=None):
        if output_dir is None:
            output_dir = get_results_dir()
        os.makedirs(output_dir, exist_ok=True)
        self.lock = threading.Lock()
        self.handles = {}
        self.written = {}  # Track written URLs per CMS

        # Load existing URLs to prevent duplicates
        for cms, fname in CMS_OUTPUT_FILES.items():
            path = os.path.join(output_dir, fname)
            self.written[cms] = set()

            # Read existing URLs
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for line in f:
                            url = line.strip()
                            if url:
                                self.written[cms].add(url)
                except Exception:
                    pass

            # Open in APPEND mode
            self.handles[cms] = open(path, "a", encoding="utf-8", buffering=1)

    def write(self, cms: str, url: str):
        """Write URL to file (append, no duplicates)."""
        with self.lock:
            if url in self.written[cms]:
                return False

            fh = self.handles.get(cms)
            if fh is None:
                return False

            try:
                fh.write(url + "\n")
                fh.flush()
                os.fsync(fh.fileno())
                self.written[cms].add(url)
                return True
            except Exception:
                return False

    def close(self):
        with self.lock:
            for fh in self.handles.values():
                try:
                    fh.close()
                except Exception:
                    pass
            self.handles.clear()

class ProgressTracker:
    def __init__(self, total):
        self.total = total
        self.processed = 0
        self.hits = 0
        self.start = time.time()
        self.lock = threading.Lock()

    def update(self, found_cms=False):
        with self.lock:
            self.processed += 1
            if found_cms:
                self.hits += 1

    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.start
            rate = self.processed / elapsed if elapsed > 0 else 0
            eta = (self.total - self.processed) / rate if rate > 0 else 0
            percent = (self.processed / self.total * 100) if self.total > 0 else 0
            return {
                "processed": self.processed,
                "hits": self.hits,
                "total": self.total,
                "percent": percent,
                "rate": rate,
                "eta": eta,
                "elapsed": elapsed
            }


def process_batch(pool, urls_batch, writer, tracker, print_lock, stop_event):
    futures = {pool.submit(detect_all, url): url for url in urls_batch}

    for future in as_completed(futures):
        if stop_event.is_set():
            future.cancel()
            continue

        url = futures[future]

        try:
            matches = future.result(timeout=TIMEOUT + 5)
        except Exception:
            matches = []

        found_any = len(matches) > 0
        tracker.update(found_cms=found_any)

        with print_lock:
            stats = tracker.get_stats()

            # Progress bar
            bar_len = 30
            filled = int(bar_len * stats['percent'] / 100)
            bar = '█' * filled + '░' * (bar_len - filled)

            if not matches:
                # No CMS detected - save to other.txt
                writer.write("other", url)

                # Print inline progress without newline
                print(f"\r  [{stats['processed']}/{stats['total']}] "
                      f"{bar} {stats['percent']:.1f}% | "
                      f"Hits: {stats['hits']} | "
                      f"Rate: {stats['rate']:.1f}/s | "
                      f"ETA: {int(stats['eta'])}s    ",
                      end='', flush=True)
                continue

            # Clear line and print hit
            print(f"\r{' ' * 100}\r", end='')  # Clear line

            for m in matches:
                cms = m["cms"]
                writer.write(cms, url)

            cms_tags = []
            for m in matches:
                c = m["cms"]
                tag = f"[{c.upper()}]"
                if m.get("version"):
                    tag += f"v{m['version']}"
                tag += f"(s{m['strong']}/w{m['weak']})"
                cms_tags.append(tag)

            print(f"  [{stats['processed']}/{stats['total']}] "
                  f"{' '.join(cms_tags)} {url}")


def cms_finder():
    global STRICT_MODE
    print()

    if not HAS_MMH3:
        print(f"  [!] Modul mmh3 tidak terinstall — "
              "favicon hash disabled.")
        print("      Install: pip install mmh3")
        print()
        sys.exit(1)

    input_file = input(
        "  [>] Input file (domain list): "
    ).strip().strip('"').strip("'")
    if not os.path.isfile(input_file):
        print(f"\n  [!] File not found: {input_file}")
        sys.exit(1)

    thr_raw = input(
        "  [>] Threads                 [150]: "
    ).strip()
    threads = int(thr_raw) if thr_raw.isdigit() and int(thr_raw) > 0 else 150
    threads = min(threads, MAX_THREADS)

    strict_raw = input(
        "  [>] Strict mode? (2 strong sig) [y/N]: "
    ).strip().lower()
    STRICT_MODE = strict_raw in ("y", "yes", "1", "true")

    print()

    print("  [*] Counting lines...", end="\r", flush=True)
    raw_lines = count_lines(input_file)
    print(f"  [*] Lines in file : {raw_lines:,}         ")
    print(f"  [*] Threads       : {threads}")
    print("  [*] Strict mode   : "
          f"{'ON (2 strong)' if STRICT_MODE else 'OFF (1 strong / 2 weak)'}")
    print("  [*] Favicon hash  : "
          f"{'ON' if HAS_MMH3 else 'OFF (install mmh3)'}")
    print("  [*] Output mode   : APPEND (bisa ditimbun)")
    print("  [*] Output format : URL only (clean)")
    output_dir = get_results_dir()
    print(f"  [*] Output folder : {output_dir}")
    print("  [*] Output files  :")
    for cms, fname in CMS_OUTPUT_FILES.items():
        output_file = os.path.join(output_dir, fname)
        exists = os.path.exists(output_file)
        existing = count_lines(output_file) if exists else 0
        status = f"{existing} existing" if exists else "new"
        print(f"      - {fname:<24} ({status})")
    print(f"  {'─' * 65}\n")

    tracker = ProgressTracker(raw_lines)
    print_lock = threading.Lock()
    stop_event = threading.Event()

    writer = OutputWriter(output_dir=output_dir)
    try:
        with ThreadPoolExecutor(max_workers=threads) as pool:
            try:
                batch = []
                for url in stream_urls(input_file):
                    batch.append(url)
                    if len(batch) >= BATCH_SIZE:
                        process_batch(pool, batch, writer, tracker,
                                      print_lock, stop_event)
                        batch = []
                if batch:
                    process_batch(pool, batch, writer, tracker,
                                  print_lock, stop_event)
            except KeyboardInterrupt:
                stop_event.set()
                pool.shutdown(wait=False, cancel_futures=True)
                print(f"\n\n  [!] Dihentikan. "
                      f"{tracker.hits} hit tersimpan.\n")
                return
    finally:
        writer.close()

    stats = tracker.get_stats()
    print(f"\n\n  {'─' * 65}")
    print(f"  [*] Selesai  : {stats['elapsed']:.1f}s")
    print(f"  [*] Total    : {stats['processed']:,} domain diproses")
    print(f"  [+] Total hit: {stats['hits']}")
    print("  [*] File output:")
    for cms, fname in CMS_OUTPUT_FILES.items():
        output_file = os.path.join(output_dir, fname)
        try:
            size = os.path.getsize(output_file)
        except OSError:
            size = 0
        lines = count_lines(output_file) if size else 0
        print(f"      - {fname:<24} {lines:>6} entri")
    print()


def clean_domain(raw):
    if not raw:
        return None
    raw = raw.strip().lower()
    raw = re.sub(r'^https?://', '', raw)
    raw = raw.split('/')[0]
    raw = raw.split(':')[0]
    if re.match(r'^[a-z0-9.-]+\.[a-z]{2,}$', raw):
        return raw
    return None


def load_grabbed_domains(output_file):
    seen_domains = set()
    try:
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            for line in f:
                domain = clean_domain(line)
                if domain:
                    seen_domains.add(domain)
    except FileNotFoundError:
        pass
    return seen_domains


def extract_defacer_net(url, output_file, page_type, source="defacer.net", seen_domains=None):
    try:
        if seen_domains is None:
            seen_domains = load_grabbed_domains(output_file)
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        count = 0
        for text in soup.stripped_strings:
            domain = clean_domain(text)
            if domain and domain not in seen_domains:
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(domain + '\n')
                seen_domains.add(domain)
                print(f'[{source}] [{page_type}] {domain:<50} → grabbed')
                count += 1
        return count
    except Exception as e:
        print(f'Gagal → {url} : {e}')
        return 0


def extract_other_site(url, output_file, page_type, source, seen_domains=None):
    try:
        if seen_domains is None:
            seen_domains = load_grabbed_domains(output_file)
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        domains = re.findall(r'<td>([\w\.-]+(?:\.\w{2,})*?)</td>', r.text, re.I)
        domains += re.findall(r'([\w\.-]+\.\w{2,})', r.text)

        count = 0
        for d in domains:
            domain = clean_domain(d)
            if domain and domain not in seen_domains:
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(domain + '\n')
                seen_domains.add(domain)
                tag = f'[{page_type[:2].lower()}]'
                print(f'[{source}] {tag} {domain:<50} → grabbed')
                count += 1
        return count
    except Exception as e:
        print(f'Gagal → {url} : {e}')
        return 0


def get_page_range():
    while True:
        try:
            start = input("Page mulai (contoh: 1) → ").strip()
            start = int(start) if start else 1
            if start < 1:
                print("Page minimal 1")
                continue

            end = input("Page akhir (contoh: 100, 500, 1000) → ").strip()
            end = int(end) if end else 100
            if end < start:
                print("Page akhir harus >= page mulai")
                continue

            return start, end
        except ValueError:
            print("Masukkan angka yang valid")


def grabber():
    print("""


  [1] Defacer.net
  [2] Zone-xsec.com
  [3] Haxor.id
  [4] Ketiga situs sekaligus
  [0] Keluar
""")

    try:
        src_choice = int(input("Pilih sumber (0-4) → "))
    except:
        print("Input salah")
        return

    if src_choice == 0:
        return

    print("""
Tipe data:
  [1] Archive
  [2] Special
  [3] Onhold
  [4] Semua tipe
""")

    try:
        type_choice = int(input("Pilih tipe (1-4) → "))
    except:
        print("Input salah")
        return

    if type_choice not in [1,2,3,4]:
        print("Pilihan tipe tidak valid")
        return

    start_page, end_page = get_page_range()

    type_names = {1: "archive", 2: "special", 3: "onhold", 4: "all"}
    current_type = type_names[type_choice]

    sources = []
    if src_choice in [1,4]: sources.append(("defacer.net", "Defacer"))
    if src_choice in [2,4]: sources.append(("zone-xsec.com", "Zone-X"))
    if src_choice in [3,4]: sources.append(("haxor.id", "Haxor"))

    for domain, short_name in sources:
        filename = os.path.join(get_results_dir(), f"{domain.replace('.', '-')}-{current_type}.txt")
        try:
            seen_domains = load_grabbed_domains(filename)
        except OSError as e:
            print(f"Gagal membaca {filename}: {e}")
            continue

        print(f"\n══════ Mulai {short_name} – {current_type.upper()} ══════")
        print(f"   Rentang page: {start_page} – {end_page}")
        print(f"   File: {filename}\n")

        total = 0

        for page in range(start_page, end_page + 1):
            try:
                if domain == "defacer.net":
                    if type_choice == 4:
                        for t in [1,2,3]:
                            url = f"https://defacer.net/{type_names[t]}/{page}"
                            c = extract_defacer_net(url, filename, type_names[t].upper(), short_name, seen_domains)
                            total += c
                    else:
                        url = f"https://defacer.net/{current_type}/{page}"
                        c = extract_defacer_net(url, filename, current_type.upper(), short_name, seen_domains)
                        total += c

                else:  # zone & haxor
                    base = "https://zone-xsec.com" if domain == "zone-xsec.com" else "https://haxor.id"
                    param = f"page={page}" if domain == "zone-xsec.com" else f"?page={page}"

                    if type_choice == 4:
                        for t in ["archive","special","onhold"]:
                            path = f"/{t}/{param}" if domain == "zone-xsec.com" else f"/{t}{param}"
                            url = f"{base}{path}"
                            c = extract_other_site(url, filename, t.upper(), short_name, seen_domains)
                            total += c
                    else:
                        path = f"/{current_type}/{param}" if domain == "zone-xsec.com" else f"/{current_type}{param}"
                        url = f"{base}{path}"
                        c = extract_other_site(url, filename, current_type.upper(), short_name, seen_domains)
                        total += c

                print(f"  page {page:>5}  |  total saat ini: {total:,}")
                time.sleep(1.0)   # delay ringan

            except KeyboardInterrupt:
                print("\nDihentikan manual oleh user.")
                return

        print(f"Selesai {short_name} → {total:,} baris")
        print(f"   File: {filename}\n")

    print("Proses scraping selesai.")


SHELL_FINDER_MARKERS = (
    'x0mb13</title>',
    'tiny file manager',
    'simpel banget nih shell',
    '<title>403webshell</title>',
    '403webshell',
    'hexid m1n1 5h3ll mobile',
    'lambo [beta]',
    './alfateam',
    'yanz webshell!',
    'l i e r shell',
    '[ home shell ]',
    'mini shell',
    'gel4y mini shell',
    'clarasec',
    'abc manager',
    'thealmightyzeus',
    'jijle3',
    'wso 5.1.4',
    'wso yanz enc bypass',
    'wso 4.2.5',
    'wso 2.6',
    'wsox enc',
    'wso 4.2.6',
    'foxwso v1.2',
    'webshellorb 2.6',
    'file manager -',
    'cod3d by adriv4',
    'bondowoso black hat shell',
    'rxrhacker',
    'xxx kelelawar cyber team xxx',
    'code by kelelawar cyber team',
    'cod3d by anonymousfox',
    'unknownsec',
    'shell bypass 403',
    'unknownsec shell',
    'adriv4',
    '[ home shell ] ',
    'rc-shell v2.0.2011.1009',
    '<title>mini shell</title>',
    'negat1ve shell',
    '[+[mad tiger]+]',
    'franz private shell',
    'webshell v1.0',
    'team-0root uploader',
    'fighter kamrul plugin',
    '- fierzaxploit -',
    '<title>fierzaxploit</title>',
    'minishell',
    'mini shell by black_shadow',
    'filemanager version 0.2 by ecws',
    'xichang1',
    'adriv4-priv8 tool',
    'b ge team file manager',
    'marijuana',
    'inesec team shell',
    'chips l pro sangad',
    '[+] mini sh3ll bypass [+]',
    'team-0root',
    'tiny file manager 2.4.3',
    '[ mini shell ]',
    'phu mini shell',
    'mr.combet webshell',
    'msq_403',
    'graybyt3 was here',
    'bypass sh3ll',
    'bypass 403 forbidden / 406 not acceptable / imunify360 / mini shell',
    'one hat cyber team',
    'c0d3d by dr.d3m0',
    ' leaf phpmailer ',
    '<title>leaf phpmailer</title>',
    'type="submit" class="upload-submit" name="upload-submit" value="upload"',
    'upload file</a></td>',
    'php file manager',
    'type="submit" name="test" value="upload"',
    "<input type=submit value='>>'>",
    'filesman',
    '<title>l i e r shell</title>',
    'action="" method="post"><input type="text" name="_rg"><input type="submit" value=">>"',
    'kill_the_net',
    '<title>fuck</title>',
    ' <title>freshtools wso 1.0</title>',
    'shell bypass 403 ge-c666c',
    'doc root:',
    'blackdragon',
    '//0x5a455553.github.io/marijuana/icon.png',
    '{ninja-shell}',
    'method= "post" action= ""> <input type="input" name ="f_p" value= ""/><input type= "submit" value= "&gt;"',
)


def shell_finder_matches(body):
    text = body[:200_000].lower()
    permissions = ('-rw-r--r', 'drwxr-xr-x', '-rw-rw-rw-')
    return (
        any(marker in text for marker in SHELL_FINDER_MARKERS)
        or ('.php' in text and any(marker in text for marker in permissions))
    )


class ShellPathProgress:
    def __init__(self):
        self.lock = threading.Lock()
        self.checked = 0
        self.last_update = None
        self.line_width = 0

    def update(self, url, path_index, path_total, completed=False):
        with self.lock:
            if completed:
                self.checked += 1
            now = time.monotonic()
            if self.last_update is not None and now - self.last_update < 0.5:
                return
            self.last_update = now
            line = f'[*] Paths checked: {self.checked} | Path {path_index}/{path_total}: {url}'
            try:
                columns = os.get_terminal_size().columns
            except OSError:
                columns = 120
            line = line[:max(1, columns - 1)]
            print('\r' + line.ljust(self.line_width), end='', flush=True)
            self.line_width = len(line)

    def message(self, text):
        with self.lock:
            if self.line_width:
                print('\r' + ' ' * self.line_width + '\r', end='', flush=True)
                self.line_width = 0
            print(text, flush=True)
            self.last_update = None


def check_shell_paths(base_url, candidate_paths, stop_event=None, progress_callback=None):
    with requests.Session() as session:
        session.headers.update(HEADERS)
        for path_index, candidate in enumerate(candidate_paths, 1):
            if stop_event is not None and stop_event.is_set():
                return None
            url = base_url.rstrip('/') + '/' + candidate.lstrip('/')
            if progress_callback is not None:
                progress_callback(url, path_index, len(candidate_paths))
            try:
                with session.get(url, timeout=10, allow_redirects=False, stream=True) as response:
                    if response.status_code != 200:
                        continue
                    body = bytearray()
                    for chunk in response.iter_content(chunk_size=8192):
                        if stop_event is not None and stop_event.is_set():
                            return None
                        body.extend(chunk[:200_000 - len(body)])
                        if len(body) >= 200_000:
                            break
                    text = body.decode(response.encoding or 'utf-8', errors='replace')
                    if shell_finder_matches(text):
                        return url
            except requests.RequestException:
                continue
            finally:
                if progress_callback is not None:
                    progress_callback(url, path_index, len(candidate_paths), completed=True)
    return None


def shell_finder():
    default_file = 'domains.txt'
    file_path = input(f'[+] Domain list [{default_file}] : ').strip().strip('"').strip("'") or default_file
    file_path_names = 'db/db4.txt'
    project_dir = os.path.dirname(os.path.abspath(__file__))
    names_path = os.path.join(project_dir, file_path_names)

    if not os.path.isfile(file_path):
        print(f'[!] File not found: {file_path}')
        return

    try:
        with open(names_path, 'r', encoding='utf-8-sig') as names_file:
            candidate_paths = list(dict.fromkeys(
                line.strip().lstrip('/')
                for line in names_file
                if line.strip() and not line.lstrip().startswith('#')
            ))
    except (OSError, UnicodeError) as error:
        print(f'[!] Cannot read {file_path_names}: {error}')
        return

    targets = list(stream_urls(file_path))
    if not targets or not candidate_paths:
        print('[!] Domain list or path list is empty.')
        return

    try:
        output_path = os.path.join(get_results_dir(), 'Shells.txt')
        try:
            with open(output_path, 'r', encoding='utf-8-sig') as existing:
                saved_urls = {line.strip() for line in existing if line.strip()}
        except FileNotFoundError:
            saved_urls = set()
        output = open(output_path, 'a', encoding='utf-8')
    except (OSError, UnicodeError) as error:
        print(f'[!] Cannot open results file: {error}')
        return

    workers = min(10, len(targets))
    stop_event = threading.Event()
    checked = 0
    found = 0
    saved = 0
    print(f'[*] Domains: {len(targets)} | Paths: {len(candidate_paths)} | Workers: {workers}')
    print(f'[*] Paths file: {file_path_names}')
    progress = ShellPathProgress()

    with output:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(check_shell_paths, target, candidate_paths, stop_event, progress.update): target
                for target in targets
            }
            try:
                for future in as_completed(futures):
                    checked += 1
                    target = futures[future]
                    try:
                        match = future.result()
                    except Exception as error:
                        progress.message(f'[!] {target}: {error}')
                        continue
                    if match:
                        found += 1
                        if match not in saved_urls:
                            output.write(match + '\n')
                            output.flush()
                            saved_urls.add(match)
                            saved += 1
                        progress.message(f'[+] Possible shell: {match}')
                    else:
                        progress.message(f'[-] [{checked}/{len(targets)}] No shell indicators: {target}')
            except (KeyboardInterrupt, OSError) as error:
                stop_event.set()
                for future in futures:
                    future.cancel()
                if isinstance(error, KeyboardInterrupt):
                    progress.message('[!] Stopped by user.')
                else:
                    progress.message(f'[!] Cannot save results: {error}')

    progress.message(f'[*] Paths checked: {progress.checked}')
    print(f'[*] Checked: {checked} | Findings: {found} | Newly saved: {saved}')
    print(f'[*] Results: {output_path}')


def main():
    if os.name == "nt":
         os.system("cls")
    else:
        os.system("clear")
        
    print(r"""
  _____ _          _____ _           _
 |_   _| |__   ___|  ___(_)_ __   __| | ___ _ __
   | | | '_ \ / _ \ |_  | | '_ \ / _` |/ _ \ '__|
   | | | | | |  __/  _| | | | | | (_| |  __/ |
   |_| |_| |_|\___|_|   |_|_| |_|\__,_|\___|_|

                       Coded by : Tyr3X
""")
    print("[1]> Admin finder\n[2]> Dir finder\n[3]> Subdomain finder\n[4]> CMS finder\n[5]> Domain Grabber\n[6]> Shell finder\n")
    x = int(input('[+] Enter Your Choice : '))

    if x == 1:
        admin()
    elif x == 2:
        dirs()
    elif x == 3:
        domain()
    elif x == 4:
        cms_finder()
    elif x == 5:
        grabber()
    elif x == 6:
        shell_finder()
    else:
        raise Exception("Enter correct input!")
            
if __name__ == "__main__":
    main()
    
    


        
            
