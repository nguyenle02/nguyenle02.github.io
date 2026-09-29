# Google Spam Policies — bản làm việc, cập nhật 2026-09-29

> Đối chiếu gốc: <https://developers.google.com/search/docs/essentials/spam-policies>
> Tài liệu này **tóm tắt để thi hành**, không thay thế văn bản gốc.
> Lần cập nhật lớn gần nhất của Google: **15/05/2026**.
> Nguồn tham khảo của bản tóm tắt: xem `RESEARCH-GITHUB-SEO-AGENTS.md` mục 5.

## 0. Điều thay đổi năm 2026 (đọc cái này trước)

Ngày 15/05/2026, Google sửa câu mở đầu định nghĩa spam:

> "spam refers to techniques used to deceive users or manipulate our Search systems into
> featuring content prominently, such as attempting to manipulate Search systems into ranking
> content highly **or attempting to manipulate generative AI responses in Google Search**."

Hệ quả thực thi: các policy **Cloaking · Scaled content abuse · Link spam · Site reputation
abuse · Doorway pages · Thin affiliation · Keyword stuffing · Hidden text** giờ áp dụng cho
**cả tư cách được trích trong AI Overviews / AI Mode**, không chỉ 10 kết quả xanh.

> **Diễn giải:** "xếp hạng" nay bao gồm "được trích dẫn". SpamBrain quét nội dung để xét
> cả hai. Nhiều trang dựng ra chỉ để được đưa vào câu trả lời AI, không có lý do gì cho
> người đọc, là scaled content abuse — và điều đó đã bị **enforce** (August 2026 spam update
> là đợt thứ ba của năm chạy sau mốc 15/05).

## 1. Timeline enforcement 2024→2026

| Ngày | Sự kiện | Ý nghĩa thực thi |
|---|---|---|
| 03/2024 | Core + spam update | Thêm 3 policy: **scaled content abuse**, **site reputation abuse**, **expired domain abuse**. Đổi tên "spammy auto-generated content" → "scaled content abuse", **cố ý** phá cách hiểu "AI content = spam" |
| 03/2024 | Helpful content signals vào core | Chất lượng bị xét **liên tục**, không còn theo từng đợt |
| 15/05/2026 | Định nghĩa spam viết lại | Mở rộng sang thao túng câu trả lời AI |
| 24–25/03/2026 | Spam update (<20h — nhanh nhất từng có) | Không có policy mới. SpamBrain tinh chỉnh. **Loại trừ** link spam & site reputation abuse |
| 24/06–đầu 07/2026 | June 2026 spam update | Cũng **loại trừ** link spam & site reputation abuse → trọng tâm là content-level: scaled content, cloaking, keyword stuffing, doorway |
| 18–21/08/2026 | August 2026 spam update | "What has changed is that 'rank' now includes 'get cited'" |

**Hai suy luận sai cần tránh:**
1. *"Update 2026 loại trừ link spam → PBN an toàn."* **Sai.** Nó chỉ nói update đó không nhắm
   link spam. Link spam vẫn là spam policy, vẫn bị hệ thống thường trực xử lý.
2. *"Disavow để phòng ngừa."* **Sai.** Disavow không giúp recovery cho các update trên
   (Google nói rõ), và disavow quá tay làm bạn mất link tốt.

## 2. 16 nhóm policy + cách PTE Magic có thể vấp

### 2.1 Scaled content abuse — mức rủi ro CAO NHẤT (được enforce mạnh nhất)

**Định nghĩa:** sản xuất nhiều trang **chủ yếu** để thao túng xếp hạng thay vì giúp người dùng,
**bất kể** bằng phương tiện nào (AI, người viết, template, programmatic).

- **Origin-blind.** Luật không quan tâm ai viết.
- **Không có ngưỡng số trang.** Google chưa từng công bố page limit hay % AI cap.
  10 trang gần-giống nhau nhắm keyword có thể vi phạm; 500 trang hữu ích thì không.
  Tiêu chí định tính: *lượng có đang chạy nhanh hơn giá trị bạn thêm được mỗi trang không?*
