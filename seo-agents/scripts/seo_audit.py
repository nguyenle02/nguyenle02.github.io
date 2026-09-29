#!/usr/bin/env python3
"""seo_audit.py — Technical + on-page + i18n + schema auditor cho ptemagic.com.

Triết lý: script này là "evidence collector". Nó chỉ báo cáo những gì ĐO ĐƯỢC từ HTML/HTTP.
Nó không suy diễn chiến lược. Việc xếp hạng ưu tiên và quyết định là của con người + agent.

Dùng:
    python scripts/seo_audit.py --site https://ptemagic.com --max-urls 200
    python scripts/seo_audit.py --offline-dir fixtures/ptemagic --config config/ptemagic.yaml
    python scripts/seo_audit.py --site https://ptemagic.com --only-url https://ptemagic.com/vi

Output:
    <out>/<date>-audit.json   (máy đọc, dùng cho drift.py và cho agent)
    <out>/<date>-audit.md     (người đọc)

Exit code: 0 = ok, 1 = có finding critical, 2 = lỗi chạy.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

from common import (  # noqa: E402
    FindingSet, Fetcher, DEFAULT_UA, SEVERITIES,
    content_tokens, headings, is_image_url, jsonld_blocks, jsonld_types,
    link_href, load_config, load_offline_dir, looks_vietnamese, main_text,
    meta_content, normalize_url, registrable_domain, same_host, shingles,
    jaccard, soup_of, thresholds, tokens, visible_text_len, write_outputs, eprint,
)

VALID_HREFLANG = re.compile(
    r"^(x-default|[a-z]{2,3}(-[A-Za-z]{4})?(-([A-Z]{2}|[0-9]{3}))?)$"
)
AI_CRAWLERS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
               "Claude-Web", "PerplexityBot", "Perplexity-User", "Google-Extended",
               "GoogleOther", "CCBot", "anthropic-ai", "Applebot-Extended",
               "meta-externalagent", "Bytespider", "Amazonbot", "cohere-ai", "MistralAI-User"]


# =========================================================================== #
# 1. Thu thập danh sách URL
# =========================================================================== #
def parse_sitemap(text: str, base: str) -> tuple[list[str], list[str]]:
    """Trả về (urls, nested_sitemaps). Tách XML bằng regex để không cần lxml."""
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text or "")
    nested, pages = [], []
    for u in urls:
        u = u.strip()
        if u.endswith(".xml") or "/sitemap" in u and "?" not in u and u.count("/") <= 5 and not is_image_url(u):
            if u.endswith(".xml"):
                nested.append(u)
                continue
        pages.append(u)
    return [urllib.parse.urljoin(base, u) for u in pages], [urllib.parse.urljoin(base, u) for u in nested]


def collect_urls_live(fetch: Fetcher, site: str, max_urls: int, use_sitemap: bool = True,
                      seeds: list[str] | None = None) -> tuple[list[str], dict]:
    site = normalize_url(site) + "/"
    info: dict = {"robots_txt": None, "sitemaps_found": [], "sitemap_url_count": 0}

    r = fetch.get(site.rstrip("/") + "/robots.txt")
    robots_text = r.get("text") or ""
    info["robots_txt"] = {"status": r.get("status"), "text": robots_text[:4000]}
    declared = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots_text)

    queue: list[str] = [site] + list(seeds or [])
    sitemap_urls: list[str] = []
    if use_sitemap:
        todo = list(declared) or [site.rstrip("/") + "/sitemap.xml"]
        seen_sm: set[str] = set()
        while todo and len(seen_sm) < 25:
            sm = todo.pop(0)
            if sm in seen_sm:
                continue
            seen_sm.add(sm)
            rr = fetch.get(sm)
            if rr.get("status") != 200:
                continue
            info["sitemaps_found"].append({"url": sm, "status": rr.get("status")})
            pages, nested = parse_sitemap(rr.get("text", ""), sm)
            sitemap_urls.extend(pages)
            todo.extend(nested)
        info["sitemap_url_count"] = len(sitemap_urls)

    # Ưu tiên URL từ sitemap (đáng tin hơn crawl), rồi mới crawl thêm
    ordered: list[str] = []
    seen: set[str] = set()
    for u in sitemap_urls + queue:
        n = normalize_url(u, keep_params=True)
        if not n or n in seen or not same_host(n, site):
            continue
        if any(seg in n for seg in ("/sso/", "/dashboard/", "/api/", "/_next/", "/wp-admin")):
            continue
        seen.add(n)
        ordered.append(n)
        if len(ordered) >= max_urls:
            break
    return ordered, info


# =========================================================================== #
# 2. Check từng trang
# =========================================================================== #
def repeated_blocks(text: str, min_words: int = 12) -> list[tuple[str, int]]:
    """Tìm đoạn văn bản lặp lại nguyên văn trong cùng 1 trang (vd carousel render 2 lần)."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(tokens(s)) >= min_words]
    counts = collections.Counter(sents)
    return [(s, c) for s, c in counts.items() if c > 1]


