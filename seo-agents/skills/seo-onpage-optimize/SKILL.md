---
name: seo-onpage-optimize
description: "Tối ưu on-page cho một trang cụ thể của ptemagic.com: title, meta, heading, ảnh, anchor, độ phủ thực thể, readability. Chạy seo_audit.py --only-url rồi sửa theo bằng chứng. Trigger: 'tối ưu trang này', 'on-page', 'check 1 URL', 'cải thiện thứ hạng trang X', 'bài này chưa lên top'."
user-invocable: true
argument-hint: "<URL hoặc file draft>"
license: MIT
metadata:
  version: "1.0.0"
  category: onpage
---

# On-page Optimization — một trang

## Trước khi sửa: phân loại 4 lý do một trang không rank

**Chẩn đoán trước, sửa sau.** Sửa bừa là nguồn lãng phí thời gian lớn nhất trong SEO.

| Triệu chứng | Nguyên nhân | Sửa gì |
|---|---|---|
| Không có impression | Query không khớp — Google không hiểu trang này nói về gì | Title/H1/heading + thực thể + internal link anchor |
| Có impression, **CTR rất thấp** | Hiện ra nhưng không ai bấm | Title + meta description + URL + rich result |
| Có impression tốt, position 11–20 | Nội dung chưa đủ tốt so với top 10 | Chiều sâu, bằng chứng, độ phủ subtopic, internal link |
| Position tốt nhưng không convert | **Không phải vấn đề SEO** | Intent mismatch giữa trang và CTA — báo product/UX |

```bash
python scripts/gsc_pull.py --days 90 --dimension query,page --out data/gsc-page.csv
grep "<slug>" data/gsc-page.csv
python scripts/seo_audit.py --site https://ptemagic.com --only-url <URL>
```

## 1. Title

- **≤ 60 ký tự** (tính cả khoảng trắng), primary keyword trong **35 ký tự đầu**
- Không lặp brand 2 lần
- Cấu trúc: `<Lợi ích hoặc con số> | <Brand>` hoặc `<Primary KW>: <chất lượng> — <Brand>`
- Với bài PTE: **số cụ thể tăng CTR rõ rệt** — "60 Questions", "7 Traits, 15 Points", "20 Minutes"
- Không clickbait (xem `references/google-spam-policies.md` mục 4.5)

## 2. Meta description (70–155 ký tự)

**Không phải** yếu tố xếp hạng. Là quảng cáo. Viết để tăng CTR:
- 1 câu nội dung có gì khác biệt · 1 con số cụ thể (400,000 học viên, 8,000 câu hỏi) ·
  1 CTA ("Start for FREE", "Luyện miễn phí")
- Chứa keyword tự nhiên, không lặp y nguyên title
- **Không** cam kết "đảm bảo 79+", "chắc chắn đậu"

## 3. Heading

- **Đúng 1 `<h1>`, chính xác 1 lần.** PTE Magic đang có 4 thẻ H1 trên trang chủ và 4 trên `/vi`
  (biến thể mobile/desktop cùng render) → giữ 1, bản kia `<span>` + `aria-hidden`.
- H1 chứa primary keyword dạng tự nhiên, không nhồi
- Không nhảy cấp (h2 → h4). `HEADING_LEVEL_SKIP`
- heading là **câu hỏi người dùng thật sự gõ** khi phù hợp — giúp cả featured snippet
  lẫn khả năng được trích trong AI Overview
- **Không** để >60% heading chứa exact-match keyword → `HEADING_KEYWORD_STUFFED` = BLOCK

## 4. Ảnh (vấn đề lớn nhất hiện tại của PTE Magic)

```bash
python scripts/seo_audit.py --site <url> --only-url <url> 2>&1 | grep NEXT_IMAGE_OVERSIZED_W
```

PTE Magic đang request `w=3840` cho **mọi** ảnh, kể cả thumbnail card và logo giải thưởng.
Yêu cầu với dev:

```tsx
<Image src={...} width={1200} height={630}
       sizes="(max-width:640px) 100vw,(max-width:1024px) 50vw,33vw"
       priority={isLCP} alt="..." />
```

