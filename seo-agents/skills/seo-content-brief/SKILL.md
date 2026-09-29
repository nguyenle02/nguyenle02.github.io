---
name: seo-content-brief
description: "Sinh content brief 1 trang cho PTE Magic (EN hoặc VI), SERP-driven, có yêu cầu E-E-A-T và policy pre-check. Đầu vào: chủ đề hoặc URL. Đầu ra: brief theo templates/content-brief.md, sẵn sàng cho người viết hoặc cho agent draft. Trigger: 'viết brief', 'dàn ý bài viết', 'content brief', 'outline cho chủ đề X', 'lên kế hoạch bài'."
user-invocable: true
argument-hint: "<chủ đề | URL cần làm lại>"
license: MIT
metadata:
  version: "1.0.0"
  category: content
---

# Content Brief — PTE Magic

Brief này là **hợp đồng giữa SEO và người viết**, không phải gợi ý. Nếu người viết phải đoán,
brief thất bại. Mục tiêu: người viết mở file lên và biết chính xác mình viết gì, cho ai,
và thứ gì làm bài bị Policy Gate chặn.

## Input
- Primary keyword (1, duy nhất)
- Locale: `en` | `vi`
- Loại trang: `informational` | `landing` | `tool` | `comparison` | `update`

## Bước 1 — Nạp (bắt buộc)
`config/ptemagic.yaml`, `context/target-keywords.md`, `context/brand-voice.md`,
`context/internal-links-map.md`, `context/seo-guidelines.md`, `references/eeat-checklist.md`

## Bước 2 — Demand: có số thì nói số, không có thì nói không có

```
GSC 90 ngày:  <impression> · <click> · <vị trí TB>
Ahrefs/Semrush: <volume ± biên độ> · <KD>          ← hoặc "CHƯA IMPORT"
```
**Không bịa.** Không có dữ liệu → `không đo được — đang đề xuất dựa trên SERP + lợi thế dữ liệu
nội bộ`. Nói dối volume là cách nhanh nhất để mất khách.

## Bước 3 — SERP landscape (60 phút, không delegate được)

Đọc **5 kết quả đầu thật**, ghi cho từng cái:

| # | URL | Loại | Độ dài | Có gì | **Thiếu gì** |
|---|---|---|---|---|---|

Cột "Thiếu gì" là toàn bộ lý do bài này tồn tại. Phổ biến ở đối thủ PTE:
- nói format nhưng không có số điểm cụ thể theo từng task
- template chung chung, không có ví dụ bài đã chấm
- không nói lỗi thường gặp theo tiếng mẹ đẻ (Việt/Ấn/Hồi/Philippines khác nhau rõ)
- số liệu cũ (pre-2024 format)
- không có ảnh score report thật
- nhầm PTE Core với PTE Academic

Nếu bạn **không tìm thấy** khoảng trống thật → dừng. Nói "không có gap, cân nhắc refresh bài
cũ thay vì viết mới". Đây là câu trả lời tốt nhất và hiếm ai đưa ra.

## Bước 4 — Value-add: chọn ≥1 (bắt buộc, không được để trống)

| Quyền | Cụ thể hoá thành |
|---|---|
| **Dữ liệu chấm AI** | "trên 1.240 bài Write Email đã chấm tháng 8/2026, 34% vượt 120 từ" |
| **Ngân hàng 8.000+ câu** | Bộ đề mẫu theo đúng dạng + phân bố chủ đề |
| **Trainer đã kiểm chứng** | Template + lý do từng câu, kèm điểm học viên đạt |
| **Trường hợp học viên có tên** |_before/after_ với sự đồng ý, không bịa, không sửa số |

Không có ít nhất một cái → **brief bị từ chối**. Đây chính xác là ranh giới giữa
"AI-assisted content có biên tập" và "scaled content abuse" — và nó là ranh giới Google
đánh giá *bằng tỷ lệ giá trị trên số lượng*, không bằng số trang.

## Bước 5 — 11 mục của brief

Theo `templates/content-brief.md`. Không được bỏ:

