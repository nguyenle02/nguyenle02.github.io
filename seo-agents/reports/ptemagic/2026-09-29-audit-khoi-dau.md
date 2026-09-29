# PTE Magic — Báo cáo audit khởi đầu

**Ngày:** 2026-09-29 · **Người thực hiện:** agent (Arena), cho Lê Duy Nguyên
**Phạm vi:** `ptemagic.com` (EN) + `/vi` + toàn bộ sitemap
**Chế độ:** thủ công qua render proxy — **xem mục "Giới hạn phương pháp" bên dưới trước khi dùng số liệu này cho khách**

---

## TL;DR

| | |
|---|---|
| Điểm sơ bộ | **không chấm** — chưa crawl được HTML thô, chấm điểm sẽ là bịa |
| Critical | 4 |
| High | 7 |
| Medium | 6 |
| Không kiểm tra được | 9 hạng mục (cần chạy `scripts/seo_audit.py` trên máy có mạng) |
| Việc nên làm đầu tiên | **Chốt kiến trúc i18n** — nó chặn 3 việc khác |

Ba phát hiện đáng tiền nhất:

1. **Toàn bộ ảnh đang request `w=3840`** kể cả thumbnail card. Đây là lỗi một-dòng-code
   sửa được cho cả site, và là thứ ảnh hưởng Core Web Vitals nặng nhất trong danh sách này.
2. **Blog đang viết cho PTE Core trong khi demand nằm ở PTE Academic.** Nhiều task
   (Repeat Sentence, Write From Dictation) có học viên nhắc đến nhưng **không có bài nào**.
3. **Kiến trúc tiếng Việt đang rối 3 tầng** (`/vi/` + bài VI ở root + `.com.vn`). Cái này
   chặn hreflang, chặn internal link planning, và chặn luôn việc đo KPI theo locale.

---

## Giới hạn phương pháp (đọc phần này trước)

Sandbox nơi agent chạy **không có quyền truy cập internet chung** — chỉ GitHub được allowlist.
Cụ thể những gì đã và chưa làm được:

| Đã làm được | Chưa làm được |
|---|---|
| Đọc `robots.txt` (raw text) | Đọc **HTML thô** → không kiểm tra được `<head>` |
| Đọc `sitemap.xml` (raw, 4 chunk) | Không verify canonical / hreflang / JSON-LD / meta robots |
| Đọc nội dung render của `/`, `/vi`, `/blogs`, `/pte-essay-topics` | Không đọc được HTTP response headers (HSTS, CSP, cache) |
| Phân tích cấu trúc heading/anchor/URL từ bản render | Không đo được Lighthouse/CrUX (PageSpeed API cần key) |
| | Không kiểm tra được HTTP status, redirect chain, page speed thật |

**Hệ quả:** các finding bên dưới được suy ra từ *kết cấu nội dung render* và *pattern URL trong
sitemap* — đáng tin về mặt **phát hiện vấn đề**, nhưng **chưa đủ để quy kết nguyên nhân kỹ thuật**.
Agent đã từ chối chấm điểm tổng (xem nguyên tắc 1 của SOP: *script đo, agent luận*).

**Chạy lệnh này trên máy bạn để có báo cáo đầy đủ, có điểm số:**
```bash
cd seo-agents && python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/seo_audit.py --site https://ptemagic.com --max-urls 300 \
    --config config/ptemagic.yaml --out reports/ptemagic/
.venv/bin/python scripts/psi_cwv.py --config config/ptemagic.yaml --strategy both \
    --out reports/ptemagic/cwv.md
```
Rồi so output với danh sách dưới đây: finding nào xác nhận → giữ; finding nào sai → sửa script,
commit. Đó là cách bộ này trở nên chính xác.

---

## CRITICAL

### C1. Ảnh phục vụ ở `w=3840` cho mọi kích thước, gồm cả thumbnail

