# Target Keywords & Cluster Map — PTE Magic

> Nạp vào mọi skill keyword/content. **Số liệu volume/KD PHẢI verify bằng Ahrefs hoặc DataForSEO
> trước khi dùng cho khách** — file này cố ý KHÔNG ghi volume bịa.
> Nguồn keyword: suy ra từ URL thật trong `sitemap.xml` + cấu trúc category trên `/blogs`.

## Trạng thái

| Trường | Giá trị |
|---|---|
| Cập nhật | 2026-09-29 |
| Nguồn | sitemap.xml thật, footer `/blogs`, tiêu đề bài viết đã crawl |
| Volume/KD | **chưa có** — cần chạy `scripts/gsc_pull.py` + export Ahrefs vào `data/` |

---

## 6 cluster trụ cột

### C1 — PTE format & structure · intent: informational/commercial · funnel: MOFU→BOFU

Trang đích: `/exam-structure-pte-academic`, `/exam-structure-pte-core`, `/pte-exam-pattern`

| Keyword | Ghi chú | URL hiện có |
|---|---|---|
| pte exam pattern | đã có bài, lastmod 2026-09-02 | `/pte-exam-pattern` |
| pte academic exam structure | trang tĩnh | `/exam-structure-pte-academic` |
| pte core exam structure | trang tĩnh | `/exam-structure-pte-core` |
| pte core vs pte academic | **GAP — chưa có URL riêng**, FAQ trên `/blogs` có nhắc | ❌ |
| pte exam duration / how long is pte | có trong bài exam pattern | `/pte-exam-pattern` |
| pte question types | rải rác, chưa có hub | ❌ |

**Hành động:** tạo `/pte-core-vs-pte-academic` — đây là query so sánh có ý định cao và
PTE Magic có cả 2 sản phẩm. Ưu tiên số 1 của C1.

---

### C2 — Task-level tips & templates · intent: informational · funnel: MOFU
### ⭐ Cluster mạnh nhất — PTE Magic có template do trainer viết (lợi thế độc quyền)

| Task | Keyword mẫu | Trạng thái |
|---|---|---|
| Write Essay | pte essay topics, pte essay template, pte write essay tips | ✅ `/pte-essay-topics` (60 topics, rất tốt) |
| Summarize Written Text | pte summarize written text template | ⚠️ chỉ có bản PTE Core: `/pte-core-...summarize-written-text`, `/cau-truc-va-meo-on-tap-pte-core-summarize-written-text` |
| Reorder Paragraph | pte reorder paragraph tips | ⚠️ chỉ có bản PTE Core |
| Fill in the Blanks | pte reading fill in the blanks | ⚠️ chỉ có bản PTE Core |
| Repeat Sentence | pte repeat sentence tips/practice | ❌ **GAP lớn** — task khó nhất với học viên, testimonial `/vi` nhắc trực tiếp ("RS và WFD") |
| Write From Dictation | pte write from dictation practice | ❌ **GAP lớn** — testimonial nhắc trực tiếp |
| Describe Image | pte describe image template | ⚠️ chỉ có bản PTE Core |
| Respond to a Situation | pte respond to a situation | ✅ `/pte-respond-to-a-situation-template` |
| Summarize Group Discussion | pte summarize group discussion | ✅ `/pte-summarize-group-discussion-template` |
| Answer Short Question | pte answer short question | ⚠️ chỉ có bản VI/PTE Core |
| Retell Lecture | pte retell lecture template | ❌ GAP |
| Highlight Correct Summary | pte listening highlight correct summary | ❌ GAP |

**Phát hiện quan trọng:** phần lớn content task-level đang viết cho **PTE Core**, trong khi
lượng tìm kiếm lớn hơn nhiều nằm ở **PTE Academic**. Đang thiếu song song bản Academic cho
hầu hết task. → Đây là mỏ content có cấu trúc rõ ràng, nhưng **cẩn thận doorway pages**:
12 bài "template cho task X" mà cùng một cái vỏ là vi phạm. Mỗi bài phải có:
đề mẫu khác nhau thật, lỗi học viên khác nhau thật, dữ liệu điểm khác nhau thật.

**Hành động đề xuất:** hub `/blogs?categoryIds=<id>` cho từng skill + 1 bài pillar
"PTE Academic: Full Task-by-Task Guide" link xuống 12 bài task.

---

### C3 — Score & scoring · intent: informational · funnel: MOFU

| Keyword | Trạng thái |
|---|---|
| how is pte scored / pte scoring system | ✅ `/how-does-pte-automated-scoring-work-a-complete-guide` |
| pte score calculator | ❌ GAP — có thể làm **công cụ tương tác** (tool = link magnet) |
| pte to ielts score conversion | ❌ GAP lớn, volume cao |
| pte score validity / how long is pte score valid | ⚠️ chỉ trong FAQ `/blogs` |
| pte score report / share pte score | ✅ `/how-to-access-and-share-your-pte-score-report-easily` |
| pte accents / how pte marks accents | ✅ `/how-does-pte-academic-mark-different-accents-all-answered` |
| pte 65 equivalent / pte 79 requirement | ❌ GAP — query gắn trực tiếp với visa, YMYL |

**Cơ hội lớn nhất cluster này:** `PTE Score Calculator` dạng công cụ. Đây là
link-earning asset thật (digital PR) chứ không phải content thường — xem `skills/seo-offpage-compliant`.

---

### C4 — Study abroad / migration theo quốc gia · intent: informational · funnel: TOFU
### ⚠️ Toàn bộ là YMYL — xem `config/ptemagic.yaml: ymyl`

Đã có ~40 bài, chia 4 nước. Đối chiếu sitemap thật:

