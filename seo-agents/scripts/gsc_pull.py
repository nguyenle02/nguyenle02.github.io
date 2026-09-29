#!/usr/bin/env python3
"""gsc_pull.py — Kéo dữ liệu Google Search Console về CSV, kèm so sánh 2 giai đoạn.

Cần:
  1. Service account Google Cloud, bật "Google Search Console API"
  2. Thêm email service account vào property GSC với quyền **Read only** (đủ rồi, đừng cấp Full)
  3. GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json

    export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/ptemagic-gsc.json
    python scripts/gsc_pull.py --days 90 --out data/gsc-90d.csv
    python scripts/gsc_pull.py --days 28 --compare-previous --out data/gsc-28d.csv
    python scripts/gsc_pull.py --days 90 --dimension query --limit 5000

Output CSV tương thích trực tiếp với scripts/cluster_keywords.py.

Nếu chưa có credentials, script in hướng dẫn rồi thoát với code 3 (không crash dây chuyền).
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from common import load_config, eprint  # noqa: E402

SETUP_HINT = """
[!] Chưa cấu hình được Google Search Console API.

Cách làm (một lần, ~10 phút):
  1. https://console.cloud.google.com → tạo/chọn project
  2. APIs & Services → Library → bật "Google Search Console API"
  3. IAM & Admin → Service Accounts → Create → (không cần role gì ở cấp project)
  4. Keys → Add key → JSON → tải file về, ví dụ ~/.config/gcloud/ptemagic-gsc.json
  5. https://search.google.com/search-console → chọn property ptemagic.com
     → Settings → Users and permissions → Add user
     → dán email của service account (kết thúc bằng @...iam.gserviceaccount.com)
     → quyền: **Restricted (Read only)** là đủ
  6. export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/ptemagic-gsc.json

