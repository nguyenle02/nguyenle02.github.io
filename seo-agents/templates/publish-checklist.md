# Pre-publish checklist

> Chạy **từng mục một, trên trang thật** (staging hoặc bản preview build).
> Không có "chắc cũng được".
> Mục nào không kiểm tra được → **dừng**, đừng publish.

## 0. Gate (bắt buộc, trước tiên)
- [ ] `python scripts/policy_gate.py --file <draft> --corpus published/` → **PASS** hoặc **WARN có ghi chú**
- [ ] `BLOCK` → **không publish**, không thương lượng. Xem `skills/seo-google-policy-gate/`.
- [ ] `reports/policy-log.csv` đã có dòng log (`--log`)
- [ ] Có **người thật** đọc từ đầu đến cuối (không phải chỉ diff)
- [ ] Nếu YMYL (visa/định cư/học bổng/chi phí/yêu cầu điểm cho nghề): có **người thứ hai** duyệt

## 1. Frontmatter / metadata
- [ ] `title` ≤60 ký tự, keyword trong **35 ký tự đầu**, **không lặp brand 2 lần**
- [ ] `meta description` 70–155 ký tự, khác title, có CTA
- [ ] `slug`: lowercase, không dấu, không ngày, ≤60 ký tự, khớp primary keyword
- [ ] `canonical` self-referencing, absolute (`CANONICAL_NOT_SELF` = 0)
- [ ] `lang`/`inLanguage` **khớp nội dung thật** (`LANG_MISMATCH` = 0)
- [ ] `author` = người thật + `author_url` có trang tồn tại. Không "SEO Team".
- [ ] `date_published` + `date_modified` = ngày **thật** (không phải ngày build)
- [ ] YMYL: `date_modified` ≤90 ngày
- [ ] OG: `og:title`, `og:description`, `og:image` **1200×630**, `og:url`. Twitter card.

## 2. hreflang / i18n  ← PTE Magic: `issues.I18N-ARCH` đang MỞ
- [ ] Đã chốt URL cho bài này (`/vi/<slug>` vs root vs `.com.vn`)?
      **Nếu chưa** → không publish bản VI, chờ.
- [ ] Mọi bản dịch **đồng thời** được tạo (không publish EN hôm nay, VI "tuần sau")
- [ ] hreflang **reciprocal** + **self-reference** + `x-default`
- [ ] URL trong hreflang là **200 cuối cùng**, tuyệt đối, không noindex
- [ ] `lastmod` per locale = ngày sửa thật

## 3. Nội dung
- [ ] **Đúng 1 `<h1>`**, chứa primary keyword một cách tự nhiên
- [ ] Không nhảy cấp heading · không heading rỗng
- [ ] Primary keyword ở: 100 từ đầu · 1 H2 · URL · meta. **Không** ở >60% heading
- [ ] Density exact-match ≤3.5%
- [ ] Độ dài ≥ target trong brief
- [ ] ≥1 **giá trị độc quyền** (dữ liệu platform / 8.000 câu hỏi / template trainer / case có tên)
- [ ] Mọi số liệu: **có nguồn + ngày**
- [ ] Không "In today's fast-paced world" / "Tóm lại" / "điều quan trọng cần lưu ý" / "hãy cùng khám phá"
- [ ] Không cam kết: "đảm bảo", "chắc chắn đậu", "100%", "bao đậu"
- [ ] Không khẳng định "đề thi thật" / gợi ý có live item bank
- [ ] Mọi số liệu PTE/visa so với **trang chính thức của Pearson/ngoại giao**, không từ blog khác
- [ ] Đoạn ≤6 dòng trên mobile · không tường thuật quá trình viết

## 4. Ảnh
- [ ] Mọi ảnh có `alt` mô tả thật; ảnh trang trí → `alt=""` (không bỏ hẳn attribute)
- [ ] `sizes` prop được truyền → **không có `w=3840`** (`NEXT_IMAGE_OVERSIZED_W` = 0)
- [ ] `width` + `height` tường minh
- [ ] LCP image: `priority` + **không** lazy
- [ ] Ảnh dưới fold: `loading="lazy"`
- [ ] Không stock ảnh không có thông tin
- [ ] Đã kiểm: alt **khớp** ảnh (PTE Magic `/blogs` đang có dấu hiệu lệch — verify)

## 5. Link
- [ ] ≥4 internal link ra, **anchor mô tả** — không "Read more" / "Xem thêm"
- [ ] ≥3 internal link **vào** trang này từ trang liên quan (không orphan)
- [ ] External link tới **nguồn gốc** (Pearson, homeaffairs.gov.au, canada.ca…)
- [ ] Mọi link trả tiền/affiliate/utm → **`rel="sponsored"`**
- [ ] Không link tới đối thủ với anchor money-text
- [ ] Không link `/sso/*`, `/dashboard/*` từ trong bài (chỉ từ CTA)

## 6. Schema
- [ ] `Article` có `author` (Person + name + url)
- [ ] `datePublished` + `dateModified`
- [ ] `publisher` + logo
- [ ] `BreadcrumbList` khớp vị trí thật
- [ ] `FAQPage`: mỗi Question có `acceptedAnswer.text` **và** nội dung hiển thị trên trang
- [ ] Không khai rating/award mà trang không hiển thị
- [ ] **Validate**: Rich Results Test + validator.schema.org → screenshot vào PR

## 7. Performance
- [ ] Ảnh < 200KB
- [ ] Không render-blocking mới
- [ ] Không script 3-party mới mà không có lý do
- [ ] `python scripts/psi_cwv.py --url <URL> --strategy mobile` — **LCP không tệ hơn trước**
- [ ] Test tay: 3G/4G, Android, lần đầu vào URL
- [ ] `drift.py baseline --site …` nếu đây là trang chiến lược

## 8. Tech SEO
- [ ] `robots` meta: **không** có `noindex` (trừ khi cố ý)
- [ ] URL có trong sitemap, `lastmod` đúng
- [ ] Không `?utm_`/`?ref=` trong internal link
- [ ] 1 hop, không redirect chain
- [ ] HTTP status 200
- [ ] `seo_audit.py --only-url <URL>` → 0 critical, 0 high ngoài dự kiến

## 9. Khi publish
- [ ] Bấm publish **sáng thứ Hai–Thứ Tư** (tránh cuối tuần — không có ai xử lý khi vỡ)
- [ ] GSC → URL Inspection → **Request Indexing** (≤10 URL/ngày, đừng lạm dụng)
- [ ] Sau 15 phút: mở URL thật, **mobile**, xem bằng mắt
- [ ] `drift.py compare --only-url <URL>` → xác nhận render đúng
- [ ] Ghi ngày publish + URL vào `plans/publish-log.md`

## 10. Sau publish
- [ ] **Ngày 7**: GSC URL đã index?
- [ ] **Ngày 14**: position + impression
- [ ] **Ngày 30**: click? trang có convert (`sign_up_free`) không?
- [ ] **Ngày 30**: CrUX có data không
- [ ] Nếu chưa index sau 14 ngày → xem lại mục 1–2
- [ ] Nếu index, rank 11–20 → đưa vào queue `REFRESH` tháng sau

---
**Ký tên:** `{tên}` · `{ngày}` · Policy Gate: `{PASS|WARN}` · `{WARN code đã chấp nhận, nếu có}`

Dòng ký tên này là lý do bạn ngủ được khi site khách tụt.