**Bằng chứng** (từ bản render, thấy rõ trên cả EN và VI):
```
https://ptemagic.com/_next/image?url=%2Fmagic-landing-page-assets%2Fresult-screen.png&w=3840&q=75
https://ptemagic.com/_next/image?url=%2Fmagic-landing-page-assets%FWorking-girl.png&w=3840&q=75
https://ptemagic.com/_next/image?url=...&w=3840&q=75      ← cả 4 logo giải thưởng
https://ptemagic.com/_next/image?url=https%3A%2F%2Fcms.ptemagic.com%2Fwp-content%2Fuploads%2F2025%2F12%2Fadvantages-nurse-PTE.webp&w=3840&q=75
                                                            ← thumbnail card trong danh sách blog
```
Ngoại lệ duy nhất quan sát được: avatar testimonial dùng `w=96` → chứng tỏ component
biết truyền `w` nhỏ, chỉ là trang blog/home không truyền.

**Vì sao nghiêm trọng:** `w=3840` trên mobile ~400px là request ảnh to gấp ~90 lần diện tích
cần thiết. `q=75` không cứu được. Đây là ứng viên số 1 cho LCP > 4s trên mobile, và
LCP là yếu tố xếp hạng.

**Fix (dev, ước lượng 0.5 ngày):**
```tsx
<Image
  src={...}
  width={1200} height={630}
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
/>
```
`next/image` sẽ tự chọn `w` phù hợp viewport. Kiểm tra thêm `deviceSizes`/`imageSizes`
trong `next.config.js` — mặc định tối đa 3840, nên hạ `imageSizes` nếu không ai cần to hơn 1920.

**Đo lường:** chạy `psi_cwv.py --url https://ptemagic.com/ --strategy mobile` TRƯỚC và SAU.
Ghi lại số. Nếu LCP không cải thiện → nguyên nhân nằm chỗ khác (TTFB/server, font, hydration).

---

### C2. Bài tiếng Việt nằm ở root domain EN → không thể khai hreflang đúng

`sitemap.xml` (chunk 0) liệt kê các URL sau **không có prefix `/vi/`**:
```
/nhung-thay-doi-ve-diem-thi-pte-quan-trong-nam-2024
/pte-magic-tai-thai-lan-truyen-cam-hung-dao-tao-tai-ngay-hoi-dek-d-2024
/quy-che-thi-lai-pte-moi-2024-thong-tin-ban-can-biet
/cau-truc-va-meo-dat-diem-cao-pte-core-reorder-paragraph
/meo-pte-core-reading-multiple-choice-multiple-answers
/meo-chinh-phuc-pte-core-reading-writing-fill-in-the-blanks
/pte-core-reading-cau-truc-de-bang-diem-va-meo-ghi-diem
/cau-truc-va-meo-on-tap-pte-core-summarize-written-text
/cau-truc-mau-dap-an-va-meo-thi-pte-core-writing-email
/pte-core-re…  (còn tiếp, bị cắt ở chunk 0)
```
Trong khi đó các trang tĩnh lại **có** prefix: `/vi/features`, `/vi/blogs`, `/vi/contact-us`,
`/vi/exam-structure-pte-academic`, `/vi/exam-structure-pte-core`.

**Hai mô hình song song trên cùng một domain.** Đây là lỗi hệ thống, không phải lỗi từng trang.

**Vì sao nghiêm trọng:**
- Google không biết bản nào là canonical cho một query tiếng Việt
- Không thể sinh hreflang tự động từ một nguồn (vì quy tắc slug không nhất quán)
- `ptemagic.com.vn` đang ở giữa → khả năng cao có duplicate cross-domain
- Bạn **không thể** lọc KPI theo locale trong GSC một cách tin cậy

**Fix:** đây là quyết định kiến trúc, không phải việc SEO tự sửa. Ba lựa chọn đã ghi trong
`config/ptemagic.yaml → issues.open_decisions[I18N-ARCH]`. Khuyến nghị: **gộp hết VI về
`/vi/` trên .com, 301 toàn bộ từ `.com.vn`**. Chi phí: 1 sprint dev + redirect map ~300 dòng.
Lợi ích: mở khoá toàn bộ phần i18n còn lại của quy trình.

