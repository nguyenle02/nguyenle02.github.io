# Quy trình SEO cho ptemagic.com

> SOP vận hành SEO theo hướng **agent-assisted, human-accountable**.
> Mục tiêu: giảm ~58% giờ công mà vẫn thoả Google Search Essentials (bản cập nhật 15/05/2026).
>
> Vai trò viết tắt: **SEO** = bạn (Lê Duy Nguyên) · **AGENT** = skill/sub-agent · **SCRIPT** = Python deterministic · **EDITOR** = người duyệt nội dung (có thể là bạn ở vai khác)

---

## 0. Nguyên tắc bất biến (đọc trước khi tối ưu bất cứ gì)

1. **Script đo, agent luận, người quyết.** Không một con số nào trong báo cáo được LLM sinh ra.
2. **Không có bước publish nào bỏ qua Policy Gate.** Gate `BLOCK` = dừng, không thương lượng.
3. **Mỗi thay đổi phải có giả thuyết + số đo trước/sau.** Không sửa vì "cảm thấy nên sửa".
4. **Mọi nội dung phải có giá trị mà đối thủ chưa có.** Với PTE Magic, lợi thế độc quyền là:
   dữ liệu chấm điểm AI trên 400.000 học viên, đề thi thật theo format Pearson, và
   trainer thật. Nếu một bài không dùng được ít nhất một trong ba thứ đó → cân nhắc không viết.
5. **Ưu tiên sửa cái đang có trước khi tạo cái mới.** Refresh 1 bài top 15 → top 5 rẻ hơn
   viết 1 bài mới và ít rủi ro scaled content abuse hơn.
6. **Ngôn ngữ nào, thị trường đó.** EN (.com), VI (.com/vi hoặc .com.vn), AU (.com.au)
   là 3 bài toán khác nhau. Không copy-paste rồi đổi ngôn ngữ.

---

## Tổng quan 7 giai đoạn

```
┌─ G0 SETUP ──┐  ┌─ G1 AUDIT ─┐  ┌─ G2 KEYWORD ─┐  ┌─ G3 BRIEF ─┐
│ 1 lần, 45ph │→ │ quý: 1.5h  │→ │ tháng: 1h    │→ │ 20ph/brief │
└─────────────┘  └────────────┘  └──────────────┘  └─────┬──────┘
                                                         ↓
┌─ G6 MEASURE ┐  ┌─ G5 PUBLISH ┐  ┌─ G4b GATE ─┐  ┌─ G4a PRODUCE ─┐
│ tuần: 15ph  │← │ 15ph/bài    │← │ 10ph/bài ⛔│← │ 90–120ph/bài  │
│ tháng: 2h   │  └─────────────┘  └────────────┘  └───────────────┘
└─────────────┘
        ↑____________________ vòng lặp ____________________|
```

| Giai đoạn | Cadence | AI/Script làm | Người làm | Giờ công |
|---|---|---|---|---|
| G0 Setup | 1 lần | sinh config, crawl thử | xác nhận domain/locale/đối thủ | 0.75h |
| G1 Audit & Baseline | quý (full) / tuần (drift) | crawl 40+ check, xuất report | đọc, xếp hạng, quyết định fix | 1.5h / 0.25h |
| G2 Keyword & Cluster | tháng | GSC pull, cluster, gap | chọn chủ đề theo business value | 1h |
| G3 Content Brief | mỗi bài | SERP-driven outline, entity, link map | duyệt intent + góc nhìn riêng | 0.33h |
| G4 Produce & Optimize | mỗi bài | draft, meta, schema, internal link | **kiểm chứng số liệu + thêm trải nghiệm thật** | 1.5–2h |
| G4b Policy Gate | mỗi bài (bắt buộc) | 12 nhóm check, PASS/WARN/BLOCK | xử lý BLOCK, ký tên chịu trách nhiệm | 0.17h |
| G5 Publish & Index | mỗi bài | checklist, sitemap, GSC inspect | duyệt lần cuối trên staging | 0.25h |
| G6 Measure & Iterate | tuần / tháng | delta GSC, drift, decay queue | quyết định refresh/prune | 0.25h / 2h |

---

## G0 — Setup (chạy 1 lần, ~45 phút)

