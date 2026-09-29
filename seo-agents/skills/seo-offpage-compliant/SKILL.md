---
name: seo-offpage-compliant
description: "Xây authority và backlink cho PTE Magic mà không vi phạm chính sách Google: digital PR dựa trên dữ liệu độc quyền, reclaim mention chưa được link, guest post có liên quan thật, citation chính thức. KÈM giải thích vì sao PBN/mua link/link exchange bị loại. Trigger: 'backlink', 'link building', 'off-page', 'PBN', 'mua link', 'guest post', 'anchor text', 'digital PR', 'xây authority'."
user-invocable: true
argument-hint: "[audit | pr | mentions | plan]"
license: MIT
metadata:
  version: "1.0.0"
  category: offpage
  ethical_constraints: true
---

# Off-page — cách xây authority mà không phải lo lắng

> ## ⚠️ Trước hết: về PBN
>
> Hồ sơ của bạn ghi "Xây dựng >250 website PBN" và "Dùng PBN & xây dựng hệ thống Backlink 1-2".
> Nói thẳng, với tư cách đồng nghiệp:
>
> **PBN là link spam theo chính sách Google hiện hành.** Trong nhóm *Link spam*, Google liệt kê
> đích danh "link farms and private blog networks (PBNs)", cùng với mua/bán link truyền
> PageRank, link exchange quá mức, guest post hàng loạt với anchor keyword-rich, và
> "automated link building programs".
>
> **Hai hiểu lầm cần tránh trong 2026:**
> 1. *"Spam update tháng 3 và 6/2026 loại trừ link spam → PBN an toàn trở lại."*
>    Không. Google loại trừ link spam khỏi **phạm vi của update đó**; link spam vẫn là spam
>    policy và vẫn bị hệ thống thường trực xử lý.
> 2. *"Vậy disavow để phòng ngừa."* Không. Disavow **không** giúp recovery cho những update
>    đó, và disavow sai có thể tự làm bạn mất link tốt.
>
> Rủi ro thật của PBN là rủi ro **mạng lưới**: SpamBrain phân tích network-level signals
> (neighborhood, fingerprint, pattern). Một site trong hệ bị phát hiện có thể kéo theo cả cụm
> — nghĩa là **nhiều khách hàng của bạn cùng lúc**.
>
> Skill này **không có** lệnh nào tự động hoá PBN, không sinh link scheme, không tối ưu anchor
> cho mạng lưới. Policy Gate sẽ `BLOCK` các mẫu đó.
>
> Đây không phải chuyện đạo đức trừu tượng. Đây là chuyện bạn có dám để khách đọc quy trình
> của mình không.

## Phần 1 — Audit link hiện có (không có API cũng làm được)

```bash
# nếu có Ahrefs token:
.venv/bin/python -c "
import os,requests,json
r=requests.get('https://api.ahrefs.com/v3/site-explorer/backlinks',
  params={'target':'ptemagic.com','output':'json','limit':1000,
          'select':'url_from,url_to,anchor_text,domain_rating,follow,first_seen'},
  headers={'Authorization':'Bearer '+os.environ['AHREFS_API_TOKEN']})
json.dump(r.json(),open('data/backlinks-ahrefs.json','w'))"

# không có token: export CSV từ Ahrefs UI vào data/backlinks.csv rồi dùng jq/awk
```

Phân tích anchor distribution — **thang đo dùng được**:

| Nhóm | Ví dụ | Tỷ lệ lành mạnh cho brand site |
|---|---|---|
| Brand | "PTE Magic", "ptemagic.com" | **50–70%** |
| URL/trần | "tại đây", "xem" → nên sửa; hoặc plain URL | 10–20% |
| Chung / chủ đề | "đề thi thử PTE", "kỳ thi PTE học thuật" | 15–25% |
| **Thương mại exact-match** | "khoá học PTE tốt nhất", "luyện PTE 79", "pte mock test online free" | **<5%** |

Nếu nhóm cuối >10–15% → hồ sơ anchor không tự nhiên.
`policy_gate.py → ANCHOR_OVER_OPTIMIZED` flag **≥40%** trên 1 trang; với **toàn bộ hồ sơ**,
>15% đã là cần xử lý.