**Không làm gì cho tới khi chốt cái này.** Viết hreflang, làm internal link map, hay đo KPI
locale đều chờ nó.

---

### C3. Nhiều hơn một `<h1>` trên trang chủ và `/vi`

Bản render cho ra, trên `ptemagic.com/`:
```
# Better Practice. Better Results.     ← heading cấp 1
# Better Practice.                       ← heading cấp 1
# Better Results.                        ← heading cấp 1
# With PTE Magic Platform.               ← heading cấp 1
```
và trên `/vi`:
```
# Nền tảng luyện thi PTE
# hàng đầu chuẩn Pearson
# dành cho người Việt
# Nền tảng luyện thi PTE hàng đầu chuẩn Pearson dành cho người Việt
```
Bản đầu tiên là biến thể một-dòng cho desktop, 3 dòng sau là biến thể nhiều-dòng cho mobile —
**cả hai cùng tồn tại trong DOM**.

**Vì sao nghiêm trọng (vừa phải):** không bị phạt, nhưng Google phải tự chọn H1 → thường chọn
cái đầu tiên ("Better Practice. Better Results." — không có keyword nào). Đồng thời nó tăng
DOM size và số node phải hydrate.

**Fix:** component hero nên render **một** `<h1>` duy nhất, phần tử phụ dùng `<span class="...">`
bên trong cùng H1 (vẫn style được khác nhau theo breakpoint), hoặc `aria-hidden` cho bản thừa.

---

### C4. Nội dung lặp nguyên khối trong DOM (`/vi`)

Ba testimonial trên `/vi` xuất hiện **hai lần, nguyên văn, cạnh nhau**:
> Thảo Nguyên (Target PTE 65) · Tấn Thịnh (Target PTE 30) · Phương Quỳnh (Target PTE 80)

Lần 1: 3 khối. Ngay sau đó lần 2: đúng 3 khối đó, cùng chữ.
Lần 3 xuất hiện thêm 2 testimonial mới (Ngọc Huyền, Hoàng Hải) → carousel render
`[mask, ...all]` để làm hiệu ứng lặp vô hạn.

**Không phải** cloaking/hidden text — nội dung này visible với người dùng. Nhưng nó:
- bơm ~600 từ trùng vào DOM
- làm loãng tỷ lệ nội dung độc đáo của trang chủ (trang quan trọng nhất site)
- là pattern **dễ bị hiểu nhầm** là scaled content khi spam update quét toàn site

**Fix:** carousel nên render 1 lần + nhân bản node bằng CSS/JS ở phía client, hoặc
đánh `aria-hidden="true"` + `inert` cho bản sao.

---

## HIGH

### H1. `lastmod` trong sitemap = thời điểm build, không phải ngày sửa nội dung

```
https://ptemagic.com/                                    2026-09-29T03:35:53.482Z
https://ptemagic.com/exam-structure-pte-academic         2026-09-29T03:35:53.482Z
https://ptemagic.com/vi/blogs                            2026-09-29T03:35:53.482Z
... (toàn bộ 7 trang tĩnh + /vi/* đều GIỐNG HỆT nhau tới từng mili-giây)
```
Trong khi đó các URL blog có lastmod **đúng thật** (`2026-09-02T18:00:50.000Z` v.v.) —
tức nguồn dữ liệu blog từ CMS đã truyền ngày chuẩn, còn trang tĩnh thì không.

**Hậu quả:** Google nói rõ sẽ bỏ qua lastmod không đáng tin. Mất tín hiệu hữu ích nhất để
crawl lại trang vừa sửa. Với site 400+ URL, crawl budget là thứ thật.

