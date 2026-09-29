---
name: seo-technical-audit
description: "Audit kỹ thuật cho ptemagic.com: crawlability, indexability, canonical, robots, sitemap, redirect, security header, JS rendering, Next.js specifics. Chạy scripts/seo_audit.py để lấy bằng chứng rồi luận. Trigger: 'audit kỹ thuật', 'technical audit', 'trang không index', 'lỗi index', 'sitemap', 'robots', 'crawl'."
user-invocable: true
argument-hint: "[url toàn site | 1 URL]"
license: MIT
metadata:
  version: "1.0.0"
  category: seo
  depends_on_scripts: ["seo_audit.py", "drift.py"]
---

# Technical SEO Audit

## Nguyên tắc

**Không có script, không có finding.** Bạn không được "xem xét" HTML bằng mắt và kết luận.
Mọi kết luận phải trỏ về một `code` trong JSON output.

```bash
python scripts/seo_audit.py --site <url> --max-urls 300 --config config/ptemagic.yaml \
    --out reports/ptemagic/
# chỉ 1 trang:
python scripts/seo_audit.py --site <url> --only-url <url>
# kiểm tra sau deploy (nhanh hơn 10 lần):
python scripts/drift.py compare --site <url>
```

Không có mạng / site chặn bot? Chạy offline:
```bash
python scripts/seo_audit.py --offline-dir <thu-muc-html-da-luu>
```

## Chín hạng mục, theo thứ tự ưu tiên sửa

### 1. Indexability (sửa trước tiên — mọi thứ khác vô nghĩa nếu cái này sai)

| Check | Code | Ngưỡng |
|---|---|---|
| meta robots | `NOINDEX_PRESENT` | noindex trên trang định rank = critical |
| canonical | `CANONICAL_MISSING`, `CANONICAL_NOT_SELF`, `CANONICAL_RELATIVE` | self-referencing, absolute |
| status | `HTTP_5XX`, `HTTP_404`, `HTTP_NON_200` | 200, không chain |
| x-robots-tag | (header — cần curl/`--site` live) | |

**Thứ tự điều tra khi "trang không index"** — làm đúng tuần tự, đừng nhảy:
1. URL có trong sitemap không?
2. robots.txt có chặn không? (chặn trong robots = Google **không thấy** noindex → tệ hơn noindex)
3. `meta robots` / `x-robots-tag`?
4. canonical có trỏ chỗ khác không? ← **phổ biến nhất**
5. `noindex` do staging leak? kiểm tra `X-Environment` header
6. Tất cả ổn → URL Inspection trong GSC, đọc "Crawled - currently not indexed"
   → thường là duplicate/soft-404/thin → về hạng mục 8

### 2. Crawl budget & sitemap

- `SITEMAP_LASTMOD_ALL_IDENTICAL` — lastmod giống hệt toàn bộ = thời điểm build, Google sẽ bỏ qua
  tín hiệu này. PTE Magic đang dính (xem `reports/ptemagic/2026-09-29-audit-khoi-dau.md` H1).
- `SITEMAP_MISSING_URLS` — trang indexable không có trong sitemap
- `ROBOTS_NO_SITEMAP`
- Sitemap nên tách theo section: `sitemap-static.xml`, `sitemap-blog-en.xml`,
  `sitemap-blog-vi.xml`, `sitemap-landing-<locale>.xml`. Với site 400+ URL, điều này cho phép
  bạn đo crawl theo section.

### 3. Crawlability

- `ROBOTS_APP_PATH_NOT_BLOCKED` — `/sso/*`, `/dashboard/*`, `/practice/*`, `/result/*`
- **Không** Disallow path đã noindex (see trên)
- `ROBOTS_DISALLOW_ALL` = critical, bỏ ngay

### 4. URL structure & redirect

- `URL_REDIRECTED` — internal link đang trỏ tới URL có redirect → sửa thành URL đích
- Chain 301 > 2 hop → flatten
- **Không trộn 301/302 trong cùng chain.** 302 không chuyển authority.
- `normalize_url` trong script bỏ trailing slash — nếu site phục vụ cả hai, cần 301 một chiều.
  Đây là lỗi kinh điển của Next.js (`trailingSlash` config).