| # | Bước | Ai | Output |
|---|---|---|---|
| 0.1 | Cài skill vào repo ptemagic: `bash install.sh --target claude --project-dir <repo>` | SEO | `.claude/` sẵn sàng |
| 0.2 | Điền `config/ptemagic.yaml`: domain, locale map, GSC property, đối thủ, seed keyword | SEO | config commit vào git |
| 0.3 | Tạo `.env` với `PSI_API_KEY` (free) + service account GSC read-only | SEO | `.env` (gitignored) |
| 0.4 | Nạp `context/`: brand voice, target keywords, internal link map, đối thủ | AGENT soạn, SEO duyệt | 6 file context |
| 0.5 | Chạy smoke test: `python scripts/seo_audit.py --site https://ptemagic.com --max-urls 30` | SCRIPT | report đầu tiên |
| 0.6 | Chạy `python scripts/drift.py baseline --site https://ptemagic.com` | SCRIPT | `data/drift/baseline-ptemagic.com.json` |

**Definition of Done (G0):** `/seo-audit` chạy không lỗi; `config/ptemagic.yaml` có đủ 4 domain
(.com, .com/vi, .com.vn, .com.au) và khai báo quan hệ hreflang dự kiến; baseline đã lưu.

> ⚠️ Câu hỏi phải trả lời ở bước 0.2 — **quyết định kiến trúc i18n**. Hiện tại đang tồn tại song song
> `/vi/` trên `.com`, các bài VI ở root `.com`, và domain riêng `.com.vn`. Ba cái này dẫm chân nhau.
> Phải chốt 1 mô hình trước khi làm hreflang, xem `skills/seo-i18n-hreflang/SKILL.md`.

---

## G1 — Audit & Baseline

### 1A. Full audit (mỗi quý, 1.5h)

```bash
/seo-audit https://ptemagic.com            # orchestrator tự bung 6 sub-agent song song
```

Sub-agent chạy song song → đây là chỗ tiết kiệm thời gian lớn nhất:

| Agent | Phạm vi | Check |
|---|---|---|
| `technical-auditor` | crawl, index, URL, redirect, security header, render | robots.txt, sitemap, canonical, noindex, chain 301/302, HSTS, JS-render |
| `performance-auditor` | Core Web Vitals | LCP/INP/CLS lab + field (CrUX), ảnh `w=3840`, font, render-blocking |
| `onpage-editor` | title/H1/meta/heading/ảnh/anchor | độ dài, trùng lặp, nhiều H1, alt thiếu, anchor mơ hồ |
| `schema-engineer` | JSON-LD | Organization, WebSite+SearchAction, Article, BreadcrumbList, FAQPage, Course, VideoObject |
| `i18n-hreflang` | đa ngôn ngữ | reciprocal, self-reference, x-default, locale sai, nội dung lệch nhau giữa EN/VI |
| `geo-analyst` | AI Overviews / AI Mode / ChatGPT / Perplexity | llms.txt, khả năng được trích dẫn, entity rõ ràng, AI crawler trong robots.txt |

**Sau khi agent trả report, SEO làm (không delegate được):**
1. Bỏ qua mọi finding có `confidence: low` cho tới khi tự tay verify 3 URL mẫu.
2. Xếp lại theo **Impact × Effort** — dùng `templates/action-plan.md`.
3. Chốt tối đa **8 việc cho quý**. Nhiều hơn 8 = không làm được cái nào.

### 1B. Drift check (mỗi tuần, 15 phút)

```bash
python scripts/drift.py compare --site https://ptemagic.com
```
Chỉ ra cái gì *thay đổi* so với baseline: title đổi, schema mất, canonical lật, hreflang gãy,
ảnh mới quá nặng. Rẻ hơn nhiều so với audit lại từ đầu.

**DoD (G1):** có `reports/ptemagic/<date>-audit.md` + `action-plan.md` đã xếp hạng + ≤8 việc được giao owner & deadline.

---

## G2 — Keyword & Cluster (mỗi tháng, 1h)

```bash
python scripts/gsc_pull.py --days 90 --out data/gsc-90d.csv
python scripts/cluster_keywords.py --in data/gsc-90d.csv --out data/clusters.md
```

`cluster_keywords.py` phân loại bằng quy tắc, không đoán:

| Trường | Cách suy ra |
|---|---|
| `intent` | informational (`how/what/why/is/can/vs`), navigational (có brand), transactional (`price/course/free/download/app/practice test`), commercial (`best/top/review`) |
| `funnel` | TOFU / MOFU / BOFU |
| `cluster` | parent topic: nhóm query có ≥ 60% token trùng sau khi bỏ stopword |
| `action` | `NEW` (chưa có URL nào rank) / `REFRESH` (rank 5–20, CTR thấp) / `CONSOLIDATE` (2 URL cùng 1 cluster cannibalise) / `PRUNE` (impression < 30 trong 90 ngày, vị trí > 60) |
| `priority` | `impression × (21 − position)/20` × hệ số business (BOFU ×1.6, MOFU ×1.2, TOFU ×1.0) |

