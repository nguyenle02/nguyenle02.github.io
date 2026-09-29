---
name: seo-reporting-drift
description: "Báo cáo SEO cho PTE Magic: tuần (GSC delta, striking distance, content decay, CWV), tháng (prune/refresh backlog, GEO citation), quý (full audit + drift + action plan). Tự động phát hiện thay đổi sau deploy bằng drift.py. Trigger: 'báo cáo', 'weekly report', 'traffic tụt', 'so tháng trước', 'drift', 'baseline', 'số liệu SEO'."
user-invocable: true
argument-hint: "[weekly | monthly | quarterly | drift]"
license: MIT
metadata:
  version: "1.0.0"
  category: reporting
  depends_on_scripts: ["gsc_pull.py", "drift.py", "psi_cwv.py", "cluster_keywords.py"]
---

# Reporting & Drift

## Cadence

| Loại | Khi | Mất | Output |
|---|---|---|---|
| **Drift check** | sau MỖI lần deploy | 5–15 phút | cảnh báo regression trong ngày |
| **Weekly** | thứ Hai | 15 phút | `reports/ptemagic/<date>-weekly.md` |
| **Monthly** | ngày làm việc đầu tháng | 2 giờ | `reviews/<YYYY-MM>.md` |
| **Quarterly** | đầu quý | 1.5 giờ | full audit + action plan |

## Drift — phần tiết kiệm tiền nhất, hay bị bỏ nhất

```bash
python scripts/drift.py baseline --site https://ptemagic.com --max-urls 300   # sau audit
python scripts/drift.py compare  --site https://ptemagic.com --out reports/ptemagic/
python scripts/drift.py history  --site https://ptemagic.com
```

`compare` chỉ báo **thay đổi**, không báo lại mọi lỗi. Nó bắt đúng loại tai nạn:

| Loại thay đổi | Mức | Thường là |
|---|---|---|
| `canonical_changed`, `canonical_missing` | critical | build config đổi, hoặc thêm `?utm` vào canonical |
| `jsonld_type_removed`, `jsonld_missing` | critical | upgrade theme/CMS plugin, hoặc `generateMetadata` bị sửa |
| `hreflang_removed` | critical | i18n map mất |
| `noindex_added` | critical | staging leak, hoặc plugin SEO bật nhầm |
| `title_changed`, `title_missing` | high | người viết sửa title tay / template đổi |
| `h1_count_changed` | high | component hero đổi (PTE Magic đã có 4 H1 — nếu dev "sửa" rồi lại đổi) |
| `oversized_images_added` | high | ai đó thêm ảnh không truyền `sizes` ← **đúng lỗi w=3840 hiện tại** |
| `html_size_surge` | medium | DOM phình vì render trùng nội dung (carousel) |
| `internal_links_drop` | medium | xoá bài mà không redirect |
| `status_changed` | critical | 200 → 404/410, hoặc đổi host |
| `page_disappeared` | critical | URL mất khỏi sitemap |
| `word_count_drop` | high | bài bị cắt khi migrate |

**Nếu dev deploy mà `compare` sạch** → hoặc deploy tốt, hoặc baseline cũ. Ghi rõ cái nào.

## Weekly — 15 phút, thứ Hai

```bash
python scripts/gsc_pull.py --days 28 --compare-previous --out data/gsc-28d.csv
python scripts/cluster_keywords.py --in data/gsc-28d.csv --out data/weekly-clusters.md
python scripts/drift.py compare --site https://ptemagic.com
python scripts/psi_cwv.py --url https://ptemagic.com/ --strategy mobile 2>/dev/null || true
```

Báo cáo theo `templates/weekly-report.md`, **tối đa 1 trang**, 6 khối:

1. **KPI thật**: click non-brand + `sign_up_free` (không phải tổng click — brand click
   chỉ dao động theo chiến dịch PR)
