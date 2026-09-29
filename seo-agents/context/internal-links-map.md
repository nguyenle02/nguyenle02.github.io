# Internal Link Map — PTE Magic

> Nạp khi `content-briefer` và `onpage-editor` quyết định link đi đâu.
> **Chỉ dùng URL có thật trong danh mục này.** Không bịa URL.
> Nguồn: `sitemap.xml` + `/blogs` + header/footer, cập nhật 2026-09-29.

## Kiến trúc mong muốn (hub → spoke)

```
                    ┌─ / (authority gốc)
                    │
   ┌────────────────┼────────────────┬───────────────┬──────────────┐
   ▼                ▼                ▼               ▼              ▼
/exam-structure  /features     /blogs (hub)   /pte-exam-pattern  /contact-us
 -pte-academic   (BOFU)             │
 -pte-core                          ├─ C2 task hub (nên có pillar riêng)
                                    ├─ C3 score hub
                                    ├─ C4 study-abroad hub (1 pillar/nước)
                                    └─ C5 PTE Core pillar
```

**Hiện trạng:** các hub C2/C3/C4/C5 **chưa tồn tại**. /blogs đang gồng vai hub
cho ~120 bài — đó là lý do `/blogs` là trang quan trọng nhất khối blog mà lại có
title yếu ("PTE Magic - PTE Magic Blog").

## Quy tắc

| Quy tắc | Ngưỡng |
|---|---|
| Link **vào** một bài mới | ≥3, từ trang liên quan thật |
| Link **ra** trong 1 bài blog | 3–8 internal + 2–5 external |
| Anchor | mô tả trang đích. **Không** "Read more"/"Xem thêm" |
| Depth từ homepage | ≤3 click |
| Bài mới publish | chưa có 3 link vào = **chưa xong** |
| Money page | mọi bài trong cluster phải có ≥1 đường tới `/features` **hoặc** `/sso/auth/register` |

## Ba lỗi internal link ĐANG TỒN TẠI (đã đo)

| # | Lỗi | Hệ quả | Fix | Effort |
|---|---|---|---|---|
| **L1** | Trên `/blogs`, **tiêu đề bài viết không phải anchor** — chỉ ảnh là link | Mất internal anchor text có giá trị nhất site, từ trang có PageRank cao nhất | Bọc `<h4><a href="/slug">Title</a></h4>` | **~10 phút** |
| **L2** | Footer link **"Payment & Refund Policy" → `/privacy-policy`**, trùng với "Privacy Policy" | Trang refund không tồn tại; 2 nav item → 1 URL | Tạo `/refund-policy` riêng + update footer | 1 giờ (cần nội dung) |
| **L3** | Category link là **query params**: `/blogs?page=1&categoryIds=10\|14\|18\|22` | Link URL có tham số từ mọi trang → khó canonical, khó đo, khó link | Cân nhắc URL tĩnh `/blogs/pte-speaking` + 301 | 1 ngày |

L1 là việc **đáng tiền nhất trên toàn bộ audit này** xét theo tỉ lệ impact/effort.

## Money pages (mọi cluster phải có đường tới đây)

| URL | Role | Khi nào link |
|---|---|---|
| `/sso/auth/register` | **primary conversion** | cuối bài, khi reader đã có đủ context |
| `/sso/auth/login` | returning users | nav/header |
| `/features` | giải thích giá trị / BOFU | "how we score it", "compare with…" |
| `/exam-structure-pte-academic` | hub bài thi | từ C2 + C3 |
| `/exam-structure-pte-core` | hub PTE Core | từ C5 |
| `/contact-us` | sales | bài dài/advanced, khoá học |
| `ptemagic.com.vn` / `ptemagic.com.au` | coaching theo quốc gia | **cẩn thận**: `I18N-ARCH` chưa chốt |

## Hub C2 — Task-level (nơi cần cấu trúc nhất)

Trụ cột đề xuất: `/pte-academic-task-guide` (chưa tồn tại) →

| Task | Bài hiện có | Bài nên có |
|---|---|---|
| Repeat Sentence | ❌ | **P1** — học viên VI nhắc trực tiếp trong testimonial |
| Write From Dictation | ❌ | **P1** — như trên |
| Describe Image | chỉ VI/Core: `/cau-truc-va-meo-on-tap-pte-core-describe-image` | bản EN PTE Academic |
| Re-tell Lecture | ❌ | P2 |
| Read Aloud | ❌ | P2 |
| Answer Short Question | chỉ VI: `/pte-core-answer-short-question-30-cau-hoi-de-gap-nhat` | bản EN |
| Summarize Written Text | chỉ Core: `/cau-truc-va-meo-on-tap-pte-core-summarize-written-text` | bản Academic |
| Re-order Paragraphs | `/pte-core-reorder-paragraph-format-tips-to-score-high`, `/cau-truc-va-meo-dat-diem-cao-pte-core-reorder-paragraph` | **đang cannibalise lẫn nhau** — gộp rồi mới link |
| Fill in the Blanks | 2 bài Core + 2 VI | gộp |
| Essay | `/pte-essay-topics` ✅ | hub này đã tốt — làm **mẫu** |