**PTE Magic có 6 cluster trụ cột** (đã map trong `context/target-keywords.md`):

1. **PTE format & structure** — `pte exam pattern`, `pte academic structure`, `pte core vs academic` → BOFU, trang tĩnh
2. **Task-level tips & templates** — `repeat sentence tips`, `write from dictation`, `describe image template`, `pte essay topics` → MOFU, hub `/blogs` + category
3. **Score & scoring** — `pte score calculator`, `how is pte scored`, `pte 65 equivalent ielts` → MOFU
4. **Migration / study abroad theo quốc gia** — `study in australia`, `pte for canada pr`, `nursing pte requirements` → TOFU, đã có ~40 bài
5. **PTE Core (Canada)** — cluster mới, ít đối thủ, đang tăng → ưu tiên cao nhất
6. **Brand & platform** — `pte magic`, `pte mock test online`, `pte practice app` → BOFU, cần bảo vệ

**SEO quyết định:** chọn 3 cluster/tháng. Ưu tiên cluster có (a) impression cao nhưng position 8–20,
(b) trùng với mục tiêu kinh doanh (PTE Core → Canada PR đang là nguồn lead mới),
(c) PTE Magic có dữ liệu độc quyền để viết khác biệt.

**DoD (G2):** `data/clusters.md` + danh sách 3 cluster được chọn, mỗi cluster có 1 pillar và 4–8 bài vệ tinh.

---

## G3 — Content Brief (20 phút/brief)

```bash
/seo-brief "PTE Core writing email template"
```

Brief sinh ra từ `templates/content-brief.md`, bắt buộc đủ 11 mục:

1. **Primary keyword + intent + funnel** (không được mập mờ)
2. **Search demand evidence** — số impression/click từ GSC, hoặc "không có data" (phải nói rõ)
3. **SERP landscape** — ai đang top 5, họ thiếu gì (chỗ PTE Magic chen vào)
4. **Góc nhìn độc quyền bắt buộc** — chọn ≥1: dữ liệu AI scoring thật / template do trainer viết / đề thi mẫu theo format Pearson / trải nghiệm học viên có tên
5. **Outline H2/H3** theo SERP, không theo ý thích
6. **Entity & semantic terms** phải xuất hiện (Pearson, PTE Academic, PTE Core, score band, communicative skills, enabling skills…)
7. **Internal links**: 3 link vào (từ bài nào) + 4 link ra (tới bài nào) — lấy từ `context/internal-links-map.md`
8. **Schema đề xuất**: `Article` + `FAQPage` + `BreadcrumbList` (+ `Course` nếu là trang khoá học)
9. **Title ≤ 60 ký tự / meta description ≤ 155 ký tự** — viết sẵn 3 phương án
10. **Ngưỡng chất lượng**: ≥ 1.200 từ cho informational, ≥ 1 FAQ thật có câu trả lời đầy đủ, có ngày cập nhật, có tên author + profile
11. **Policy pre-check** — brief tự khai: bài này có phải biến thể của bài đã có không? Nếu "gần giống" → dừng, chuyển sang `REFRESH` bài cũ.

**DoD (G3):** brief ≤ 1 trang, EDITOR duyệt, và mục 4 (góc độc quyền) không được để trống.

---

## G4 — Produce & Optimize (90–120 phút/bài)

### G4a. Sản xuất

| Phút | Việc | Ai |
|---|---|---|
| 0–20 | Draft theo outline brief | AGENT (`content-briefer` → `onpage-editor`) |
| 20–50 | **Kiểm chứng mọi số liệu**: format đề, thời gian, thang điểm, lệ phí, yêu cầu visa | **SEO/EDITOR — không delegate** |
| 50–70 | Thêm phần "trải nghiệm thật": lỗi học viên hay mắc, dữ liệu từ platform, ảnh chụp màn hình score report | SEO |
| 70–85 | Meta title/description, heading, alt ảnh, internal link, JSON-LD | AGENT, SEO duyệt |
| 85–105 | Đọc tomột lượt toàn bài, cắt phần AI-văn-mẫu, viết lại đoạn mở đầu bằng ngôn ngữ người thật | **SEO/EDITOR** |
| 105–120 | Chạy on-page score, sửa tới khi ≥ 85/100 | SCRIPT + AGENT |