Cách xử lý **không** phải là disavow hàng loạt. Theo thứ tự:
1. Liên hệ webmaster để đổi anchor sang brand — hiệu quả nhất, bị bỏ qua nhiều nhất
2. Xin gỡ link spam rõ ràng
3. Disavow **theo domain**, file nhỏ, ghi chú từng dòng tại sao. Disavow hàng nghìn dòng
   = bạn không còn kiểm soát được thứ mình đang loại

## Phần 2 — Tài sản link-earning PTE Magic đã có sẵn

Đây là phần đáng tiền nhất. PTE Magic có dữ liệu **thật** mà gần như không đối thủ PTE nào có:

| Tài sản | Biến thành | Ai sẽ link |
|---|---|---|
| 400.000+ học viên, 60+ quốc gia | **"PTE Score Reality: dữ liệu ẩn danh từ 400.000 lượt luyện thi"** — báo cáo quý | Blog du học, báo giáo dục, diễn đàn di trú |
| Dữ liệu chấm AI speaking/writing | "Tỷ lệ lỗi phát âm theo tiếng mẹ đẻ: Việt vs Ấn vs Hồi vs Philippines" — **có ý nghĩa học thuật** | Kênh ESL, nghiên cứu, podcast |
| 8.000+ câu hỏi đã phân loại | "Độ khó thực đo của từng task type, theo tỷ lệ học viên đạt" | Cộng đồng PTE, Reddit, Quora |
| Pearson Elite Partner 2025 | Trang "Pearson's Elite Partner" có verify + logo | Trang partner của Pearson, PR |
| Bett Asia / Edu 4.0 award | Trang giải thưởng + press kit | Báo trong ngành EdTech VN |
| Case study có tên + điểm | "Từ 58 lên 83 trong 6 tuần: log luyện tập thật" | Blog du học, cộng đồng điều dưỡng |

**Vì sao nó hoạt động mà mua link không hoạt động:** người ta link vì nội dung *giúp bài viết
của họ đáng tin hơn*, không vì bạn trả tiền. Đó là định nghĩa của liên kết tự nhiên.

### Kịch bản outreach (ngắn, không spam)

```
Subject: Dữ liệu PTE theo tiếng mẹ đẻ — có thể dùng cho bài của anh/chị

Chào anh/chị [Tên],

Thấy bài "[tiêu đề]" của anh/chị về [chủ đề]. Chúng tôi là PTE Magic, có dữ liệu ẩn danh
từ ~400.000 lượt luyện thi, trong đó có phần phân tích lỗi phát âm chia theo tiếng mẹ đẻ
(Việt / Ấn / Philippines / Ả Rập).

Nếu hữu ích, gửi anh/chị bảng + biểu đồ để dùng tự do (ghi nguồn). Không cần link,
chỉ cần nó giúp bài chính xác hơn.

[Tên] · PTE Magic · [kết nối hồ sơ LinkedIn]
```

**"Không cần link"** là câu làm tăng tỉ lệ phản hồi. Khi họ thấy dữ liệu tốt, link tự đến
— và đó là loại link bền.

Kỳ vọng thật: 30–50 email → 3–6 đặt link. Không phải 100.

## Phần 3 — Reclaim mention chưa được link

Tài sản dễ nhất, gần như luôn bỏ sót:

```bash
# Google (thủ công — tìm brand không kèm link)
"pte magic" -site:ptemagic.com -inurl:(login|dashboard)
intitle:"pte magic" review
"pte magic" (reddit OR quora OR medium)
```
+ Ahrefs → **Link intersect**: Competitors → "Link intersect" (đã link đối thủ, chưa link mình)
+ Similarweb / BuzzSumo: social mentions
+ Nhắc đến "đề thi thử PTE có AI chấm" mà không gọi tên → trả lời, giúp, rồi mới nhắc brand

Thứ tự giá trị (cao → thấp):

| Ưu tiên | Loại |
|---|---|
| 1 | Bài báo/organisations **đã nhắc PTE Magic** nhưng không link |
| 2 | Trang đối tác / hiệp hội EdTech / danh sách giải thưởng (có quyền edit) |
| 3 | Danh bạ đại học/du học có trang "English test requirements" |
| 4 | Reddit / Quora — **trả lời thật, hữu ích**, brand chỉ khi được hỏi. Không farming |
| 5 | Directory chất lượng cao về giáo dục. **Không** package 500 directory |