def check_page(page: dict, cfg: dict, ctx: dict) -> tuple[list, dict]:
    fs = FindingSet()
    url = page["url"]
    status = page.get("status")
    html = page.get("text") or ""
    final_url = page.get("final_url") or url
    headers = {k.lower(): v for k, v in (page.get("headers") or {}).items()}
    rec: dict = {"url": url, "status": status, "final_url": final_url,
                 "elapsed_ms": page.get("elapsed_ms"), "error": page.get("error")}

    if page.get("error"):
        fs.add(code="FETCH_ERROR", severity="high", category="technical", url=url,
               message="Không fetch được trang.", evidence=str(page["error"])[:200],
               fix="Kiểm tra DNS/SSL/chặn bot. Nếu là URL nội bộ, loại khỏi sitemap.",
               confidence="high")
        return fs.items, rec
    if status is None:
        return fs.items, rec

    # ---- HTTP status ----
    if status >= 500:
        fs.add(code="HTTP_5XX", severity="critical", category="technical", url=url,
               message=f"Server trả về {status}.", evidence=f"HTTP {status}",
               fix="Sửa lỗi server ngay; URL 5xx trong sitemap làm tụt crawl budget.",
               confidence="high")
        return fs.items, rec
    if status == 404:
        fs.add(code="HTTP_404", severity="critical", category="technical", url=url,
               message="Trang 404 nhưng vẫn nằm trong danh sách crawl/sitemap.",
               evidence=f"HTTP 404", fix="Gỡ khỏi sitemap hoặc 301 về trang liên quan.",
               confidence="high")
        return fs.items, rec
    if status not in (200, 304):
        fs.add(code="HTTP_NON_200", severity="high", category="technical", url=url,
               message=f"HTTP {status} (không phải 200).", evidence=f"HTTP {status} → {final_url}",
               fix="Chuỗi redirect nên kết thúc ở 200 với 1 hop duy nhất.", confidence="high")
    if normalize_url(final_url) != normalize_url(url) and status == 200:
        fs.add(code="URL_REDIRECTED", severity="medium", category="technical", url=url,
               message="URL bị redirect tới URL khác.", evidence=f"{url} → {final_url}",
               fix="Dùng thẳng URL đích trong internal link và sitemap.", confidence="high")
    if url != final_url and normalize_url(url) == normalize_url(final_url):
        pass  # chỉ khác trailing slash / case, đã xử lý ở site-level

    if not html.strip():
        fs.add(code="EMPTY_BODY", severity="critical", category="technical", url=url,
               message="Body rỗng.", evidence="0 byte HTML", fix="Kiểm tra SSR/rendering.",
               confidence="high")
        return fs.items, rec

    soup = soup_of(html)
    rec["html_bytes"] = len(html)

    # ---- robots meta ----
    robots_meta = (meta_content(soup, name="robots") or "").lower()
    rec["robots_meta"] = robots_meta
    if "noindex" in robots_meta:
        fs.add(code="NOINDEX_PRESENT", severity="info", category="technical", url=url,
               message="Trang có meta robots noindex.", evidence=robots_meta,
               fix="Đúng nếu là trang app/login. Sai nếu là trang muốn rank.", confidence="high")

    # ---- title ----
    title_tag = soup.find("title")
    title = title_tag.get_text(" ", strip=True) if title_tag else ""
    rec["title"] = title
    tmin, tmax = thresholds(cfg, "on_page", "title_min", default=30), thresholds(cfg, "on_page", "title_max", default=60)
    if not title:
        fs.add(code="TITLE_MISSING", severity="critical", category="onpage", url=url,
               message="Không có <title>.", evidence="",
               fix="Viết title ≤ 60 ký tự, chứa primary keyword, không lặp brand 2 lần.", confidence="high")
    else:
        if len(title) > tmax:
            fs.add(code="TITLE_TOO_LONG", severity="medium", category="onpage", url=url,
                   message=f"Title {len(title)} ký tự (>{tmax}) — Google sẽ cắt.",
                   evidence=title[:120], fix="Rút gọn, đưa keyword lên đầu.", confidence="high")
        elif len(title) < tmin:
            fs.add(code="TITLE_TOO_SHORT", severity="low", category="onpage", url=url,
                   message=f"Title chỉ {len(title)} ký tự (<{tmin}).", evidence=title,
                   fix="Bổ sung lợi ích/keyword phụ.", confidence="high")
        brand = (cfg.get("business") or {}).get("name", "")
        if brand and title.lower().count(brand.lower()) >= 2:
            fs.add(code="TITLE_BRAND_DUPLICATED", severity="medium", category="onpage", url=url,
                   message=f"Brand '{brand}' xuất hiện {title.lower().count(brand.lower())} lần trong title.",
                   evidence=title, fix="Chỉ giữ brand 1 lần, thường ở cuối.", confidence="high")
        if re.search(r"\|\s*$|-\s*$|^\s*\||^\s*-", title):
            fs.add(code="TITLE_SEPARATOR_DANGLING", severity="low", category="onpage", url=url,
                   message="Title có ký tự phân tách treo ở đầu/cuối.", evidence=title,
                   fix="Sửa template title.", confidence="high")

    # ---- meta description ----
    desc = meta_content(soup, name="description") or ""
    rec["meta_description"] = desc
    dmin, dmax = thresholds(cfg, "on_page", "meta_desc_min", default=70), thresholds(cfg, "on_page", "meta_desc_max", default=155)
    if not desc:
        fs.add(code="META_DESC_MISSING", severity="high", category="onpage", url=url,
               message="Không có meta description.", evidence="",
               fix="Viết 120-155 ký tự, có keyword + CTA, không trùng với title.", confidence="high")
    elif len(desc) > dmax:
        fs.add(code="META_DESC_TOO_LONG", severity="low", category="onpage", url=url,
               message=f"Meta description {len(desc)} ký tự (>{dmax}).", evidence=desc[:180],
               fix="Rút còn ≤155 ký tự.", confidence="high")
    elif len(desc) < dmin:
        fs.add(code="META_DESC_TOO_SHORT", severity="low", category="onpage", url=url,
               message=f"Meta description chỉ {len(desc)} ký tự.", evidence=desc,
               fix="Viết đầy đủ hơn, thêm lợi ích.", confidence="high")
    if desc and title and desc.strip().lower() == title.strip().lower():
        fs.add(code="META_DESC_EQUALS_TITLE", severity="medium", category="onpage", url=url,
               message="Meta description trùng title.", evidence=title,
               fix="Viết description khác, tập trung vào lợi ích/CTA.", confidence="high")

    # ---- canonical ----
    canon_tag = soup.find("link", attrs={"rel": "canonical"})
    canon = canon_tag.get("href") if canon_tag else None
    if canon:
        canon_abs = urllib.parse.urljoin(final_url, canon.strip())
        rec["canonical"] = canon_abs
        if canon.strip().startswith("/"):
            fs.add(code="CANONICAL_RELATIVE", severity="medium", category="technical", url=url,
                   message="Canonical là đường dẫn tương đối.", evidence=canon,
                   fix="Google chấp nhận nhưng nên dùng absolute URL để tránh lỗi.", confidence="high")
        if normalize_url(canon_abs, True) != normalize_url(final_url, True) and status == 200 \
           and "noindex" not in robots_meta:
            fs.add(code="CANONICAL_NOT_SELF", severity="high", category="technical", url=url,
                   message="Canonical trỏ tới URL khác URL đang đứng (không phải trang phân trang/filter).",
                   evidence=f"{final_url} → canonical {canon_abs}",
                   fix="Nếu vô ý: đổi về self-referencing. Nếu cố ý: đảm bảo URL đích index được.",
                   confidence="medium")
    else:
        rec["canonical"] = None
        if "noindex" not in robots_meta:
            fs.add(code="CANONICAL_MISSING", severity="high", category="technical", url=url,
                   message="Không có rel=canonical.", evidence="",
                   fix="Thêm canonical self-referencing absolute cho mọi trang indexable.", confidence="high")

    # ---- headings ----
    hs = headings(soup)
    rec["headings"] = {k: len(v) for k, v in hs.items()}
    h1s = [h for h in hs["h1"] if h.strip()]
    h1_expected = thresholds(cfg, "on_page", "h1_count_exact", default=1)
    if len(hs["h1"]) == 0:
        fs.add(code="H1_MISSING", severity="high", category="onpage", url=url,
               message="Không có <h1>.", evidence="",
               fix="Thêm đúng 1 H1 chứa primary keyword.", confidence="high")
    elif len(hs["h1"]) > h1_expected:
        fs.add(code="MULTIPLE_H1", severity="high", category="onpage", url=url,
               message=f"Có {len(hs['h1'])} thẻ <h1> (chuẩn: {h1_expected}).",
               evidence=" | ".join(hs["h1"])[:300],
               fix="Thường do biến thể mobile/desktop cùng nằm trong DOM. "
                   "Giữ 1 H1 thật, phần còn lại đổi sang <p>/<span> class riêng hoặc aria-hidden.",
               confidence="high")
    if len(set(h1s)) == 1 and len(h1s) > 1:
        fs.add(code="H1_DUPLICATED_TEXT", severity="medium", category="onpage", url=url,
               message="Nhiều H1 với nội dung giống hệt nhau (render trùng).",
               evidence=h1s[0][:200], fix="Bỏ bản render trùng.", confidence="high")
    # empty headings
    for lvl in range(1, 7):
        empties = [h for h in hs[f"h{lvl}"] if not h.strip()]
        if empties:
            fs.add(code="EMPTY_HEADING", severity="low", category="onpage", url=url,
                   message=f"Có {len(empties)} thẻ <h{lvl}> rỗng.",
                   evidence=f"h{lvl}", fix="Xoá heading rỗng — chúng làm loãng cấu trúc.", confidence="high")
    # heading level skip
    order = [int(t.name[1]) for t in soup.find_all(re.compile(r"^h[1-6]$"))]
    skips = [(a, b) for a, b in zip(order, order[1:]) if b - a > 1]
    if skips:
        fs.add(code="HEADING_LEVEL_SKIP", severity="low", category="onpage", url=url,
               message=f"Nhảy cấp heading (vd h{skips[0][0]}→h{skips[0][1]}).",
               evidence=f"chuỗi heading: {order[:20]}",
               fix="Giữ thứ tự lồng nhau hợp lý để reader/AI hiểu cấu trúc.", confidence="medium")

    # ---- body text ----
    body = main_text(soup)
    words = visible_text_len(body)
    rec["word_count"] = words
    rec["vi_ratio"] = round(looks_vietnamese(body), 4)

    # ---- ngôn ngữ: thẻ lang vs nội dung vs URL ----
    html_tag = soup.find("html")
    lang_attr = (html_tag.get("lang") or "").strip() if html_tag else ""
    rec["lang_attr"] = lang_attr
    detected = "vi" if looks_vietnamese(body) > 0.004 else "en"
    rec["detected_lang"] = detected
    if not lang_attr:
        fs.add(code="LANG_ATTR_MISSING", severity="medium", category="i18n", url=url,
               message="Không có thuộc tính lang trên <html>.", evidence="",
               fix='Thêm lang="en" hoặc lang="vi". Ảnh hưởng dịch tự động + screen reader + tín hiệu ngôn ngữ.',
               confidence="high")
    elif lang_attr.split("-")[0].lower() != detected:
        fs.add(code="LANG_MISMATCH", severity="high", category="i18n", url=url,
               message=f'lang="{lang_attr}" nhưng nội dung phát hiện là "{detected}".',
               evidence=f"vi_ratio={rec['vi_ratio']}, lang_attr={lang_attr}",
               fix="Sửa lang cho đúng, hoặc đúng ra trang này thuộc locale khác.", confidence="medium")

    # URL locale vs nội dung
    path = urllib.parse.urlsplit(final_url).path
    url_locale = "vi" if path.startswith("/vi/") or path == "/vi" else "en"
    rec["url_locale"] = url_locale
    if url_locale != detected and words > 150:
        sev = "high" if detected == "vi" else "medium"
        fs.add(code="LOCALE_CONTENT_MISMATCH", severity=sev, category="i18n", url=url,
               message=f"URL thuộc locale '{url_locale}' nhưng nội dung phát hiện là '{detected}'.",
               evidence=f"path={path}, vi_ratio={rec['vi_ratio']}, words={words}",
               fix="Đây là nguyên nhân chính gây vỡ hreflang. Xem config/ptemagic.yaml → issues.I18N-ARCH.",
               confidence="medium")

    # ---- hreflang ----
    hreflangs = [(l.get("hreflang", "").strip(), urllib.parse.urljoin(final_url, l.get("href", "").strip()))
                 for l in soup.find_all("link", rel=lambda v: v and "alternate" in " ".join(v).lower()
                                         and "hreflang" in " ".join(v).lower())]
    hreflangs += [(l.get("hreflang", "").strip(), urllib.parse.urljoin(final_url, l.get("href", "").strip()))
                  for l in soup.find_all("link") if l.get("hreflang")]
    hreflangs = list(dict.fromkeys(hreflangs))
    rec["hreflang"] = hreflangs
    if hreflangs:
        for hl, href in hreflangs:
            if not VALID_HREFLANG.match(hl or ""):
                fs.add(code="HREFLANG_INVALID_CODE", severity="high", category="i18n", url=url,
                       message=f"hreflang không hợp lệ: '{hl}'.", evidence=href,
                       fix="Dùng mã ISO 639-1 (+ ISO 3166-1 Alpha 2 nếu cần), vd 'vi', 'en', 'en-au', 'x-default'.",
                       confidence="high")
        if not any(hl.lower() == "x-default" for hl, _ in hreflangs):
            fs.add(code="HREFLANG_NO_XDEFAULT", severity="medium", category="i18n", url=url,
                   message="Có hreflang nhưng thiếu x-default.",
                   evidence=f"{len(hreflangs)} hreflang tags",
                   fix="Thêm x-default trỏ về bản EN toàn cầu.", confidence="high")
        self_ref = [h for hl, h in hreflangs
                    if normalize_url(h) == normalize_url(final_url)]
        if not self_ref:
            fs.add(code="HREFLANG_NO_SELF_REFERENCE", severity="high", category="i18n", url=url,
                   message="Cluster hreflang không có self-reference (bắt buộc theo Google).",
                   evidence=f"hreflang: {[h for _, h in hreflangs][:6]}",
                   fix="Mỗi trang phải tự khai báo chính nó trong cluster hreflang.", confidence="high")
    else:
        rec["hreflang"] = []

    # ---- viewport / mobile ----
    if not soup.find("meta", attrs={"name": "viewport"}):
        fs.add(code="VIEWPORT_MISSING", severity="high", category="technical", url=url,
               message="Không có meta viewport.", evidence="",
               fix='Thêm <meta name="viewport" content="width=device-width, initial-scale=1">',
               confidence="high")

    # ---- ảnh ----
    imgs = soup.find_all("img")
    rec["img_count"] = len(imgs)
    no_alt = [i.get("src", "")[:120] for i in imgs if not (i.get("alt") or "").strip()]
    if no_alt:
        fs.add(code="IMG_ALT_MISSING", severity="medium", category="images", url=url,
               message=f"{len(no_alt)}/{len(imgs)} ảnh thiếu alt.",
               evidence="; ".join(no_alt[:4]),
               fix="Alt mô tả nội dung ảnh, có keyword khi tự nhiên. Ảnh trang trí dùng alt=\"\".",
               confidence="high")
    no_dims = [i.get("src", "")[:100] for i in imgs
               if not (i.get("width") and i.get("height")) and not (i.get("style") and "aspect-ratio" in i.get("style", ""))]
    if no_dims and len(imgs) > 2:
        fs.add(code="IMG_NO_DIMENSIONS", severity="medium", category="performance", url=url,
               message=f"{len(no_dims)}/{len(imgs)} ảnh không khai báo width/height → rủi ro CLS.",
               evidence="; ".join(no_dims[:3]),
               fix="Khai báo width/height hoặc aspect-ratio trong CSS.", confidence="medium")
    max_w_card = thresholds(cfg, "core_web_vitals", "next_image_max_width_for_card", default=768)
    oversized = []
    for i in imgs:
        src = i.get("src") or i.get("data-src") or ""
        m = re.search(r"[?&]w=(\d+)", src)
        if m and int(m.group(1)) > max_w_card:
            oversized.append(f"w={m.group(1)}:{src.split('/')[-1][:40]}")
    if oversized:
        fs.add(code="NEXT_IMAGE_OVERSIZED_W", severity="high", category="performance", url=url,
               message=f"{len(oversized)} ảnh /_next/image đang request w > {max_w_card}px.",
               evidence="; ".join(oversized[:6]),
               fix="Truyền sizes/srcset đúng kích thước hiển thị. Card blog chỉ cần w=384-768, hero w=1200-1920. "
                   "w=3840 làm LCP mobile tụt nặng.",
               confidence="high")
    modern = sum(1 for i in imgs if re.search(r"\.(webp|avif)", (i.get("src") or ""), re.I))
    if len(imgs) >= 5 and modern == 0:
        fs.add(code="IMG_NO_MODERN_FORMAT", severity="low", category="images", url=url,
               message=f"{len(imgs)} ảnh, không thấy WebP/AVIF nào trong src.",
               evidence="(Next.js /_next/image thường trả WebP tự động — verify bằng response header)",
               fix="Bật format WebP/AVIF trong next.config hoặc serve qua CDN.", confidence="low")
    lazy_missing = [i.get("src", "")[:80] for i in imgs
                    if not (i.get("loading") or "") and not (i.get("fetchpriority") or "")]
    if len(imgs) > 8 and len(lazy_missing) > len(imgs) * 0.5:
        fs.add(code="IMG_LOADING_ATTR_MISSING", severity="low", category="performance", url=url,
               message=f"{len(lazy_missing)}/{len(imgs)} ảnh không có loading/fetchpriority.",
               evidence="; ".join(lazy_missing[:3]),
               fix="Ảnh dưới màn hình đầu: loading=\"lazy\". Ảnh LCP: fetchpriority=\"high\", không lazy.",
               confidence="medium")

    # ---- link ----
    anchors = [a for a in soup.find_all("a") if a.get("href")]
    internal, external = [], []
    for a in anchors:
        href = link_href(final_url, a)
        if not href:
            continue
        (internal if same_host(href, final_url, include_sub=True) else external).append((href, a))
    rec["links_internal"] = len(internal)
    rec["links_external"] = len(external)
    rec["outbound"] = [h for h, _ in external][:200]

    empty_anchor = [link_href(final_url, a) for a in anchors
                    if not a.get_text(" ", strip=True) and not a.find("img")]
    if empty_anchor:
        fs.add(code="ANCHOR_EMPTY", severity="medium", category="links", url=url,
               message=f"{len(empty_anchor)} link không có anchor text lẫn ảnh.",
               evidence="; ".join(empty_anchor[:4]),
               fix="Thêm anchor mô tả hoặc aria-label.", confidence="high")
    vague = [a.get_text(" ", strip=True) for a in anchors
             if re.fullmatch(r"(?i)\s*(read more|xem thêm|click here|here|tại đây|chi tiết|more|tìm hiểu thêm)\s*",
                             a.get_text(" ", strip=True) or "")]
    if len(vague) >= 3:
        fs.add(code="ANCHOR_VAGUE", severity="medium", category="links", url=url,
               message=f"{len(vague)} link dùng anchor mơ hồ ('Read more'/'Xem thêm').",
               evidence="; ".join(set(vague))[:200],
               fix="Anchor nên chứa chủ đề trang đích. Với danh sách bài blog, biến TIÊU ĐỀ thành link.",
               confidence="high")
    paid_missing_rel = []
    for href, a in external:
        rel = " ".join(a.get("rel") or []).lower()
        if re.search(r"(utm_|gclid|fbclid|ref=|affiliate|partner=)", href) and not (
                "sponsored" in rel or "nofollow" in rel or "ugc" in rel):
            paid_missing_rel.append(href[:110])
    if paid_missing_rel:
        fs.add(code="PAID_LINK_MISSING_REL", severity="high", category="policy", url=url,
               message=f"{len(paid_missing_rel)} link ra ngoài có tham số tracking/affiliate nhưng thiếu rel=sponsored.",
               evidence="; ".join(paid_missing_rel[:4]),
               fix='Thêm rel="sponsored". Thiếu thẻ này nằm trong nhóm Link spam của Google.',
               confidence="medium")
    if len(external) > 25:
        fs.add(code="MANY_OUTBOUND_LINKS", severity="low", category="links", url=url,
               message=f"{len(external)} link ra ngoài trên 1 trang.",
               evidence="", fix="Rà lại: link nào không giúp người đọc thì bỏ.", confidence="low")

    # bài blog: tiêu đề có phải anchor không
    if re.search(r"/blog|/blogs", final_url) and len(internal) > 5:
        h_links = [a for a in soup.find_all(["h2", "h3", "h4"]) if a.find("a", href=True) or a.name == "a"]
        card_like = len(soup.find_all(["h4", "h5"]))
        if card_like >= 5 and len(h_links) == 0:
            fs.add(code="BLOG_TITLE_NOT_LINKED", severity="high", category="links", url=url,
                   message=f"Có {card_like} heading dạng card bài viết nhưng KHÔNG heading nào chứa link.",
                   evidence="Chỉ ảnh mới là link → mất anchor text có keyword",
                   fix="Bọc tiêu đề bài viết trong <a href>. Đây là internal anchor text quan trọng nhất của blog.",
                   confidence="medium")

    # ---- JSON-LD ----
    blocks = jsonld_blocks(soup)
    types = jsonld_types(blocks)
    rec["jsonld_types"] = sorted(types)
    for b in blocks:
        if isinstance(b, dict) and "__parse_error__" in b:
            fs.add(code="JSONLD_PARSE_ERROR", severity="high", category="schema", url=url,
                   message="JSON-LD không parse được.", evidence=b["__parse_error__"][:200],
                   fix="Validate tại https://validator.schema.org và Rich Results Test.", confidence="high")
    if not types:
        fs.add(code="JSONLD_MISSING", severity="medium", category="schema", url=url,
               message="Không có structured data JSON-LD nào.", evidence="",
               fix="Tối thiểu: Organization + WebSite (site-wide), BreadcrumbList, và Article/FAQPage cho blog.",
               confidence="high")
    else:
        if "Article" in types or "BlogPosting" in types or "NewsArticle" in types:
            art = [b for b in blocks if isinstance(b, dict)
                   and set(map(str, b.get("@type") if isinstance(b.get("@type"), list) else [b.get("@type")]))
                   & {"Article", "BlogPosting", "NewsArticle"}]
            for b in art:
                if not b.get("author"):
                    fs.add(code="ARTICLE_NO_AUTHOR", severity="high", category="schema", url=url,
                           message="Schema Article thiếu author.", evidence=json.dumps(b)[:200],
                           fix='author: {"@type":"Person","name":"...","url":"..."} — bắt buộc cho E-E-A-T.',
                           confidence="high")
                if not (b.get("datePublished") or b.get("dateCreated")):
                    fs.add(code="ARTICLE_NO_DATE", severity="medium", category="schema", url=url,
                           message="Schema Article thiếu datePublished.", evidence=json.dumps(b)[:160],
                           fix="Thêm datePublished + dateModified (ISO 8601).", confidence="high")
        if "FAQPage" in types:
            faq = [b for b in blocks if isinstance(b, dict) and b.get("@type") == "FAQPage"]
            for b in faq:
                qs = b.get("mainEntity") or []
                bad = [q for q in qs if not (isinstance(q, dict) and q.get("acceptedAnswer"))]
                if bad:
                    fs.add(code="FAQ_MISSING_ANSWER", severity="high", category="schema", url=url,
                           message=f"{len(bad)}/{len(qs)} câu FAQ thiếu acceptedAnswer.",
                           evidence=json.dumps(bad[:1])[:200],
                           fix="Mỗi Question phải có acceptedAnswer.text. Thiếu = không đủ điều kiện rich result.",
                           confidence="high")
        if "BreadcrumbList" not in types and path.count("/") >= 2:
            fs.add(code="BREADCRUMB_SCHEMA_MISSING", severity="low", category="schema", url=url,
                   message="URL có ≥2 cấp thư mục nhưng không có BreadcrumbList.",
                   evidence=path, fix="Thêm BreadcrumbList để có breadcrumb rich result.", confidence="medium")
    # Organization / WebSite nên có ở homepage
    if path in ("/", "/vi") and not ({"Organization", "EducationalOrganization"} & types):
        fs.add(code="ORG_SCHEMA_MISSING", severity="medium", category="schema", url=url,
               message="Trang chủ thiếu schema Organization/EducationalOrganization.", evidence="",
               fix="Thêm Organization với logo, sameAs (social), award, memberOf — PTE Magic có giải thưởng thật để khai báo.",
               confidence="high")

    # ---- Open Graph ----
    og_missing = [k for k in ("og:title", "og:description", "og:image", "og:url")
                  if not meta_content(soup, prop=k)]
    if og_missing:
        fs.add(code="OG_INCOMPLETE", severity="low", category="onpage", url=url,
               message=f"Thiếu Open Graph: {', '.join(og_missing)}.", evidence="",
               fix="Bổ sung để share lên Facebook/Zalo/LinkedIn/X có preview đúng (kênh quan trọng của PTE Magic).",
               confidence="high")

    # ---- duplicate block trong trang ----
    reps = repeated_blocks(body)
    if reps:
        worst = max(reps, key=lambda x: x[1] * visible_text_len(x[0]))
        total_dup_words = sum((c - 1) * visible_text_len(s) for s, c in reps)
        sev = "high" if total_dup_words > 120 else "medium"
        fs.add(code="DUPLICATE_TEXT_BLOCK_IN_PAGE", severity=sev, category="content", url=url,
               message=f"{len(reps)} đoạn văn bản lặp nguyên văn trong trang (~{total_dup_words} từ thừa).",
               evidence=f"x{worst[1]}: \"{worst[0][:150]}…\"",
               fix="Thường do carousel/tab render cả 2 bản (mobile+desktop) trong DOM. "
                   "Giữ 1 bản, bản kia aria-hidden + display:none, hoặc render có điều kiện. "
                   "Không phải spam nhưng làm nặng DOM và loãng nội dung.",
               confidence="medium")

    # ---- word count ----
    is_blog = bool(re.search(r"/blogs?/|/blogs?$", path)) or (path.count("/") == 1 and words > 400)
    wmin = thresholds(cfg, "on_page", "words_min_informational", default=1200)
    if is_blog and words and words < wmin * 0.5:
        fs.add(code="THIN_CONTENT", severity="medium", category="content", url=url,
               message=f"Bài blog chỉ ~{words} từ (< {wmin//2}).", evidence="",
               fix="Nếu không mở rộng được bằng giá trị thật, cân nhắc gộp vào bài trụ cột (consolidate).",
               confidence="medium")
    if words and words < 120 and "noindex" not in robots_meta:
        fs.add(code="VERY_THIN_PAGE", severity="high", category="content", url=url,
               message=f"Trang indexable chỉ ~{words} từ.", evidence=body[:200],
               fix="Thêm nội dung thật hoặc noindex. Trang mỏng hàng loạt là dấu hiệu scaled content abuse.",
               confidence="medium")

    # ---- performance hints từ HTML ----
    render_blocking = [t.get("href") or t.get("src") for t in
                       soup.find_all("link", rel=lambda v: v and "stylesheet" in " ".join(v))
                       if not t.get("media") or t.get("media") == "all"]
    rec["render_blocking_css"] = len(render_blocking)
    inline_scripts = len(soup.find_all("script", src=False))
    rec["inline_scripts"] = inline_scripts
    if len(html) > 400_000:
        fs.add(code="HTML_TOO_LARGE", severity="medium", category="performance", url=url,
               message=f"HTML {len(html)//1024}KB — rất lớn.",
               evidence=f"{len(html)} bytes",
               fix="Nguyên nhân thường là nội dung render trùng + inline JSON state. "
                   "Cắt DOM không cần thiết, defer hydration data.", confidence="high")
    if inline_scripts > 60:
        fs.add(code="TOO_MANY_INLINE_SCRIPTS", severity="low", category="performance", url=url,
               message=f"{inline_scripts} thẻ <script> inline.", evidence="",
               fix="Gộp lại; inline script nhiều làm tăng HTML size và chặn parse.", confidence="low")

    # ---- security headers (site-level, ghi vào ctx) ----
    ctx.setdefault("headers_seen", {}).update({k: v for k, v in headers.items()
                                               if k in ("strict-transport-security", "x-content-type-options",
                                                        "content-security-policy", "referrer-policy",
                                                        "permissions-policy", "x-frame-options")})

    # ---- llms.txt / AI crawler hint (chỉ homepage) ----
    if path in ("/", ""):
        ctx["homepage_html"] = html
        ctx["homepage_url"] = final_url

    ctx.setdefault("internal_edges", []).extend(
        (normalize_url(final_url, True), normalize_url(h, True)) for h, _ in internal)
    ctx.setdefault("all_titles", {})[normalize_url(final_url, True)] = title
    ctx.setdefault("all_descs", {})[normalize_url(final_url, True)] = desc
    ctx.setdefault("all_h1", {})[normalize_url(final_url, True)] = " | ".join(h1s)
    ctx.setdefault("all_canonical", {})[normalize_url(final_url, True)] = rec.get("canonical")
    ctx.setdefault("all_hreflang", {})[normalize_url(final_url, True)] = rec["hreflang"]
    ctx.setdefault("shingles", {})[normalize_url(final_url, True)] = shingles(body, 5)
    ctx.setdefault("lang_detected", {})[normalize_url(final_url, True)] = detected
    ctx.setdefault("page_records", []).append(rec)

    return fs.items, rec