- Điểm quyết định là chữ **"primarily"**: nếu trang tồn tại trước hết để bắt query,
  và chỉ tình cờ giúp ai đó → rủi ro.

Bằng chứng thực địa 2026 (nhiều nguồn độc lập, không phải số liệu Google công bố):

| Mẫu | Kết quả |
|---|---|
| 50–100 bài AI **có biên tập**, có chuyên môn | traffic **+30…+80%** |
| ≥1.000 trang AI **không biên tập** | traffic **−40…−90%** |
| 1 site 1.800 bài auto-generated | mất phần lớn traffic trong **9 ngày** |

| Scaled content abuse | AI-assisted hợp lệ |
|---|---|
| Spin trang để phủ biến thể keyword | Trang dựng để trả lời một câu hỏi thật |
| Publish hàng loạt, không ai review | Có người biên tập, fact-check, định hình |
| Đổi chủ đề, giữ nguyên vỏ | Có dữ liệu gốc, ví dụ, trải nghiệm trực tiếp |
| Không author, không accountability | Author thật, quyền biên tập rõ |
| Tồn tại để bắt traffic | Tồn tại vì hữu ích; rank là hệ quả |

**Rủi ro cụ thể của PTE Magic:**
- 32 bài "study in <nước> × <chủ đề>" cùng một vỏ → `TEMPLATE_SHELL`
- 12 bài "template cho task X" nếu chỉ khác tiêu đề → như trên
- Dịch 1:1 bài EN sang VI rồi coi là bài mới → `NEAR_DUPLICATE` + Cannibalisation
- Bulk content mùa tuyển sinh (tháng 2 & tháng 7) mà không thêm gì → mẫu hình dễ bị quét

**Phòng thủ:** mỗi trang phải có ≥1 tài sản độc quyền: dữ liệu chấm AI trên 400.000+ học viên ·
8.000+ câu hỏi đã phân loại · template trainer viết · case học viên có tên + điểm.
Người biên tập có tên, và bạn tự đọc được.

### 2.2 Site reputation abuse

Host site đăng nội dung bên thứ ba **chủ yếu để tận dụng ranking signal của chính domain**.
Ví dụ kinh điển: trang tin/giáo dục mở "chuyên mục sponsored" đầy coupon, vay nặng lãi, gambling.

**Không cấm** nội dung bên thứ ba. Syndicated wire content, guest column, sponsored có
disclosure — đều ổn. Cái bị nhắm: arrangement mà nội dung nằm trên domain đó **chỉ vì**
sức mạnh ranking của domain.

**PTE Magic:** nếu cho trung tâm du học/đối tác đăng bài trên `/blogs`:
phải có editorial review ghi lại được · chủ đề thuộc lĩnh vực PTE/du học · disclose ·
không biến blog thành hạ tầng link (5 đối tác × 20 bài link về site họ = **link scheme**,
dù content tốt).

### 2.3 Expired domain abuse
Mua domain hết hạn thì ổn **nếu** nội dung mới liên quan niche cũ. Vi phạm khi nội dung
không liên quan và tồn tại để lợi dụng reputation cũ.
→ bạn có kinh nghiệm tư vấn domain cho khách: đây là checklist **trước khi** mua, không phải sau.

### 2.4 Link spam
Mua/bán link truyền PageRank · link exchange quá mức · guest post hàng loạt anchor keyword-rich ·
chương trình build link tự động · **link farms and private blog networks (PBNs)** ·
link footer phân phối trên mạng site không liên quan · forum signature spam · directory chất lượng thấp.

Liên kết **được** là hợp lệ. Vi phạm nằm ở **ý định**: đặt để giúp người đọc tìm thứ hữu ích,
hay để truyền ranking credit.
**Paid/sponsored phải có `rel="sponsored"`** (hoặc nofollow). Có rel mà vẫn bán link để
truyền PageRank thì vẫn vi phạm.