2. Delta so với tuần trước, **tách EN và VI** (GSC: filter `page:(.../vi/*)` vs `-page:(.../vi/*)`)
3. Top 5 query tăng / top 5 giảm
4. **Striking distance** — query vị trí 5–15, impression cao → với mỗi cái: URL nào, cần gì
5. **Content decay** — bài giảm ≥30% click so với 28 ngày trước → vì sao
   (bị tụt vị trí / nội dung cũ / đối thủ mới / update)
6. **3 việc cho tuần này**, có owner

Không có mục 6 thì báo cáo chỉ là đồ trang trí.

## Monthly — 2 giờ

1. **Decay queue** — click giảm ≥30% trong 90 ngày
2. **Cannibalisation** — ≥2 URL cùng cluster cùng rank cho 1 query → gộp hoặc tách intent
3. **Prune** — <30 impression/90 ngày + vị trí >60 + **không** internal link vào →
   cân nhắc 301 về bài liên quan gần nhất.
   **Không** xoá hàng loạt rồi 404 — pattern đó Google xử lý như xóa sổ để lại thin
4. **GEO/AEO** — chạy 25 prompt trong `context/ai-citation-targets.md` qua Perplexity (có API)
   → ghi `reports/ptemagic/geo-baseline.csv`. KPI: **AI citation rate**
5. **Link** — referring domains mới, **anchor distribution** (xem `seo-offpage-compliant`),
   link gãy; **không** mua link, **không** PBN
6. **Policy log** — đếm số lần `BLOCK` trong `reports/policy-log.csv`.
   Xu hướng giảm = quy trình đang chín. Xu hướng tăng = ai đó đang production nội dung
   chưa kịp nghĩ

## Quarterly — audit đầy đủ

```bash
python scripts/seo_audit.py --site https://ptemagic.com --max-urls 800 \
    --config config/ptemagic.yaml --out reports/ptemagic/
python scripts/psi_cwv.py --config config/ptemagic.yaml --strategy both \
    --out reports/ptemagic/<date>-cwv.md
python scripts/gsc_pull.py --days 365 --out data/gsc-365d.csv
python scripts/drift.py baseline --site https://ptemagic.com
```
→ `templates/audit-report.md` → `templates/action-plan.md`

## Cách trình bày cho khách (kỹ năng bán hàng, không phải kỹ năng SEO)

| Đừng viết | Viết thay thế |
|---|---|
| "Traffic tăng 12%" | "Click không thương hiệu tăng 12% (3.400 → 3.810/28 ngày) — 41 đăng ký miễn phí mới" |
| "Đã tối ưu Core Web Vitals" | "LCP mobile của trang chủ: 4.2s → 2.6s, do ảnh hero giảm từ 3840px xuống 1200px. 6 tháng CrUX sẽ xác nhận" |
| "Xây 15 backlink" | "65 bài đề cập PTE Magic không kèm link; đã reclaim 7, 34 còn lại đang outreach" |
| "Điểm audit 91/100" | "3 lỗi critical: hreflang không reciprocal, schema Article thiếu author, lastmod là ngày build" |
| "Content đang chuẩn SEO" | "8 bài ở vị trí 11–20, tổng 24.000 impression/90 ngày. 3 bài trong số đó đã có toàn bộ ý nội dung top 5 có → chỉ thiếu độ sâu + internal link" |

Mọi con số phải có **nguồn** (GSC / Ahrefs export / Lighthouse / `drift.py`) + **ngày**.
Không có nguồn → đừng ghi. Khách có thể không đọc báo cáo, nhưng họ sẽ đọc khi traffic tụt.

## Kết nối SEO với doanh thu

```bash
# GA4 — cần GA4_PROPERTY_ID trong .env
# query: organic search → sign_up → course_purchase
```
Report nào cũng phải trả lời được 1 câu: **"organic tuần này tạo ra bao nhiêu đăng ký?"**

Với PTE Magic: KPI là `sign_up_free` (xem `config/ptemagic.yaml → business.primary_kpi`),
không phải traffic. Nếu SEO làm traffic tăng mà đăng ký không tăng → đang bắt đúng
search intent nhưng sai trang đích, và cần nói ra ngay, đừng để quý sau.