# =========================================================================== #
# 3. Check cấp site (cần toàn bộ trang)
# =========================================================================== #
def check_site(fs: FindingSet, ctx: dict, cfg: dict, urls: list[str]) -> None:
    titles = ctx.get("all_titles", {})
    descs = ctx.get("all_descs", {})
    h1s = ctx.get("all_h1", {})
    canons = ctx.get("all_canonical", {})
    hreflang_map = ctx.get("all_hreflang", {})
    sh_map = ctx.get("shingles", {})
    lang_map = ctx.get("lang_detected", {})

    # ---- duplicate title / desc / h1 ----
    for label, mapping, code, sev, fix in [
        ("title", titles, "DUPLICATE_TITLE", "high",
         "Mỗi URL cần title riêng. Title trùng khiến Google chọn ngẫu nhiên và làm mất CTR."),
        ("meta description", descs, "DUPLICATE_META_DESC", "medium",
         "Viết description riêng cho từng trang."),
        ("H1", h1s, "DUPLICATE_H1", "medium",
         "H1 trùng giữa các trang thường là dấu hiệu template chưa được cá nhân hoá."),
    ]:
        groups: dict[str, list[str]] = collections.defaultdict(list)
        for u, v in mapping.items():
            if v and v.strip():
                groups[v.strip().lower()].append(u)
        dups = {k: v for k, v in groups.items() if len(v) > 1}
        for text, group in list(dups.items())[:20]:
            fs.add(code=code, severity=sev, category="onpage", url=", ".join(group[:3]),
                   message=f"{len(group)} trang dùng chung {label}: \"{text[:90]}\".",
                   evidence=f"urls: {', '.join(group[:6])}", fix=fix, confidence="high")
        if dups:
            fs.add(code=code + "_SUMMARY", severity="info", category="onpage", url="(site-wide)",
                   message=f"Tổng cộng {len(dups)} nhóm {label} bị trùng, ảnh hưởng "
                           f"{sum(len(v) for v in dups.values())} URL.",
                   evidence="", fix="Xem chi tiết ở các finding cùng code phía trên.", confidence="high")

    # ---- canonical trỏ nhiều URL về 1 ----
    cgroups: dict[str, list[str]] = collections.defaultdict(list)
    for u, c in canons.items():
        if c:
            cgroups[normalize_url(c, True)].append(u)
    for target, group in cgroups.items():
        if len(group) > 1 and target not in group:
            fs.add(code="CANONICAL_CLUSTER", severity="info", category="technical",
                   url=", ".join(group[:3]),
                   message=f"{len(group)} URL cùng canonical về {target}.",
                   evidence="; ".join(group[:6]),
                   fix="Đúng nếu là phân trang/filter/sorting. Sai nếu là các trang nội dung khác nhau.",
                   confidence="medium")

    # ---- hreflang reciprocal ----
    problems = 0
    for u, hls in hreflang_map.items():
        if not hls:
            continue
        for hl, href in hls:
            n = normalize_url(href, True)
            peer = hreflang_map.get(n)
            if peer is None:
                continue  # trang đích không nằm trong tập audit
            back = [normalize_url(h, True) for _, h in peer]
            if n != u and u not in back:
                problems += 1
                if problems <= 15:
                    fs.add(code="HREFLANG_NOT_RECIPROCAL", severity="high", category="i18n", url=u,
                           message=f"{u} khai hreflang {hl}→{href}, nhưng trang đích không khai ngược lại.",
                           evidence=f"hreflang của {href}: {back[:6]}",
                           fix="Google yêu cầu hreflang 2 chiều. Thiếu chiều ngược = cả cặp bị bỏ qua.",
                           confidence="high")
    if problems > 15:
        fs.add(code="HREFLANG_NOT_RECIPROCAL_SUMMARY", severity="info", category="i18n",
               url="(site-wide)", message=f"Tổng cộng {problems} cặp hreflang không reciprocal.",
               evidence="", fix="Sinh hreflang tập trung từ một nguồn duy nhất (i18n config).",
               confidence="high")

    pages_with_hreflang = sum(1 for v in hreflang_map.values() if v)
    if hreflang_map and pages_with_hreflang == 0:
        fs.add(code="HREFLANG_ABSENT_SITEWIDE", severity="critical", category="i18n",
               url="(site-wide)",
               message=f"{len(hreflang_map)} trang đã audit, KHÔNG trang nào có hreflang — trong khi site "
                       f"phục vụ cả EN và VI trên nhiều domain.",
               evidence="locales: en, vi, .com.vn, .com.au",
               fix="Ưu tiên số 1 về i18n. Đọc skills/seo-i18n-hreflang/SKILL.md và chốt issues.I18N-ARCH trước.",
               confidence="high")

    # ---- ngôn ngữ lệch URL hàng loạt ----
    mism = [u for u, d in lang_map.items()
            if ("/vi/" in u or u.endswith("/vi")) != (d == "vi")]
    if len(mism) >= 3:
        fs.add(code="LOCALE_MISMATCH_SITEWIDE", severity="high", category="i18n",
               url="(site-wide)",
               message=f"{len(mism)} trang có locale URL không khớp ngôn ngữ nội dung.",
               evidence="; ".join(mism[:6]),
               fix="Rà lại kiến trúc URL đa ngôn ngữ (issues.I18N-ARCH).", confidence="medium")

    # ---- near-duplicate content ----
    nd_threshold = thresholds(cfg, "policy_gate", "near_duplicate_jaccard_warn", default=0.50)
    keys = list(sh_map.keys())
    pairs_found = 0
    for a, b in itertools.combinations(keys, 2):
        if not sh_map[a] or not sh_map[b]:
            continue
        # cheap prefilter: độ lớn chênh lệch quá thì bỏ
        if min(len(sh_map[a]), len(sh_map[b])) / max(len(sh_map[a]), len(sh_map[b])) < 0.5:
            continue
        j = jaccard(sh_map[a], sh_map[b])
        if j >= nd_threshold:
            pairs_found += 1
            if pairs_found <= 12:
                sev = "critical" if j >= thresholds(cfg, "policy_gate",
                                                    "near_duplicate_jaccard_block", default=0.70) else "high"
                fs.add(code="NEAR_DUPLICATE_CONTENT", severity=sev, category="content", url=a,
                       message=f"Giống {j*100:.0f}% với trang khác (Jaccard trên 5-gram).",
                       evidence=f"{a}  ≈  {b}",
                       fix="≥70% = rủi ro scaled content abuse. Gộp (301), hoặc viết lại để mỗi trang có "
                           "giá trị riêng (dữ liệu, ví dụ, góc nhìn khác nhau).",
                       confidence="high")
    if pairs_found > 12:
        fs.add(code="NEAR_DUPLICATE_SUMMARY", severity="info", category="content", url="(site-wide)",
               message=f"Tổng cộng {pairs_found} cặp trang gần trùng nhau (≥{nd_threshold*100:.0f}%).",
               evidence="", fix="Chạy scripts/policy_gate.py --corpus để có danh sách đầy đủ.",
               confidence="high")

    # ---- orphan page / link graph ----
    edges = ctx.get("internal_edges", [])
    linked_to: set[str] = {t for _, t in edges}
    home = None
    for u in urls:
        if urllib.parse.urlsplit(u).path in ("/", ""):
            home = normalize_url(u, True)
            break
    audited = {normalize_url(u, True) for u in urls}
    orphans = [u for u in audited if u not in linked_to and u != home]
    if orphans and len(audited) > 10:
        fs.add(code="ORPHAN_PAGES", severity="high", category="links", url="(site-wide)",
               message=f"{len(orphans)}/{len(audited)} trang không có internal link nào trỏ tới (orphan).",
               evidence="; ".join(orphans[:8]),
               fix="Thêm link từ trang chuyên mục/bài liên quan. Orphan page gần như không rank được.",
               confidence="medium")
    if edges:
        out_deg = collections.Counter(s for s, _ in edges)
        heavy = [u for u, c in out_deg.items() if c > 150]
        if heavy:
            fs.add(code="TOO_MANY_INTERNAL_LINKS", severity="low", category="links", url=heavy[0],
                   message=f"{len(heavy)} trang có >150 internal link.",
                   evidence=f"{heavy[0]}: {out_deg[heavy[0]]} links",
                   fix="Quá nhiều link làm loãng PageRank nội bộ và khó crawl.", confidence="medium")

    # ---- robots.txt / AI crawler ----
    rb = ctx.get("robots_info") or {}
    rtext = (rb.get("robots_txt") or {}).get("text") or ""
    if rb and not rtext.strip():
        fs.add(code="ROBOTS_TXT_MISSING", severity="medium", category="technical", url="(robots.txt)",
               message="Không đọc được robots.txt.", evidence=f"status={(rb.get('robots_txt') or {}).get('status')}",
               fix="Tạo robots.txt khai báo sitemap và chặn path app.", confidence="high")
    elif rtext:
        if "sitemap" not in rtext.lower():
            fs.add(code="ROBOTS_NO_SITEMAP", severity="low", category="technical", url="(robots.txt)",
                   message="robots.txt không khai báo Sitemap.", evidence=rtext[:200],
                   fix="Thêm dòng 'Sitemap: https://ptemagic.com/sitemap.xml'.", confidence="high")
        app_paths = [p for p in ((cfg.get("site") or {}).get("app_paths_must_noindex") or [])]
        for p in app_paths:
            pat = p.rstrip("*").rstrip("/")
            if pat and pat not in rtext:
                fs.add(code="ROBOTS_APP_PATH_NOT_BLOCKED", severity="medium", category="technical",
                       url="(robots.txt)",
                       message=f"Path app '{p}' chưa bị chặn trong robots.txt.",
                       evidence=rtext[:200],
                       fix=f"Thêm 'Disallow: {pat}/' hoặc đảm bảo các trang đó có meta noindex.",
                       confidence="medium")
        mentioned = [c for c in AI_CRAWLERS if c.lower() in rtext.lower()]
        if not mentioned:
            fs.add(code="ROBOTS_NO_AI_CRAWLER_POLICY", severity="info", category="geo",
                   url="(robots.txt)",
                   message="robots.txt không nhắc tới AI crawler nào (GPTBot, ClaudeBot, PerplexityBot, "
                           "Google-Extended…).",
                   evidence=f"robots.txt hiện tại: {rtext[:160]!r}",
                   fix="Quyết định có chủ đích: CHO PHÉP (muốn được cite trong AI Overviews/ChatGPT) "
                       "hoặc CHẶN (bảo vệ nội dung). Mặc định của chiến lược GEO là cho phép "
                       "OAI-SearchBot, PerplexityBot, Google-Extended. Xem skills/seo-geo-visibility.",
                   confidence="high")
        if re.search(r"(?im)^\s*user-agent:\s*\*\s*$", rtext) and re.search(r"(?im)^\s*disallow:\s*/\s*$", rtext):
            fs.add(code="ROBOTS_DISALLOW_ALL", severity="critical", category="technical",
                   url="(robots.txt)", message="robots.txt đang Disallow: / cho mọi bot.",
                   evidence=rtext[:200], fix="Bỏ ngay — site sẽ bị loại khỏi index.", confidence="high")

    # ---- sitemap lastmod ----
    sm = ctx.get("sitemap_meta") or {}
    if sm.get("lastmod_values"):
        vals = sm["lastmod_values"]
        uniq = len(set(vals))
        if len(vals) >= 5 and uniq == 1:
            fs.add(code="SITEMAP_LASTMOD_ALL_IDENTICAL", severity="medium", category="technical",
                   url="(sitemap.xml)",
                   message=f"Toàn bộ {len(vals)} lastmod trong sitemap giống hệt nhau: {list(vals)[0]}.",
                   evidence="Đây là thời điểm build/deploy, không phải ngày sửa nội dung",
                   fix="Xuất lastmod từ CMS theo ngày cập nhật nội dung thật. Google bỏ qua lastmod "
                       "không đáng tin, và nó có thể làm chậm việc crawl lại trang vừa sửa.",
                   confidence="high")
    if sm.get("missing_from_sitemap"):
        miss = sm["missing_from_sitemap"]
        fs.add(code="SITEMAP_MISSING_URLS", severity="low", category="technical", url="(sitemap.xml)",
               message=f"{len(miss)} URL indexable không có trong sitemap.",
               evidence="; ".join(miss[:8]),
               fix="Thêm vào sitemap để được phát hiện nhanh hơn.", confidence="medium")

    # ---- security headers ----
    hs = ctx.get("headers_seen") or {}
    if hs:
        if "strict-transport-security" not in hs:
            fs.add(code="HSTS_MISSING", severity="low", category="technical", url="(site-wide)",
                   message="Thiếu header Strict-Transport-Security.", evidence="",
                   fix='Thêm "Strict-Transport-Security: max-age=31536000; includeSubDomains; preload".',
                   confidence="high")
        if "x-content-type-options" not in hs:
            fs.add(code="XCTO_MISSING", severity="low", category="technical", url="(site-wide)",
                   message="Thiếu X-Content-Type-Options: nosniff.", evidence="",
                   fix="Thêm header. Tín hiệu chất lượng tổng thể của site.", confidence="high")

    # ---- llms.txt ----
    llms = ctx.get("llms_txt")
    if llms is not None and llms.get("status") != 200:
        fs.add(code="LLMS_TXT_MISSING", severity="info", category="geo", url="(llms.txt)",
               message="Không có /llms.txt.", evidence=f"status={llms.get('status')}",
               fix="Không bắt buộc với Google, nhưng giúp AI engine hiểu site. "
                   "Cân nhắc nếu theo đuổi chiến lược GEO.", confidence="medium")

    # ---- phản hồi chậm ----
    slow = [r for r in ctx.get("page_records", [])
            if r.get("elapsed_ms") and r["elapsed_ms"] > 1500]
    if len(slow) >= max(3, len(ctx.get("page_records", [])) * 0.2):
        fs.add(code="SLOW_RESPONSES", severity="high", category="performance", url="(site-wide)",
               message=f"{len(slow)} trang phản hồi > 1500ms (đo từ sandbox, chưa phải TTFB thật).",
               evidence="; ".join(f"{r['url'][-45:]}={r['elapsed_ms']}ms" for r in slow[:5]),
               fix="Đo lại bằng scripts/psi_cwv.py (field data CrUX) trước khi kết luận.",
               confidence="low")