### 2.5–2.16 các nhóm còn lại

| Policy | Định nghĩa ngắn | Check tự động trong bộ này |
|---|---|---|
| **Keyword stuffing** | Nhét từ khoá để thao túng xếp hạng | `policy_gate.py` density >3.5%, heading >60% |
| **Doorway pages** | Trang vô nghĩa, dẫn tới nội dung thực/giả; tạo nhiều trang gần trùng nhắm truy vấn chung | `TEMPLATE_SHELL` |
| **Cloaking** | Trình nội dung khác cho Googlebot và người dùng | `CLOAKING_*` |
| **Hidden text & link abuse** | Chữ/link đặt ra chỉ cho máy đọc. **Accordion/tooltip/slider vì usability thì không vi phạm** — ranh giới là ý định | `HIDDEN_TEXT` (chỉ khi text ẩn **chứa keyword**) |
| **Sneaky redirects** | Redirect tới đích khác cái bot thấy, hoặc theo user-agent | `drift.py` + `CLOAKING_BOT_SNIFFING` |
| **Thin content with little value** | Trang thêm rất ít giá trị, để trang đơn lẻ hoặc hàng loạt | `THIN_CONTENT`, `NEAR_DUPLICATE` |
| **Affiliate abuse / thin affiliation** | Trang affiliate trùng nội dung nhà cung cấp, không có đánh giá/giữ liệu gốc | `NO_VALUE_ADD` |
| **Scraped content** | Mượn/xào nội dung người khác, không thêm giá trị gốc | `NEAR_DUPLICATE` vs corpus (một phần) |
| **Hacked content** | Trang bị chèn nội dung spam | `drift.py` (`title_changed`/`page_appeared` bất thường) |
| **User-generated spam** | Comment/forum spam do kẻ xấu đăng trên site bạn | cần moderation — không tự động |
| **Misleading functionality** | Nói một đường làm một nẻo (nút tải → khảo sát) | không tự động — review tay |
| **Deceptive content** | nội dung gây hiểu lầm/ giả mạo/ lừa | `GUARANTEE_CLAIM` |
| **Unauthorized copyrighted content** | đăng nội dung có bản quyền | ⚠️ **đặc thù PTE**: "đề thi thật" là tài sản Pearson |
| **Automatically generated traffic / malware / unwanted software** | ngoài phạm vi content | — |

## 3. E-E-A-T & helpful content (nơi bạn thắng)

Không phải "policy" — không có manual action vì "thiếu E-E-A-T". Nhưng nó là **hệ thống xếp hạng**,
và nó là lý do khiến scaled content abuse bị phát hiện.

Bốn tầng, áp cho PTE Magic:

| Tầng | PTE Magic có sẵn | Cần thêm |
|---|---|---|
| **Experience** (người viết đã thật sự làm) | 400.000 học viên, trainer đã chấm bài | Mỗi bài phải có 1 chi tiết chỉ người trong cuộc mới biết |
| **Expertise** (năng lực đúng chủ đề) | đội PTE trainer | `author` có chức danh + profile; `reviewer` cho nội dung điểm số/visa |
| **Authoritativeness** (domain) | **Pearson Elite Partner 2025**, Bett Asia Top 10, Edu 4.0, VN–Úc EdTech Alliance | phản ánh vào `Organization.award`/`memberOf` + trang về giải thưởng |
| **Trustworthiness** | testimonial có tên + điểm | trang "Payment & Refund" **thật** (hiện trỏ về /privacy-policy), tác giả thật, ngày cập nhật |

**YMYL:** với PTE Magic = nội dung **visa / định cư / học bổng / chi phí / vay / yêu cầu điểm
cho đăng ký hành nghề**. Nhóm này bị áp E-E-A-T cao nhất. Quy trình: `policy_gate.py`
→ `YMYL_MISSING_EVIDENCE` (BLOCK nếu thiếu author, ngày ≤90 ngày, hoặc nguồn chính phủ).