Checklist ảnh:
- [ ] `alt` mô tả ảnh, không lặp keyword. Ảnh trang trí → `alt=""` (**không** bỏ hẳn thuộc tính)
- [ ] `width`/`height` tường minh → tránh CLS (`IMG_NO_DIMENSIONS`)
- [ ] Ảnh dưới màn hình đầu: `loading="lazy"`. **Ảnh LCP: `priority` + KHÔNG lazy**
- [ ] WebP/AVIF (`/ _next/image` tự làm nếu `images.formats` cấu hình đúng — verify)
- [ ] Alt phải **khớp** ảnh. Trên `/blogs` có dấu hiệu alt lệch với bài (cần verify bằng HTML thô)
- [ ] Không dùng ảnh làm anchor duy nhất — tiêu đề bài phải là link (xem `BLOG_TITLE_NOT_LINKED`)

## 5. Link

| Loại | Quy tắc |
|---|---|
| Internal ra | 3–8 link, anchor mô tả. Link tới trang chuyển đổi (features/register) khi có lý do |
| Internal vào | Trang này phải có ≥3 link **vào** từ trang liên quan (xem `internal-links-map.md`) |
| Liên kết | Dùng tuyệt đối path ổn định. Không link `/blogs?page=1&categoryIds=X` từ trong bài — tạo tham số không cần thiết |
| Ra ngoài | 2–5 tới nguồn thật sự hữu ích (Pearson, cơ quan di trú). `target="_blank"` + `rel="noopener"` |
| Trả tiền / affiliate / có `utm_` | **`rel="sponsored"` bắt buộc** → `PAID_LINK_MISSING_REL` |
| UGC (bình luận, review) | `rel="ugc"` |
| Không muốn truyền | `rel="nofollow"` — đừng dùng cho internal; dùng noindex |

## 6. Nội dung

- **Đủ độ phủ**: với informational, mọi H2 của top 5 kết quả phải được trả lời (không cần có
  heading cùng tên). Thiếu → thêm section hoặc thêm vào trang trụ cột
- **Bằng chứng thay cho tính từ**: "đề thi sát thực tế" → "8.000 câu theo format Pearson,
  cập nhật 2 tuần/lần, n=1.240 bài chấm tháng 8/2026"
- **Có ít nhất 1 thứ đối thủ không có** (xem `seo-content-brief` bước 4)
- **Ghi ngày cập nhật thật.** `Last updated: <ngày>`. Với nội dung điểm số/visa, thông tin
  cũ = mất niềm tin + rủi ro YMYL
- Readability: câu ngắn, đa số ≤ 25 từ. Bảng cho dữ liệu so sánh. Không tường thuật
  quá trình viết. **Không** cụm sáo rỗng: "In today's fast-paced world", "It's important to note",
  "Tóm lại", "Hãy cùng khám phá", "điều quan trọng cần lưu ý" → `AI_BOILERPLATE`
- Xuống dòng đoạn >180 từ. Không đoạn nào quá 6 dòng trên mobile

## 7. Schema

_delegate_ → `seo-schema-markup`. Tối thiểu cho bài blog: `Article` có `author` (Person với
`name` + `url`), `datePublished`, `dateModified`, `publisher`; `BreadcrumbList`;
`FAQPage` nếu có ≥3 Q&A; `Course`+`Offer` cho landing khoá học.

## 8. Kiểm tra sau khi sửa

```bash
python scripts/seo_audit.py --site <url> --only-url <URL>       # còn finding nào?
python scripts/policy_gate.py --file <draft.md> --corpus published/
python scripts/psi_cwv.py --url <URL> --strategy mobile          # nếu đụng đến ảnh
python scripts/drift.py baseline --site <url>                    # chốt baseline mới
```

Ghi vào action plan: ngày sửa · finding nào đã biến mất · **chưa đo được ranking
(khoảng 2–8 tuần)**, đặt lịch đo.

## Không bao giờ

| ❌ | Vì sao |
|---|---|
| Nhồi keyword cho đủ chỉ tiêu | `KEYWORD_STUFFING` = BLOCK, và 6/2026 update nhắm thẳng keyword stuffing |
| Giấu text để nhét keyword | `HIDDEN_TEXT` = BLOCK. Accordion/tab vì usability thì OK — khác nhau ở **ý định** |
| Bịa author ("SEO Team", "Admin") | Tín hiệu E-E-A-T giả, và là gian lận khi tư vấn |
| `noindex` rồi để link nội bộ trỏ vào | Lãng phí crawl + confuses relevance |
| Đổi URL hàng loạt cho "chuẩn SEO" | 301 làm mất tạm thời; chỉ làm khi có lỗi thật |
| Sửa title mỗi tuần để "test" | Không có test nào cả, bạn đang phá baseline. Đổi → chờ 4–6 tuần |