| Nước | Số bài (ước lượng từ sitemap) | Ví dụ slug |
|---|---|---|
| Australia | ~8 | `how-to-study-in-australia-as-an-international-student`, `best-universities-in-australia-for-international-students`, `checklist-for-moving-to-australia-...`, `how-to-apply-for-a-permanent-resident-visa-in-australia-2026-guide-...` |
| Canada | ~10 | `best-universities-in-canada-for-international-students`, `canada-post-graduate-work-permit-requirements`, `what-is-the-cost-of-living-in-canada-for-foreign-students`, `the-best-scholarships-for-international-students-in-canada` |
| New Zealand | ~8 | `how-to-study-in-new-zealand-as-an-international-student`, `changes-to-new-zealand-language-test-requirements-whats-new`, `post-study-work-visa-in-new-zealand-...` |
| UK | 1 | `study-in-the-uk-requirements-cas-costs-deadlines` |

**Rủi ro cần kiểm:** 4 nước × cùng 8 chủ đề (study / job / accommodation / visa / scholarship /
universities / cost of living / part-time jobs) = **32 bài có cấu trúc y hệt nhau**.
Đây chính xác là hình dạng của *doorway pages* nếu phần thân không đủ khác biệt.
→ `scripts/policy_gate.py --corpus published/` sẽ đo. Nếu Jaccard ≥ 0.50 giữa các bài
"cùng chủ đề khác nước" → phải viết lại để mỗi bài có dữ liệu riêng của nước đó
(học phí thật, tên trường thật, yêu cầu visa thật, ngày hiệu lực thật).

**UK đang thiếu nặng** (1 bài so với 8–10 của nước khác) — nhưng đừng viết chỉ để cho đủ.
Hỏi trước: PTE Magic có bao nhiêu học viên target UK? Nếu ít, đừng đầu tư.

---

### C5 — PTE Core (Canada) · intent: informational/commercial · funnel: MOFU→BOFU
### ⭐ Cluster mới, ít đối thủ, đang tăng

Đã có (từ sitemap): `pte-core-listening-format-modules-success-tips`,
`pte-core-reading-multiple-choice-single-answer-tips`,
`pte-core-reading-fill-in-the-blanks-format-tips`,
`pte-core-reorder-paragraph-format-tips-to-score-high`,
`pte-core-reading-and-writing-fill-in-the-blanks-tips`,
`pte-core-answer-short-question-30-cau-hoi-de-gap-nhat`,
`pte-core-respond-to-a-situation-cau-truc-va-meo-on-tap`,
`pte-core-writing-email` (bản VI),
`pte-accepted-for-student-direct-stream-visas-in-canada`,
`best-english-test-for-australian-immigration-full-comparison`.

**Vấn đề phát hiện được:** nhiều bài PTE Core có **slug tiếng Việt nhưng nội dung có thể ở EN**
(vd `/meo-pte-core-reading-multiple-choice-multiple-answers`,
`/cau-truc-va-meo-dat-diem-cao-pte-core-reorder-paragraph`) và **trùng chủ đề với slug tiếng Anh**
(`/pte-core-reorder-paragraph-format-tips-to-score-high` vs `/tips-pte-core-reading-multiple-choice-multiple-answers`
vs `/meo-pte-core-reading-multiple-choice-multiple-answers`).
→ **Nguy cơ cannibalisation EN/VI rất cao.** Phải map 1-1 và đặt hreflang, hoặc gộp.

**Hành động ưu tiên số 2 sau C1:** chạy `scripts/cluster_keywords.py` riêng cho các slug
`*pte-core*` để tìm cặp trùng.

---

### C6 — Brand & platform · intent: navigational/transactional · funnel: BOFU
### Cần BẢO VỆ, không cần mở rộng

| Keyword | Ghi chú |
|---|---|
| pte magic / pte magic login / pte magic app | đảm bảo sitelinks, không để đối thủ chạy ads chèn |
| pte mock test online / free | ✅ `/features` nhưng chưa tối ưu cho query này |
| pte practice test free | cơ hội landing riêng |
| pte ai scoring | khác biệt hoá chính của sản phẩm |
| pearson elite partner pte | trust signal, nên có trang riêng hoặc section |

---

## Từ khoá phủ định (KHÔNG viết bài cho những cái này)

| Keyword | Lý do |
|---|---|
| pte exam leak / pte real questions 2026 / đề thi thật hôm nay | Vi phạm bản quyền Pearson + rủi ro pháp lý. Blog hiện tại đã xử lý đúng ("not copied from live tests") — giữ chuẩn này. |
| pte hack / cheat / bypass scoring | Gian lận thi cử — rủi ro brand và pháp lý |
| ielts vs pte which is easier (bản so sánh thiên vị) | Chỉ viết nếu so sánh trung thực có số liệu, không dìm đối thủ |
| visa guaranteed / cam kết đậu visa | YMYL + quảng cáo sai sự thật |
| mọi keyword về cờ bạc, vay nóng, coupon không liên quan | Site reputation abuse |

---

## Quy tắc đặt keyword vào brief

1. **1 primary keyword / 1 URL.** Hai URL cùng 1 primary = cannibalisation → phải gộp.
2. Keyword phải xuất hiện ở: title (đầu câu nếu được), H1, 100 từ đầu, 1 H2, URL slug, meta description.
   **Không** xuất hiện ở > 60% heading (Policy Gate #3 sẽ BLOCK).
3. Mật độ exact-match ≤ 3.5%. Dùng biến thể tự nhiên và entity liên quan.
4. Với bài tiếng Việt: keyword tiếng Việt, **không** nhét keyword tiếng Anh vào bài VI
   trừ khi đó là thuật ngữ cố định (PTE Core, Write From Dictation, Repeat Sentence…).