**Fix:** cấp lastmod cho trang tĩnh từ cùng nguồn với blog (field `updated_at` trong CMS),
hoặc hard-code ngày cập nhật thật gần nhất cho từng trang tĩnh. `seo_audit.py` có check
`SITEMAP_LASTMOD_ALL_IDENTICAL` để bắt cái này tự động.

### H2. `robots.txt` quá sơ và không chặn path app

```
User-Agent: *
Allow: /

Sitemap: https://ptemagic.com/sitemap.xml
```
`/sso/auth/login`, `/sso/auth/register` được link từ header/footer của mọi trang
(nhìn thấy rõ trong bản render). Không thấy khai báo noindex hay Disallow.

**Rủi ro:** trang app sau login có nội dung gần rỗng cho crawler → crawl waste + index
những trang không nên index. Nếu có trang render khác nhau giữa logged-out/logged-in mà
không noindex → dễ bị nhìn nhận là doorway.

**Fix:** đảm bảo `/sso/*`, `/dashboard/*`, `/practice/*`, `/result/*` có
`<meta name="robots" content="noindex">`. **Không** Disallow trong robots.txt cho trang
đã noindex — Disallow chặn crawl khiến Google *không thấy* thẻ noindex, tệ hơn.

Đồng thời: khai báo có chủ đích với AI crawler (GPTBot, OAI-SearchBot, PerplexityBot,
Google-Extended) — quyết định, không để mặc định. Xem skill `seo-geo-visibility`.

### H3. Trên `/blogs`, tiêu đề bài viết không phải link

```
![PTE Accepted Countries for Nurses 2026](...advantages-nurse-PTE.webp...)   ← có link
##### PTE Accepted Countries for Nurses 2026                                   ← KHÔNG có link
```
Chỉ ảnh là anchor. Tiêu đề là text thường.

**Vì sao quan trọng:** đây là **internal anchor text** giá trị nhất site — nó nằm ở trang
danh sách có PageRank cao nhất và tự nhiên khớp exact-match với query. Để nó thành text
trần là bỏ không dùng.

**Fix:** bọc `<h4><a href="/slug">Tiêu đề</a></h4>`. 10 phút dev.

Liên quan: một số `alt` ảnh thumbnail có vẻ **lệch** với bài bên cạnh
(alt "PTE Accepted Countries for Nurses 2026" xuất hiện ngay dưới heading
"PTE Exam Pattern 2026"). Có thể là lỗi off-by-one trong markup render, cũng có thể là
artifact của bộ convert HTML→markdown. **Cần verify bằng HTML thô** — đừng sửa khi chưa chắc.

### H4. Title của `/blogs` = "PTE Magic - PTE Magic Blog"

Brand lặp 2 lần, **zero keyword**. Đây là trang hub của ~120 bài — page authority cao nhất
khối blog. `seo_audit.py` có check `TITLE_BRAND_DUPLICATED` bắt đúng pattern này.

**Fix:** `PTE Exam Tips, Templates & Guides | PTE Magic` (46 ký tự).
Đồng thời check các trang tĩnh khác có lặp template title tương tự không.

### H5. "Payment & Refund Policy" trỏ về `/privacy-policy`

```
[Privacy Policy](https://ptemagic.com/privacy-policy)
[Payment & Refund Policy](https://ptemagic.com/privacy-policy)   ← cùng một URL
```
Hai menu item, một đích. Với một sản phẩm có thanh toán (khoá học trả phí), đây là:
- thiếu trang chính sách hoàn tiền thật → **rủi ro cho Google Ads** (chính sách thanh toán
  là yêu cầu với tài khoản chạy quảng cáo) và rủi rotrust cho người mua
- liên kết điều hướng gây nhiễu cho crawler

**Fix:** tạo `/refund-policy` thật, cập nhật footer, và khai
`hasOfferCatalog`/`offers` trong schema nếu có bán khoá học.

### H6. Part-time job / accommodation / cost-of-living content là chủ đề ngoài năng lực lõi

