#!/usr/bin/env python3
"""psi_cwv.py — Core Web Vitals từ PageSpeed Insights API (lab + field/CrUX).

Vì sao cần script riêng: `seo_audit.py` chỉ SUY RA rủi ro CWV từ HTML (vd phát hiện
`/_next/image?w=3840`). Nó không đo được LCP/INP/CLS thật. Script này đo thật.

    export PSI_API_KEY=...        # miễn phí: https://developers.google.com/speed/docs/insights/v5/get-started
    python scripts/psi_cwv.py --config config/ptemagic.yaml
    python scripts/psi_cwv.py --url https://ptemagic.com/ --url https://ptemagic.com/vi --strategy mobile
    python scripts/psi_cwv.py --url https://ptemagic.com/ --json-out data/cwv.json

Lưu ý quota: PSI không có API key thì quota gần như bằng 0 (Google đã siết). Bắt buộc có key.
Giới hạn thực tế ~25.000 request/ngày nhưng nên giữ delay ≥ 2s giữa các URL.

Số liệu field (CrUX) là thứ Google dùng để xếp hạng — lab chỉ để chẩn đoán.
Ngưỡng 2026: LCP ≤2.5s tốt / >4s kém · INP ≤200ms tốt / >500ms kém · CLS ≤0.1 tốt / >0.25 kém.
INP thay FID từ 12/03/2024; FID đã bị bỏ khỏi CrUX/PSI ngày 09/09/2024 — KHÔNG báo cáo FID.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from common import load_config, thresholds, eprint  # noqa: E402

try:
    import requests  # type: ignore
except ImportError:
    eprint("[!] Cần requests: pip install requests")
    raise

PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

# Lighthouse audit id → tên dễ đọc + vì sao nó quan trọng
KEY_AUDITS = [
    ("largest-contentful-paint-element", "LCP element", "Phần tử gây LCP — thường là ảnh hero"),
    ("prioritize-lcp-image", "Ưu tiên ảnh LCP", "Preload ảnh LCP, bỏ lazy-load"),
    ("total-blocking-time", "Total Blocking Time", "JS chặn main thread → ảnh hưởng INP"),
    ("unused-javascript", "JS không dùng", "Bytes JS tải về nhưng không chạy"),
    ("unused-css-rules", "CSS không dùng", "Bytes CSS thừa"),
    ("render-blocking-resources", "Render-blocking", "Tài nguyên chặn render đầu trang"),
    ("modern-image-formats", "Ảnh chưa WebP/AVIF", "Tiết kiệm bytes ảnh"),
    ("properly-size-images", "Ảnh sai kích thước", "Phục vụ ảnh đúng kích thước hiển thị"),
    ("uses-responsive-images", "Ảnh không responsive", "srcset/sizes"),
    ("layout-shifts", "Layout shift", "Nguyên nhân CLS"),
    ("non-composited-animations", "Animation không composite", "Gây CLS/jank"),
    ("font-display", "Font display", "FOIT/FOUT ảnh hưởng LCP"),
    ("server-response-time", "TTFB", "Thời gian server phản hồi"),
    ("dom-size", "DOM size", "DOM quá lớn → chậm hydration (Next.js)"),
    ("third-party-summary", "Bên thứ ba", "Script third-party chiếm bao nhiêu"),
    ("image-size-responsive", "Ảnh responsive", "width/height/sizes"),
]


def verdict(value: float, good: float, poor: float, higher_is_worse: bool = True) -> str:
    if value is None:
        return "?"
    if higher_is_worse:
        return "GOOD" if value <= good else ("POOR" if value >= poor else "NI")
    return "GOOD" if value >= good else ("POOR" if value <= poor else "NI")


def icon(v: str) -> str:
    return {"GOOD": "🟢", "NI": "🟡", "POOR": "🔴", "?": "⚪"}.get(v, "⚪")


def call_psi(url: str, strategy: str, api_key: str | None, timeout: int = 120,
             category: str = "performance") -> dict:
    params = {"url": url, "strategy": strategy, "category": category,
              "locale": "en"}
    if api_key:
        params["key"] = api_key
    try:
        r = requests.get(PSI_URL, params=params, timeout=timeout)
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {str(e)[:160]}"}
    if r.status_code == 429:
        return {"error": "429 quota/rate limit — thêm delay hoặc kiểm tra PSI_API_KEY"}
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        return {"error": f"JSON decode: {e}"}


def extract(url: str, strategy: str, data: dict) -> dict:
    out: dict = {"url": url, "strategy": strategy}
    if "error" in data:
        out["error"] = data["error"]
        return out

    lhr = (data.get("lighthouseResult") or {})
    audits = lhr.get("audits") or {}
    cats = lhr.get("categories") or {}
    perf = (cats.get("performance") or {}).get("score")
    out["lighthouse_perf_score"] = round(perf * 100) if isinstance(perf, (int, float)) else None
    out["lighthouse_version"] = lhr.get("lighthouseVersion")
    out["fetch_time"] = lhr.get("fetchTime")
    out["final_url"] = ((data.get("loadingExperience") or {}).get("initial_url")
                        or lhr.get("finalDisplayedUrl") or url)

    # ---- lab metrics ----
    def ms(key):
        v = (audits.get(key) or {}).get("numericValue")
        return round(v) if isinstance(v, (int, float)) else None

    def unitless(key):
        v = (audits.get(key) or {}).get("numericValue")
        return round(v, 4) if isinstance(v, (int, float)) else None

    lab = {
        "lcp_ms": ms("largest-contentful-paint"),
        "tbt_ms": ms("total-blocking-time"),
        "cls": unitless("cumulative-layout-shift"),
        "speed_index_ms": ms("speed-index"),
        "ttfb_ms": ms("server-response-time"),
        "fcp_ms": ms("first-contentful-paint"),
        "si_ms": ms("speed-index"),
    }
    out["lab"] = lab

    # ---- field metrics (CrUX) — thứ Google dùng để xếp hạng ----
    le = data.get("loadingExperience") or {}
    out["crux_state"] = le.get("overall_category")      # GOOD / AVERAGE / POOR / None
    out["crux_origin"] = (data.get("originLoadingExperience") or {}).get("overall_category")
    metrics = le.get("metrics") or {}
    def pct(key, sub):
        m = metrics.get(key) or {}
        d = (m.get("percentile") or {})
        return d.get(sub) if isinstance(d, dict) else None
    field = {
        "lcp_p75_ms": pct("LARGEST_CONTENTFUL_PAINT_MS", "LARGEST_CONTENTFUL_PAINT_MS")
                      or (metrics.get("LARGEST_CONTENTFUL_PAINT_MS") or {}).get("percentile"),
        "inp_p75_ms": (metrics.get("INTERACTION_TO_NEXT_PAINT") or {}).get("percentile"),
        "cls_p75": (metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE") or {}).get("percentile"),
        "fcp_p75_ms": (metrics.get("FIRST_CONTENTFUL_PAINT_MS") or {}).get("percentile"),
        "ttfb_p75_ms": (metrics.get("EXPERIMENTAL_TIME_TO_FIRST_BYTE") or {}).get("percentile"),
    }
    out["field"] = field
    out["field_distributions"] = {
        k: (v or {}).get("histogram") for k, v in metrics.items()
    }

    # ---- cơ hội & chẩn đoán ----
    opps, diags = [], []
    for aid, name, why in KEY_AUDITS:
        a = audits.get(aid)
        if not a:
            continue
        score = a.get("score")
        if score is None:
            continue
        if score < 0.9:
            item = {"audit": aid, "name": name, "why": why, "score": score,
                    "display": a.get("displayValue") or "",
                    "savings_ms": (a.get("details") or {}).get("overallSavingsMs"),
                    "savings_kb": (a.get("details") or {}).get("overallSavingsBytes")
                                  and round((a["details"]["overallSavingsBytes"] or 0) / 1024)}
            if a.get("scoreDisplayMode") == "metricSavings" or (a.get("details") or {}).get("type") in (
                    "opportunity", "table") and item["savings_ms"]:
                opps.append(item)
            else:
                diags.append(item)
    out["opportunities"] = sorted(opps, key=lambda x: -(x.get("savings_ms") or 0))[:12]
    out["diagnostics"] = diags[:20]

    # LCP element chi tiết — thứ dev cần để sửa
    lcp_el = audits.get("largest-contentful-paint-element") or {}
    items = ((lcp_el.get("details") or {}).get("items") or [])
    if items:
        node = (items[0].get("items") or [{}])[0].get("node") or {}
        out["lcp_element"] = {"selector": node.get("selector"),
                              "snippet": (node.get("snippet") or "")[:200],
                              "explanation": (node.get("explanation") or "")[:300]}
    return out


def render_md(results: list[dict], cfg: dict) -> str:
    lcp_g = thresholds(cfg, "core_web_vitals", "lcp_good_ms", default=2500)
    lcp_p = thresholds(cfg, "core_web_vitals", "lcp_poor_ms", default=4000)
    inp_g = thresholds(cfg, "core_web_vitals", "inp_good_ms", default=200)
    inp_p = thresholds(cfg, "core_web_vitals", "inp_poor_ms", default=500)
    cls_g = thresholds(cfg, "core_web_vitals", "cls_good", default=0.10)
    cls_p = thresholds(cfg, "core_web_vitals", "cls_poor", default=0.25)

    out = ["# Core Web Vitals — PTE Magic", "",
           f"- **Ngày đo:** {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
           "- **Nguồn:** PageSpeed Insights API v5 (lab = Lighthouse, field = CrUX 28 ngày, p75)",
           "- ⚠️ **Field data là thứ Google dùng để đánh giá.** Lab chỉ để chẩn đoán nguyên nhân.",
           "- INP đã thay FID từ 12/03/2024. Không có FID trong báo cáo này là đúng.", ""]

    out += ["## Field data (CrUX) — quan trọng nhất", "",
            "| URL | Trạng thái | LCP p75 | INP p75 | CLS p75 |", "|---|---|---|---|---|"]
    any_field = False
    for r in results:
        if r.get("error"):
            out.append(f"| `{r['url']}` | ⚠️ lỗi: {r['error'][:70]} | - | - | - |")
            continue
        f = r.get("field") or {}
        state = r.get("crux_state") or "chưa đủ traffic"
        if r.get("crux_state"):
            any_field = True
        lcp = f.get("lcp_p75_ms")
        out.append(f"| `{r['url'][:52]}` ({r['strategy']}) | {state} | "
                   f"{icon(verdict(lcp/1000 if lcp else None, lcp_g/1000, lcp_p/1000))} "
                   f"{(str(round(lcp))+'ms') if lcp else '—'} | "
                   f"{icon(verdict(f.get('inp_p75_ms'), inp_g, inp_p))} "
                   f"{(str(f['inp_p75_ms'])+'ms') if f.get('inp_p75_ms') else '—'} | "
                   f"{icon(verdict(f.get('cls_p75'), cls_g, cls_p))} "
                   f"{f['cls_p75'] if f.get('cls_p75') is not None else '—'} |")
    out.append("")
    if not any_field:
        out += ["> **CrUX chưa có dữ liệu field** cho các URL này. Nguyên nhân thường gặp: "
                "lượng người dùng Chrome thật chưa đủ ngưỡng, hoặc URL mới. Khi đó Google "
                "chưa phạt về CWV — nhưng cũng có nghĩa là bạn đang bay mù. Dùng số lab bên "
                "dưới làm proxy và đo lại hàng tháng.", ""]

    out += ["## Lab data (Lighthouse) — để chẩn đoán", "",
            "| URL | Perf | LCP | TBT | CLS | TTFB |", "|---|---|---|---|---|---|"]
    for r in results:
        if r.get("error"):
            continue
        lab = r.get("lab") or {}
        out.append(f"| `{r['url'][:48]}` ({r['strategy']}) | "
                   f"{icon(verdict(-(r.get('lighthouse_perf_score') or 0), -90, -50))} "
                   f"{r.get('lighthouse_perf_score')} | "
                   f"{icon(verdict(lab.get('lcp_ms'), lcp_g, lcp_p))} {lab.get('lcp_ms') or '—'}ms | "
                   f"{lab.get('tbt_ms') or '—'}ms | "
                   f"{icon(verdict(lab.get('cls'), cls_g, cls_p))} {lab.get('cls') if lab.get('cls') is not None else '—'} | "
                   f"{lab.get('ttfb_ms') or '—'}ms |")
    out.append("")

    for r in results:
        if r.get("error") or not (r.get("opportunities") or r.get("lcp_element")):
            continue
        out += [f"### `{r['url']}` ({r['strategy']})", ""]
        if r.get("lcp_element"):
            le = r["lcp_element"]
            out += [f"**LCP element:** `{le.get('selector') or '?'}`", "",
                    f"```\n{(le.get('snippet') or '').strip()}\n```", ""]
        if r.get("opportunities"):
            out += ["**Cơ hội cải thiện (xếp theo ms tiết kiệm được):**", "",
                    "| Audit | Tiết kiệm | Chi tiết | Vì sao quan tâm |", "|---|---|---|---|"]
            for o in r["opportunities"]:
                save = o.get("savings_ms")
                save_s = f"{int(save)}ms" if save else (f"{o['savings_kb']}KB" if o.get("savings_kb") else "—")
                out.append(f"| {o['name']} | {save_s} | {(o.get('display') or '')[:60]} | {o['why']} |")
            out.append("")
    out += ["## Cách đọc báo cáo này", "",
            "1. **Bắt đầu từ field data.** Nếu CrUX `POOR` → đó là vấn đề xếp hạng thật, sửa trước.",
            "2. Nếu CrUX chưa có data → dùng lab, nhưng hiểu rằng lab đo trên mạng/máy lý tưởng, "
            "thực tế mobile 4G Việt Nam/Ấn Độ sẽ tệ hơn 1.5-2 lần.",
            "3. **LCP element** cho biết chính xác phần tử nào cần sửa — đưa thẳng cho dev.",
            "4. Đừng đuổi theo điểm Lighthouse 100. Đuổi theo `GOOD` ở cả 3 chỉ số field trên ≥75% URL.",
            ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Đo Core Web Vitals bằng PageSpeed Insights API.")
    p.add_argument("--url", action="append", default=[], help="URL cần đo (lặp lại nhiều lần)")
    p.add_argument("--strategy", default="mobile", choices=["mobile", "desktop", "both"])
    p.add_argument("--config", default=None)
    p.add_argument("--out", default=None, help="Ghi báo cáo Markdown")
    p.add_argument("--json-out", default=None)
    p.add_argument("--delay", type=float, default=2.5)
    p.add_argument("--retries", type=int, default=2)
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    api_key = os.environ.get("PSI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        eprint("[warn] Chưa đặt PSI_API_KEY. Quota ẩn danh của PSI gần như bằng 0 — "
               "khả năng cao sẽ nhận 429. Tạo key miễn phí tại "
               "https://console.cloud.google.com/apis/credentials")

    urls = args.url or (((cfg.get("data_sources") or {}).get("pagespeed") or {}).get("priority_urls") or [])
    if not urls:
        urls = ["https://ptemagic.com/", "https://ptemagic.com/vi", "https://ptemagic.com/blogs"]
    strategies = ["mobile", "desktop"] if args.strategy == "both" else [args.strategy]

    results: list[dict] = []
    for u in urls:
        for s in strategies:
            eprint(f"[psi] {s:7s} {u}")
            data = {}
            for attempt in range(args.retries + 1):
                data = call_psi(u, s, api_key)
                if "error" not in data:
                    break
                eprint(f"   thử lại ({attempt+1}): {data.get('error','')[:90]}")
                time.sleep(args.delay * (attempt + 2))
            results.append(extract(u, s, data))
            time.sleep(args.delay)

    md = render_md(results, cfg)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        open(args.out, "w", encoding="utf-8").write(md)
        eprint(f"[ok] {args.out}")
    else:
        print(md)
    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)) or ".", exist_ok=True)
        json.dump(results, open(args.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        eprint(f"[ok] {args.json_out}")

    errs = [r for r in results if r.get("error")]
    if len(errs) == len(results) and results:
        eprint("[!] Tất cả request đều lỗi — kiểm tra PSI_API_KEY và quota.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