⚠️ 12 bài "template cho task X" cùng một vỏ = **doorway pages**. `TEMPLATE_SHELL` (BLOCK).
Mỗi bài phải có đề mẫu riêng, lỗi riêng, số liệu riêng.

## Hub C3 — Score & scoring

| URL | Link từ |
|---|---|
| `/how-does-pte-automated-scoring-work-a-complete-guide` | mọi bài C2 (sau khi giải thích task) |
| `/how-does-pte-academic-mark-different-accents-all-answered` | bài Speaking, phát âm |
| `/how-to-access-and-share-your-pte-score-report-easily` | bài score report / sending |
| `/pte-home-a1-a2-b1-tests-everything-you-need-to-know` | bài so sánh loại bài thi |
| **`/pte-score-calculator`** (chưa có) | bài "pte to ielts", "is pte 65 good" → **tool = link-earning asset** |

## Hub C4 — Study abroad ⚠️ YMYL + rủi ro doorway

Hiện ~27 URL: 4 nước × ~7 chủ đề. **Đừng link từ mọi bài.**

| Nước | Pillar đề xuất | Bài hiện có |
|---|---|---|
| Úc | `/study-in-australia` | `how-to-study-in-australia-as-an-international-student`, `best-universities-in-australia-for-international-students`, `top-benefits-of-studying-in-australia-for-international-students`, `study-in-australia-requirements-costs-intakes-scholarships`, `checklist-for-moving-to-australia-as-an-international-student-dos-donts`, `how-to-apply-for-a-permanent-resident-visa-in-australia-2026-guide-for-international-graduates`, `how-to-find-a-job-in-australia-as-an-international-student`, `how-to-find-accommodation-in-australia-for-international-students` |
| Canada | `/study-in-canada` | `best-universities-in-canada-for-international-students`, `the-best-scholarships-for-international-students-in-canada`, `high-paying-part-time-jobs-in-canada-for-international-students`, `how-to-find-a-job-in-canada-as-an-international-student`, `how-to-find-accommodation-in-canada-for-students`, `best-part-time-jobs-for-international-students-in-canada`, `where-do-international-students-live-in-canada`, `best-multicultural-cities-in-canada-for-foreign-students`, `what-is-the-cost-of-living-in-canada-for-foreign-students`, `canada-post-graduate-work-permit-requirements`, `what-are-the-benefits-of-studying-in-canada-for-international-students`, `things-to-know-about-studying-in-canada-the-a-to-z-list`, `study-in-canada-requirements-costs-intakes-scholarships` |
| New Zealand | `/study-in-new-zealand` | `how-to-study-in-new-zealand-as-an-international-student`, `new-zealand-accommodation-guide-for-international-students`, `how-to-find-a-job-in-new-zealand-as-an-international-student`, `how-to-apply-for-a-permanent-resident-visa-in-new-zealand`, `post-study-work-visa-in-new-zealand-for-international-students`, `international-student-loan-in-new-zealand`, `how-to-apply-for-a-student-visa-in-new-zealand`, `changes-to-new-zealand-language-test-requirements-whats-new`, `the-best-universities-in-new-zealand-for-international-students`, `study-in-new-zealand-requirements-costs-intakes` |
| UK | `/study-in-the-uk` | **chỉ có 1 bài**: `study-in-the-uk-requirements-cas-costs-deadlines` |

**Canada có 13 bài, UK có 1.**
Trước khi viết thêm cho UK: chạy `policy_gate.py --corpus` và tự hỏi *"UK có học viên thật không,
và bài có dữ liệu riêng của UK không?"*.
Nếu không → đừng viết. UK không cải thiện `sign_up_free`.

**Cả 4 pillar chỉ nên publish sau khi xong `I18N-ARCH`** — nếu không, bạn đang nhân bản
vấn đề Cannibalisation.

## Anchor text (dùng thật, không sáng tác)

| Context | Anchor |
|---|---|
| Nói về format | "PTE Academic exam structure", "cấu trúc bài thi PTE Core" |
| Nói về chấm điểm | "how PTE automated scoring works" |
| Nói về điểm mục tiêu | "PTE score requirements for [nước]" |
| Nói về nói & viết | "PTE Speaking task-by-task guide" |
| CTA | "start for free", "luyện thử miễn phí" |

**Không dùng làm anchor:** "click here", "xem thêm", "read more", "tại đây" → `ANCHOR_VAGUE`.

## Maintenance

| Khi | Việc |
|---|---|
| Mỗi bài publish | thêm 3+ link **vào** bài mới |
| Hàng tháng | `python scripts/seo_audit.py --site … --max-urls 300` → xem `ORPHAN_PAGES` |
| Khi gộp/xoá bài | 301 về bài liên quan gần nhất + **sửa nguồn link** |
| Khi có hub mới | cập nhật file này + `plans/publish-log.md` |

**Test:** bài nào `ORPHAN_PAGES` >14 ngày → hoặc link vào, hoặc noindex. Đừng để tồn tại ở giữa.