## Phần 4 — Guest post hợp lệ vs không hợp lệ

| | Được | Không được |
|---|---|---|
| Tồn tại vì | Người đọc trang đó được lợi | PageRank chảy về |
| Nội dung | Có chuyên môn, đứng tên người thật | Spin, generic, "top 10 tips for…" |
| Link | 1–2 link, có ngữ cảnh, brand hoặc URL | 5 link exact-match money anchor |
| Có trả tiền? | Có → **`rel="sponsored"` disclosure rõ** | Mua link không disclose |
| Tần suất | Vài cái mỗi quý | 20+/tháng = pattern |
| Đa dạng | Nhiều domain, nhiều loại | 10 link từ cùng 1 network |

**Test duy nhất:** *bài này có được đăng nếu nó không kèm link không?* Nếu không → đó là
mua link, không phải PR.

## Phần 5 — Internal linking = off-page không tốn tiền

Trước khi đi xin link, sửa link trong nhà. Audit đã chỉ ra:

- **`ORPHAN_PAGES`** — blog không có cấu trúc hub/spoke. Có category page
  (`/blogs?page=1&categoryIds=10|14|18|22`) nhưng **không có trang trụ cột**
- **`BLOG_TITLE_NOT_LINKED`** — ở `/blogs`, tiêu đề bài **không phải** anchor; chỉ ảnh là link
  → bỏ mất internal anchor text mạnh nhất site, vì nó nằm trên trang có PageRank cao nhất
- **`ANCHOR_VAGUE`** — hàng loạt "Read more"
- **`SITEMAP_MISSING_URLS`** — bài tiếng Việt ở root domain EN (xem `seo-i18n-hreflang`)
- **Footer** là nơi phân phối authority tốt nhất hiện có: đang link `/exam-structure-*`,
  `/features`, `/blogs`, category pages. Đang link **`/privacy-policy` hai lần** cho
  "Privacy Policy" và "Payment & Refund Policy" → trang refund thật thiếu.

Sửa 5 cái này rẻ hơn mua 20 backlink và không có rủi ro chính sách.

## Phần 6 — Đo lường

| Chỉ tiêu | Nguồn | Cadence |
|---|---|---|
| Referring domains mới | Ahrefs / Common Crawl | tháng |
| Anchor distribution % theo nhóm | Ahrefs CSV | quý |
| Linked page count / orphan count | `seo_audit.py` | quý |
| Link từ trang **có traffic thật** | Ahrefs `Traffic value` | quý |
| Mentions chưa link còn lại | tìm kiếm thủ công | quý |
| Liên kết gãy 404 nội bộ | `seo_audit.py` | tháng |

**Không dùng** làm KPI: DR/DA trung bình, tổng số backlink, "số link đã mua". Đó là vanity metrics
và là thứ khiến bạn giải trình với khách khi traffic không tăng.

## Phần 7 — Khi khách đòi mua link / PBN

Kịch bản thực tế, trả lời được ngay:

> **"Anh muốn em làm 20 backlink DR 60 cho site này."**

Ba câu:
1. **"Kết quả anh mong là gì?"** — thường là top 5 cho 1 từ khoá cụ thể. Nếu đúng,
   có thể có con đường ngắn hơn qua content + internal link (xem mục 5).
2. **"Nếu traffic tụt 50% trong 6 tháng thì sao?"** — nói rõ cơ chế (SpamBrain,
   network-level signals, recovery không đảm bảo, disavow không giúp).
3. **Đề xuất thay thế cùng ngân sách**: 1 digital PR asset từ chính dữ liệu của khách
   + sửa internal linking + refresh 5 bài đang ở vị trí 11–20.
   Thường đạt kết quả tốt hơn và **không để lại nợ**.

Nếu khách vẫn muốn → **từ chối**. Nói rõ: *"Tôi không làm việc đó vì tôi không bảo vệ được
kết quả khi nó hỏng, và tôi không nhận tiền cho việc tôi biết là sẽ gây hại."*
Mất một hợp đồng, giữ được danh sách khách hàng dài hơn. Đó là tính toán kinh doanh,
không phải lý tưởng.