## 4. Hệ quả khi bị phát hiện

| Cơ chế | Ai quyết | Hiện ở đâu |
|---|---|---|
| **Algorithmic demotion** (SpamBrain) | thuật toán, liên tục | không thông báo — chỉ thấy traffic tụt |
| **Manual action** | webspam team người thật | GSC → *Security and Manual Actions* |
| **Suspension / removal** | với vi phạm nghiêm trọng (malware, hacked, cloaking nặng) | GSC + email |

**Không có "kháng cáo nhanh".** Xem mục 5.

## 5. Recovery — nếu nghi bị hit

Đừng làm 4 việc: viết thêm content · mua link mới · đổi title hàng loạt · cài tool "penalty recovery".

**Làm 6 bước, theo thứ tự:**
1. **GSC → Security and Manual Actions.** Có entry hay không? Nếu **không có** = đang bị
   algorithmic. Bạn **không** được thông báo.
2. GSC Performance, vẽ đường theo **ngày**, đối chiếu với timeline mục 1. Khớp với đợt
   spam/core update nào?
3. Phân tách phạm vi mất: **toàn bộ site** vs **1 thư mục** vs **1 mẫu URL**.
   Đây là bước quan trọng nhất: quyết định mức độ và hướng.
4. Audit **các trang mất traffic** so với cùng danh mục ở mục 2. Đọc 10 trang tệ nhất
   thật sự — không đọc báo cáo tool.
5. Sửa **vi phạm thật**. Không gỡ nội dung để "cho qua mặt". Không đổi ngày để giả vờ cập nhật.
6. **Chờ.** Recovery là chu kỳ re-crawl/re-index, thường 2 tuần tới vài tháng.
   Đừng phản ứng dây chuyền bằng cách sửa lần hai khi chưa có số.

Kháng cáo (chỉ khi manual action): mô tả **nguyên nhân gốc** (không phải triệu chứng),
**việc đã làm**, **cam kết thay đổi quy trình**. Ngắn, sự thật, có dẫn chứng.

## 6. Checklist 14 điểm trước publish (bản in được)

**Nội dung**
- [ ] Trả lời một câu hỏi thật, có thể nêu trong 1 câu
- [ ] Có ≥1 thứ chưa trang nào top 10 có
- [ ] Không phải bản sao/ẩn-sao của trang đã publish (đã chạy `--corpus`)
- [ ] Mọi số liệu kiểm chứng được, có nguồn + ngày
- [ ] Không có claim không có nguồn, không hứa kết quả

**E-E-A-T**
- [ ] Author là người thật, có chuyên môn, có profile
- [ ] Nội dung YMYL có `reviewer`
- [ ] Ngày updated thật, không phải ngày build
- [ ] Với điểm số/visa: link nguồn chính thức

**Kỹ thuật**
- [ ] 1 H1 · title ≤60 · meta ≤155 · canonical self-ref
- [ ] Ảnh có `sizes`, không request `w` quá khổ
- [ ] Schema validate, mô tả thứ có thật trên trang

**Liên kết**
- [ ] Anchor ra ngoài mô tả, không money-text; paid → `rel="sponsored"`
- [ ] ≥3 internal link vào, ≥4 ra, anchor mô tả
- [ ] Không link scheme, không PBN, không link exchange

## 7. Điều không nằm ở đâu trong chính sách, nhưng bạn nên nói với khách

**Bền hơn nhanh.** Mọi tactic trong danh mục 2.4 (link spam) đều có hạn sử dụng, và hạn đó
do Google quyết, không do bạn. Trong PTE / EdTech cụ thể: Pearson là đối tác của bạn,
nên "tăng tốc" bằng cách gây rủi ro cho domain là đánh cược thứ bạn không sở hữu.

Đừng dùng tài liệu này để dọa khách. Dùng để giải thích tại sao bạn tính phí cho
8 bài có biên tập thay vì 80 bài spin.