1. Primary keyword + intent + funnel
2. Demand evidence (có nguồn hoặc ghi rõ "không có")
3. SERP landscape + gap
4. **Value-add đã chọn (mục 4)**
5. Outline H2/H3 — **theo SERP, không theo sở thích**; mỗi H2 ghi rõ nó trả lời câu hỏi nào
6. Entity & semantic terms phải xuất hiện: `Pearson`, `PTE Academic`, `PTE Core`,
   `Write Essay`, `Repeat Sentence`, `Write From Dictation`, `communicative skills`,
   `enabling skills`, `10-90`, `Enabling Skills Profile`, `Score Report`, `Skill Enabling`
   → với bài VI: giữ nguyên thuật ngữ tiếng Anh, giải thích bằng tiếng Việt
7. Internal links: **3 link vào** (từ URL nào, anchor gì) + **4 link ra** (tới URL nào)
   — lấy từ `context/internal-links-map.md`, không bịa URL
8. Schema đề xuất: `Article` (+ `author`, `datePublished`, `dateModified`), `BreadcrumbList`,
   `FAQPage` nếu có ≥3 Q&A, `Course`/`Offer` nếu là landing khoá học, `HowTo` chỉ nếu đúng 5.3
9. Title ≤60 ký tự (3 phương án) + meta ≤155 ký tự (3 phương án) —
   **không lặp brand 2 lần** (bài học từ title `/blogs` = "PTE Magic - PTE Magic Blog")
10. Ngưỡng chất lượng: informational ≥1.200 từ, ≥1 FAQ có câu trả lời đầy đủ,
    author + profile, ngày publish + ngày updated
11. **Policy pre-check** — xem dưới

## Bước 6 — Policy pre-check (người viết tự khai)

| Câu | Nếu "có" |
|---|---|
| Bài này có phải bản sao/ẩn-sao của bài đã publish, chỉ đổi quốc gia/năm/format? | **Dừng.** Chuyển thành `REFRESH` bài cũ |
| Có khẳng định gì về kết quả thi/visa mà bạn không chắc? | Bỏ hoặc thêm điều kiện + ngày + nguồn |
| Có dùng số liệu không có nguồn? | Bỏ |
| Có nhắc "đề thi thật"/"exam leak"/bản quyền Pearson? | Bỏ, đổi thành "practice prompts in PTE style" |
| Có nội dung do bên thứ ba cung cấp nhằm hưởng traffic trên domain mình? | Dừng, xem site reputation abuse |
| Chủ đề visa/học bổng/chi phí? | YMYL → bắt buộc author có chức danh, ngày cập nhật <90 ngày, link nguồn chính phủ, không hứa hẹn |

Ghi 6 dòng này vào cuối brief, yêu cầu người viết tick.

## Bước 7 — Brief cho bản dịch tiếng Việt

**Không phải dịch.** Brief riêng, khác 3 điểm:
- **Khác query**: "cách viết email pte core" ≠ "pte core writing email"
- **Khác ví dụ**: lỗi của học viên Việt (phát âm /θ/, /ð/, s+z, dấu câu tiếng Việt trong ô
  nhập tiếng Anh, thói quen viết dài)
- **Khác CTA/proof**: với thị trường VI, "Pearson Elite Partner" và testimonial tên Việt
  thuyết phục hơn so sánh quốc tế. (Bản `/vi` hiện làm tốt hơn bản EN ở điểm này.)
- Nếu `.com/vi/` vs `.com.vn` chưa chốt → brief phải ghi rõ giả định URL.

## Output
File `plans/<locale>-<slug>-brief.md`, **tối đa 1 trang**. Dài hơn = người viết không đọc =
brief vô dụng. Kết thúc bằng:

```
Cần người quyết: <1 câu hỏi duy nhất, có phương án A/B>
Ước lượng: <X phút> cho người viết quen · <Y phút> cho người mới
Rủi ro chính sách nếu làm ẩu: <1 dòng, chỉ ra check cụ thể trong policy_gate.py>
```
