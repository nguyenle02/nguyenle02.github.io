#!/usr/bin/env python3
"""drift.py — Lưu baseline SEO rồi so sánh để phát hiện cái gì VỪA thay đổi.

Ý tưởng lấy từ sub-skill `seo-drift` của AgriciDaniel/claude-seo (MIT), viết lại cho
bộ này: chỉ fingerprint những thứ hay bị vỡ khi deploy (Next.js rebuild, đổi theme,
đổi CMS) — không audit lại toàn bộ.

    python scripts/drift.py baseline --site https://ptemagic.com
    python scripts/drift.py compare  --site https://ptemagic.com
    python scripts/drift.py history  --site https://ptemagic.com
    python scripts/drift.py compare  --offline-dir fixtures/ptemagic      # test không cần mạng

Giá trị thật: sau mỗi lần dev deploy, chạy `compare` trong 2 phút thay vì audit lại 1.5 giờ.
Nếu title/schema/hreflang/canonical vừa bị mất, biết ngay trong ngày thay vì 3 tuần sau
khi traffic tụt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from common import (  # noqa: E402
    Fetcher, headings, jsonld_types, jsonld_blocks, link_href, load_offline_dir,
    looks_vietnamese, main_text, meta_content, normalize_url, registrable_domain,
    same_host, soup_of, visible_text_len, eprint,
)
from seo_audit import collect_urls_live  # noqa: E402

DRIFT_DIR_DEFAULT = os.path.join("data", "drift")

# Những thay đổi này là nghiêm trọng — thường là tai nạn khi deploy
SEVERITY_MAP = {
    "title_changed": "high",
    "title_missing": "critical",
    "h1_count_changed": "high",
    "canonical_changed": "critical",
    "canonical_missing": "critical",
    "noindex_added": "critical",
    "noindex_removed": "info",
    "jsonld_type_removed": "critical",
    "jsonld_type_added": "info",
    "jsonld_missing": "high",
    "hreflang_removed": "critical",
    "hreflang_added": "info",
    "hreflang_count_changed": "high",
    "lang_changed": "high",
    "status_changed": "critical",
    "page_disappeared": "critical",
    "page_appeared": "info",
    "word_count_drop": "high",
    "word_count_gain": "info",
    "image_count_surge": "medium",
    "oversized_images_added": "high",
    "html_size_surge": "medium",
    "internal_links_drop": "medium",
    "duplicate_blocks_added": "medium",
}
SEV_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def fingerprint(page: dict) -> dict | None:
    """Trích các tín hiệu hay bị vỡ. Rẻ hơn audit đầy đủ ~10 lần."""
    html = page.get("text") or ""
    if not html.strip():
        return {"status": page.get("status"), "empty": True}
    soup = soup_of(html)
    title_tag = soup.find("title")
    hs = headings(soup)
    blocks = jsonld_blocks(soup)
    types = sorted(jsonld_types(blocks))
    canon = soup.find("link", attrs={"rel": "canonical"})
    hreflang = [l.get("hreflang") for l in soup.find_all("link") if l.get("hreflang")]
    imgs = soup.find_all("img")
    oversized = sum(1 for i in imgs
                    if (m := re.search(r"[?&]w=(\d+)", i.get("src") or "")) and int(m.group(1)) > 1200)
    body = main_text(soup)
    anchors = [a for a in soup.find_all("a") if a.get("href")]
    internal = sum(1 for a in anchors
                   if same_host(link_href(page.get("final_url") or page["url"], a),
                                page.get("final_url") or page["url"], include_sub=True))
    return {
        "status": page.get("status"),
        "final_url": page.get("final_url"),
        "title": (title_tag.get_text(" ", strip=True) if title_tag else None),
        "meta_description": meta_content(soup, name="description"),
        "h1_count": len(hs["h1"]),
        "h1_first": (hs["h1"][0][:120] if hs["h1"] else None),
        "h2_count": len(hs["h2"]),
        "canonical": (canon.get("href") if canon else None),
        "robots_meta": meta_content(soup, name="robots"),
        "jsonld_types": types,
        "hreflang": hreflang,
        "lang": (soup.find("html").get("lang") if soup.find("html") else None),
        "word_count": visible_text_len(body),
        "vi_ratio": round(looks_vietnamese(body), 4),
        "img_count": len(imgs),
        "oversized_imgs": oversized,
        "internal_links": internal,
        "html_bytes": len(html),
        "body_hash": hashlib.sha1(re.sub(r"\s+", " ", body).encode()).hexdigest()[:12],
    }


def collect(pages_arg) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in pages_arg:
        url = normalize_url(p.get("final_url") or p["url"], keep_params=True)
        fp = fingerprint(p)
        if fp:
            out[url] = fp
    return out


def diff(base: dict[str, dict], cur: dict[str, dict]) -> list[dict]:
    changes: list[dict] = []

    def add(kind: str, url: str, detail: str, before=None, after=None):
        changes.append({"kind": kind, "severity": SEVERITY_MAP.get(kind, "medium"),
                        "url": url, "detail": detail, "before": before, "after": after})

    for url in sorted(set(base) - set(cur)):
        add("page_disappeared", url, "URL có trong baseline nhưng không crawl được lần này",
            base[url].get("status"), None)
    for url in sorted(set(cur) - set(base)):
        add("page_appeared", url, "URL mới xuất hiện so với baseline", None, cur[url].get("status"))

    for url in sorted(set(base) & set(cur)):
        b, c = base[url], cur[url]
        if b.get("status") != c.get("status"):
            add("status_changed", url, f"HTTP {b.get('status')} → {c.get('status')}",
                b.get("status"), c.get("status"))
        if b.get("title") != c.get("title"):
            add("title_missing" if not c.get("title") else "title_changed", url,
                "Title thay đổi", b.get("title"), c.get("title"))
        if b.get("h1_count") != c.get("h1_count"):
            add("h1_count_changed", url,
                f"Số H1: {b.get('h1_count')} → {c.get('h1_count')}", b.get("h1_count"), c.get("h1_count"))
        bc = normalize_url(b["canonical"], True) if b.get("canonical") else None
        cc = normalize_url(c["canonical"], True) if c.get("canonical") else None
        if bc != cc:
            add("canonical_missing" if not cc else "canonical_changed", url,
                f"Canonical: {b.get('canonical')} → {c.get('canonical')}", b.get("canonical"), c.get("canonical"))
        bn = "noindex" in (b.get("robots_meta") or "")
        cn = "noindex" in (c.get("robots_meta") or "")
        if bn != cn:
            add("noindex_added" if cn else "noindex_removed", url,
                f"meta robots: {b.get('robots_meta')} → {c.get('robots_meta')}",
                b.get("robots_meta"), c.get("robots_meta"))
        bt, ct = set(b.get("jsonld_types") or []), set(c.get("jsonld_types") or [])
        for t in sorted(bt - ct):
            add("jsonld_type_removed", url, f"Mất schema type '{t}'", t, None)
        for t in sorted(ct - bt):
            add("jsonld_type_added", url, f"Thêm schema type '{t}'", None, t)
        if not ct and b.get("jsonld_types"):
            add("jsonld_missing", url, "Trang mất toàn bộ structured data", b.get("jsonld_types"), [])
        bh, ch = b.get("hreflang") or [], c.get("hreflang") or []
        if bh and not ch:
            add("hreflang_removed", url, f"Mất toàn bộ hreflang ({len(bh)} tag)", bh, [])
        elif not bh and ch:
            add("hreflang_added", url, f"Thêm {len(ch)} hreflang", [], ch)
        elif len(bh) != len(ch):
            add("hreflang_count_changed", url, f"hreflang: {len(bh)} → {len(ch)} tag", len(bh), len(ch))
        if (b.get("lang") or "").lower() != (c.get("lang") or "").lower():
            add("lang_changed", url, f'lang: {b.get("lang")} → {c.get("lang")}', b.get("lang"), c.get("lang"))
        bw, cw = b.get("word_count") or 0, c.get("word_count") or 0
        if bw and cw < bw * 0.7:
            add("word_count_drop", url, f"Nội dung giảm {bw} → {cw} từ (-{100*(bw-cw)//max(1,bw)}%)", bw, cw)
        elif cw > bw * 1.5 and cw - bw > 300:
            add("word_count_gain", url, f"Nội dung tăng {bw} → {cw} từ", bw, cw)
        if (c.get("oversized_imgs") or 0) > (b.get("oversized_imgs") or 0):
            add("oversized_images_added", url,
                f"Ảnh quá khổ (w>1200) tăng {b.get('oversized_imgs')} → {c.get('oversized_imgs')}",
                b.get("oversized_imgs"), c.get("oversized_imgs"))
        if (c.get("html_bytes") or 0) > (b.get("html_bytes") or 0) * 1.5 and (c.get("html_bytes") or 0) > 200_000:
            add("html_size_surge", url,
                f"HTML phình {b.get('html_bytes',0)//1024}KB → {c.get('html_bytes',0)//1024}KB",
                b.get("html_bytes"), c.get("html_bytes"))
        if (b.get("internal_links") or 0) and (c.get("internal_links") or 0) < (b.get("internal_links") or 0) * 0.6:
            add("internal_links_drop", url,
                f"Internal link giảm {b.get('internal_links')} → {c.get('internal_links')}",
                b.get("internal_links"), c.get("internal_links"))
        if b.get("body_hash") != c.get("body_hash") and bw and abs(cw - bw) < bw * 0.05:
            add("low" if False else "content_touched", url,
                "Nội dung có thay đổi nhưng độ dài gần như không đổi (sửa câu chữ)",
                b.get("body_hash"), c.get("body_hash"))

    changes.sort(key=lambda x: (SEV_RANK.get(x["severity"], 9), x["url"]))
    return changes


def baseline_path(site: str, drift_dir: str) -> str:
    dom = registrable_domain(site or "site")
    os.makedirs(drift_dir, exist_ok=True)
    return os.path.join(drift_dir, f"baseline-{dom}.json")


def render_md(site: str, changes: list[dict], base_meta: dict, cur_count: int) -> str:
    counts: dict[str, int] = {}
    for c in changes:
        counts[c["severity"]] = counts.get(c["severity"], 0) + 1
    lines = [f"# SEO Drift — {site}", "",
             f"- **Baseline:** {base_meta.get('created_at', '?')} ({base_meta.get('url_count', '?')} URL)",
             f"- **So sánh lúc:** {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} ({cur_count} URL)",
             f"- **Thay đổi:** {len(changes)} "
             f"(critical {counts.get('critical',0)} · high {counts.get('high',0)} · "
             f"medium {counts.get('medium',0)} · info {counts.get('info',0)})", ""]
    if not changes:
        lines += ["✅ Không có thay đổi nào so với baseline.", "",
                  "Nếu vừa deploy mà không có drift: hoặc deploy sạch, hoặc baseline cũ quá. "
                  "Chạy `drift.py baseline` lại sau mỗi lần audit quý.", ""]
        return "\n".join(lines)
    crit = [c for c in changes if c["severity"] in ("critical", "high")]
    if crit:
        lines += ["## ⛔ Cần xem ngay", "",
                  "| Mức | Thay đổi | URL | Trước | Sau |", "|---|---|---|---|---|"]
        for c in crit[:60]:
            b = str(c.get("before"))[:60].replace("|", "\\|")
            a = str(c.get("after"))[:60].replace("|", "\\|")
            lines.append(f"| {c['severity']} | `{c['kind']}` | `{c['url'][-60:]}` | {b or '—'} | {a or '—'} |")
        lines.append("")
    other = [c for c in changes if c["severity"] not in ("critical", "high")]
    if other:
        lines += ["## Thay đổi khác (info/medium)", ""]
        kind_count: dict[str, int] = {}
        for c in other:
            kind_count[c["kind"]] = kind_count.get(c["kind"], 0) + 1
        lines += ["| Loại | Số lần |", "|---|---|"]
        for k, n in sorted(kind_count.items(), key=lambda kv: -kv[1]):
            lines.append(f"| `{k}` | {n} |")
        lines += ["", "<details><summary>Chi tiết</summary>", "",
                  "| Loại | URL | Chi tiết |", "|---|---|---|"]
        for c in other[:120]:
            lines.append(f"| `{c['kind']}` | `{c['url'][-60:]}` | {c['detail'][:110]} |")
        lines += ["", "</details>", ""]
    lines += ["## Hành động", "",
              "1. Nếu `canonical_changed` / `jsonld_type_removed` / `hreflang_removed` xuất hiện "
              "ngay sau một lần deploy → đó là regression, báo dev revert hoặc fix trong ngày.",
              "2. Nếu `title_changed` là chủ đích (bạn vừa tối ưu) → chạy lại `baseline` để "
              "lần sau không báo nữa.",
              "3. Không sửa gì nếu chưa xác nhận là lỗi. Drift report là tín hiệu, không phải kết luận.", ""]
    return "\n".join(lines)


def gather_pages(args) -> tuple[list[dict], str]:
    if args.offline_dir:
        pages = load_offline_dir(args.offline_dir)
        site = "https://" + registrable_domain(pages[0]["url"]) + " (offline)" if pages else args.offline_dir
        return pages, site
    fetch = Fetcher(delay=args.delay, respect_robots=not args.no_respect_robots,
                    cache_dir=args.cache_dir or os.path.join(".cache", "drift"))
    if args.only_url:
        urls = [normalize_url(u, True) for u in args.only_url]
    else:
        urls, _ = collect_urls_live(fetch, args.site, args.max_urls, seeds=args.seed or [])
    pages = [fetch.get(u) | {"url": u} for u in urls]
    return pages, args.site


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Baseline & drift SEO.")
    p.add_argument("cmd", choices=["baseline", "compare", "history"])
    p.add_argument("--site", default=None)
    p.add_argument("--offline-dir", default=None)
    p.add_argument("--only-url", action="append", default=[])
    p.add_argument("--seed", action="append", default=[])
    p.add_argument("--max-urls", type=int, default=150)
    p.add_argument("--delay", type=float, default=0.5)
    p.add_argument("--no-respect-robots", action="store_true")
    p.add_argument("--cache-dir", default=None)
    p.add_argument("--drift-dir", default=DRIFT_DIR_DEFAULT)
    p.add_argument("--baseline", default=None, help="Đường dẫn baseline (mặc định tự suy ra từ site)")
    p.add_argument("--out", default=None, help="Thư mục/file ghi báo cáo compare")
    args = p.parse_args(argv)

    if not args.site and not args.offline_dir:
        eprint("[fatal] cần --site hoặc --offline-dir")
        return 2

    pages, site = gather_pages(args)
    cur = collect(pages)
    bpath = args.baseline or baseline_path(site, args.drift_dir)

    if args.cmd == "baseline":
        payload = {"site": site, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "url_count": len(cur), "fingerprints": cur}
        os.makedirs(os.path.dirname(os.path.abspath(bpath)), exist_ok=True)
        json.dump(payload, open(bpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        eprint(f"[ok] baseline {len(cur)} URL → {bpath}")
        return 0

    if args.cmd == "history":
        d = args.drift_dir
        if not os.path.isdir(d):
            print("(chưa có baseline nào)"); return 0
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                try:
                    j = json.load(open(os.path.join(d, f), encoding="utf-8"))
                    print(f"  {f:42s} {j.get('created_at','?'):22s} {j.get('url_count','?')} URL")
                except Exception:
                    print(f"  {f:42s} (không đọc được)")
        return 0

    # compare
    if not os.path.exists(bpath):
        eprint(f"[fatal] chưa có baseline tại {bpath}. Chạy: drift.py baseline --site {site}")
        return 2
    base_doc = json.load(open(bpath, encoding="utf-8"))
    base = base_doc.get("fingerprints", {})
    changes = diff(base, cur)
    md = render_md(site, changes, base_doc, len(cur))
    if args.out:
        target = args.out
        if os.path.isdir(target) or target.endswith(os.sep):
            os.makedirs(target, exist_ok=True)
            target = os.path.join(target, time.strftime("%Y-%m-%d", time.gmtime()) + "-drift.md")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        open(target, "w", encoding="utf-8").write(md)
        json.dump({"site": site, "changes": changes},
                  open(os.path.splitext(target)[0] + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        eprint(f"[ok] {target}")
    print(md)
    crit = sum(1 for c in changes if c["severity"] == "critical")
    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main())
