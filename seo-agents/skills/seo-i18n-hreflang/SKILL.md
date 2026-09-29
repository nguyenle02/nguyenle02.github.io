---
name: seo-i18n-hreflang
description: "Xử lý đa ngôn ngữ / đa domain cho PTE Magic: ptemagic.com (EN), /vi, ptemagic.com.vn, ptemagic.com.au. Chốt mô hình URL, sinh + kiểm hreflang, phát hiện cannibalisation EN↔VI, xử lý duplicate cross-domain. Trigger: 'hreflang', 'đa ngôn ngữ', 'i18n', 'bản tiếng Việt', 'com.vn', 'duplicate cross-domain', 'localization'."
user-invocable: true
argument-hint: "[audit | generate | decide]"
license: MIT
metadata:
  version: "1.0.0"
  category: i18n
---

# International SEO — PTE Magic

> **Đây là vấn đề số 1 của site này.** Không làm xong skill này thì hreflang, internal link
> planning và đo KPI theo locale đều đang đặt trên cát.
> Xem `config/ptemagic.yaml → issues.open_decisions[I18N-ARCH]`.

## 1. Hiện trạng (đo được, không suy đoán)

Ba mô hình **đồng thời** đang chạy:

| Mô hình | Bằng chứng | Vấn đề |
|---|---|---|
| A. Subfolder `/vi/` | `/vi`, `/vi/features`, `/vi/blogs`, `/vi/contact-us`, `/vi/exam-structure-pte-academic`, `/vi/exam-structure-pte-core` | Chỉ 6 URL. Too nhỏ để là chiến lược |
| B. Bài VI ở **root** của .com | `/nhung-thay-doi-ve-diem-thi-pte-quan-trong-nam-2024`, `/quy-che-thi-lai-pte-moi-2024-thong-tin-ban-can-biet`, `/cau-truc-va-meo-dat-diem-cao-pte-core-reorder-paragraph`, `/meo-pte-core-reading-multiple-choice-multiple-answers`, `/cau-truc-mau-dap-an-va-meo-thi-pte-core-writing-email`… | **Không có namespace** → Google không suy ra được locale từ URL; không filter/measure được |
| C. ccTLD riêng | `ptemagic.com.vn` ("Vietnamese PTE Coaching"), `ptemagic.com.au` ("International PTE Coaching") — link từ footer .com | Trùng content với A/B? Chưa verify. ccTLD = tín hiệu quốc gia mạnh → xung đột với subfolder |

Đồng thời: **không thấy hreflang nào** trong nội dung render của các trang đã xem
(`HREFLANG_ABSENT_SITEWIDE`).

Và một lỗi nội dung cụ thể: trên `/vi` có khối testimonial **lặp 2 lần nguyên văn**
(Thảo Nguyên / Tấn Thịnh / Phương Quỳnh) — không phải vấn đề i18n nhưng nó nằm trong cùng
carousel và sẽ bị đọc là duplicated content nếu bạn render cả 2 bản cho 2 breakpoint.

## 2. Lệnh

```bash
python scripts/seo_audit.py --site https://ptemagic.com --max-urls 300 --out reports/ptemagic/
# codes: HREFLANG_NOT_RECIPROCAL, HREFLANG_NO_SELF_REFERENCE, HREFLANG_INVALID_CODE,
#        HREFLANG_NO_XDEFAULT, LOCALE_CONTENT_MISMATCH, LOCALE_MISMATCH_SITEWIDE,
#        HREFLANG_ABSENT_SITEWIDE, LANG_ATTR_MISSING, LANG_MISMATCH
```

## 3. Chọn mô hình — khung quyết định

Không có mô hình "đúng"; có mô hình phù hợp với nguồn lực. Bảng này để đưa vào
cuộc họp với founder + dev:

| | **A. Subfolder** `/vi/` | **B. ccTLD** `.com.vn` | **C. Subdomain** `vi.` |
|---|---|---|---|
| Sức mạnh ban đầu | Kế thừa từ .com | **Không kế thừa** — xây từ đầu | Kế thừa một phần |
| Rào cản quốc gia | Yếu (cần hreflang để phân biệt) | **Mạnh** — .vn = "cho Việt Nam" | Trung tính |
| Chi phí kỹ thuật | Thấp nhất (1 codebase) | Cao (2 deploy, 2 CMS view) | Trung bình |
| Rủi ro migration | Thấp | **Cao** — phải 301 hàng trăm URL | Trung bình |
| Đo lường | 1 property GSC, lọc theo `page:(https://ptemagic.com/vi/*)` | 2 property, so sánh thủ công | 2 property |
| Hợp khi | Một đội nội dung, nhiều ngôn ngữ | Thị trường có **sản phẩm/đội sales/pháp nhân riêng** | Tạm thời |