> Bước 20–50 và 50–70 là **toàn bộ giá trị** của bài viết. Nếu bỏ hai bước đó, bài sẽ rơi
> đúng vào scaled content abuse và Policy Gate sẽ BLOCK ở G4b.

### Quy tắc cứng khi viết cho PTE Magic

- **Không bao giờ khẳng định "đề thi thật"** nếu không phải nội dung Pearson công bố.
  Blog hiện tại viết đúng ("not copied from live tests") — giữ chuẩn này.
- Số liệu về điểm/format phải dẫn nguồn Pearson và ghi ngày kiểm chứng.
- Nội dung visa/định cư/học bổng = **YMYL**. Bắt buộc: author có tên thật + ngày cập nhật
  trong 90 ngày + link nguồn chính phủ (immi.homeaffairs.gov.au, canada.ca, education.govt.nz).
- Tiếng Việt cho người Việt: không dịch word-by-word từ bản EN. Văn phong `context/brand-voice.md`.
- Mỗi bài phải có ≥1 thứ chỉ PTE Magic có: bảng thống kê điểm học viên, template trainer viết,
  hoặc ảnh score report thật.

---

## G4b — Policy Gate (10 phút/bài, **bắt buộc**)

```bash
/seo-policy-check drafts/pte-core-email.md
# hoặc trực tiếp:
python scripts/policy_gate.py --file drafts/pte-core-email.md --corpus published/ --format md
```

Gate kiểm 12 nhóm (chi tiết: `references/google-spam-policies.md`):

| # | Nhóm | Đối chiếu chính sách Google | Mức |
|---|---|---|---|
| 1 | Near-duplicate ≥70% với corpus | Scaled content abuse | BLOCK |
| 2 | Template-shell lặp ≥8 URL, thân khác <30% | Doorway pages | BLOCK |
| 3 | Keyword density >3.5% / heading nhồi >60% | Keyword stuffing | BLOCK |
| 4 | Anchor ra ngoài ≥40% exact-match | Link spam | BLOCK |
| 5 | Link trả tiền thiếu `rel="sponsored"` | Link spam | BLOCK |
| 6 | Text ẩn chứa keyword | Hidden text & link abuse | BLOCK |
| 7 | Redirect theo UA / nội dung khác cho bot | Cloaking, sneaky redirect | BLOCK |
| 8 | YMYL thiếu author/ngày/nguồn | E-E-A-T, helpful content | BLOCK |
| 9 | Nội dung bên thứ ba mượn authority | Site reputation abuse | BLOCK |
| 10 | Domain hết hạn đổi nội dung không liên quan | Expired domain abuse | WARN→BLOCK |
| 11 | Không có value-add so với SERP hiện tại | Helpful content | WARN |
| 12 | AI disclosure & dấu vết biên tập người | AI content guidance | WARN |

**Khi gate trả BLOCK:** không publish, không "sửa cho qua gate". Sửa nội dung thật, rồi chạy lại.
Mọi lần BLOCK/WARN được ghi log vào `reports/policy-log.csv` để nhìn lại xu hướng theo tháng.

**Người ký:** SEO ghi tên + ngày vào cuối bài (`Reviewed by:`). Đây là accountability thật —
thứ Google tìm trong E-E-A-T và cũng là thứ bảo vệ bạn khi làm cho khách.

---

## G5 — Publish & Index (15 phút/bài)

Checklist trước khi bấm publish (agent `seo-reporter` tự sinh từ `templates/publish-checklist.md`):

- [ ] URL đúng chuẩn: lowercase, không dấu tiếng Việt có dấu, không ngày trong slug, ≤ 60 ký tự
- [ ] Bài VI: quyết định đặt ở `/vi/<slug>` hay `.com.vn` — **nhất quán với mô hình đã chốt ở G0**
- [ ] `canonical` self-referencing, absolute
- [ ] `hreflang` reciprocal với tất cả bản dịch + `x-default`
- [ ] `og:` / `twitter:` đủ, ảnh OG 1200×630
- [ ] JSON-LD validate (Rich Results Test) — `Article`, `BreadcrumbList`, `FAQPage` nếu có FAQ
- [ ] Ảnh: WebP/AVIF, `width`/`height` explicit, `w=` trong `/_next/image` khớp kích thước hiển thị (không phải 3840)
- [ ] `lastmod` trong sitemap = ngày sửa nội dung thật, **không phải** thời điểm build
- [ ] Internal link: ≥3 link vào từ bài liên quan, ≥4 link ra, anchor mô tả
- [ ] Author box + ngày publish + ngày updated
- [ ] Policy Gate = `PASS` (hoặc `WARN` đã ghi chú)
- [ ] Mobile test tay trên 3G: trang đọc được trong < 3s
- [ ] Submit URL trong GSC → Request Indexing (tối đa 10 URL/ngày, đừng lạm dụng)