Cluster "study abroad" hiện có ~27/120 URL (ước lượng từ sitemap chunk 0). Nhiều bài lệch
khỏi chuyên môn PTE: *cách tìm việc làm thêm*, *tìm nhà ở*, *vay du học*, *thành phố đa văn
hoá nhất Canada*.

Hai rủi ro cộng dồn:
1. **Scaled content / thin affiliation** — trang không có chuyên môn thật, viết để bắt traffic.
   Google đánh giá theo *tỷ lệ giá trị trên số lượng*, không theo số trang.
2. **YMYL không đủ E-E-A-T** — học phí, vay vốn, visa là money/immigration topics.

**Không có nghĩa là phải xoá.** Có nghĩa là: hoặc đầu tư thật (số liệu riêng cho từng nước,
phỏng vấn học viên thật, cập nhật theo quý), hoặc gộp vào bài trụ cột rồi 301.
`policy_gate.py --corpus` sẽ đo độ khác biệt giữa 4 nước × 8 chủ đề.

> ⚠️ Chưa đọc được toàn văn các bài này (chỉ đọc được metadata + URL) nên nhận định ở đây
> là **cảnh báo rủi ro**, không phải kết luận vi phạm.

### H7. Cluster nội dung lệch với demand: PTE Core dày, PTE Academic mỏng

Từ sitemap, phần lớn bài task-level gắn nhãn `pte-core-*`:
`pte-core-listening-format-modules-success-tips`, `pte-core-reading-multiple-choice-single-answer-tips`,
`pte-core-reading-fill-in-the-blanks-format-tips`, `pte-core-reorder-paragraph-format-tips-to-score-high`,
`pte-core-reading-and-writing-fill-in-the-blanks-tips`, `pte-core-answer-short-question-30-cau-hoi-de-gap-nhat`,
`pte-core-respond-to-a-situation-cau-truc-va-meo-on-tap`, `pte-core-re…`

Trong khi PTE Academic là bài mà đa số học viên Việt Nam thi. Testimonial trên `/vi` nói thẳng:
> "2 dạng bài mình thấy lo nhất là **RS và WFD**"

Vậy mà **không có URL nào** cho `pte repeat sentence practice` hay `pte write from dictation`
(trong những gì sitemap chunk 0 lộ ra).

**Hành động:** đây là mỏ content có cấu trúc rõ. Nhưng — xem cảnh báo ở `context/target-keywords.md`:
12 bài "template cho task X" cùng một cái vỏ **chính xác là hình dạng của doorway pages**.
Mỗi bài phải có: đề mẫu khác thật, lỗi học viên khác thật, số liệu điểm khác thật.

---

## MEDIUM

| # | Finding | Bằng chứng | Fix |
|---|---|---|---|
| M1 | Category link dùng query param, tất cả đều `?page=1` | `/blogs?page=1&categoryIds=18` (Speaking), `14` (Reading), `10` (Listening), `22` (Writing) | Trang lọc/pagination cần canonical về `/blogs`; hoặc tạo URL tĩnh `/blogs/category/pte-speaking` để index được và có anchor text |
| M2 | Ảnh blog serve từ `cms.ptemagic.com` qua `/_next/image` | `url=https%3A%2F%2Fcms.ptemagic.com%2Fwp-content%2Fuploads%2F…` | Thêm 1 origin + 1 hop. Kiểm tra CDN cache-hit; cân nhắc copy asset sang cùng origin |
| M3 | Footer EN ↔ VI có nội dung **không tương đương** | VI có "Top 20 thương hiệu giáo dục 2023" + `golden-brand.png`; EN **không có** | EN bỏ sót 1 trust asset. Đồng bộ proof points giữa các locale |
| M4 | Copy hero EN/VI định vị khác nhau, không bản nào mạnh hơn | EN: "Better Practice. Better Results." (tính năng) · VI: "Nền tảng luyện thi PTE hàng đầu chuẩn Pearson dành cho người Việt" (vị thế + Pearson) | VI đang bán tốt hơn. Cân nhắc mang "Pearson Elite Partner" lên EN hero — đây là differentiator thật (recognised 2025) |
| M5 | Blog URL không có prefix `/blogs/` | `ptemagic.com/pte-essay-topics` | Không migrate hàng loạt (rủi ro > lợi ích). Nhưng sitemap nên tách section riêng và bài mới nhất quán |
| M6 | Chưa có `llms.txt` | chỉ suy ra được là *không thấy nhắc tới* — chưa verify | Không bắt buộc. Nếu theo đuổi GEO thì thêm; chi tiết trong skill `seo-geo-visibility` |