### Khuyến nghị cho PTE Magic: **A mở rộng, và coi `.com.vn` như redirect**

Lý do: `/vi` đã tồn tại nhưng chỉ có **6** URL, trong khi **toàn bộ blog tiếng Việt** nằm ở
mô hình B và ở `.com.vn` — cấu hình hiện tại chỉ là *sự tồn dư* của một cuộc di cư chưa làm xong.

Kế hoạch 3 mốc:

**Mốc 1 — Dừng đổ thêm (0 chi phí, làm ngay)**
- Mọi **bài VI mới** phải có URL `https://ptemagic.com/vi/<slug>`
- Đóng băng: không tạo thêm bài VI ở root nữa
- Ghi vào `context/seo-guidelines.md` để người viết/khách không làm lệch thêm

**Mốc 2 — Gộp trong 1 quý**
- Sinh **redirect map** từ sitemap: mọi root-slug tiếng Việt → `/vi/<slug>`
  (phát hiện bằng `looks_vietnamese()` — đã có trong `lib/common.py`)
- 301 từng cái một, theo lô 20–30 URL/lần, theo dõi 2 tuần giữa các lô
- Gộp phần nội dung trùng giữa `.com.vn` và `/vi/` **trước khi** redirect, đừng redirect
  2 bản về cùng 1 URL khi cả 2 đều có giá trị riêng
- Cập nhật sitemap: thêm `<xhtml:link rel="alternate" hreflang="…">`
- Kiểm tra canonical sau mỗi lô: `drift.py compare`

**Mốc 3 — Sau 6 tháng**
- Nếu `.com.vn` mang về lead + doanh thu thật → **đảo quyết định**, tách VI ra ccTLD,
  và xoá `/vi`. Dữ liệu phải dẫn đường, không phải reverse-engineering sau khi đã migrate.

## 4. Đặc sản rủi ro: cannibalisation EN ↔ VI trên cùng root

Cặp thật, rút từ sitemap:

```
/pte-core-reorder-paragraph-format-tips-to-score-high          (EN)
/cau-truc-va-meo-dat-diem-cao-pte-core-reorder-paragraph       (VI)
/pte-core-reading-multiple-choice-single-answer-tips           (EN)
/meo-pte-core-reading-multiple-choice-multiple-answers         (VI)
/pte-core-reading-and-writing-fill-in-the-blanks-tips          (EN)
/meo-chinh-phuc-pte-core-reading-writing-fill-in-the-blanks    (VI)
```

Nếu **cùng một bài, hai bản dịch** → đó là tập hreflang, phải khai báo.
Nếu **hai bài khác nhau, cùng chủ đề, cùng domain, cùng ngôn ngữ** → Cannibalisation, phải gộp.
Nếu **bản EN và bản VI cùng nhắm một query tiếng Việt** → Google sẽ tự chọn, thường chọn sai.

```bash
python scripts/cluster_keywords.py --in data/gsc-90d.csv --out data/clusters.md
# tìm action CONSOLIDATE; sau đó:
grep -oE '"/(cau-truc|meo)-[^"]*"' <<< "$(cat sitemap.xml)" | head
```

**Quy tắc:** 1 query → 1 URL per locale. Một bài dịch sang VI thì **phải** có
`hreflang: en ↔ vi`, không thể để cả hai cùng index độc lập.

## 5. Đặc sản: "study in Australia / Canada / NZ / UK"

Cùng chủ đề × 4 quốc gia × ~8 dạng bài = **32 bài có hình dạng giống hệt nhau**.
Đây là **vấn đề trang cổng thông tin**, không phải vấn đề hreflang, và nó nằm trong
`policy_gate.py → TEMPLATE_SHELL`:

> ≥8 URL cùng khung heading + phần thân khác nhau <30% ⇒ **BLOCK**

Cách thoát (không phải "thêm 1 đoạn cho qua"): mỗi bài quốc gia phải có
học phí **thật** của nước đó, tên trường **thật**, yêu cầu visa **thật** của cơ quan di trú nước đó,
và ngày kiểm chứng. Nếu làm được → không còn là trang cổng thông tin. Nếu không → **gộp**
thành 1 bài "Study abroad: Australia vs Canada vs NZ vs UK" có bảng so sánh.

## 6. Spec hreflang

**Cú pháp** (đặt trong `<head>`, hoặc trong sitemap, hoặc HTTP header — nhất quán 1 chỗ):
```html
<link rel="alternate" hreflang="en"    href="https://ptemagic.com/features" />
<link rel="alternate" hreflang="vi"    href="https://ptemagic.com/vi/features" />
<link rel="alternate" hreflang="x-default" href="https://ptemagic.com/features" />
```