# =========================================================================== #
# main
# =========================================================================== #
def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="SEO auditor cho ptemagic.com (và site bất kỳ).")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--site", help="URL gốc cần audit (chế độ live)")
    src.add_argument("--offline-dir", help="Thư mục HTML đã lưu + manifest.json (chế độ offline/test)")
    p.add_argument("--config", help="Đường dẫn config YAML (default: config/ptemagic.yaml)")
    p.add_argument("--max-urls", type=int, default=200)
    p.add_argument("--only-url", action="append", default=[], help="Chỉ audit (các) URL này")
    p.add_argument("--seed", action="append", default=[], help="URL seed bổ sung khi crawl")
    p.add_argument("--out", default="reports/ptemagic")
    p.add_argument("--delay", type=float, default=0.5)
    p.add_argument("--no-respect-robots", action="store_true")
    p.add_argument("--no-sitemap", action="store_true")
    p.add_argument("--cache-dir", default=None, help="Cache HTTP vào thư mục này (mặc định: .cache/audit)")
    p.add_argument("--json-only", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)
    cfg = load_config(args.config)
    fs = FindingSet(site=args.site or args.offline_dir)
    ctx: dict = {}

    # --- lấy trang ---
    if args.offline_dir:
        pages = load_offline_dir(args.offline_dir)
        if args.only_url:
            want = {normalize_url(u, True) for u in args.only_url}
            pages = [p for p in pages if normalize_url(p["url"], True) in want]
        urls = [p["url"] for p in pages]
        mode = "offline"
        if pages:
            fs.site = "https://" + registrable_domain(pages[0]["url"]) + " (offline fixtures)"
        eprint(f"[offline] {len(pages)} trang từ {args.offline_dir}")
    else:
        fetch = Fetcher(delay=args.delay, respect_robots=not args.no_respect_robots,
                        cache_dir=args.cache_dir or os.path.join(".cache", "audit"))
        if args.only_url:
            urls = [normalize_url(u, True) for u in args.only_url]
            rinfo = {}
        else:
            urls, rinfo = collect_urls_live(fetch, args.site, args.max_urls,
                                            use_sitemap=not args.no_sitemap, seeds=args.seed)
            ctx["robots_info"] = rinfo
            sm_urls = []
            eprint(f"[live] {len(urls)} URL (sitemap khai báo {rinfo.get('sitemap_url_count', 0)})")
        pages = [fetch.get(u) | {"url": u} for u in urls]
        mode = "live"

    if not pages:
        eprint("[fatal] Không có trang nào để audit.")
        return 2

    # --- check từng trang ---
    records = []
    for i, page in enumerate(pages, 1):
        try:
            found, rec = check_page(page, cfg, ctx)
            fs.extend(found)
            records.append(rec)
        except Exception as e:  # noqa: BLE001
            eprint(f"[warn] lỗi khi audit {page.get('url')}: {type(e).__name__}: {e}")
        if i % 25 == 0:
            eprint(f"  … {i}/{len(pages)} trang, {len(fs)} finding")

    # --- sitemap meta (live only) ---
    if mode == "live" and ctx.get("robots_info"):
        try:
            sm_url = (args.site.rstrip("/") + "/sitemap.xml")
            r = fetch.get(sm_url)
            if r.get("status") == 200:
                lastmods = re.findall(r"<lastmod>\s*([^<\s]+)\s*</lastmod>", r["text"])
                ctx["sitemap_meta"] = {"lastmod_values": lastmods[:500],
                                       "missing_from_sitemap": []}
            llms = fetch.get(args.site.rstrip("/") + "/llms.txt")
            ctx["llms_txt"] = {"status": llms.get("status")}
        except Exception:
            pass

    # --- check cấp site ---
    try:
        check_site(fs, ctx, cfg, urls)
    except Exception as e:  # noqa: BLE001
        eprint(f"[warn] site-level check lỗi: {type(e).__name__}: {e}")

    payload = fs.to_json()
    payload["mode"] = mode
    payload["pages_audited"] = len(pages)
    payload["urls"] = urls[:2000]
    payload["page_records"] = records
    payload["summary"] = {
        "locales_detected": collections.Counter(ctx.get("lang_detected", {}).values()),
        "jsonld_types_seen": sorted({t for r in records for t in (r.get("jsonld_types") or [])}),
        "avg_word_count": round(sum(r.get("word_count", 0) for r in records) / max(1, len(records))),
        "avg_html_kb": round(sum(r.get("html_bytes", 0) for r in records) / max(1, len(records)) / 1024, 1),
        "pages_with_hreflang": sum(1 for r in records if r.get("hreflang")),
        "pages_noindexed": sum(1 for r in records if "noindex" in (r.get("robots_meta") or "")),
    }

    md = fs.to_markdown(meta={"pages_audited": len(pages), "mode": mode,
                              "run_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())})
    md += "\n## Summary kỹ thuật\n\n```json\n" + json.dumps(payload["summary"], ensure_ascii=False,
                                                            indent=2, default=str) + "\n```\n"

    stem = time.strftime("%Y-%m-%d", time.gmtime()) + "-audit"
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return 1 if fs.by_severity()["critical"] else 0

    jp, mp = write_outputs(args.out, stem, payload, md)
    sev = fs.by_severity()
    eprint(f"\n=== {payload['score']}/100 · {len(pages)} trang · "
           f"C:{sev['critical']} H:{sev['high']} M:{sev['medium']} L:{sev['low']} I:{sev['info']} ===")
    eprint(f"JSON: {jp}\nMD:   {mp}")
    return 1 if sev["critical"] else 0


if __name__ == "__main__":
    sys.exit(main())