---

## Đã kiểm tra và KHÔNG có vấn đề

Quan trọng ngang finding — để bạn không sửa những thứ đang ổn:

- ✅ **robots.txt cho phép toàn bộ** `User-Agent: * / Allow: /` — không chặn nhầm
- ✅ **Có khai báo Sitemap** trong robots.txt
- ✅ **Sitemap tồn tại và parse được**, có `<lastmod>`, có cả 7 trang tĩnh + `/vi/*` + blog
- ✅ **Nội dung bài blog chất lượng cao thật.** Đọc `/pte-essay-topics`: mở đầu bằng ràng buộc
  cụ thể (1 essay, 20 phút, 200–300 từ, 7 traits/15 điểm), có bảng format, **tự khai rõ**
  "These are practice prompts written in the style and register PTE uses. They are not copied
  from live tests — no one outside Pearson has the live item bank".
  Câu đó chính xác là hành vi E-E-A-T tốt, và nó tránh rủi ro pháp lý với Pearson. **Giữ nguyên
  giọng này.**
- ✅ **Có ghi nguồn**: "_Format and scoring details follow the official PTE Academic guidance
  published by Pearson._"
- ✅ **Testimonial có tên + quốc gia + điểm số + mục tiêu** — trust signal tốt (dù cần
  xin phép/verify là thật trước khi quảng bá rộng)
- ✅ **Không phát hiện nội dung ngoài lĩnh vực** (gambling/loan/coupon) trong các URL đã thấy
  → hiện không có rủi ro site reputation abuse

---

## Action plan xếp theo Impact × Effort

| # | Việc | Impact | Effort | Owner | Chặn bởi |
|---|---|---|---|---|---|
| 1 | `next/image` sizes/srcset — bỏ `w=3840` | Cao | **Thấp** (0.5d) | Dev | — |
| 2 | Chạy `seo_audit.py` + `psi_cwv.py` trên máy có mạng để có baseline thật | Cao | **Rất thấp** (20ph) | SEO | — |
| 3 | Sửa title `/blogs` + audit trùng title toàn site | Trung bình | Rất thấp | SEO | — |
| 4 | Bọc tiêu đề bài viết trong `/blogs` bằng `<a>` | Trung bình | Rất thấp (10ph) | Dev | — |
| 5 | Tạo `/refund-policy` thật + sửa footer | Trung bình (ads + trust) | Thấp | SEO + Pháp lý | — |
| 6 | Sửa `lastmod` nguồn dữ liệu cho trang tĩnh | Trung bình | Thấp | Dev | — |
| 7 | noindex path app (`/sso/*`, `/dashboard/*`) | Trung bình | Thấp | Dev | — |
| 8 | 1 H1 duy nhất cho hero EN + VI | Thấp–Trung bình | Thấp | Dev | — |
| 9 | Sửa carousel render testimonial trùng | Thấp | Trung bình | Dev | — |
| 10 | **Chốt kiến trúc i18n** (C2) rồi mới làm hreflang | **Rất cao** | **Cao** (1 sprint) | SEO + Dev + Founder | — |
| 11 | Đồng bộ proof points EN ↔ VI (M3, M4) | Thấp | Rất thấp | SEO | 10 |
| 12 | Content plan: 6 bài task-level PTE Academic (C2 cluster) | Cao | 6 × 2.5h | SEO + Editor | 10 (nếu làm cả VI) |
| 13 | Audit + quyết định prune/gộp cho 27 bài study-abroad | Trung bình | 4h | SEO | — |

