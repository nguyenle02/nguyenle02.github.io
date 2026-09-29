#!/usr/bin/env python3
"""cluster_keywords.py — Gom query thành cluster + quyết định hành động.

Nhận CSV export từ:
  * Google Search Console (qua scripts/gsc_pull.py hoặc export tay):
      query,page,country,device,clicks,impressions,ctr,position
  * Ahrefs / Semrush / DataForSEO (tự nhận diện cột):
      keyword,volume,kd,difficulty,position,url,serp_url,intent

Không gọi API, không đoán volume. Nếu cột volume không có thì nói rõ là không có.

    python scripts/cluster_keywords.py --in data/gsc-90d.csv --out data/clusters.md
    python scripts/cluster_keywords.py --in data/ahrefs.csv --csv-out data/clusters.csv

Triết lý: phân loại bằng QUY TẮC đọc được, không bằng mô hình. Người dùng phải kiểm tra
được vì sao một query bị gán là REFRESH.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import collections
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
from common import content_tokens, jaccard, load_config, eprint  # noqa: E402

BRAND_TERMS = ["pte magic", "ptemagic", "pte magic login", "magic pte"]

NAV = re.compile(r"\b(login|sign in|signin|app|website|official|trang chủ|đăng nhập|"
                 r"tai app|tải app)\b", re.I)
TRANS = re.compile(r"\b(price|pricing|cost|fee|buy|purchase|course|courses|free|download|"
                   r"register|sign up|subscribe|plan|mock test|practice test|test online|"
                   r"trial|discount|coupon|học phí|khoá học|khóa học|giá|miễn phí|đăng ký|"
                   r"luyện đề|thi thử|mua)\b", re.I)
COMMERCIAL = re.compile(r"\b(best|top|review|reviews|vs|versus|alternative|compare|"
                        r"comparison|which|recommend|tốt nhất|so sánh|nên học|đánh giá)\b", re.I)
INFO = re.compile(r"\b(how|what|why|when|where|who|is|are|can|do|does|guide|tutorial|tips|"
                   r"tip|example|examples|template|format|structure|pattern|meaning|"
                   r"cách|là gì|tại sao|khi nào|ở đâu|hướng dẫn|mẹo|cấu trúc|đề|nghĩa)\b", re.I)

# Bucket chủ đề theo domain PTE — quy tắc đọc được, sửa được
TOPIC_RULES: list[tuple[str, re.Pattern]] = [
    ("C6-brand-platform",  re.compile(r"(pte magic|ptemagic|mock test|practice test|practice app|test online|free test)", re.I)),
    ("C5-pte-core",        re.compile(r"pte[\s-]?core", re.I)),
    ("C1-format-structure",re.compile(r"(exam pattern|exam structure|test format|test structure|question types|exam format|cấu trúc|định dạng|format đề)", re.I)),
    ("C3-score-scoring",   re.compile(r"(score|scoring|band|calculator|equivalent|conversion|result|valid|chấm điểm|điểm|quy đổi|tính điểm)", re.I)),
    ("C2-task-tips",       re.compile(r"(repeat sentence|write from dictation|describe image|retell lecture|reorder paragraph|fill in the blank|summarize|summary|essay|answer short question|highlight|multiple choice|respond to a situation|read aloud|oral fluency|pronunciation)", re.I)),
    ("C4-study-abroad",    re.compile(r"(study|student|university|scholarship|visa|migration|immigration|work permit|accommodation|cost of living|part.?time job|du học|học bổng|định cư|visa|trường)", re.I)),
    ("C2-skill-generic",   re.compile(r"(speaking|listening|reading|writing)", re.I)),
    ("C1-exam-generic",    re.compile(r"(pte|pearson|ielts|toefl|english test)", re.I)),
]

FUNNEL_WEIGHT = {"BOFU": 1.6, "MOFU": 1.2, "TOFU": 1.0}

ALIASES = {
    "query": ["query", "keyword", "keywords", "search term", "search_query", "từ khóa", "tu khoa"],
    "page": ["page", "url", "landing page", "landing_page", "page_url", "serp_url", "trang"],
    "clicks": ["clicks", "click", "lượt nhấp"],
    "impressions": ["impressions", "impression", "searches", "volume", "search_volume", "lượt hiển thị"],
    "position": ["position", "avg position", "average position", "rank", "position_avg"],
    "ctr": ["ctr", "click through rate"],
    "country": ["country", "country_code", "quốc gia"],
    "device": ["device", "thiết bị"],
    "kd": ["kd", "keyword difficulty", "difficulty", "difficulty_index"],
}


def norm(s) -> str:
    return str(s or "").strip()


def detect_columns(header: list[str]) -> dict[str, str]:
    low = {h.strip().lower().replace(" ", "_"): h for h in header}
    out: dict[str, str] = {}
    for canon, names in ALIASES.items():
        for n in names:
            k = n.lower().replace(" ", "_")
            if k in low:
                out[canon] = low[k]
                break
    return out


@dataclass
class Row:
    query: str = ""
    page: str = ""
    clicks: float = 0.0
    impressions: float = 0.0
    position: float = 0.0
    ctr: float = 0.0
    country: str = ""
    device: str = ""
    kd: float | None = None
    topic: str = "C0-uncategorised"
    intent: str = "informational"
    funnel: str = "TOFU"
    cluster: str = ""
    action: str = "REVIEW"
    priority: float = 0.0
    reason: str = ""


def to_float(v, default=0.0) -> float:
    s = norm(v).replace(",", "").replace("%", "")
    try:
        return float(s)
    except Exception:
        return default


def classify_topic(q: str) -> str:
    for name, pat in TOPIC_RULES:
        if pat.search(q):
            return name
    return "C0-uncategorised"


def classify_intent(q: str) -> tuple[str, str]:
    ql = q.lower()
    if any(b in ql for b in BRAND_TERMS) or NAV.search(ql):
        return "navigational", "BOFU"
    if TRANS.search(ql):
        return "transactional", "BOFU"
    if COMMERCIAL.search(ql):
        return "commercial", "MOFU"
    if INFO.search(ql):
        # tip/template cho từng task = người đang chuẩn bị thi → MOFU, không phải TOFU thuần
        if re.search(r"(tips?|template|practice|cách làm|mẹo|đề|example)", ql):
            return "informational", "MOFU"
        if re.search(r"(visa|scholarship|cost of living|migration|định cư|học bổng)", ql):
            return "informational", "TOFU"
        return "informational", "TOFU"
    return "informational", "TOFU"


def decide_action(r: Row, pages_in_cluster: collections.Counter) -> tuple[str, str]:
    """Quy tắc hành động. Ghi rõ lý do để người dùng kiểm tra được."""
    q = r.query
    if not r.page:
        if r.impressions >= 50 or (r.kd is not None and r.impressions >= 20):
            return "NEW", (f"Chưa có URL nào rank cho query này, impression={int(r.impressions)} "
                           f"→ có nhu cầu thật, cần trang mới.")
        return "MONITOR", f"Chưa có URL rank và impression chỉ {int(r.impressions)} → theo dõi, chưa đầu tư."
    if r.position <= 3:
        return "DEFEND", f"Đang top {r.position:.1f} → giữ, tối ưu CTR (title/description), đừng đụng cấu trúc."
    if r.position <= 10:
        return "PUSH", f"Đang top {r.position:.1f} → thêm internal link + section mới để vào top 3."
    if r.position <= 20:
        return "REFRESH", (f"Striking distance: position {r.position:.1f}, impression {int(r.impressions)}. "
                           f"Cập nhật nội dung + schema + internal link thường vượt được vào top 10.")
    if r.impressions < 30:
        return "PRUNE", f"Position {r.position:.0f} và chỉ {int(r.impressions)} impression → không đáng đầu tư."
    if pages_in_cluster[r.cluster] > 1:
        return "CONSOLIDATE", (f"{pages_in_cluster[r.cluster]} URL cùng cluster '{r.cluster}' và cùng rank "
                               f"cho query này → cannibalisation, cân nhắc gộp/301.")
    return "REWRITE", f"Position {r.position:.0f} với {int(r.impressions)} impression → nội dung chưa khớp intent."


def cluster_within_topic(rows: list[Row], min_jaccard: float = 0.5) -> None:
    """Gom query trong cùng topic bucket theo chồng lấn token (tham lam, deterministic)."""
    for topic in {r.topic for r in rows}:
        group = sorted([r for r in rows if r.topic == topic],
                       key=lambda r: -r.impressions)
        centres: list[tuple[str, set]] = []
        for r in group:
            toks = set(content_tokens(r.query))
            if not toks:
                r.cluster = f"{topic}::misc"
                continue
            best, bestj = None, 0.0
            for name, cset in centres:
                j = jaccard(toks, cset)
                if j > bestj:
                    best, bestj = name, j
            if best and bestj >= min_jaccard:
                r.cluster = best
                # mở rộng tâm cụm để bắt các biến thể dài hơn
                centres = [(n, s | toks if n == best else s) for n, s in centres]
            else:
                label = f"{topic}::{'-'.join(sorted(toks)[:3])}"
                r.cluster = label
                centres.append((label, toks))


def priority(r: Row) -> float:
    base = r.impressions if r.impressions else 0.0
    pos_factor = max(0.0, (21.0 - min(r.position, 21.0))) / 20.0 if r.position else 1.0
    if r.action in ("NEW", "MONITOR"):
        pos_factor = 1.0
    kd_penalty = 1.0
    if r.kd is not None:
        kd_penalty = max(0.3, 1.0 - (r.kd / 150.0))
    return round(base * pos_factor * FUNNEL_WEIGHT.get(r.funnel, 1.0) * kd_penalty, 1)


def load_rows(path: str) -> list[Row]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(8192)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except Exception:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        header = reader.fieldnames or []
        cols = detect_columns(header)
        if "query" not in cols:
            raise SystemExit(f"[fatal] không tìm thấy cột query/keyword trong {header}")
        rows: list[Row] = []
        for raw in reader:
            r = Row()
            r.query = norm(raw.get(cols["query"])).lower().strip()
            if not r.query or len(r.query) < 3:
                continue
            r.page = norm(raw.get(cols.get("page", ""), ""))
            r.clicks = to_float(raw.get(cols.get("clicks", ""), 0))
            r.impressions = to_float(raw.get(cols.get("impressions", ""), 0))
            r.position = to_float(raw.get(cols.get("position", ""), 0))
            r.ctr = to_float(raw.get(cols.get("ctr", ""), 0))
            r.country = norm(raw.get(cols.get("country", ""), ""))
            r.device = norm(raw.get(cols.get("device", ""), ""))
            if cols.get("kd"):
                r.kd = to_float(raw.get(cols["kd"], 0)) or None
            r.topic = classify_topic(r.query)
            r.intent, r.funnel = classify_intent(r.query)
            rows.append(r)
    # gộp query trùng (GSC export thường tách theo page/device/country)
    agg: dict[str, Row] = {}
    for r in rows:
        key = r.query + "|" + r.page
        if key in agg:
            a = agg[key]
            a.clicks += r.clicks
            a.impressions += r.impressions
            if r.position and (not a.position or r.impressions > a.impressions):
                a.position = r.position
        else:
            agg[key] = r
    return list(agg.values())


def build_markdown(rows: list[Row], src: str) -> str:
    total_impr = sum(r.impressions for r in rows)
    out = [f"# Keyword Clusters — {src}", "",
           f"- **Số query:** {len(rows)}",
           f"- **Tổng impression:** {int(total_impr):,}",
           f"- **Có dữ liệu volume bên thứ 3:** "
           f"{'có' if any(r.kd is not None for r in rows) else 'không (chỉ dùng impression GSC)'}",
           "",
           "## Hành động đề xuất (tổng hợp)", "",
           "| Action | Số query | Ý nghĩa |", "|---|---|---|"]
    counts = collections.Counter(r.action for r in rows)
    meaning = {
        "NEW": "Tạo trang/bài mới — chưa có URL nào rank",
        "REFRESH": "Striking distance (top 11-20) — cập nhật để vào top 10",
        "PUSH": "Top 4-10 — thêm internal link/section để vào top 3",
        "DEFEND": "Top 3 — giữ, chỉ tối ưu CTR",
        "CONSOLIDATE": "Cannibalisation — gộp hoặc 301",
        "REWRITE": "Có demand nhưng content lệch intent",
        "PRUNE": "Không đáng đầu tư",
        "MONITOR": "Theo dõi, chưa làm gì",
    }
    for a, n in counts.most_common():
        out.append(f"| `{a}` | {n} | {meaning.get(a,'')} |")
    out += ["", "---", ""]

    # theo topic bucket
    for topic in sorted({r.topic for r in rows}):
        group = [r for r in rows if r.topic == topic]
        out += [f"## {topic}", "",
                f"{len(group)} query · {int(sum(r.impressions for r in group)):,} impression · "
                f"{int(sum(r.clicks for r in group)):,} click", "",
                "| Priority | Query | Intent | Funnel | Pos | Impr | Click | Action | Trang hiện tại |",
                "|---|---|---|---|---|---|---|---|---|"]
        for r in sorted(group, key=lambda x: -x.priority)[:40]:
            page = r.page.replace("https://ptemagic.com", "") or "—"
            out.append(f"| {r.priority:.0f} | `{r.query}` | {r.intent} | {r.funnel} | "
                       f"{r.position:.1f} | {int(r.impressions)} | {int(r.clicks)} | "
                       f"`{r.action}` | {page} |")
        # cluster chi tiết
        clusters = collections.defaultdict(list)
        for r in group:
            clusters[r.cluster].append(r)
        if len(clusters) > 1:
            out += ["", "**Cluster con:**", ""]
            for cname, items in sorted(clusters.items(), key=lambda kv: -sum(x.impressions for x in kv[1])):
                impr = int(sum(x.impressions for x in items))
                acts = collections.Counter(x.action for x in items)
                out.append(f"- `{cname}` — {len(items)} query, {impr:,} impression, "
                           f"actions: {dict(acts)}")
        out += ["", "---", ""]

    # Top việc phải làm
    out += ["## Việc nên làm trước (top 15 theo priority)", "",
            "| # | Query | Action | Vì sao | Trang |", "|---|---|---|---|---|"]
    top = sorted(rows, key=lambda r: -r.priority)
    top = [r for r in top if r.action not in ("MONITOR", "PRUNE")][:15]
    for i, r in enumerate(top, 1):
        out.append(f"| {i} | `{r.query}` | `{r.action}` | {r.reason[:150]} | "
                   f"{r.page.replace('https://ptemagic.com','') or '—'} |")
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gom query thành cluster + đề xuất hành động.")
    p.add_argument("--in", dest="inp", required=True, help="CSV từ GSC/Ahrefs/Semrush")
    p.add_argument("--out", default=None, help="File Markdown output")
    p.add_argument("--csv-out", default=None, help="Xuất CSV đã phân loại")
    p.add_argument("--json-out", default=None)
    p.add_argument("--config", default=None)
    p.add_argument("--min-jaccard", type=float, default=0.5,
                   help="Ngưỡng chồng lấn token để gom vào cùng cluster con (default 0.5)")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    brand = ((cfg.get("business") or {}).get("name") or "").lower()
    if brand and brand not in BRAND_TERMS:
        BRAND_TERMS.append(brand)

    rows = load_rows(args.inp)
    if not rows:
        eprint("[fatal] CSV rỗng hoặc không parse được")
        return 2
    cluster_within_topic(rows, args.min_jaccard)
    page_counter: collections.Counter = collections.Counter(r.cluster for r in rows if r.page)
    for r in rows:
        r.action, r.reason = decide_action(r, page_counter)
        r.priority = priority(r)

    md = build_markdown(rows, os.path.basename(args.inp))
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        open(args.out, "w", encoding="utf-8").write(md)
        eprint(f"[ok] {args.out}")
    else:
        print(md)

    if args.csv_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.csv_out)), exist_ok=True)
        with open(args.csv_out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["query", "page", "topic", "cluster", "intent", "funnel", "action",
                        "priority", "position", "impressions", "clicks", "ctr", "kd",
                        "country", "device", "reason"])
            for r in sorted(rows, key=lambda x: -x.priority):
                w.writerow([r.query, r.page, r.topic, r.cluster, r.intent, r.funnel, r.action,
                            r.priority, r.position, int(r.impressions), int(r.clicks), r.ctr,
                            r.kd if r.kd is not None else "", r.country, r.device, r.reason])
        eprint(f"[ok] {args.csv_out}")

    if args.json_out:
        json.dump([vars(r) for r in rows], open(args.json_out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        eprint(f"[ok] {args.json_out}")

    c = collections.Counter(r.action for r in rows)
    eprint(f"\n{len(rows)} query → " + " · ".join(f"{k}:{v}" for k, v in c.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