Quy tắc:
- **Reciprocal 2 chiều** — mỗi URL trong nhóm khai báo **đủ và giống hệt** các URL còn lại
- **Tự tham chiếu** (self-reference) — trang luôn liệt kê chính nó
- `hreflang` dùng ISO 639-1 (+ ISO 3166-1 nếu cần region): `vi`, `en`, `en-au`, `en-in`, `en-gb`
  → **không** dùng `vi-VN` cho toàn bộ người Việt (người Úc gốc Việt cũng đọc `vi`)
- URL tuyệt đối, **đã index được** (không noindex, không bị chặn trong robots.txt)
- Trỏ tới **URL 200 cuối cùng** sau redirect — không trỏ vào URL redirect
- `x-default` = bản dành cho người chưa rõ ngôn ngữ → ở đây là `ptemagic.com/` (EN)
- Không có `en-vn` nếu không có nội dung **thật sự** khác cho người Anh ở Việt Nam.
  Nếu không có → đừng thêm để "cho đủ"

**Chọn mã vùng cho các domain:**
| URL | hreflang | Vì sao |
|---|---|---|
| `ptemagic.com/` | `en` | EN toàn cầu, không gắn quốc gia |
| `ptemagic.com/vi` | `vi` | VI toàn cầu |
| `ptemagic.com.vn/` | `vi` | ccTLD `.vn` = khu vực VN; `vi` (không phải `vi-VN`) vì ngôn ngữ là biến phân biệt |
| `ptemagic.com.au/` | `en-au` | ccTLD `.au` → region signal có chủ đích |

Nếu `.com.vn` và `/vi` trùng nội dung, hreflang **không thể cứu** được đó — hai URL cùng
`vi` trỏ lẫn nhau tạo ra ambiguity. Giải pháp là 301 (Mốc 2) hoặc làm cho nội dung khác
nhau thật sự (khác CTA/khác chứng minh thị trường/khác sản phẩm), và lúc đó vẫn phải có canonical
riêng.

## 7. Sinh hreflang từ một nguồn duy nhất

**Đừng viết hreflang bằng tay.** Lỗi chắc chắn xảy ra khi thêm blog.
Tạo `data/i18n-map.csv` (khởi đầu từ `data/i18n-map.example.csv`) với mỗi hàng = 1 đơn vị nội dung:

```csv
id,slug_en,url_en,slug_vi,url_vi,lang_primary,lastmod
pte-essay-topics,pte-essay-topics,https://ptemagic.com/pte-essay-topics,,,\
```

Rồi render `hreflang` cho mọi trang từ file đó (Next.js `generateMetadata`).
100 URL reciprocal 2 chiều không maintain được bằng tay.

## 8. Bản dịch thật sự khác nhau

Trên `/vi` và `ptemagic.com` nội dung không chỉ dịch mà **định vị khác nhau**:

```
EN:  "Better Practice. Better Results."                       (lợi ích)
VI:  "Nền tảng luyện thi PTE hàng đầu chuẩn Pearson dành cho người Việt"  (vị thế + Pearson)
```

Kèm proof points khác nhau: EN nêu "Promising Education Technology Award 2023 by Edu 4.0" (bản
gốc), VI thêm huy hiệu **Top 20** khác (`golden-brand.png`) mà EN không có.

Điều này tốt, và không phá vỡ hreflang — **định vị khác nhau là bình thường**.
**hreflang chỉ yêu cầu cùng _ý định tìm kiếm_, không phải cùng câu chữ.**
Không dịch máy 1-1 chỉ để cho khớp hreflang.

## 9. Verification loop

```bash
# 1. dump hreflang của 5 trang mẫu
python scripts/seo_audit.py --site https://ptemagic.com --only-url https://ptemagic.com/ \
    --only-url https://ptemagic.com/vi --json-only | jq '.findings[]|select(.code|startswith("HREFLANG"))'

# 2. đếm số cặp không reciprocal
python scripts/seo_audit.py --site https://ptemagic.com --max-urls 300 2>/dev/null \
  | grep -c HREFLANG_NOT_RECIPROCAL

# 3. mọi hreflang target phải HTTP 200
jq -r '.page_records[].hreflang[]?|.href' <audit.json> | sort -u \
  | xargs -I{} curl -sI -o /dev/null -w "%{http_code} {}\n" {} | grep -v ^200

# 4. baseline lại
python scripts/drift.py baseline --site https://ptemagic.com
```

**Định nghĩa xong (G4-i18n):** 0 `HREFLANG_NOT_RECIPROCAL` · 0 `HREFLANG_INVALID_CODE` ·
0 `HREFLANG_NO_SELF_REFERENCE` · mỗi nhóm ngôn ngữ có `x-default` ·
0 `LOCALE_CONTENT_MISMATCH` · `drift.py compare` sạch.