**Thứ tự khuyến nghị cho tuần đầu:** 2 → 1 → 3 → 4 → 7 → 5 → 10 (họp chốt) .
Đừng bắt đầu bằng 10 — cần số liệu từ 2 để thuyết phục dev/founder.

**Không làm:** không viết thêm blog, không build hreflang, không mua/chạy link cho tới khi
mục 1, 2, 10 xong. Audit trước, tối ưu sau — đó là lý do SOP đặt G1 trước G2.

---

## Chỗ này tôi muốn nói thẳng với bạn, với tư cách người làm nghề

Ba điều bạn nên tự kiểm trước khi mang bộ quy trình này đi bán cho khách:

1. **PBN là link spam theo spam policies của Google**, được liệt kê đích danh cùng
   "link farms and private blog networks". Mình không đưa skill tự động hoá PBN vào đây, và
   Policy Gate sẽ BLOCK anchor pattern kiểu đó. Đây là vấn đề rủi ro nghề nghiệp của bạn,
   không phải vấn đề đạo đức trừu tượng: một mạng lưới bị phát hiện kéo theo nhiều khách
   cùng lúc. Tài sản PTE Magic có thật để làm digital PR (dữ liệu 400.000 học viên,
   Pearson Elite Partner, Bett Asia Top 10) — dùng cái đó trước.

2. **Report này chưa đủ để đưa cho khách.** Nó ghi rõ giới hạn phương pháp và không có điểm số.
   Đó là chuẩn bạn nên giữ: một báo cáo audit có 40 con số nhưng 10 trong số đó do LLM đoán
   sẽ giết uy tín của bạn nhanh hơn nhiều so với việc không có điểm.

3. **Đừng tối ưu cho AI Overviews theo kiểu "viết trang để được cite".** Từ 15/05/2026,
   spam policies áp dụng thẳng cho việc thao túng câu trả lời AI, và SpamBrain quét nội dung
   vì mục đích cite. Cách an toàn — và cũng là cách hiệu quả — là làm nội dung mà một người
   đọc xong thấy đáng tin và muốn dẫn nguồn. PTE Magic đang làm đúng ở `/pte-essay-topics`.

---

## Phụ lục: lệnh tái hiện

```bash
cd seo-agents
cp -n reports/ptemagic/2026-09-29-audit-khoi-dau.md /tmp/   # giữ bản này để so

.venv/bin/python scripts/seo_audit.py --site https://ptemagic.com \
    --max-urls 300 --config config/ptemagic.yaml --out reports/ptemagic/
# → reports/ptemagic/<date>-audit.md + .json

.venv/bin/python scripts/psi_cwv.py --config config/ptemagic.yaml \
    --strategy both --out reports/ptemagic/cwv.md

.venv/bin/python scripts/drift.py baseline --site https://ptemagic.com --max-urls 300

# Sau khi dev sửa mục 1 (ảnh):
.venv/bin/python scripts/psi_cwv.py --url https://ptemagic.com/ --strategy mobile
.venv/bin/python scripts/drift.py compare --site https://ptemagic.com --max-urls 300
```

Kiểm tra lại từng finding bằng cách grep trong JSON:
```bash
.venv/bin/python -c "
import json,glob
d=json.load(glob.glob('reports/ptemagic/*-audit.json')[-1])
for c in ['NEXT_IMAGE_OVERSIZED_W','MULTIPLE_H1','SITEMAP_LASTMOD_ALL_IDENTICAL','TITLE_BRAND_DUPLICATED']:
    hits=[f for f in d['findings'] if f['code']==c]
    print(f'{c:34s} {len(hits):3d}  ', *sorted({h['url'][-55:] for h in hits})[:3])
"
```
