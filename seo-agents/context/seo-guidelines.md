# SEO Guidelines — PTE Magic

> **File này là "hiến pháp".** Content brief, editor và agent phải tuân theo.
> Thay đổi phải **commit + ghi ngày + giải thích vì sao**. Không sửa im lặng.
> Chi tiết policy: `references/google-spam-policies.md`.

---

## A. Cứng — vi phạm là **dừng bài**

| # | Quy tắc | Kiểm bằng |
|---|---|---|
| A1 | **1 primary keyword = 1 URL.** Hai URL cùng 1 primary → gộp hoặc tách intent. | `cluster_keywords.py` → `CONSOLIDATE` |
| A2 | **Không trang nào là bản biến thể** (đổi nước / đổi năm / đổi format) của trang khác mà không có dữ liệu thật khác. | `policy_gate.py` → `NEAR_DUPLICATE`, `TEMPLATE_SHELL` |
| A3 | **Mọi bài có số liệu phải có nguồn + ngày.** Không có → xoá số liệu. | editor |
| A4 | **Không cam kết kết quả**: "đảm bảo", "chắc chắn đậu", "100%", "bao đậu". | `GUARANTEE_CLAIM` |
| A5 | **Không "đề thi thật"/"live questions"/"exam leak".** | `pte-domain-glossary.md` mục 6 |
| A6 | **Paid/sponsored/affiliate/utm → `rel="sponsored"`.** | `PAID_LINK_MISSING_REL` |
| A7 | **Không text ẩn.** Accordion/tab vì UX thì OK. | `HIDDEN_TEXT` |
| A8 | **Không mua link, không PBN, không link exchange, không farming directory.** | `seo-offpage-compliant` |
| A9 | **YMYL** (visa/định cư/học bổng/chi phí/vay/điểm cho đăng ký hành nghề): author có tên + chức danh, ngày ≤90 ngày, link nguồn chính phủ, **người thứ hai duyệt**. | `YMYL_MISSING_EVIDENCE` |
| A10 | **Đúng 1 H1 / trang.** | `MULTIPLE_H1`, `H1_MISSING` |
| A11 | **Không publish khi Policy Gate = BLOCK.** Không có ngoại lệ "gấp". | `policy_gate.py` |
| A12 | **Không đổi URL hàng loạt cho "chuẩn SEO".** 301 chỉ khi có lỗi thật. | editor |
| A13 | **Không bịa:** author, số liệu, rating, testimonial, đối tác, giải thưởng. | người + schema |
| A14 | Bài **VI không phải bản dịch** bài EN. Intent/ví dụ/CTA riêng, không đối xứng. | `brand-voice.md` |

## B. Kỹ thuật — mặc định

| Hạng mục | Chuẩn |
|---|---|
| Title | ≤60 ký tự, KW trong 35 ký tự đầu, brand ≤1 lần |
| Meta description | 70–155 ký tự, khác title, có CTA |
| Heading | 1 H1 → H2 → H3, không nhảy cấp, không rỗng |
| URL | lowercase, không dấu, ≤60 ký tự, không ngày |
| Canonical | self-referencing, tuyệt đối |
| hreflang | reciprocal + self-ref + `x-default`, URL 200 |
| Ảnh | `alt` có nghĩa · `width`/`height` · `sizes` prop · không `w` >1920 · LCP có `priority` + không lazy · WebP/AVIF |
| JSON-LD | `Article` có `author`+`datePublished`+`dateModified` · `BreadcrumbList` · `FAQPage` (mỗi Question có `acceptedAnswer.text` **và** hiển thị trên trang) |
| Internal link | ≥3 vào / ≥4 ra / anchor mô tả |
| lastmod | ngày sửa **nội dung** — **không** phải ngày build |
| `robots` | không noindex cho trang muốn index; **không** Disallow trang đã noindex |

## C. Nội dung

**Trước khi viết, đủ 2/3:**
1. Người dùng làm được điều gì sau khi đọc mà trước đó không làm được?
2. Có ≥1 dữ kiện top 5 không có?
3. Nếu xoá bài, site có tệ đi?

**Cấu trúc:**
- Mở bài = **ràng buộc**, không dẫn nhập. *"20 minutes, 200–300 words, seven traits, 15 points."*
- Bảng khi có so sánh. Mỗi H2 = một câu hỏi người dùng thật gõ.
- Có "common mistakes" với **số**, không có tính từ.
- Kết = hành động + **link money page**.

**Không:** tường thuật quá trình viết · filler ở câu mở · "In today's fast-paced world" ·
"delve" · "game-changer" · "Tóm lại" · "điều quan trọng cần lưu ý" · "hãy cùng khám phá" ·
đoạn >6 dòng trên mobile.

**Số:** luôn có `n` và ngày ("trên 1.240 bài, tháng 8/2026").
**Người:** tác giả có thật + profile.
**Hình:** screenshot platform/score report, không stock.

## D. Language

| | EN | VI |
|---|---|---|
| Giọng | trực tiếp, nặng số, chủ động, không idiom | "mình/bạn", ấm hơn, cụ thể theo bối cảnh VN |
| Độ dài câu | ≤20 từ | ≤25 từ |
| Thuật ngữ | tên task tiếng Anh | **giữ nguyên task tiếng Anh + giải thích** |
| CTA | "Start for FREE" | "Luyện thử miễn phí" |
| Proof mạnh nhất | Pearson **Elite Partner** | "chuẩn Pearson dành cho người Việt" + tên + điểm |

## E. Đo lường — quy tắc chống tự lừa

- KPI chính = **`sign_up_free` từ organic**, không phải traffic.
- Non-brand click là KPI SEO; tổng click chỉ tham khảo.
- Không báo cáo mà không có delta + nguồn + ngày.
- Không đổi title/meta hàng loạt khi chưa có baseline → `drift.py baseline` **trước**.
- Không "tối ưu" vì một đối thủ làm → đi qua bộ lọc value-add.
- Traffic tụt >15%: **dừng mọi thay đổi**, chẩn đoán 24h trước.
- Không gọi là thành công nếu chưa có `drift.py compare` + GSC diff.

## F. Quy trình (tóm tắt SOP)

```
G0 setup → G1 audit → G2 keyword → G3 brief → G4a produce
                                              → G4b POLICY GATE ⛔
                                              → G5 publish → G6 measure ─┐
       ↑──────────────────────── quay lại────────────────────────────────┘
```

**Không bỏ:** G4b (luôn), G1 trước G2/G3, `drift.py baseline` sau mỗi G1.

## G. Bảo trì file này

| Khi | Việc |
|---|---|
| Phát hiện pattern lặp lại | thêm 1 dòng A/B — **không** viết lại section |
| `policy_gate.py` báo lỗi | thêm case test, **không** nới ngưỡng |
| Chính sách Google đổi | cập nhật `references/` **đầu tiên**, rồi mới file này |
| Mỗi quý | rà lại, xoá quy tắc không còn dùng |

## Nhật ký

| Ngày | Mục | Thay đổi | Vì sao |
|---|---|---|---|
| 2026-09-29 | tất cả | v1.0 | Phát hành cùng audit khởi đầu |
