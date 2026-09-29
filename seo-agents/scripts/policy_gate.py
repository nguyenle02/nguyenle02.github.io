#!/usr/bin/env python3
"""policy_gate.py — Cổng kiểm tra chính sách Google TRƯỚC khi publish.

Đây là phần mà 8 repo SEO agent trên GitHub (đã research 2026-09-29) KHÔNG có:
chúng tối ưu, không từ chối. Script này từ chối.

Đối chiếu: Google Search Essentials / Spam Policies, bản cập nhật 15/05/2026 —
trong đó định nghĩa spam được mở rộng sang cả việc "manipulate generative AI
responses in Google Search" (AI Overviews, AI Mode), không chỉ 10 link xanh.

Dùng:
    python scripts/policy_gate.py --file drafts/bai-viet.md
    python scripts/policy_gate.py --file drafts/bai-viet.md --corpus published/ --log reports/policy-log.csv
    python scripts/policy_gate.py --file page.html --format html --json

Verdict:
    PASS  — publish được
    WARN  — publish được nhưng phải ghi chú lý do
    BLOCK — KHÔNG publish. Sửa nội dung thật, không sửa để lách gate.

Exit code: 0=PASS, 10=WARN, 20=BLOCK, 2=lỗi chạy. Dùng được trong CI/pre-commit.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

from common import (  # noqa: E402
    content_tokens, jaccard, load_config, shingles, soup_of, thresholds, tokens, eprint,
)

# --------------------------------------------------------------------------- #
# Ngưỡng mặc định (config/ptemagic.yaml có thể ghi đè)
# --------------------------------------------------------------------------- #
DEFAULTS = {
    "near_duplicate_block": 0.70,
    "near_duplicate_warn": 0.50,
    "shingle_size": 5,
    "template_shell_min_urls": 8,
    "template_shell_body_delta_min": 0.30,
    "keyword_density_max": 0.035,
    "keyword_in_heading_ratio_max": 0.60,
    "outbound_exact_match_anchor_max": 0.40,
    "min_words_warn": 250,
    "ymwl_max_days_since_update": 90,
    "ymwl_min_words": 800,
}

# Nội dung YMYL: sức khoẻ, tiền bạc, pháp lý, di trú. PTE Magic chạm vào nhóm DI TRÚ/GIÁO DỤC.
YMYL_KEYWORDS = [
    "visa", "định cư", "dinh cu", "migration", "immigration", "permanent resident", "pr ",
    "scholarship", "học bổng", "hoc bong", "tuition", "học phí", "hoc phi",
    "cost of living", "chi phí sinh hoạt", "chi phi sinh hoat", "student loan", "vay du học",
    "work permit", "post-study work", "post-graduate work permit",
    "nursing registration", "nurse registration", "y tá", "yta", "điều dưỡng",
    "skillselect", "189", "190", "482", "express entry", "cas number",
    "bảo lãnh", "bao lanh", "tị nạn", "quốc tịch", "citizenship",
]

OFF_TOPIC_TERMS = [
    "casino", "gambling", "cá độ", "ca do", "lô đề", "lo de", "xổ số", "xo so",
    "vay nóng", "vay nong", "tín dụng đen", "tin dung den", "payday loan",
    "coupon code", "discount code", "mã giảm giá", "ma giam gia",
    "adult", "porn", "escort", "crypto pump", "forex signal",
]

# Câu "chắc chắn/cam kết" — rủi ro quảng cáo sai sự thật trong ngữ cảnh YMYL
GUARANTEE_PATTERNS = [
    r"cam kết (đậu|đạt|có visa|đầu ra)", r"chắc chắn (sẽ )?(đậu|đạt|có|thành công)",
    r"đảm bảo (đậu|đạt|100%|có visa)", r"bao đậu", r"đậu 100%",
    r"\bguaranteed? (to )?(pass|score|succeed|visa)\b", r"\b100% (pass|success) rate\b",
    r"\bpass or (your )?money back\b", r"\bensure your visa\b",
]

AI_BOILERPLATE = [
    r"\bin today'?s (fast-paced|digital|competitive) world\b",
    r"\bit'?s (important|worth) (to note|noting) that\b",
    r"\bin conclusion,?\b", r"\bdelve (into|deeper)\b", r"\bnavigating the (landscape|world|complexities)\b",
    r"\bunlock the (power|secret|potential)\b", r"\bgame[- ]changer\b", r"\belevate your\b",
    r"\bembark on (a |this )?journey\b", r"\bwhether you'?re a .{0,30} or a\b",
    r"\btóm lại,?\b", r"\bđiều quan trọng (là|cần)\b", r"\btrong thời đại\b",
    r"\bkhông thể phủ nhận\b", r"\bhành trình\b.{0,20}\bchinh phục\b",
    r"\bhãy cùng (tìm hiểu|khám phá)\b", r"\bbài viết (này|sau đây) sẽ\b",
]

HIDDEN_TEXT_CSS = re.compile(
    r"(color\s*:\s*(#fff\b|#ffffff\b|white\b|transparent\b)"
    r"|font-size\s*:\s*(0(px)?|1px)\b"
    r"|visibility\s*:\s*hidden"
    r"|display\s*:\s*none"
    r"|opacity\s*:\s*0(\.0+)?\s*[;\"']"
    r"|text-indent\s*:\s*-\d{4,}"
    r"|clip(-path)?\s*:\s*(rect\(0|inset\(100%|polygon\(0)"
    r"|position\s*:\s*absolute[^;\"']*(left|top)\s*:\s*-\d{4,})",
    re.I)

BOT_SNIFFING = re.compile(
    r"(googlebot|bingbot|gptbot|claudebot|perplexitybot)['\"]?\s*[)=]"
    r"|is(?:Google)?Bot\s*[=(&|]"
    r"|user-?agent[^\n]{0,60}(googlebot|bot)\b",
    re.I)

OFFICIAL_SOURCE_DOMAINS = [
    "pearsonpte.com", "pearson.com", "gov.au", "homeaffairs.gov.au", "canada.ca",
    "gov.uk", "immigration.govt.nz", "education.govt.nz", "gov.vn", "moet.gov.vn",
    "immi.homeaffairs.gov.au", "usvisa-info.com", "britishcouncil.org",
]

MONEY_ANCHOR = re.compile(
    r"(best|top|cheap|cheapest|discount|coupon|deal|price|pricing|buy|order|free download|"
    r"\d+% off|money back)|"
    r"(rẻ nhất|tốt nhất|giảm giá|mã giảm|khuyến mãi|báo giá|mua ngay|tải miễn phí|cam kết đầu ra)",
    re.I)

FIRST_HAND_MARKERS = re.compile(
    r"\b(we tested|our data|our analysis|we analysed|we analyzed|in our experience|"
    r"i have|i tested|first-hand|we surveyed|n\s*=\s*\d|\d[\d.,]*\s*(learners|students|học viên))\b|"
    r"(dữ liệu (nội bộ|thật)|chúng tôi (đã )?(kiểm thử|phân tích|khảo sát)|"
    r"theo (thống kê|số liệu)|kinh nghiệm (thực tế|trực tiếp)|phản hồi (từ|của) (trainer|học viên))",
    re.I)

HAS_NUMBER = re.compile(r"\d")


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Link:
    href: str
    text: str
    rel: str = ""
    external: bool = False


@dataclass
class Doc:
    path: str
    raw: str
    fmt: str = "md"
    fm: dict = field(default_factory=dict)
    title: str = ""
    body: str = ""
    headings: list = field(default_factory=list)      # [(level, text)]
    links: list = field(default_factory=list)         # [Link]
    words: int = 0
    toks: list = field(default_factory=list)
    sh: set = field(default_factory=set)
    skeleton: tuple = ()
    url: str = ""

    @property
    def name(self) -> str:
        return os.path.basename(self.path)


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw
    block, rest = m.group(1), raw[m.end():]
    fm: dict = {}
    try:
        import yaml  # type: ignore
        fm = yaml.safe_load(block) or {}
        if not isinstance(fm, dict):
            fm = {}
    except Exception:
        for line in block.splitlines():
            mm = re.match(r'^\s*([A-Za-z_][\w-]*)\s*:\s*(.*)$', line)
            if mm:
                v = mm.group(2).strip().strip('"').strip("'")
                if v.startswith("[") and v.endswith("]"):
                    fm[mm.group(1)] = [x.strip().strip('"\'') for x in v[1:-1].split(",") if x.strip()]
                else:
                    fm[mm.group(1)] = v
    return fm, rest


def strip_markdown(text: str) -> str:
    """Bỏ cú pháp markdown, GIỮ lại HTML inline (để phát hiện hidden text / anchor rel)."""
    t = re.sub(r"^```.*?```", " ", text, flags=re.S | re.M)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"^\s*\[([^\]]+)\]\([^)]+\)\s*:\s*\S+\s*$", " ", t, flags=re.M)  # ref defs
    t = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"[\1]", t)                          # images
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.M)
    t = re.sub(r"^>\s?", "", t, flags=re.M)
    t = re.sub(r"^[-*+]\s+", "", t, flags=re.M)
    t = re.sub(r"^\d+\.\s+", "", t, flags=re.M)
    t = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", t)
    t = re.sub(r"^\|.*\|\s*$", lambda m: " ".join(
        c.strip() for c in m.group(0).strip("|").split("|")), t, flags=re.M)
    t = re.sub(r"^[\s|:-]+$", " ", t, flags=re.M)
    return t


def md_links(text: str, base_url: str = "https://ptemagic.com") -> list[Link]:
    out: list[Link] = []
    # markdown [text](href "title")
    for m in re.finditer(r'(?<!!)\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"[^"]*")?\s*\)', text):
        href = m.group(2).strip()
        if href.startswith(("#", "mailto:", "tel:")):
            continue
        absu = urllib.parse.urljoin(base_url + "/", href)
        out.append(Link(href=absu, text=m.group(1).strip(),
                        external=urllib.parse.urlsplit(absu).hostname not in
                                 (urllib.parse.urlsplit(base_url).hostname,)))
    # inline HTML anchors
    for m in re.finditer(r'<a\b([^>]*)>(.*?)</a>', text, re.S | re.I):
        attrs, inner = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        hm = re.search(r'href\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
        rm = re.search(r'rel\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
        if not hm or hm.group(1).startswith(("#", "mailto:", "tel:")):
            continue
        absu = urllib.parse.urljoin(base_url + "/", hm.group(1))
        out.append(Link(href=absu, text=inner.strip(), rel=(rm.group(1) if rm else ""),
                        external=urllib.parse.urlsplit(absu).hostname not in
                                 (urllib.parse.urlsplit(base_url).hostname,)))
    return out


def load_doc(path: str, fmt: str = "auto") -> Doc:
    raw = open(path, encoding="utf-8", errors="replace").read()
    if fmt == "auto":
        fmt = "html" if path.lower().endswith((".html", ".htm")) else "md"
    if fmt == "html":
        soup = soup_of(raw)
        fm: dict = {}
        title_tag = soup.find("title")
        h1 = soup.find(["h1", "h2"])
        title = (title_tag.get_text(" ", strip=True) if title_tag
                 else (h1.get_text(" ", strip=True) if h1 else os.path.basename(path)))
        for sel in ("script", "style", "noscript"):
            for t in soup.find_all(sel):
                t.extract()
        heads = [(int(h.name[1]), h.get_text(" ", strip=True))
                 for h in soup.find_all(re.compile(r"^h[1-6]$"))]
        body_soup = soup.body or soup
        body = re.sub(r"\s+", " ", body_soup.get_text(" ", strip=True))
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            links.append(Link(href=href, text=a.get_text(" ", strip=True),
                              rel=" ".join(a.get("rel") or []),
                              external=href.startswith("http") and "ptemagic.com" not in href))
        url = ""
        c = soup.find("link", rel="canonical")
        if c and c.get("href"):
            url = c["href"]
        doc = Doc(path=path, raw=raw, fmt="html", fm=fm, title=title, body=body,
                  headings=heads, links=links, url=url or path)
    else:
        fm, rest = parse_frontmatter(raw)
        title = str(fm.get("title") or "").strip()
        m = re.search(r"^#\s+(.+)$", rest, re.M)
        if not title and m:
            title = m.group(1).strip()
        heads = [(len(hm.group(1)), hm.group(2).strip())
                 for hm in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", rest, re.M)]
        body = strip_markdown(rest)
        # bỏ dòng heading để đo mật độ keyword trên prose, nhưng vẫn giữ heading để đo tỷ lệ
        doc = Doc(path=path, raw=raw, fmt="md", fm=fm, title=title or os.path.basename(path),
                  body=re.sub(r"\s+", " ", body), headings=heads,
                  links=md_links(rest), url=str(fm.get("slug") or fm.get("url") or path))
    doc.words = len(tokens(doc.body))
    doc.toks = content_tokens(doc.body)
    doc.sh = shingles(doc.body, DEFAULTS["shingle_size"])
    doc.skeleton = tuple(re.sub(r"[^a-z0-9 ]", "", h[1].lower()).strip()
                         for h in doc.headings if h[0] >= 2)
    return doc


def load_corpus(directory: str, exclude: str, limit: int = 400) -> list[Doc]:
    if not directory or not os.path.isdir(directory):
        return []
    out: list[Doc] = []
    ex = os.path.abspath(exclude)
    for root, _dirs, files in os.walk(directory):
        for f in sorted(files):
            if not f.lower().endswith((".md", ".markdown", ".html", ".htm")):
                continue
            p = os.path.abspath(os.path.join(root, f))
            if p == ex:
                continue
            try:
                out.append(load_doc(p))
            except Exception as e:  # noqa: BLE001
                eprint(f"[warn] bỏ qua {p}: {e}")
            if len(out) >= limit:
                return out
    return out


# --------------------------------------------------------------------------- #
# Hit & registry
# --------------------------------------------------------------------------- #
@dataclass
class Hit:
    code: str
    severity: str          # "BLOCK" | "WARN"
    policy: str            # tên chính sách Google tương ứng
    message: str
    evidence: str = ""
    fix: str = ""

    def to_dict(self) -> dict:
        return {"code": self.code, "severity": self.severity, "policy": self.policy,
                "message": self.message, "evidence": self.evidence[:400], "fix": self.fix}


def cfgval(cfg: dict, key: str):
    v = thresholds(cfg, "policy_gate", key, default=None)
    return DEFAULTS[key] if v is None else v


# --------------------------------------------------------------------------- #
# Các check
# --------------------------------------------------------------------------- #
def c_near_duplicate(doc, corpus, cfg) -> list[Hit]:
    if not corpus:
        return []
    hits = []
    for peer in corpus:
        if not doc.sh or not peer.sh:
            continue
        j = jaccard(doc.sh, peer.sh)
        if j >= cfgval(cfg, "near_duplicate_block"):
            hits.append(Hit(
                "NEAR_DUPLICATE", "BLOCK", "Scaled content abuse",
                f"Giống {j*100:.0f}% với '{peer.name}' đã publish "
                f"(ngưỡng BLOCK {cfgval(cfg,'near_duplicate_block')*100:.0f}%).",
                f"{doc.name} ≈ {peer.name} · Jaccard={j:.3f} trên 5-gram",
                "Không publish bản này. Hoặc gộp vào bài cũ (301), hoặc viết lại để nó trả lời "
                "một câu hỏi KHÁC với dữ liệu/ví dụ/góc nhìn khác. Đổi tiêu đề và vài câu "
                "không làm giảm độ giống có ý nghĩa."))
        elif j >= cfgval(cfg, "near_duplicate_warn"):
            hits.append(Hit(
                "NEAR_DUPLICATE_WARN", "WARN", "Scaled content abuse",
                f"Giống {j*100:.0f}% với '{peer.name}' (ngưỡng cảnh báo "
                f"{cfgval(cfg,'near_duplicate_warn')*100:.0f}%).",
                f"Jaccard={j:.3f}",
                "Rà lại: bài này có lý do tồn tại độc lập không? Nếu chỉ khác 1 biến thể "
                "(quốc gia, năm, format) → cân nhắc gộp thành 1 bài có section."))
    return hits[:6]


def c_template_shell(doc, corpus, cfg) -> list[Hit]:
    """Doorway pages: nhiều URL dùng chung 1 vỏ heading, phần thân khác nhau rất ít."""
    if not doc.skeleton or len(corpus) < 3:
        return []
    same = []
    for peer in corpus:
        if not peer.skeleton:
            continue
        a, b = set(doc.skeleton), set(peer.skeleton)
        if not a or not b:
            continue
        skel_j = jaccard(a, b)
        if skel_j >= 0.85:
            same.append((peer, skel_j))
    min_urls = cfgval(cfg, "template_shell_min_urls")
    if len(same) + 1 < min_urls:
        return []
    deltas = [jaccard(doc.sh, p.sh) for p, _ in same]
    avg_delta = sum(deltas) / len(deltas) if deltas else 0.0
    threshold = cfgval(cfg, "template_shell_body_delta_min")
    if avg_delta >= threshold:
        return [Hit(
            "TEMPLATE_SHELL", "BLOCK", "Doorway pages / Scaled content abuse",
            f"{len(same)+1} URL dùng chung một khung heading (giống ≥85%) trong khi nội dung "
            f"thân cũng giống nhau {avg_delta*100:.0f}%.",
            "skeleton H2/H3: " + " → ".join(list(doc.skeleton)[:8])
            + f" | các file: {', '.join(p.name for p, _ in same[:6])}",
            "Đây là hình dạng kinh điển của doorway pages: cùng một cái vỏ, chỉ đổi biến thể "
            "(quốc gia / năm / format bài thi). Google xét 'lượng có đang chạy nhanh hơn giá trị "
            "mỗi trang thêm được không'. Hoặc gộp thành 1 bài có section, hoặc làm cho mỗi trang "
            "thật sự khác: số liệu riêng, yêu cầu riêng của nước/trường đó, ví dụ riêng, "
            "nguồn chính phủ riêng.")]
    return [Hit(
        "TEMPLATE_SHELL_WARN", "WARN", "Doorway pages",
        f"{len(same)+1} URL chung khung heading, nhưng thân đủ khác biệt ({avg_delta*100:.0f}% giống).",
        "skeleton: " + " → ".join(list(doc.skeleton)[:6]),
        "Chấp nhận được NẾU mỗi trang có dữ liệu riêng thật. Kiểm tra tay 2 trang bất kỳ "
        "trong nhóm: nếu đổi tên quốc gia là xong thì đó là doorway.")]


def _primary_keywords(doc) -> list[str]:
    out = []
    for k in ("primary_keyword", "keyword", "target_keyword", "focus_keyword"):
        v = doc.fm.get(k)
        if isinstance(v, list):
            out.extend(str(x) for x in v)
        elif v:
            out.append(str(v))
    if not out and doc.title:
        out.append(doc.title.split("|")[0].strip())
    return [k for k in out if k]


def c_keyword_stuffing(doc, corpus, cfg) -> list[Hit]:
    hits = []
    if doc.words < 40:
        return hits
    body_l = doc.body.lower()
    max_d = cfgval(cfg, "keyword_density_max")
    # Trang ngắn lặp chủ đề là chuyện tự nhiên; chỉ siết chặt ngưỡng khi bài đã đủ dài.
    # Không có điều này thì một bài 200 từ đúng chuẩn vẫn bị báo stuffing.
    if doc.words < 500:
        max_d = max_d * 1.6
    max_h = cfgval(cfg, "keyword_in_heading_ratio_max")
    for kw in _primary_keywords(doc):
        kwl = kw.lower().strip()
        if len(tokens(kwl)) < 2:
            continue
        # (a) Heading bị nhồi — đo độc lập, không phụ thuộc số lần lặp trong thân bài
        if doc.headings:
            with_kw = sum(1 for _lvl, h in doc.headings if kwl in h.lower())
            hratio = with_kw / len(doc.headings)
            if hratio > max_h and with_kw >= 3:
                hits.append(Hit(
                    "HEADING_KEYWORD_STUFFED", "BLOCK", "Keyword stuffing",
                    f"{with_kw}/{len(doc.headings)} heading chứa exact-match '{kwl}' "
                    f"({hratio*100:.0f}% > {max_h*100:.0f}%).",
                    "; ".join(h for _l, h in doc.headings if kwl in h.lower())[:200],
                    "Heading phải mô tả nội dung của section, không phải chỗ nhét keyword."))
        n = len(re.findall(re.escape(kwl), body_l))
        # (b) Mật độ trong thân bài. Yêu cầu ≥4 lần lặp TRƯỚC khi kết luận "nhồi":
        # một lần xuất hiện của cụm 6 từ trong bài 80 từ cho ra "mật độ 7.5%" — đó là
        # toán học vô nghĩa. Gate báo oan một lần là người ta tắt gate.
        if n < 4:
            continue
        density = (n * len(tokens(kwl))) / max(1, doc.words)
        if density > max_d:
            hits.append(Hit(
                "KEYWORD_STUFFING", "BLOCK", "Keyword stuffing",
                f"Mật độ exact-match '{kwl}' = {density*100:.1f}% (>{max_d*100:.1f}%).",
                f"{n} lần trong {doc.words} từ",
                "Viết lại cho người đọc. Dùng biến thể tự nhiên, đại từ, và entity liên quan "
                "(PTE Academic, Pearson, communicative skills) thay vì lặp nguyên cụm."))
    return hits[:4]


def c_hidden_text(doc, corpus, cfg) -> list[Hit]:
    raw = doc.raw
    hits = []
    kwset = {k.lower() for k in _primary_keywords(doc)}
    for m in re.finditer(r'<(span|div|p|a|li)\b([^>]*)>(.*?)</\1>', raw, re.S | re.I):
        attrs, inner = m.group(2), m.group(3)
        style = attrs
        sm = re.search(r'style\s*=\s*["\']([^"\']*)["\']', attrs, re.I)
        if sm:
            style = sm.group(1)
        cls = re.search(r'class\s*=\s*["\']([^"\']*)["\']', attrs, re.I)
        cls = cls.group(1) if cls else ""
        hidden = bool(HIDDEN_TEXT_CSS.search(style)) or re.search(
            r"\b(sr-only-hidden|visually-hidden-fake|seo-text-hidden|hidden-seo)\b", cls, re.I)
        if not hidden:
            continue
        text = re.sub(r"<[^>]+>", " ", inner).strip()
        if len(tokens(text)) < 3:
            continue
        has_kw = any(k in text.lower() for k in kwset) or bool(
            re.search(r"(pte|mock test|practice test|course|khoá học|khóa học)", text, re.I))
        if has_kw:
            hits.append(Hit(
                "HIDDEN_TEXT", "BLOCK", "Hidden text & link abuse",
                "Có khối text bị ẩn bằng CSS và chứa keyword.",
                f"style/class={style[:80] or cls[:60]!r} · text={text[:160]!r}",
                "Xoá hoàn toàn. Lưu ý: accordion/tab/slider ẩn vì lý do usability thì KHÔNG vi phạm; "
                "vi phạm là khi ẩn chỉ để nhét keyword cho bot đọc."))
    return hits[:5]


def c_cloaking(doc, corpus, cfg) -> list[Hit]:
    hits = []
    if BOT_SNIFFING.search(doc.raw):
        hits.append(Hit(
            "CLOAKING_BOT_SNIFFING", "BLOCK", "Cloaking / Sneaky redirects",
            "Code có phân nhánh theo user-agent của bot.",
            BOT_SNIFFING.search(doc.raw).group(0)[:120],
            "Bỏ ngay. Phục vụ cùng một nội dung cho Googlebot và người dùng. "
            "Nếu cần render khác cho bot vì lý do kỹ thuật, dùng dynamic rendering có chủ đích "
            "và đảm bảo nội dung tương đương."))
    if doc.fmt == "html":
        soup = soup_of(doc.raw)
        nos = soup.find_all("noscript")
        if nos:
            nos_text = " ".join(n.get_text(" ", strip=True) for n in nos)
            vis_text = doc.body
            if len(tokens(nos_text)) > 60:
                j = jaccard(shingles(nos_text, 5), shingles(vis_text, 5))
                if j < 0.2:
                    hits.append(Hit(
                        "CLOAKING_NOSCRIPT_MISMATCH", "WARN", "Cloaking",
                        "Nội dung trong <noscript> khác hẳn nội dung hiển thị "
                        f"(chỉ giống {j*100:.0f}%).",
                        nos_text[:180],
                        "Kiểm tra: nếu <noscript> chứa nhiều keyword hơn bản hiển thị, "
                        "Google có thể xem là cloaking."))
    return hits


def c_anchor_over_optimized(doc, corpus, cfg) -> list[Hit]:
    ext = [l for l in doc.links if l.external]
    if len(ext) < 2:
        return []
    money = [l for l in ext if MONEY_ANCHOR.search(l.text or "")]
    ratio = len(money) / len(ext)
    limit = cfgval(cfg, "outbound_exact_match_anchor_max")
    if ratio > limit:
        return [Hit(
            "ANCHOR_OVER_OPTIMIZED", "BLOCK", "Link spam",
            f"{len(money)}/{len(ext)} anchor link ra ngoài là dạng commercial/money "
            f"({ratio*100:.0f}% > {limit*100:.0f}%).",
            "; ".join(f'"{l.text[:40]}" → {l.href[:50]}' for l in money[:5]),
            "Anchor ra ngoài phải mô tả trang đích, không phải chỗ đặt keyword thương mại. "
            "Nếu đây là link được trả tiền → bắt buộc rel=\"sponsored\" (xem check kế tiếp), "
            "và cân nhắc bỏ hẳn nếu không giúp người đọc.")]
    return []


def c_paid_link_rel(doc, corpus, cfg) -> list[Hit]:
    bad = []
    for l in doc.links:
        if not l.external:
            continue
        tracked = re.search(r"(utm_|gclid|fbclid|ref=|aff=|affiliate|partner=|tag=)", l.href, re.I)
        paid_hint = MONEY_ANCHOR.search(l.text or "")
        if (tracked or paid_hint) and not re.search(r"(sponsored|nofollow|ugc)", l.rel or "", re.I):
            bad.append(l)
    if not bad:
        return []
    return [Hit(
        "PAID_LINK_MISSING_REL", "BLOCK", "Link spam",
        f"{len(bad)} link ra ngoài có dấu hiệu tracking/thương mại nhưng thiếu rel=\"sponsored\".",
        "; ".join(f"{l.text[:30]} → {l.href[:60]}" for l in bad[:5]),
        'Thêm rel="sponsored" (hoặc nofollow nếu không chắc đây là link trả tiền). '
        'Google coi link mua/bán truyền PageRank mà không khai báo là link spam.')]


def c_off_topic(doc, corpus, cfg) -> list[Hit]:
    """BLOCK khi thuật ngữ ngoài lĩnh vực nằm ở TITLE/HEADING (chủ đích của trang);
    chỉ WARN khi nó thoáng xuất hiện trong thân bài (có thể là trích dẫn/ngữ cảnh)."""
    heading_text = (doc.title + " " + " ".join(h for _l, h in doc.headings)).lower()
    body_l = doc.body.lower()
    in_heading = [t for t in OFF_TOPIC_TERMS if t in heading_text]
    in_body = [t for t in OFF_TOPIC_TERMS if t in body_l and t not in in_heading]
    advice = ("PTE Magic là domain có authority về luyện thi tiếng Anh. Đăng nội dung không liên "
              "quan (coupon, gambling, vay nóng, affiliate sản phẩm) để mượn authority là site "
              "reputation abuse — vi phạm tính từ phía HOST. Xoá, hoặc chuyển sang domain khác, "
              "hoặc đặt ở subdomain tách biệt có editorial oversight + noindex.")
    if in_heading:
        return [Hit(
            "SITE_REPUTATION_ABUSE", "BLOCK", "Site reputation abuse",
            f"Title/heading chứa thuật ngữ ngoài lĩnh vực PTE/du học: {', '.join(in_heading[:5])}.",
            doc.title[:120], advice)]
    if in_body:
        return [Hit(
            "OFF_TOPIC_TERMS_IN_BODY", "WARN", "Site reputation abuse",
            f"Thân bài thoáng chứa thuật ngữ ngoài lĩnh vực: {', '.join(in_body[:5])}.",
            doc.title[:120],
            "Kiểm tra ngữ cảnh. Nếu chỉ là trích dẫn/ví dụ thì bỏ qua. Nếu là nội dung affiliate "
            "thật thì " + advice[0].lower() + advice[1:])]
    # heuristic: nội dung quá lệch topic PTE/du học
    topic_terms = {"pte", "pearson", "exam", "test", "english", "visa", "study", "du học",
                   "thi", "điểm", "score", "migration", "định cư", "học", "student", "university"}
    overlap = len(topic_terms & set(doc.toks))
    if doc.words > 200 and overlap <= 1:
        return [Hit(
            "OFF_TOPIC_CONTENT", "WARN", "Site reputation abuse / Helpful content",
            f"Bài {doc.words} từ nhưng gần như không liên quan chủ đề PTE/du học "
            f"(chỉ {overlap} term trùng).",
            doc.title[:120],
            "Xác nhận bài này thuộc về PTE Magic. Nếu là nội dung đối tác/khách đặt → cần "
            "editorial review, disclosure rõ, và cân nhắc noindex.")]
    return []


def _is_ymyl(doc, cfg) -> bool:
    hay = (doc.url + " " + doc.title + " " + doc.body[:4000]).lower()
    pats = list(YMYL_KEYWORDS)
    for p in ((cfg.get("ymyl") or {}).get("url_patterns") or []):
        pats.append(p.strip("*").lower())
    return any(p and p in hay for p in pats)


def _parse_date(v) -> float | None:
    """Parse ngày từ frontmatter (date object, ISO, hoặc dd/mm/yyyy). Trả epoch hoặc None."""
    if not v:
        return None
    if hasattr(v, "timestamp"):          # datetime.date / datetime.datetime (PyYAML tự parse)
        try:
            return float(v.timestamp() if hasattr(v, "hour") else
                         time.mktime(v.timetuple()))
        except Exception:
            return None
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m"):
        try:
            return time.mktime(time.strptime(s[:len(fmt) + 4] if fmt.endswith("%S") else s, fmt))
        except Exception:
            continue
    m = re.match(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        try:
            return time.mktime(time.strptime(
                f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", "%Y-%m-%d"))
        except Exception:
            return None
    return None


def c_ymyl(doc, corpus, cfg) -> list[Hit]:
    if not _is_ymyl(doc, cfg):
        return []
    hits = []
    author = doc.fm.get("author") or ""
    reviewed = re.search(r"(?im)^\s*(reviewed by|người duyệt|duyệt bởi|kiểm chứng bởi)\s*[:\-]?\s*(.+)$",
                         doc.raw)
    if not author and not reviewed:
        hits.append(Hit(
            "YMYL_NO_AUTHOR", "BLOCK", "E-E-A-T / Helpful content",
            "Nội dung YMYL (visa/định cư/học phí/học bổng/y tế) nhưng không có author.",
            f"title: {doc.title[:100]}",
            'Thêm frontmatter `author:` + `author_url:` trỏ trang profile thật, và dòng '
            '"Reviewed by: <tên> · <ngày>" ở cuối bài. Với nội dung di trú, người review nên '
            'là người có chuyên môn (trainer, cố vấn du học) và nói rõ vai trò.'))
    d = _parse_date(doc.fm.get("date_modified") or doc.fm.get("date_updated")
                   or doc.fm.get("date_published") or doc.fm.get("date"))
    max_days = cfgval(cfg, "ymwl_max_days_since_update")
    if not d:
        hits.append(Hit(
            "YMYL_NO_DATE", "BLOCK", "E-E-A-T / Helpful content",
            "Nội dung YMYL không có ngày publish/update.",
            "frontmatter thiếu date_published/date_modified",
            "Thêm ngày. Yêu cầu visa và điểm số thay đổi theo năm; Google và người đọc đều cần "
            "biết thông tin còn hiệu lực không."))
    else:
        age = (time.time() - d) / 86400.0
        if age > max_days:
            hits.append(Hit(
                "YMYL_STALE", "BLOCK", "E-E-A-T / Helpful content",
                f"Nội dung YMYL đã {int(age)} ngày chưa cập nhật (>{max_days} ngày).",
                f"date={time.strftime('%Y-%m-%d', time.localtime(d))}",
                "Kiểm chứng lại toàn bộ số liệu với nguồn chính phủ hiện hành rồi cập nhật "
                "date_modified. Không chỉ đổi ngày mà không kiểm tra nội dung."))
    official = [l for l in doc.links
                if any(dm in l.href for dm in OFFICIAL_SOURCE_DOMAINS)]
    if not official:
        hits.append(Hit(
            "YMYL_NO_OFFICIAL_SOURCE", "BLOCK", "E-E-A-T / Helpful content",
            "Nội dung YMYL không link tới nguồn chính thức nào "
            "(Pearson, homeaffairs.gov.au, canada.ca, immigration.govt.nz, gov.uk…).",
            f"các link hiện có: {[l.href[:45] for l in doc.links[:5]]}",
            "Thêm link nguồn chính phủ/Pearson tại đúng chỗ khẳng định số liệu. "
            "Đây là tín hiệu Trust mạnh nhất cho nội dung di trú."))
    if doc.words < cfgval(cfg, "ymwl_min_words"):
        hits.append(Hit(
            "YMYL_TOO_THIN", "WARN", "Helpful content",
            f"Nội dung YMYL chỉ {doc.words} từ (<{cfgval(cfg,'ymwl_min_words')}).",
            doc.title[:100],
            "Chủ đề visa/học bổng cần đủ sâu: yêu cầu, chi phí thật, mốc thời gian, "
            "rủi ro, nguồn. Nếu không đủ, gộp vào bài trụ cột."))
    return hits


def c_guarantee(doc, corpus, cfg) -> list[Hit]:
    hits = []
    for pat in GUARANTEE_PATTERNS:
        m = re.search(pat, doc.body + " " + doc.title, re.I)
        if m:
            hits.append(Hit(
                "GUARANTEE_CLAIM", "BLOCK", "Deceptive content / Spam policies",
                f"Câu cam kết kết quả: \"{m.group(0)}\".",
                (doc.body[max(0, m.start()-70):m.start()+90]).strip(),
                "Bỏ khẳng định chắc chắn về điểm/visa. Đổi thành dạng có điều kiện: "
                "\"học viên đạt X sau Y tháng luyện tập\" (kèm số liệu thật), hoặc "
                "\"theo yêu cầu của <cơ quan>, bạn cần điểm Z\". Cam kết đầu ra trong nội "
                "dung di trú vừa là rủi ro pháp lý vừa là deceptive content theo spam policies."))
    return hits[:3]


def c_ai_unedited(doc, corpus, cfg) -> list[Hit]:
    hits = []
    found = []
    for pat in AI_BOILERPLATE:
        for m in re.finditer(pat, doc.body, re.I):
            found.append(m.group(0))
    if len(found) >= 3:
        hits.append(Hit(
            "AI_BOILERPLATE", "WARN", "Scaled content abuse / Helpful content",
            f"{len(found)} cụm văn mẫu đặc trưng của AI chưa được biên tập.",
            ", ".join(sorted(set(f.lower() for f in found))[:6]),
            "Đây không phải bằng chứng vi phạm, nhưng là dấu hiệu bài chưa qua tay người. "
            "Viết lại các câu này bằng ngôn ngữ bạn thật sự dùng khi tư vấn học viên."))
    return hits


def c_no_value_add(doc, corpus, cfg) -> list[Hit]:
    signals = {
        "số liệu cụ thể": bool(re.search(r"\d[\d.,]*\s*(%|phần trăm|bài|học viên|students|learners|n\s*=)",
                                         doc.body, re.I)) or len(re.findall(r"\b\d{2,}\b", doc.body)) >= 4,
        "nguồn trích dẫn": len(doc.links) >= 1 and any(
            d in l.href for l in doc.links for d in OFFICIAL_SOURCE_DOMAINS),
        "trải nghiệm trực tiếp": bool(FIRST_HAND_MARKERS.search(doc.body)),
        "author/reviewer": bool(doc.fm.get("author") or re.search(r"(?i)reviewed by", doc.raw)),
    }
    missing = [k for k, v in signals.items() if not v]
    if len(missing) >= 3:
        return [Hit(
            "NO_VALUE_ADD", "WARN", "Helpful content / Scaled content abuse",
            f"Thiếu {len(missing)}/4 tín hiệu giá trị: {', '.join(missing)}.",
            json.dumps(signals, ensure_ascii=False),
            "Tiêu chí của Google là 'giá trị độc đáo so với những gì đang rank'. Thêm ÍT NHẤT một "
            "thứ chỉ PTE Magic có: thống kê từ dữ liệu chấm AI, template trainer viết, ảnh score "
            "report thật, hoặc lỗi cụ thể của học viên Việt Nam.")]
    if len(missing) == 2 and _is_ymyl(doc, cfg):
        return [Hit(
            "NO_VALUE_ADD", "WARN", "Helpful content",
            f"Nội dung YMYL thiếu 2/4 tín hiệu giá trị: {', '.join(missing)}.",
            json.dumps(signals, ensure_ascii=False),
            "Với YMYL, chuẩn cao hơn. Bổ sung cả 4 tín hiệu.")]
    return []


def c_thin(doc, corpus, cfg) -> list[Hit]:
    if doc.words < cfgval(cfg, "min_words_warn") and "noindex" not in str(doc.fm.get("robots", "")):
        return [Hit(
            "THIN_CONTENT", "WARN", "Scaled content abuse / Thin content",
            f"Bài chỉ ~{doc.words} từ (ngưỡng cảnh báo {cfgval(cfg,'min_words_warn')}).",
            doc.title[:100],
            "Không có ngưỡng từ khoá chính thức nào của Google, nhưng trang mỏng hàng loạt là "
            "dấu hiệu rõ nhất của scaled content abuse. Mở rộng bằng giá trị thật hoặc gộp bài.")]
    return []


def c_expired_domain(doc, corpus, cfg) -> list[Hit]:
    dh = (cfg.get("domain_history") or {})
    if dh.get("acquired_expired"):
        return [Hit(
            "EXPIRED_DOMAIN_REUSE", "WARN", "Expired domain abuse",
            f"Domain {dh.get('domain','?')} được mua lại từ chủ cũ "
            f"({dh.get('previous_niche','không rõ')}), nay dùng cho {dh.get('current_niche','?')}.",
            json.dumps(dh, ensure_ascii=False)[:300],
            "Mua domain hết hạn thì hợp lệ NẾU nội dung mới liên quan niche cũ. Nếu không liên "
            "quan mà chỉ để mượn authority cũ → expired domain abuse. Kiểm tra backlink profile "
            "cũ và disavow/301 có chủ đích.")]
    return []


CHECKS = [c_near_duplicate, c_template_shell, c_keyword_stuffing, c_hidden_text,
          c_cloaking, c_anchor_over_optimized, c_paid_link_rel, c_off_topic,
          c_ymyl, c_guarantee, c_ai_unedited, c_no_value_add, c_thin, c_expired_domain]

ALL_CHECK_CODES = {
    "NEAR_DUPLICATE", "NEAR_DUPLICATE_WARN", "TEMPLATE_SHELL", "TEMPLATE_SHELL_WARN",
    "KEYWORD_STUFFING", "HEADING_KEYWORD_STUFFED", "HIDDEN_TEXT",
    "CLOAKING_BOT_SNIFFING", "CLOAKING_NOSCRIPT_MISMATCH",
    "ANCHOR_OVER_OPTIMIZED", "PAID_LINK_MISSING_REL",
    "SITE_REPUTATION_ABUSE", "OFF_TOPIC_CONTENT", "OFF_TOPIC_TERMS_IN_BODY",
    "EXPIRED_DOMAIN_REUSE",
    "YMYL_NO_AUTHOR", "YMYL_NO_DATE", "YMYL_STALE", "YMYL_NO_OFFICIAL_SOURCE",
    "YMYL_TOO_THIN", "YMYL_MISSING_EVIDENCE", "GUARANTEE_CLAIM",
    "AI_BOILERPLATE", "NO_VALUE_ADD", "THIN_CONTENT",
}

# Alias: gộp các code YMYL chi tiết thành 1 code tổng để báo cáo dễ đọc
YMYL_CODES = {"YMYL_NO_AUTHOR", "YMYL_NO_DATE", "YMYL_STALE", "YMYL_NO_OFFICIAL_SOURCE"}


def run_gate(path: str, corpus_dir: str = "", cfg: dict | None = None,
             fmt: str = "auto") -> dict:
    cfg = cfg or {}
    doc = load_doc(path, fmt)
    corpus = load_corpus(corpus_dir, path)
    hits: list[Hit] = []
    for fn in CHECKS:
        try:
            hits.extend(fn(doc, corpus, cfg))
        except Exception as e:  # noqa: BLE001
            eprint(f"[warn] check {fn.__name__} lỗi: {type(e).__name__}: {e}")

    # gộp YMYL chi tiết → thêm 1 hit tổng (để code YMYL_MISSING_EVIDENCE xuất hiện)
    ymyl_hits = [h for h in hits if h.code in YMYL_CODES]
    if ymyl_hits:
        hits.append(Hit(
            "YMYL_MISSING_EVIDENCE", "BLOCK", "E-E-A-T / Helpful content",
            f"Nội dung YMYL thiếu {len(ymyl_hits)} yếu tố bắt buộc: "
            f"{', '.join(sorted({h.code for h in ymyl_hits}))}.",
            " · ".join(h.message[:90] for h in ymyl_hits[:3]),
            "Xem references/eeat-checklist.md. Với chủ đề visa/định cư, thiếu 1 trong 4 yếu tố "
            "(author thật, ngày hiệu lực, nguồn chính phủ, độ sâu) là không publish."))

    blocks = [h for h in hits if h.severity == "BLOCK"]
    warns = [h for h in hits if h.severity == "WARN"]
    verdict = "BLOCK" if blocks else ("WARN" if warns else "PASS")

    return {
        "file": path,
        "title": doc.title,
        "words": doc.words,
        "format": doc.fmt,
        "corpus_size": len(corpus),
        "verdict": verdict,
        "is_ymyl": _is_ymyl(doc, cfg),
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "counts": {"BLOCK": len(blocks), "WARN": len(warns)},
        "checks": [h.to_dict() for h in hits],
        "policy_reference": "Google Search Essentials / Spam Policies, updated 2026-05-15",
    }


def to_markdown(res: dict) -> str:
    icon = {"PASS": "✅", "WARN": "⚠️", "BLOCK": "⛔"}[res["verdict"]]
    out = [f"# Policy Gate — {icon} {res['verdict']}", "",
           f"- **File:** `{res['file']}`",
           f"- **Title:** {res['title']}",
           f"- **Số từ:** {res['words']} · **YMYL:** {'có' if res['is_ymyl'] else 'không'}",
           f"- **Corpus so sánh:** {res['corpus_size']} tài liệu đã publish",
           f"- **BLOCK:** {res['counts']['BLOCK']} · **WARN:** {res['counts']['WARN']}",
           f"- **Đối chiếu:** {res['policy_reference']}", ""]
    if res["verdict"] == "BLOCK":
        out += ["> ⛔ **KHÔNG PUBLISH.** Sửa nội dung thật rồi chạy lại.",
                "> Không sửa để lách gate — gate là để bảo vệ bạn và khách hàng.", ""]
    elif res["verdict"] == "WARN":
        out += ["> ⚠️ Publish được, nhưng **phải ghi chú lý do** vào báo cáo tuần "
                "và nói rõ với khách hàng nếu làm dịch vụ.", ""]
    else:
        out += ["> ✅ Đạt. Vẫn cần người đọc lại lần cuối trước khi bấm publish.", ""]

    if res["checks"]:
        out += ["## Chi tiết", "", "| Mức | Code | Chính sách Google | Vấn đề |", "|---|---|---|---|"]
        for h in sorted(res["checks"], key=lambda x: 0 if x["severity"] == "BLOCK" else 1):
            out.append(f"| {h['severity']} | `{h['code']}` | {h['policy']} | {h['message']} |")
        out += ["", "## Bằng chứng & cách sửa", ""]
        for h in res["checks"]:
            out += [f"### {h['severity']} · `{h['code']}` — {h['policy']}", "",
                    h["message"], ""]
            if h["evidence"]:
                out += [f"**Bằng chứng:** `{h['evidence']}`", ""]
            if h["fix"]:
                out += [f"**Cách sửa:** {h['fix']}", ""]
    else:
        out += ["## Chi tiết", "", "Không có finding nào.", ""]
    return "\n".join(out)


def append_log(log_path: str, res: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
    new = not os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["checked_at", "file", "title", "verdict", "blocks", "warns",
                        "words", "ymyl", "codes"])
        w.writerow([res["checked_at"], res["file"], res["title"][:80], res["verdict"],
                    res["counts"]["BLOCK"], res["counts"]["WARN"], res["words"],
                    int(res["is_ymyl"]),
                    ";".join(sorted({h["code"] for h in res["checks"]}))])


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Google policy gate — chặn trước khi publish.")
    p.add_argument("--file", required=True, help="File cần kiểm tra (.md hoặc .html)")
    p.add_argument("--corpus", default="", help="Thư mục chứa nội dung ĐÃ publish để so trùng lặp")
    p.add_argument("--config", default=None)
    p.add_argument("--format", default="auto", choices=["auto", "md", "html"])
    p.add_argument("--json", action="store_true", help="Xuất JSON ra stdout")
    p.add_argument("--out", default=None, help="Ghi báo cáo Markdown vào file này")
    p.add_argument("--log", default=None, help="Append 1 dòng vào CSV log (vd reports/policy-log.csv)")
    p.add_argument("--allow-warn", action="store_true",
                   help="Exit 0 kể cả khi WARN (dùng trong CI khi đã có người duyệt)")
    args = p.parse_args(argv)

    if not os.path.exists(args.file):
        eprint(f"[fatal] không tìm thấy {args.file}")
        return 2
    cfg = load_config(args.config)
    res = run_gate(args.file, args.corpus, cfg, args.format)

    if args.log:
        try:
            append_log(args.log, res)
        except Exception as e:  # noqa: BLE001
            eprint(f"[warn] không ghi log được: {e}")

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        md = to_markdown(res)
        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            open(args.out, "w", encoding="utf-8").write(md)
            eprint(f"[ok] báo cáo → {args.out}")
        print(md)

    if res["verdict"] == "BLOCK":
        return 20
    if res["verdict"] == "WARN" and not args.allow_warn:
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