---

## G6 — Measure & Iterate

### Tuần (15 phút, thứ Hai)

```bash
/seo-weekly
```
Output: `reports/ptemagic/<date>-weekly.md` gồm
1. Click / impression / CTR / position trung bình, delta so với tuần trước, tách theo locale
2. Top 5 query tăng, top 5 query giảm
3. **Striking distance**: query ở vị trí 5–15 có impression cao → hành động cụ thể cho từng cái
4. CWV field data: URL nào đang `Poor`
5. 3 việc của tuần này (không hơn)

### Tháng (2h, ngày làm việc đầu tháng)

1. **Content decay**: bài có click giảm ≥30% trong 90 ngày → vào hàng đợi refresh
2. **Cannibalisation**: 2+ URL cùng cluster cùng rank cho 1 query → consolidate/301
3. **Prune**: bài <30 impression/90 ngày, position >60, không có link vào → cân nhắc gộp hoặc xoá
   (xoá phải 301 về bài liên quan gần nhất, không 404 trần)
4. **GEO/AEO**: chạy `/seo-geo` — hỏi ChatGPT/Perplexity/Gemini/AI Overviews 10 prompt mục tiêu
   (trong `context/ai-citation-targets.md`), ghi nhận PTE Magic được cite hay không
5. **Backlink**: kiểm link mới, anchor distribution, toxic; **không** mua link, không PBN
6. Cập nhật `context/` — bộ nhớ phải tươi thì brief tháng sau mới tốt

### KPI quý (đề xuất cho PTE Magic)

| KPI | Cách đo | Ghi chú |
|---|---|---|
| Non-brand click | GSC, filter bỏ query chứa "pte magic" | KPI chính, đừng nhìn tổng click |
| Số URL vào top 10 | GSC position ≤ 10 | ưu tiên cluster PTE Core |
| CWV "Good" | CrUX, % URL pass cả 3 chỉ số mobile | mục tiêu ≥ 75% |
| AI citation rate | % prompt trong `ai-citation-targets.md` có cite PTE Magic | KPI mới, ngày càng quan trọng |
| Đăng ký free từ organic | GA4 event `sign_up` × source organic | nối SEO với doanh thu |
| Số lần Policy Gate BLOCK | `reports/policy-log.csv` | xu hướng giảm = quy trình đang tốt lên |

---

## Ngân sách giờ theo tháng (1 người)

| Hạng mục | Số lần | Giờ/lần | Tổng |
|---|---|---|---|
| Drift check tuần | 4 | 0.25 | 1.0 |
| Weekly report | 4 | 0.25 | 1.0 |
| Monthly review + prune + GEO | 1 | 2.0 | 2.0 |
| Keyword & cluster | 1 | 1.0 | 1.0 |
| Brief | 8 | 0.33 | 2.7 |
| Sản xuất + tối ưu bài | 8 | 1.75 | 14.0 |
| Policy gate | 8 | 0.17 | 1.4 |
| Publish + index | 8 | 0.25 | 2.0 |
| Refresh bài cũ | 4 | 1.0 | 4.0 |
| Technical fix từ action plan | — | — | 6.0 |
| Full audit (chỉ tháng có quý) | 0.33 | 1.5 | 0.5 |
| **Tổng** | | | **~36h/tháng** |

Cùng khối lượng đó làm thuần thủ công: ~85–95h/tháng.

---

## Khi nào KHÔNG dùng quy trình này

- Site đang bị **manual action** trong GSC → dừng mọi thứ, xử lý manual action trước
  (`references/google-spam-policies.md` mục Recovery). Đừng publish thêm content mới.
- Đang trong đợt **core update** rollout → giữ nguyên, không phản ứng; đo lại sau khi rollout xong.
- Trang có lỗi kỹ thuật Critical chưa sửa (index/canonical/redirect sai) → viết content lúc này là lãng phí.

---

## Nhật ký thay đổi quy trình

| Ngày | Thay đổi | Lý do |
|---|---|---|
| 2026-09-29 | v1.0 — ban hành | Research 8 repo GitHub + audit thật ptemagic.com |
