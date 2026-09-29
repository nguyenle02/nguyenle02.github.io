"""Thư viện dùng chung cho bộ script SEO PTE Magic.

Thiết kế:
  * Phụ thuộc tối thiểu. `requests` và `beautifulsoup4` là bắt buộc cho chế độ crawl;
    chế độ --offline-dir chỉ cần beautifulsoup4. Không có PyYAML thì đọc JSON thay thế.
  * Mọi thứ đo được đều trả về `Finding` có `code`, `severity`, `evidence`, `confidence`.
    Agent KHÔNG được suy ra số liệu; nó chỉ đọc JSON do các hàm ở đây sinh ra.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import hashlib
import urllib.parse
import urllib.robotparser
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable

# --------------------------------------------------------------------------- #
# Dependency guard
# --------------------------------------------------------------------------- #
try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "[FATAL] Thiếu beautifulsoup4. Chạy:\n"
        "    pip install -r scripts/requirements.txt\n"
    )
    raise

try:
    import requests  # type: ignore
    HAS_REQUESTS = True
except ImportError:  # pragma: no cover
    requests = None
    HAS_REQUESTS = False

try:
    import yaml  # type: ignore
    HAS_YAML = True
except ImportError:  # pragma: no cover
    yaml = None
    HAS_YAML = False


SEVERITIES = ("critical", "high", "medium", "low", "info")
SEVERITY_WEIGHT = {"critical": 12.0, "high": 6.0, "medium": 2.0, "low": 0.5, "info": 0.0}
SEVERITY_ORDER = {s: i for i, s in enumerate(SEVERITIES)}

DEFAULT_UA = (
    "PTEMagicSEOBot/1.0 (+internal audit tool; respects robots.txt) "
    "Mozilla/5.0 (compatible)"
)

VI_DIACRITICS = set("ăâêôơưđÀÁẢÃẠằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ")


# --------------------------------------------------------------------------- #
# Finding
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    """Một phát hiện đơn lẻ. `code` là khoá ổn định để dedupe/so drift."""

    code: str
    severity: str
    category: str
    url: str
    message: str
    evidence: str = ""
    fix: str = ""
    confidence: str = "high"  # high | medium | low

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity không hợp lệ: {self.severity}")
        self.evidence = (self.evidence or "")[:600]

    @property
    def penalty(self) -> float:
        return SEVERITY_WEIGHT.get(self.severity, 0.0)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FindingSet:
    """Gom finding, tính điểm, xuất JSON/Markdown."""

    def __init__(self, site: str = "") -> None:
        self.site = site
        self.items: list[Finding] = []

    def add(self, *args: Any, **kwargs: Any) -> Finding:
        f = Finding(*args, **kwargs) if args else Finding(**kwargs)
        self.items.append(f)
        return f

    def extend(self, findings: Iterable[Finding]) -> None:
        self.items.extend(findings)

    # -- aggregation ------------------------------------------------------- #
    def __len__(self) -> int:
        return len(self.items)

    def by_severity(self) -> dict[str, int]:
        out = {s: 0 for s in SEVERITIES}
        for f in self.items:
            out[f.severity] += 1
        return out

    def by_category(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.items:
            out[f.category] = out.get(f.category, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def codes(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for f in self.items:
            out[f.code] = out.get(f.code, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def score(self, pages_audited: int) -> float:
        """Điểm 0-100, trừ điểm có trần theo mức độ nghiêm trọng.

        Công thức cố tình đơn giản để giải thích được cho khách hàng:
            critical −10/cái (trần −30) · high −4/cái (trần −40)
            medium  −1.5/cái (trần −20) · low −0.3/cái (trần −10)
        Có trần để một site lớn với nhiều lỗi vặt không bị về 0 — khi đó phải nhìn
        vào điểm theo hạng mục và danh sách finding, không nhìn mỗi điểm tổng.
        """
        sev = self.by_severity()
        ded = (min(30.0, 10.0 * sev["critical"])
               + min(40.0, 4.0 * sev["high"])
               + min(20.0, 1.5 * sev["medium"])
               + min(10.0, 0.3 * sev["low"]))
        return round(max(0.0, 100.0 - ded), 1)

    def category_score(self, category: str, pages_audited: int) -> float:
        """Điểm riêng cho 1 hạng mục, cùng công thức nhưng trần nhỏ hơn."""
        sev = {s: 0 for s in SEVERITIES}
        for f in self.items:
            if f.category == category:
                sev[f.severity] += 1
        ded = (min(40.0, 14.0 * sev["critical"])
               + min(45.0, 7.0 * sev["high"])
               + min(25.0, 3.0 * sev["medium"])
               + min(10.0, 1.0 * sev["low"]))
        return round(max(0.0, 100.0 - ded), 1)

    def sorted(self) -> list[Finding]:
        return sorted(
            self.items,
            key=lambda f: (SEVERITY_ORDER[f.severity], f.category, f.url),
        )

    # -- export ------------------------------------------------------------ #
    def to_json(self) -> dict[str, Any]:
        pages = len({f.url for f in self.items if f.url})
        return {
            "site": self.site,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pages_with_findings": pages,
            "score": self.score(pages or 1),
            "by_severity": self.by_severity(),
            "by_category": self.by_category(),
            "by_code": self.codes(),
            "findings": [f.to_dict() for f in self.sorted()],
        }

    def to_markdown(self, meta: dict[str, Any] | None = None) -> str:
        meta = meta or {}
        pages = meta.get("pages_audited", len({f.url for f in self.items if f.url}))
        lines: list[str] = []
        lines.append(f"# SEO Audit — {self.site or meta.get('site','?')}")
        lines.append("")
        lines.append(f"- **Ngày chạy:** {meta.get('run_at', time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()))}")
        lines.append(f"- **Số URL đã audit:** {pages}")
        lines.append(f"- **Chế độ:** {meta.get('mode', 'live')}")
        lines.append(f"- **Điểm tổng:** **{self.score(pages or 1)}/100**")
        lines.append("")
        sev = self.by_severity()
        lines.append("| Critical | High | Medium | Low | Info |")
        lines.append("|---|---|---|---|---|")
        lines.append(f"| {sev['critical']} | {sev['high']} | {sev['medium']} | {sev['low']} | {sev['info']} |")
        lines.append("")
        lines.append("## Điểm theo hạng mục")
        lines.append("")
        lines.append("| Hạng mục | Điểm | Số finding |")
        lines.append("|---|---|---|")
        for cat, n in self.by_category().items():
            lines.append(f"| {cat} | {self.category_score(cat, pages or 1)} | {n} |")
        lines.append("")

        # Nhóm theo code để không lặp lại 200 lần cùng một lỗi
        grouped: dict[str, list[Finding]] = {}
        for f in self.sorted():
            grouped.setdefault(f.code, []).append(f)

        lines.append("## Finding theo mức độ nghiêm trọng")
        for severity in SEVERITIES:
            codes = [c for c, fs in grouped.items() if fs[0].severity == severity]
            if not codes:
                continue
            lines.append("")
            lines.append(f"### {severity.upper()}")
            for code in codes:
                fs = grouped[code]
                first = fs[0]
                lines.append("")
                lines.append(f"#### `{code}` — {len(fs)} lần · [{first.category}] · confidence: {first.confidence}")
                lines.append("")
                lines.append(f"{first.message}")
                if first.fix:
                    lines.append("")
                    lines.append(f"**Cách sửa:** {first.fix}")
                shown = fs[:12]
                lines.append("")
                lines.append("| URL | Bằng chứng |")
                lines.append("|---|---|")
                for f in shown:
                    ev = (f.evidence or "").replace("|", "\\|").replace("\n", " ")[:180]
                    lines.append(f"| `{f.url or '-'}` | {ev or '-'} |")
                if len(fs) > len(shown):
                    lines.append("")
                    lines.append(f"_…và {len(fs) - len(shown)} URL nữa (xem JSON)._")
        lines.append("")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
def load_config(path: str | None) -> dict[str, Any]:
    """Đọc config YAML (hoặc JSON). Không tìm thấy file thì trả dict rỗng."""
    if not path:
        here = os.path.dirname(os.path.abspath(__file__))
        for cand in (
            os.path.join(here, "..", "config", "ptemagic.yaml"),
            os.path.join(here, "..", "config", "ptemagic.json"),
        ):
            if os.path.exists(cand):
                path = cand
                break
    if not path or not os.path.exists(path):
        return {}
    raw = open(path, "r", encoding="utf-8").read()
    if path.endswith((".yaml", ".yml")):
        if not HAS_YAML:
            sys.stderr.write(f"[warn] Không có PyYAML, bỏ qua config {path}\n")
            return {}
        return yaml.safe_load(raw) or {}
    return json.loads(raw)


def thresholds(cfg: dict[str, Any], *keys: str, default: Any = None) -> Any:
    node: Any = cfg.get("thresholds", {})
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            return default
        node = node[k]
    return node


# --------------------------------------------------------------------------- #
# URL helpers
# --------------------------------------------------------------------------- #
FRAGMENT_STRIP = ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                  "gclid", "fbclid", "ref", "source")


def normalize_url(url: str, keep_params: bool = False) -> str:
    """Chuẩn hoá URL để so sánh: bỏ fragment, hạ thấp host, bỏ trailing slash (trừ root)."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    p = urllib.parse.urlsplit(url)
    scheme = (p.scheme or "https").lower()
    host = (p.hostname or "").lower()
    port = p.port
    netloc = host + (f":{port}" if port and port not in (80, 443) else "")
    path = p.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/") or "/"
    query = ""
    if keep_params and p.query:
        pairs = sorted(
            (k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
            if k.lower() not in FRAGMENT_STRIP
        )
        query = urllib.parse.urlencode(pairs)
    return urllib.parse.urlunsplit((scheme, netloc, path, query, ""))


def same_host(a: str, b: str, include_sub: bool = False) -> bool:
    ha, hb = urllib.parse.urlsplit(a).hostname or "", urllib.parse.urlsplit(b).hostname or ""
    ha, hb = ha.lower().lstrip("www."), hb.lower().lstrip("www.")
    if include_sub:
        return ha == hb or ha.endswith("." + hb) or hb.endswith("." + ha)
    return ha == hb


def registrable_domain(url: str) -> str:
    h = (urllib.parse.urlsplit(url).hostname or "").lower()
    parts = h.split(".")
    if len(parts) >= 3 and parts[-2] in ("com", "co", "net", "org", "gov", "edu", "ac"):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else h


def is_image_url(url: str) -> bool:
    path = urllib.parse.urlsplit(url).path.lower()
    return path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg", ".bmp"))


def looks_vietnamese(text: str) -> float:
    """Tỷ lệ ký tự có dấu tiếng Việt đặc trưng. > 0.01 thường là văn bản tiếng Việt."""
    if not text:
        return 0.0
    hits = sum(1 for ch in text if ch in VI_DIACRITICS)
    return hits / max(1, len(text))


# --------------------------------------------------------------------------- #
# Near-duplicate detection (shingle + Jaccard)
# --------------------------------------------------------------------------- #
_WS = re.compile(r"\s+")
_NONWORD = re.compile(r"[^\w\s]", re.UNICODE)


def tokens(text: str) -> list[str]:
    cleaned = _NONWORD.sub(" ", (text or "").lower())
    return [w for w in _WS.split(cleaned) if w]


def shingles(text: str, k: int = 5) -> set[str]:
    """Tập k-gram đã băm. Dùng để đo độ giống mà không cần so chuỗi thô."""
    toks = tokens(text)
    if len(toks) < k:
        return {" ".join(toks)} if toks else set()
    return {hashlib.md5(" ".join(toks[i:i + k]).encode("utf-8")).hexdigest()[:16]
            for i in range(len(toks) - k + 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter)


STOPWORDS = set("""a an the and or but if then else of to in on for from by with without at as is are was were be been
being do does did doing have has had having i you he she it we they them his her its our their this that these those
there here what which who whom when where why how all any both each few more most other some such no nor not only own
same so than too very can will just should now about into over after before during between under above again further
once trong và của là có cho với không được một những các này kia gì sao như để bị từ trên dưới khi mà đã sẽ cũng rất
""".split())


def content_tokens(text: str) -> list[str]:
    return [t for t in tokens(text) if t not in STOPWORDS and len(t) > 1]


# --------------------------------------------------------------------------- #
# HTML extraction
# --------------------------------------------------------------------------- #
BOILERPLATE_SELECTORS = ["nav", "header", "footer", "script", "style", "noscript", "form", "aside"]


def soup_of(html: str):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def meta_content(soup, name: str = None, prop: str = None) -> str | None:
    attrs = {"name": name} if name else {"property": prop}
    tag = soup.find("meta", attrs=attrs)
    if tag is None and name:
        tag = soup.find("meta", attrs={"name": name.lower()})
    if tag is None and name:
        tag = soup.find("meta", attrs={"property": f"og:{name}"})
    return tag.get("content", "").strip() if tag and tag.get("content") else None


def all_meta(soup, attr: str, key: str) -> list[tuple[str, str]]:
    out = []
    for tag in soup.find_all("meta"):
        if tag.get(attr, "").lower() == key.lower():
            out.append((tag.get(attr), (tag.get("content") or "").strip()))
    return out


def headings(soup) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for level in range(1, 7):
        out[f"h{level}"] = [h.get_text(" ", strip=True) for h in soup.find_all(f"h{level}")]
    return out


def main_text(soup, strip_boilerplate: bool = True) -> str:
    """Chữ trong <main>/<article> nếu có, nếu không thì toàn body trừ boilerplate."""
    root = soup.find("main") or soup.find("article")
    if root is None:
        root = soup.body or soup
    if strip_boilerplate:
        root = BeautifulSoup(str(root), "html.parser")
        for sel in BOILERPLATE_SELECTORS:
            for t in root.find_all(sel):
                t.decompose()
    return re.sub(r"\s+", " ", root.get_text(" ", strip=True))


def visible_text_len(text: str) -> int:
    return len(tokens(text))


def jsonld_blocks(soup) -> list[Any]:
    """Trả về danh sách object JSON-LD (đã flatten @graph)."""
    out: list[Any] = []
    for tag in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        raw = tag.string or tag.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            out.append({"__parse_error__": raw[:200]})
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                if "@graph" in node:
                    stack.extend(node["@graph"] if isinstance(node["@graph"], list) else [node["@graph"]])
                    ctx = {k: v for k, v in node.items() if k != "@graph"}
                    if ctx:
                        stack.append(ctx)
                else:
                    out.append(node)
    return out


def jsonld_types(blocks: list[Any]) -> set[str]:
    types: set[str] = set()
    for b in blocks:
        if not isinstance(b, dict):
            continue
        t = b.get("@type")
        if isinstance(t, list):
            types.update(str(x) for x in t)
        elif t:
            types.add(str(t))
    return types


def link_href(abs_url: str, tag) -> str:
    href = tag.get("href")
    if not href:
        return ""
    href = href.strip()
    if href.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
        return ""
    return urllib.parse.urljoin(abs_url, href)


# --------------------------------------------------------------------------- #
# Fetching (live mode)
# --------------------------------------------------------------------------- #
class Fetcher:
    """HTTP client có tôn trọng robots.txt, cache đĩa, và giới hạn tốc độ.

    Chặn SSRF: từ chối IP private/loopback/link-local, chỉ cho http/https.
    """

    def __init__(self, ua: str = DEFAULT_UA, delay: float = 0.5, timeout: int = 20,
                 cache_dir: str | None = None, respect_robots: bool = True,
                 verify_ssl: bool = True) -> None:
        if not HAS_REQUESTS:
            raise RuntimeError("Cần `requests` để chạy chế độ live. pip install requests")
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": ua, "Accept-Language": "en,vi;q=0.9"})
        self.delay = delay
        self.timeout = timeout
        self.cache_dir = cache_dir
        self.respect_robots = respect_robots
        self.verify_ssl = verify_ssl
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._last = 0.0
        self.stats = {"requests": 0, "cache_hits": 0, "errors": 0, "blocked_by_robots": 0}
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    # -- safety ------------------------------------------------------------ #
    @staticmethod
    def is_safe_url(url: str) -> bool:
        p = urllib.parse.urlsplit(url)
        if p.scheme not in ("http", "https"):
            return False
        host = (p.hostname or "").lower()
        if not host:
            return False
        if host in ("localhost", "0.0.0.0", "127.0.0.1", "::1", "[::1]"):
            return False
        if host.endswith(".local") or host.endswith(".internal"):
            return False
        m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", host)
        if m:
            octs = [int(x) for x in m.groups()]
            if octs[0] in (0, 10, 127) or (octs[0] == 192 and octs[1] == 168) \
               or (octs[0] == 172 and 16 <= octs[1] <= 31) or (octs[0] == 169 and octs[1] == 254):
                return False
        return True

    def _cache_key(self, url: str) -> str:
        return hashlib.sha1(url.encode("utf-8")).hexdigest()[:24]

    def _cache_path(self, url: str) -> str:
        return os.path.join(self.cache_dir or "", self._cache_key(url) + ".json")

    # -- robots ------------------------------------------------------------ #
    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        p = urllib.parse.urlsplit(url)
        origin = f"{p.scheme}://{p.netloc}"
        if origin not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(origin + "/robots.txt", timeout=self.timeout, verify=self.verify_ssl)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except Exception:
                rp = None
            self._robots[origin] = rp
        rp = self._robots[origin]
        if rp is None:
            return True
        return rp.can_fetch("*", url)

    # -- core -------------------------------------------------------------- #
    def get(self, url: str, use_cache: bool = True) -> dict[str, Any]:
        """Trả về {url, final_url, status, headers, text, elapsed_ms, error, from_cache}."""
        result: dict[str, Any] = {
            "url": url, "final_url": url, "status": None, "headers": {},
            "text": "", "elapsed_ms": None, "error": None, "from_cache": False,
        }
        if not self.is_safe_url(url):
            result["error"] = "unsafe_url"
            return result
        if self.cache_dir and use_cache and os.path.exists(self._cache_path(url)):
            try:
                cached = json.load(open(self._cache_path(url), encoding="utf-8"))
                cached["from_cache"] = True
                self.stats["cache_hits"] += 1
                return cached
            except Exception:
                pass
        if not self.allowed(url):
            result["error"] = "blocked_by_robots"
            self.stats["blocked_by_robots"] += 1
            return result

        wait = self.delay - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.time()

        t0 = time.time()
        try:
            r = self.s.get(url, timeout=self.timeout, allow_redirects=True, verify=self.verify_ssl)
            result.update(
                status=r.status_code,
                final_url=str(r.url),
                headers={k.lower(): v for k, v in r.headers.items()},
                text=r.text,
                elapsed_ms=int((time.time() - t0) * 1000),
            )
            self.stats["requests"] += 1
        except Exception as e:  # noqa: BLE001
            result["error"] = f"{type(e).__name__}: {str(e)[:160]}"
            result["elapsed_ms"] = int((time.time() - t0) * 1000)
            self.stats["errors"] += 1
        if self.cache_dir and result["status"] is not None:
            try:
                slim = {k: v for k, v in result.items() if k != "from_cache"}
                json.dump(slim, open(self._cache_path(url), "w", encoding="utf-8"))
            except Exception:
                pass
        return result

    def redirect_chain(self, url: str, max_hops: int = 8) -> list[dict[str, Any]]:
        """Trace từng hop để phát hiện chain dài / trộn 301-302."""
        chain: list[dict[str, Any]] = []
        cur = url
        for _ in range(max_hops):
            try:
                r = self.s.head(cur, timeout=self.timeout, allow_redirects=False, verify=self.verify_ssl)
            except Exception:
                try:
                    r = self.s.get(cur, timeout=self.timeout, allow_redirects=False,
                                   stream=True, verify=self.verify_ssl)
                except Exception as e:  # noqa: BLE001
                    chain.append({"url": cur, "error": str(e)[:120]})
                    break
            loc = r.headers.get("Location", "")
            chain.append({"url": cur, "status": r.status_code, "location": loc})
            if r.status_code not in (301, 302, 303, 307, 308) or not loc:
                break
            cur = urllib.parse.urljoin(cur, loc)
            time.sleep(self.delay)
        return chain


# --------------------------------------------------------------------------- #
# Offline corpus loading
# --------------------------------------------------------------------------- #
def load_offline_dir(directory: str) -> list[dict[str, Any]]:
    """Đọc HTML đã lưu sẵn.

    Hỗ trợ:
      * `manifest.json` = [{"url": ..., "file": ...}, ...]  (khuyến nghị)
      * không có manifest → mỗi `*.html` trong thư mục, url suy ra từ tên file
    """
    directory = os.path.abspath(directory)
    if not os.path.isdir(directory):
        raise NotADirectoryError(directory)
    manifest = os.path.join(directory, "manifest.json")
    pages: list[dict[str, Any]] = []
    if os.path.exists(manifest):
        for entry in json.load(open(manifest, encoding="utf-8")):
            path = entry["file"]
            if not os.path.isabs(path):
                path = os.path.join(directory, path)
            if not os.path.exists(path):
                continue
            pages.append({
                "url": entry.get("url") or os.path.basename(path),
                "status": entry.get("status", 200),
                "final_url": entry.get("final_url", entry.get("url")),
                "headers": entry.get("headers", {}),
                "text": open(path, encoding="utf-8", errors="replace").read(),
                "error": None, "elapsed_ms": None, "from_cache": True,
            })
    else:
        for name in sorted(os.listdir(directory)):
            if not name.lower().endswith((".html", ".htm")):
                continue
            path = os.path.join(directory, name)
            stem = re.sub(r"\.html?$", "", name, flags=re.I)
            pages.append({
                "url": stem, "status": 200, "final_url": stem, "headers": {},
                "text": open(path, encoding="utf-8", errors="replace").read(),
                "error": None, "elapsed_ms": None, "from_cache": True,
            })
    return pages


def write_outputs(out_dir: str, stem: str, payload: dict[str, Any], markdown: str) -> tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    jp = os.path.join(out_dir, stem + ".json")
    mp = os.path.join(out_dir, stem + ".md")
    json.dump(payload, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(mp, "w", encoding="utf-8").write(markdown)
    return jp, mp


def eprint(*a: Any) -> None:
    print(*a, file=sys.stderr)