- UTM params trên internal link → `FRAGMENT_STRIP` bỏ khi so sánh, nhưng vẫn phải sửa ở nguồn

### 5. Rendering (Next.js / App Router)

PTE Magic dùng Next.js + `/_next/image` + CMS headless. Check:

| Câu hỏi | Cách kiểm |
|---|---|
| Nội dung có trong HTML thô hay chỉ sau JS? | `curl -A Googlebot <url>` vs `curl <url>`; nếu khác → dynamic rendering cần thiết |
| Streaming/ Suspense có làm LCP element xuất hiện muộn? | PSI: `largest-contentful-paint-element` + `prioritize-lcp-image` |
| RSC payload phình HTML? | `HTML_TOO_LARGE` (ngưỡng 400KB); `__next_f` push chunks |
| hydration lớn? | Lighthouse `unused-javascript`, `dom-size` |
| `next/image` request `w` quá lớn? | `NEXT_IMAGE_OVERSIZED_W` ← **PTE Magic đang dính w=3840** |

### 6. Security & headers

`HSTS_MISSING`, `XCTO_MISSING`. Cần đo header thật — script chỉ thấy header ở chế độ `--site`.
Chuẩn tối thiểu: HSTS 1 năm + `includeSubDomains`, `X-Content-Type-Options: nosniff`,
`Referrer-Policy: strict-origin-when-cross-origin`. CSP lý tưởng nhưng thường vỡ Next.js —
nếu bật, test kỹ, đừng vì CSP mà làm site trắng.

### 7. HTTPS & mixed content

- `http://` trong src/href của HTML đã serve HTTPS → browser block, trang vỡ
- `www` vs apex, 80 vs 443: phải có đúng 1 hop 301

### 8. Content-level technical (nơi technical gặp policy)

- `THIN_CONTENT` / `VERY_THIN_PAGE` — hàng loạt = rủi ro **scaled content abuse**
- `NEAR_DUPLICATE_CONTENT` — Jaccard ≥ 0.70 giữa 2 URL = critical
- `DUPLICATE_TITLE` / `DUPLICATE_META_DESC` / `DUPLICATE_H1`
- `ORPHAN_PAGES` — không internal link nào trỏ tới → gần như không thể rank
- `BLOG_TITLE_NOT_LINKED` — tiêu đề card không phải anchor
- `ANCHOR_VAGUE` — "Read more" / "Xem thêm"

### 9. International SEO

Chạy `seo-i18n-hreflang` riêng — **đừng trộn vào đây**. Kết quả của nó ảnh hưởng thứ tự sửa:
PTE Magic đang có `issues.open_decisions[I18N-ARCH]` MỞ, và khi i18n architecture chưa chốt thì
mọi fix canonical/hreflang đều có thể phải làm lại.

## Cách trình bày output

```markdown
## Critical (chặn mọi thứ khác)
1. <code> — <số URL bị ảnh hưởng> — <fix cụ thể, ai làm, bao lâu>
   Bằng chứng: `<trích từ JSON evidence>`

## High
...

## Cần verify (tôi không đủ dữ liệu)
- <finding> — lệnh để kiểm: `<bash>`

## Đã kiểm tra, ổn
- <hạng mục> — vì sao ổn
```

Mục **"Đã kiểm tra, ổn"** là bắt buộc. Nó chứng minh bạn đã nhìn, và nó chặn bạn khỏi
đề xuất sửa thứ đang chạy tốt.

## Khi không đủ dữ liệu

Nói thẳng: "Chưa kiểm tra được X vì <lý do>. Lệnh để kiểm: <bash>."
**Không** suy đoán. Một báo cáo có 40 con số mà 10 con số do đoán sẽ phá huỷ uy tín của bạn
nhanh hơn nhiều so với một báo cáo 12 con số nhưng chắc chắn.