Kiểm tra: python scripts/gsc_pull.py --days 7 --limit 5
"""


def get_service():
    try:
        from googleapiclient.discovery import build  # type: ignore
        from google.oauth2 import service_account  # type: ignore
    except ImportError:
        eprint("[!] Thiếu thư viện. Chạy: pip install google-api-python-client google-auth")
        return None
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        eprint(SETUP_HINT)
        return None
    try:
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
        return build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    except Exception as e:  # noqa: BLE001
        eprint(f"[!] Không tạo được client: {type(e).__name__}: {e}")
        eprint(SETUP_HINT)
        return None


def query_gsc(service, site_url: str, start: str, end: str, dimensions: list[str],
              row_limit: int = 25000, dimension_filter: list | None = None) -> list[dict]:
    rows: list[dict] = []
    start_row = 0
    page = min(row_limit, 25000)
    while True:
        body = {
            "startDate": start, "endDate": end,
            "dimensions": dimensions, "rowLimit": page, "startRow": start_row,
            "dataState": "final", "type": "web",
        }
        if dimension_filter:
            body["dimensionFilterGroups"] = dimension_filter
        try:
            resp = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
        except Exception as e:  # noqa: BLE001
            eprint(f"[!] GSC query lỗi tại startRow={start_row}: {type(e).__name__}: {str(e)[:200]}")
            break
        batch = resp.get("rows") or []
        rows.extend(batch)
        if len(batch) < page:
            break
        start_row += page
        if start_row >= row_limit:
            break
    return rows


def rows_to_records(rows: list[dict], dimensions: list[str]) -> list[dict]:
    out = []
    for r in rows:
        keys = r.get("keys") or []
        rec = {d: (keys[i] if i < len(keys) else "") for i, d in enumerate(dimensions)}
        rec["clicks"] = int(r.get("clicks", 0))
        rec["impressions"] = int(r.get("impressions", 0))
        rec["ctr"] = round(float(r.get("ctr", 0)), 4)
        rec["position"] = round(float(r.get("position", 0)), 2)
        out.append(rec)
    return out


def merge_compare(cur: list[dict], prev: list[dict], dimensions: list[str]) -> list[dict]:
    """Ghép 2 giai đoạn theo key để tính delta — phát hiện content decay sớm."""
    def key(r):
        return "|".join(str(r.get(d, "")) for d in dimensions)
    pmap = {key(r): r for r in prev}
    out = []
    for r in cur:
        p = pmap.get(key(r))
        merged = dict(r)
        merged["clicks_prev"] = p["clicks"] if p else 0
        merged["impressions_prev"] = p["impressions"] if p else 0
        merged["position_prev"] = p["position"] if p else None
        merged["clicks_delta"] = r["clicks"] - (p["clicks"] if p else 0)
        merged["impressions_delta"] = r["impressions"] - (p["impressions"] if p else 0)
        merged["position_delta"] = (round(r["position"] - p["position"], 2) if p else None)
        merged["is_new"] = p is None
        # content decay: click giảm >= 30% mà impression không giảm tương ứng
        if p and p["clicks"] >= 10 and r["clicks"] < p["clicks"] * 0.7:
            merged["decay"] = True
        else:
            merged["decay"] = False
        out.append(merged)
    # query biến mất hoàn toàn (có ở kỳ trước, không còn kỳ này) — dấu hiệu mất index/rank
    ckeys = {key(r) for r in cur}
    for r in prev:
        if key(r) not in ckeys and r["clicks"] >= 5:
            lost = dict(r)
            lost.update({"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0,
                         "clicks_prev": r["clicks"], "impressions_prev": r["impressions"],
                         "position_prev": r["position"], "clicks_delta": -r["clicks"],
                         "impressions_delta": -r["impressions"], "position_delta": None,
                         "is_new": False, "decay": True, "lost": True})
            out.append(lost)
    return out


def summarise(records: list[dict]) -> str:
    tot_clicks = sum(r["clicks"] for r in records)
    tot_impr = sum(r["impressions"] for r in records)
    brand = [r for r in records if "pte magic" in str(r.get("query", "")).lower()]
    nonbrand = [r for r in records if r not in brand]
    decay = [r for r in records if r.get("decay")]
    new = [r for r in records if r.get("is_new")]
    striking = [r for r in records if r.get("position") and 5 <= r["position"] <= 20
                and r["impressions"] >= 50]
    lines = [
        f"Tổng click: {tot_clicks:,} · Tổng impression: {tot_impr:,} · "
        f"CTR: {tot_clicks/max(1,tot_impr)*100:.2f}%",
        f"Brand query: {len(brand)} dòng, {sum(r['clicks'] for r in brand):,} click "
        f"({sum(r['clicks'] for r in brand)/max(1,tot_clicks)*100:.0f}% tổng)",
        f"Non-brand: {sum(r['clicks'] for r in nonbrand):,} click  ← KPI chính",
    ]
    if any("clicks_prev" in r for r in records):
        lines += [
            f"Striking distance (position 5-20, impression ≥50): {len(striking)} query",
            f"Content decay (click giảm ≥30%): {len(decay)} dòng",
            f"Query mới xuất hiện: {len(new)}",
        ]
        if striking:
            lines.append("\nTop striking distance:")
            for r in sorted(striking, key=lambda x: -x["impressions"])[:12]:
                lines.append(f"  · {r.get('query','')[:52]:54s} pos {r['position']:5.1f} "
                             f"impr {r['impressions']:6,} click {r['clicks']:4d} "
                             f"{str(r.get('page','')).replace('https://ptemagic.com','')[:40]}")
        if decay:
            lines.append("\nContent decay (cần refresh):")
            for r in sorted(decay, key=lambda x: x.get("clicks_delta", 0))[:12]:
                lines.append(f"  · {str(r.get('query',''))[:52]:54s} "
                             f"click {r.get('clicks_prev',0)} → {r['clicks']} "
                             f"({r.get('clicks_delta',0):+d})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Kéo dữ liệu Google Search Console.")
    p.add_argument("--site-url", default=None, help="vd https://ptemagic.com/ hoặc sc-domain:ptemagic.com")
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--end-date", default=None, help="YYYY-MM-DD (mặc định: hôm qua)")
    p.add_argument("--dimension", default="query,page,country,device",
                   help="query,page,country,device,date (phân tách bằng dấu phẩy)")
    p.add_argument("--limit", type=int, default=25000)
    p.add_argument("--compare-previous", action="store_true",
                   help="Kéo thêm giai đoạn liền trước cùng độ dài để tính delta/decay")
    p.add_argument("--out", default="data/gsc.csv")
    p.add_argument("--summary-out", default=None)
    p.add_argument("--config", default=None)
    p.add_argument("--dry-run", action="store_true", help="Chỉ in cấu hình sẽ dùng, không gọi API")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    site_url = args.site_url or os.environ.get("GSC_SITE_URL")
    if not site_url:
        props = ((cfg.get("data_sources") or {}).get("gsc") or {}).get("properties") or []
        site_url = props[0] if props else "https://ptemagic.com/"
    dims = [d.strip() for d in args.dimension.split(",") if d.strip()]

    end = args.end_date or (dt.date.today() - dt.timedelta(days=1)).isoformat()
    start = (dt.date.fromisoformat(end) - dt.timedelta(days=args.days - 1)).isoformat()

    eprint(f"[gsc] site={site_url}  range={start}..{end} ({args.days} ngày)  dims={dims}")
    if args.dry_run:
        print(json.dumps({"site_url": site_url, "start": start, "end": end, "dimensions": dims,
                          "compare_previous": args.compare_previous}, ensure_ascii=False, indent=2))
        return 0

    service = get_service()
    if service is None:
        return 3

    cur = rows_to_records(query_gsc(service, site_url, start, end, dims, args.limit), dims)
    eprint(f"[gsc] {len(cur)} dòng giai đoạn hiện tại")
    if args.compare_previous and cur is not None:
        p_end = (dt.date.fromisoformat(start) - dt.timedelta(days=1)).isoformat()
        p_start = (dt.date.fromisoformat(p_end) - dt.timedelta(days=args.days - 1)).isoformat()
        prev = rows_to_records(query_gsc(service, site_url, p_start, p_end, dims, args.limit), dims)
        eprint(f"[gsc] {len(prev)} dòng giai đoạn trước ({p_start}..{p_end})")
        records = merge_compare(cur, prev, dims)
    else:
        records = cur

    if not records:
        eprint("[!] Không có dữ liệu. Kiểm tra: property đúng chưa, service account đã được "
               "thêm vào Users & permissions chưa, khoảng ngày có dữ liệu chưa.")
        return 4

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    fieldnames = list(dims) + ["clicks", "impressions", "ctr", "position"]
    if args.compare_previous:
        fieldnames += ["clicks_prev", "impressions_prev", "position_prev",
                       "clicks_delta", "impressions_delta", "position_delta",
                       "is_new", "decay"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in sorted(records, key=lambda x: -x["clicks"]):
            w.writerow(r)
    eprint(f"[ok] {args.out} ({len(records)} dòng)")

    summary = summarise(records)
    if args.summary_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.summary_out)) or ".", exist_ok=True)
        open(args.summary_out, "w", encoding="utf-8").write("# GSC Summary\n\n```\n" + summary + "\n```\n")
        eprint(f"[ok] {args.summary_out}")
    print("\n" + summary)
    print("\n→ Bước tiếp theo: python scripts/cluster_keywords.py --in "
          f"{args.out} --out data/clusters.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
