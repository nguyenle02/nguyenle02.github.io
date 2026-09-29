# Research: SEO Skills & Agents trên GitHub

**Ngày research:** 2026-09-29 · **Người thực hiện:** agent, cho Lê Duy Nguyên
**Mục tiêu:** tìm bộ skill/agent SEO tốt nhất trên GitHub, rồi thiết kế quy trình cho `ptemagic.com`
mà không vi phạm chính sách Google.

---

## 1. Bối cảnh: "Agent Skills" là gì và vì sao SEO là mảng bùng nổ

Một *skill* là một thư mục chứa file `SKILL.md` mà agent nạp theo yêu cầu (on-demand).
Anthropic công bố format tháng 10/2025 và mở thành open standard tháng 12/2025; hiện chạy được trên
Claude Code, Claude.ai, Claude API, OpenAI Codex, Cursor, Gemini CLI, Antigravity, OpenClaw và Windsurf.
SEO là một trong những mảng đầu tiên format này bùng nổ, với các pack hàng chục nghìn sao.
Nguồn: [RankSpotAI/awesome-seo-agent-skills](https://github.com/RankSpotAI/awesome-seo-agent-skills) ([1](https://github.com/RankSpotAI/awesome-seo-agent-skills)).

Điều này quan trọng với bạn vì: **skill viết một lần, chạy trên nhiều tool**. Nếu khách hàng của bạn
dùng Cursor còn bạn dùng Claude Code, cùng một bộ skill vẫn dùng được.

---

## 2. Các repo đã khảo sát (số liệu lấy trực tiếp từ GitHub API ngày 2026-09-29)

| Repo | Stars | License | Push cuối | Phạm vi | Đã clone & đọc |
|---|---|---|---|---|---|
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | 51.823 | MIT | 2026-09-05 | Marketing tổng hợp: CRO, copywriting, SEO, analytics, growth | ✅ |
| [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) | 17.899 | MIT | 2026-09-28 | 26 sub-skill + 19 sub-agent SEO chuyên sâu, 9 extension (DataForSEO, Ahrefs, Firecrawl, Matomo…) | ✅ |
| [zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) | 10.875 | MIT | 2026-09-28 | GEO-first: citability, AI crawler, llms.txt, brand mention | ✅ |
| [TheCraigHewitt/seomachine](https://github.com/TheCraigHewitt/seomachine) | 7.468 | MIT | 2026-08-05 | Workspace sản xuất content dài: 26 command + tầng `context/` | ✅ |
| [Bhanunamikaze/Agentic-SEO-Skill](https://github.com/Bhanunamikaze/Agentic-SEO-Skill) | 941 | MIT | 2026-07-23 | 16 sub-skill, 10 agent, 88 script "evidence collector", đa runtime | ✅ |
| [seranking/seo-skills](https://github.com/seranking/seo-skills) | 151 | MIT | 2026-06-25 | Skill chính hãng của SE Ranking (MCP server) | ✅ |
| [lionkiii/claude-seo-skills](https://github.com/lionkiii/claude-seo-skills) | 21 | MIT | 2026-06-11 | 42 command: Ahrefs backlink, GSC, SERP, brief, schema | ✅ |
| [metawhisp/amazing-seo-skill](https://github.com/metawhisp/amazing-seo-skill) | 11 | Apache-2.0 | 2026-08-25 | SEO+AEO+GEO, CWV bằng Playwright, theo dõi citation LLM thật | ⚠️ đọc qua search |

Bảng xếp hạng đối chiếu độc lập: [Top 10 SEO Skills on GitHub, Ranked by Stars (2026)](https://thegeocommunity.com/blogs/generative-engine-optimization/top-10-seo-skills-github-stars/) ([9](https://thegeocommunity.com/blogs/generative-engine-optimization/top-10-seo-skills-github-stars/)).
Danh mục sub-agent: [VoltAgent/awesome-claude-code-subagents → seo-specialist](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/categories/07-specialized-domains/seo-specialist.md) ([5](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/categories/07-specialized-domains/seo-specialist.md)).

---

## 3. Mổ xẻ: cái gì hay, cái gì không

### 3.1 AgriciDaniel/claude-seo — chuẩn mực về kiến trúc

**Học được:**
- **Hub-and-spoke.** `skills/seo/SKILL.md` của claude-seo là hub liệt kê 26 lệnh, mỗi lệnh trỏ tới một leaf skill.
  Hub chỉ dùng "khi domain rõ nhưng workflow chưa rõ" — tránh nạp nhầm ngữ cảnh.
- **Script có launcher thống nhất.** Mọi skill gọi script qua một đường dẫn canonical
  (`${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo run <script.py>`), và tài liệu ghi rõ
  *"Never invoke bundled scripts with a bare Python interpreter."* → không vỡ khi cài ở chỗ khác.
- **Agent khai báo `maxTurns` và `tools` giới hạn.** Ví dụ `seo-technical`: `model: sonnet`,
  `maxTurns: 45`, `tools: Read, Bash, Write, Glob, Grep`. Giới hạn tool = giới hạn rủi ro.
- **Trọng số điểm công khai và được đồng bộ bằng CI.** Có hẳn commit
  *"Fix scoring weight mismatch: seo-audit/SKILL.md now matches seo/SKILL.md (Technical 22%, Content 23%, AI Search 10% — was 25/25/5)"* —
  tức là họ test cả sự nhất quán tài liệu. Đáng học.
- **Cập nhật chuẩn kỹ thuật kịp thời:** ghi rõ INP thay FID từ 12/03/2024, FID bị bỏ khỏi
  CrUX/PSI ngày 09/09/2024, và *"Never reference FID in any output."*
- **Có extension tách rời** (Ahrefs, DataForSEO, Firecrawl, Matomo, Bing Webmaster, SERanking,
  unlighthouse) → không ép người dùng trả phí.

**Không phù hợp với bạn:**
- Quá lớn (26 skill + 19 agent). Nạp hết vào một phiên làm loãng ngữ cảnh và tốn token.
- Không có tầng **context riêng cho doanh nghiệp** — nó generic.
- Không có **policy gate** chặn trước khi publish. Nó tối ưu, không từ chối.

### 3.2 TheCraigHewitt/seomachine — ý tưởng đáng giá nhất: tầng `context/`

Repo này có thư mục `context/` với: `brand-voice.md`, `target-keywords.md`, `internal-links-map.md`,
`seo-guidelines.md`, `style-guide.md`, `competitor-analysis.md`, `ai-citation-targets.md`,
`features.md`, `cro-best-practices.md`, `writing-examples.md`, `reddit-strategy.md`.

Đây là **bộ nhớ dài hạn của dự án**. Mọi command đều đọc nó trước khi sinh nội dung.
Kết quả: brief lần thứ 20 tốt như brief lần thứ 1, và không phải nhắc lại "brand tôi là gì" mỗi lần.

Kiến trúc **Command → Agent** cũng rất rõ: *"`/write` sinh bài vào `drafts/`, tự động kích hoạt
SEO Optimizer, Meta Creator, Internal Linker, Keyword Mapper"*. Người dùng chỉ gõ 1 lệnh,
4 agent chạy nối tiếp.

**Đã áp dụng 100% vào bộ của bạn:** thư mục `context/` (rút còn 6 file thiết yếu cho PTE Magic)
và mô hình command-orchestrates-agents.

**Không phù hợp:** repo tập trung vào content/blog, yếu về technical audit và i18n.
Có sẵn script DataForSEO nhưng buộc phải có key.

### 3.3 Bhanunamikaze/Agentic-SEO-Skill — chuẩn mực về đa runtime & "evidence collector"

**Học được:**
- **Bảng tương thích runtime rất cụ thể** (Claude Code, Codex CLI, Antigravity, Claude Cowork,
  Cursor `.cursor/rules/*.mdc`, Windsurf, Continue.dev, GitHub Copilot
  `.github/copilot-instructions.md`, Cline `.clinerules`) — mỗi tool một đường dẫn cài riêng.
  `install.sh --target <x>` xử lý hết.
- **Triết lý "LLM-first, script as evidence collector"**: 88 script không phải để ra quyết định,
  mà để *thu thập bằng chứng* cho LLM lập luận. Script đưa ra "reproducible verdicts",
  LLM đưa ra phán đoán và ưu tiên.
- **Có `resources/config/scoring.json`** — điểm số tách khỏi code, chỉnh được không cần sửa script.

**Đã áp dụng:** `install.sh` đa target, và nguyên tắc "script đo / agent luận" (mục 0 của SOP).

**Không phù hợp:** 88 script là quá nhiều để bảo trì; nhiều script trùng chức năng.
Bộ của bạn rút còn 6 script có mục đích rõ ràng.

### 3.4 zubair-trabzada/geo-seo-claude — đúng xu hướng 2026

GEO-first: tối ưu để **được trích dẫn trong câu trả lời AI** thay vì chỉ xếp hạng.
Workflow: citability → AI crawler access → llms.txt → brand mentions → structured data →
technical SEO → content quality → reporting → compare over time.

**Vì sao quan trọng với PTE Magic:** từ 15/05/2026 Google viết lại định nghĩa spam,
áp dụng cả cho việc *"manipulate generative AI responses in Google Search"* —
tức AI Overviews và AI Mode ([10](https://modo25.com/blog/seo/googles-august-spam-update-how-to-avoid-scaled-content-abuse/)).
Học sinh hỏi ChatGPT "PTE Core khác PTE Academic thế nào" ngày càng nhiều.
Nếu PTE Magic không được cite, mất một kênh acquisition.

**Đã áp dụng:** skill `seo-geo-visibility`, agent `geo-analyst`, `context/ai-citation-targets.md`,
và mục kiểm tra AI crawler trong robots.txt.

**Lưu ý khi đánh giá:** README repo này có câu *"If you want learn how to sell this to real
businesses, check out the skool community"* — tức là có phễu bán hàng phía sau.
Skill vẫn MIT và dùng được, nhưng đừng xem nó là nguồn trung lập.

### 3.5 metawhisp/amazing-seo-skill — ý tưởng hay, độ chín thấp

Mô hình dữ liệu 4 tầng rất đáng học:
**L0** LLM reasoning · **L1** ~29 Python checker deterministic · **L2** local CLI engine
(CWV bằng browser thật, audit 251 luật) · **L3** external API (Ahrefs, GSC) ·
**L4** multi-LLM ensemble test citation thật trên ChatGPT/Perplexity/Claude/Grok.

Điểm khác biệt họ nêu: *"Standard SEO tools tell you a site is 92/100 while ChatGPT, Perplexity,
Claude, and Grok don't cite it once"* ([8](https://github.com/metawhisp/amazing-seo-skill)).

**Nhưng:** chỉ 11 sao, đẩy code 2026-08-25. Rủi ro bị bỏ bảo trì cao. Mình lấy **ý tưởng phân tầng**,
không lấy code.

### 3.6 coreyhaines31/marketingskills — nhiều sao nhất, nhưng không phải SEO

51.823 sao vì nó là pack marketing tổng (CRO, copywriting, ads, analytics, growth engineering),
không phải công cụ SEO chuyên sâu. SEO chỉ là một "lane" trong đó.
Nguồn đối chiếu khuyên rõ: dùng khi cần *shared marketing context*, tránh dùng làm mặc định
khi bạn chỉ cần một technical audit có kiểm soát ([9](https://thegeocommunity.com/blogs/generative-engine-optimization/top-10-seo-skills-github-stars/)).
→ **Loại** khỏi stack của bạn (bạn là SEO specialist, không cần CRO/copywriting/ads).

### 3.7 seranking/seo-skills & lionkiii/claude-seo-skills — phụ thuộc vendor

- `seranking/seo-skills` là skill chính hãng cho SE Ranking MCP server. Chất lượng tốt
  (content brief, AI search share of voice, backlink gap, keyword cluster, schema, sitemap, GEO),
  nhưng **cần tài khoản SE Ranking**. Họ có ghi chú mọi API call đều được document nên có thể adapt.
- `lionkiii/claude-seo-skills` (21 sao, 42 command) phụ thuộc Ahrefs + GSC.

→ **Không cài**, nhưng mình mượn cấu trúc output của content brief và cách họ trình bày backlink gap.

---

## 4. Kết luận research: không có repo nào dùng ngay được cho ptemagic.com

Cả 8 repo đều là **generic**. Bốn khoảng trống mà không repo nào lấp:

| Khoảng trống | Vì sao nghiêm trọng với PTE Magic |
|---|---|
| **Không có policy gate chặn trước publish** | Bạn làm freelancer, làm cho nhiều khách. Một bài bị phạt là mất uy tín cả hợp đồng. Mọi repo chỉ *tối ưu*, không *từ chối*. |
| **Không hiểu kiến trúc i18n phức tạp** | PTE Magic có `.com` (EN) + `.com/vi` + bài VI ở root `.com` + `.com.vn` + `.com.au`. Đây là bài toán hreflang/duplicate cross-domain mà skill generic bỏ qua. |
| **Không có ngữ cảnh ngành PTE/du học** | Không repo nào biết "PTE Core" là gì, thang điểm Pearson ra sao, hay nội dung visa là YMYL. |
| **Không gắn SEO với business metric** | KPI của PTE Magic là `sign_up` free, không phải traffic. |

**Quyết định:** không cài nguyên xi repo nào. Viết bộ riêng ~10 skill + 9 agent,
kế thừa 5 ý tưởng kiến trúc đã kiểm chứng:

| Ý tưởng | Lấy từ | Áp dụng vào |
|---|---|---|
| Hub-and-spoke SKILL.md, script qua launcher thống nhất | claude-seo | `skills/seo-orchestrator/`, `scripts/` |
| Tầng `context/` làm bộ nhớ dự án | seomachine | `context/` (6 file) |
| Command → nhiều agent chạy song song | seomachine + claude-seo | `commands/`, `agents/` |
| Script = evidence collector, LLM = người lập luận | Agentic-SEO-Skill | nguyên tắc 1 trong SOP |
| Phân tầng dữ liệu L0–L4 | amazing-seo-skill | `scripts/` degrade theo key có sẵn |
| GEO/AEO + AI crawler + llms.txt | geo-seo-claude | `skills/seo-geo-visibility/` |
| `install.sh` đa runtime | Agentic-SEO-Skill | `install.sh` (7 target) |

**Mới, không có ở repo nào:** Policy Gate map 1-1 với 16 nhóm Google Spam Policies bản 15/05/2026,
và xử lý rủi ro **PBN** một cách thẳng thắn (xem `skills/seo-offpage-compliant/`).

---

## 5. Tình trạng chính sách Google (cập nhật đến 09/2026) — nền tảng của Policy Gate

Đây là phần research quan trọng nhất, vì nó quyết định *cái gì không được làm*.

### 5.1 Mốc thời gian

| Ngày | Sự kiện | Hệ quả |
|---|---|---|
| 03/2024 | Core update + spam policies mới | Thêm 3 nhóm: **scaled content abuse**, **site reputation abuse**, **expired domain abuse**. Đổi tên "spammy auto-generated content" → "scaled content abuse", cố ý bỏ cách hiểu "AI content là spam" ([8](https://www.seo-kreativ.de/en/blog/google-march-2026-spam-update/)) |
| 03/2024 | Helpful content signals vào core ranking | Chất lượng bị đánh giá **liên tục**, không còn theo đợt update ([2](https://www.layer3labs.io/guides/google-ai-content-guidelines)) |
| 15/05/2026 | **Google viết lại dòng mở đầu spam policies** | Spam giờ gồm cả *"attempting to manipulate generative AI responses in Google Search"* → chính sách áp dụng cho AI Overviews và AI Mode, không chỉ 10 link xanh ([10](https://modo25.com/blog/seo/googles-august-spam-update-how-to-avoid-scaled-content-abuse/)) |
| 24–25/03/2026 | Spam update nhanh nhất lịch sử (<20h) | Không có policy mới; SpamBrain nhắm cloaking, doorway, hidden text, mass-generated content. **Không** nhắm link spam và site reputation abuse ([8](https://www.seo-kreativ.de/en/blog/google-march-2026-spam-update/)) |
| 24/06 – đầu 07/2026 | June 2026 spam update | Google xác nhận **loại trừ** link spam và site reputation abuse → trọng tâm là content-level: scaled content abuse, cloaking, keyword stuffing ([4](https://cliquestudios.com/university/resources/google-june-2026-spam-update)) |
| 18–21/08/2026 | August 2026 spam update | Lần thứ 2 chạy sau mốc 15/05. *"What has changed is that 'rank' now includes 'get cited'"* — nhiều trang dựng ra để được đưa vào AI Overview mà không có lý do cho người đọc = scaled content abuse ([10](https://modo25.com/blog/seo/googles-august-spam-update-how-to-avoid-scaled-content-abuse/)) |

Tài liệu spam policies cập nhật gần nhất là **15/05/2026**, gồm 16 nhóm
([3](https://www.seosavages.com/blog/google-spam-policies-seo/)).

### 5.2 Ranh giới scaled content abuse — thứ quyết định cách bạn dùng AI

Chính sách **cố ý origin-blind**: người viết hay AI viết đều bị xét cùng một luật.
Từ khoá là **"primarily"** — nếu trang tồn tại trước hết để bắt query, và chỉ tình cờ giúp được ai đó,
thì nó vẫn có rủi ro, bất kể bạn viết 3 trang hay 3.000 trang ([9](https://quillly.com/blogs/scaled-content-abuse)).

**Không có ngưỡng số trang cố định.** Google chưa từng công bố page limit hay AI-percentage cap.
Mười trang gần giống nhau, keyword-first có thể vi phạm; 500 trang thật sự hữu ích thì an toàn.
Tiêu chí là định tính: *lượng của bạn có đang chạy nhanh hơn giá trị bạn thêm được mỗi trang không?*
([9](https://quillly.com/blogs/scaled-content-abuse))

Số liệu thực tế 2026: site 50–100 bài AI **có biên tập** tăng traffic 30–80%;
site ≥1.000 trang AI **không biên tập** giảm 40–90% ([9](https://quillly.com/blogs/scaled-content-abuse)).
Một site 1.800 bài auto-generated mất phần lớn traffic Google trong 9 ngày ([9](https://quillly.com/blogs/scaled-content-abuse)).

| Scaled content abuse | AI-assisted hợp lệ |
|---|---|
| Trang spin để bắt biến thể keyword | Trang dựng để trả lời một câu hỏi thật |
| Publish hàng loạt, không ai review | Có người biên tập, fact-check, định hình |
| Đổi chủ đề nhưng giữ nguyên cái vỏ | Có dữ liệu gốc, ví dụ, trải nghiệm trực tiếp |
| Không author, không accountability | Author thật, quyền biên tập rõ ràng |
| Tồn tại để bắt traffic | Tồn tại vì hữu ích; rank là hệ quả |

*(bảng tổng hợp từ [5](https://postforsuccess.com/scaled-content-abuse))*

**→ Đây chính là lý do SOP của bạn có bước 20–70 phút "người làm" không được delegate,
và Policy Gate check #1 (near-duplicate) + #2 (template-shell).**

### 5.3 Về PBN — phải nói thẳng với bạn

Profile của bạn ghi "Xây dựng >250 website PBN" và "Dùng PBN & xây dựng hệ thống Backlink 1-2".
Chính sách Google liệt kê rõ trong nhóm **Link spam**: *"Link farms and private blog networks (PBNs)"*,
cùng với mua/bán link truyền PageRank, link exchange quá mức, guest post hàng loạt với anchor
keyword-rich, và chương trình build link tự động ([1](https://metaflow.life/blog/google-search-essentials-spam-policies-compliance-guide)).

Hai điểm cần biết để tư vấn khách cho đúng:

1. **Các spam update 03/2026 và 06/2026 đều được Google xác nhận là KHÔNG nhắm link spam**
   ([4](https://cliquestudios.com/university/resources/google-june-2026-spam-update),
   [8](https://www.seo-kreativ.de/en/blog/google-march-2026-spam-update/)).
   Nhiều người đọc nhầm thành "PBN an toàn trở lại". Không phải — link spam vẫn là spam policy,
   vẫn bị xử lý bởi hệ thống thường trực, và disavow **không** giúp recovery cho các update này
   ([4](https://cliquestudios.com/university/resources/google-june-2026-spam-update)).
2. **SpamBrain phân tích network-level signals** và ngày càng lộ ra các nguồn link nguỵ trang
   ([8](https://www.seo-kreativ.de/en/blog/google-march-2026-spam-update/)). Rủi ro của PBN là rủi ro
   *mạng lưới* — một site trong hệ bị phát hiện có thể kéo theo cả cụm, tức là kéo theo nhiều khách
   của bạn cùng lúc.

**Quan điểm của bộ này:** không tự động hoá PBN, không có skill nào build PBN.
Thay bằng `skills/seo-offpage-compliant/` — digital PR dựa trên dữ liệu độc quyền
(PTE Magic có dữ liệu chấm điểm của 400.000+ học viên: đây là asset link-earning thật sự),
unlinked mention reclamation, guest post có liên quan thật về du học/định cư,
và citation từ đối tác chính thức (Pearson Elite Partner 2025, Vietnam–Australia EdTech Alliance,
Bett Asia — những thứ PTE Magic **đã có** và chưa khai thác cho SEO).

Đây không phải vấn đề đạo đức trừu tượng: nó là vấn đề **rủi ro kinh doanh** của bạn.
Một bộ quy trình mà bạn dám đưa cho khách ký tên chịu trách nhiệm thì phải sạch.

### 5.4 Site reputation abuse & expired domain abuse

- **Site reputation abuse:** host site đăng nội dung bên thứ ba chủ yếu để tận dụng ranking signal
  của chính domain mình. Ví dụ kinh điển: trang tin tức/giáo dục mở "chuyên mục sponsored" chứa
  coupon, vay nặng lãi, gambling, affiliate. Chính sách này **không cấm** nội dung bên thứ ba —
  syndicated wire content, guest column, sponsored có disclosure đều ổn. Cái bị nhắm là
  *arrangement mà nội dung nằm trên domain đó chỉ vì sức mạnh ranking của domain*
  ([6](https://coozmoo.com/blogs/seo/google-spam-policies-guide), [7](https://viralgroww.com/blogs/google-june-2026-spam-update/)).
  **Liên hệ PTE Magic:** nếu có kế hoạch cho đối tác/trung tâm du học đăng bài trên `/blogs`
  → phải có editorial review, nội dung phải liên quan PTE/du học thật, và disclose rõ.
- **Expired domain abuse:** mua domain có reputation cũ (site chính phủ, nonprofit, trường học)
  rồi đổi sang nội dung thương mại không liên quan để dựa authority cũ. Mua domain hết hạn thì ổn
  **nếu** nội dung mới liên quan niche của domain ([6](https://coozmoo.com/blogs/seo/google-spam-policies-guide)).
  **Liên hệ:** bạn có kinh nghiệm tư vấn domain cho khách → đây là checklist phải hỏi trước khi mua.

### 5.5 Các nhóm còn lại cần check tự động

Cloaking · sneaky redirects · doorway pages · hidden text & link abuse · keyword stuffing ·
thin affiliation · scraped content · hacked content · automatically generated traffic.
Định nghĩa và cách detect: `references/google-spam-policies.md`.

Lưu ý về **hidden text**: accordion, tooltip, slider toggle vì lý do usability thì **không** bị xem là vi phạm.
Vi phạm là khi nội dung bị ẩn *chỉ để thao túng ranking*
([6](https://coozmoo.com/blogs/seo/google-spam-policies-guide)).
→ Policy Gate chỉ flag khi text ẩn **chứa keyword** và không có aria/interaction thật.
Điều này quan trọng vì PTE Magic đang có khối testimonial lặp 2 lần trong DOM (carousel
render cả mobile + desktop): không phải spam, nhưng là vấn đề hiệu năng và cần sửa.

---

## 6. Nếu bạn muốn tự cài thêm repo gốc để so sánh

```bash
# Repo toàn diện nhất (26 skill + 19 agent) — MIT
git clone https://github.com/AgriciDaniel/claude-seo ~/.claude/skills/claude-seo

# GEO-first — MIT
git clone https://github.com/zubair-trabzada/geo-seo-claude ~/.claude/skills/geo-seo-claude

# Đa runtime, 88 script evidence collector — MIT
git clone https://github.com/Bhanunamikaze/Agentic-SEO-Skill.git /tmp/agentic-seo
bash /tmp/agentic-seo/install.sh --target claude

# Content workspace với tầng context/ — MIT
git clone https://github.com/TheCraigHewitt/seomachine /tmp/seomachine
```

Khuyến nghị: cài `claude-seo` vào một project *thử nghiệm* để xem cách nó chấm điểm,
rồi so với report của bộ này trên cùng một URL. Chỗ nào nó tìm ra mà bộ này bỏ sót →
bổ sung check vào `scripts/seo_audit.py`. Đó là cách giữ bộ này sống.

**Đừng** cài 3–4 pack cùng lúc vào một project: description của các SKILL.md sẽ chồng lấn,
agent nạp sai skill, và bạn không biết output đến từ đâu.

---

## 7. Nguồn tham khảo

**GitHub repos:** [1](https://github.com/RankSpotAI/awesome-seo-agent-skills) [2](https://github.com/Bhanunamikaze/Agentic-SEO-Skill) [3](https://github.com/VoltAgent/awesome-agent-skills) [5](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/categories/07-specialized-domains/seo-specialist.md) [8](https://github.com/metawhisp/amazing-seo-skill)

**Phân tích & chính sách:** [9](https://thegeocommunity.com/blogs/generative-engine-optimization/top-10-seo-skills-github-stars/) ·
[Google Spam Policies 2026](https://www.seosavages.com/blog/google-spam-policies-seo/) ([3](https://www.seosavages.com/blog/google-spam-policies-seo/)) ·
[AI Content Guidelines](https://www.layer3labs.io/guides/google-ai-content-guidelines) ([2](https://www.layer3labs.io/guides/google-ai-content-guidelines)) ·
[June 2026 Spam Update](https://cliquestudios.com/university/resources/google-june-2026-spam-update) ([4](https://cliquestudios.com/university/resources/google-june-2026-spam-update)) ·
[Scaled Content Abuse](https://postforsuccess.com/scaled-content-abuse) ([5](https://postforsuccess.com/scaled-content-abuse)) ·
[Spam Policies Explained](https://coozmoo.com/blogs/seo/google-spam-policies-guide) ([6](https://coozmoo.com/blogs/seo/google-spam-policies-guide)) ·
[June 2026 Update](https://viralgroww.com/blogs/google-june-2026-spam-update/) ([7](https://viralgroww.com/blogs/google-june-2026-spam-update/)) ·
[March 2026 Spam Update](https://www.seo-kreativ.de/en/blog/google-march-2026-spam-update/) ([8](https://www.seo-kreativ.de/en/blog/google-march-2026-spam-update/)) ·
[Scaled Content Abuse explainer](https://quillly.com/blogs/scaled-content-abuse) ([9](https://quillly.com/blogs/scaled-content-abuse)) ·
[August 2026 Spam Update](https://modo25.com/blog/seo/googles-august-spam-update-how-to-avoid-scaled-content-abuse/) ([10](https://modo25.com/blog/seo/googles-august-spam-update-how-to-avoid-scaled-content-abuse/)) ·
[Search Essentials Compliance Guide](https://metaflow.life/blog/google-search-essentials-spam-policies-compliance-guide) ([1](https://metaflow.life/blog/google-search-essentials-spam-policies-compliance-guide))

> Nguồn chính sách nên được kiểm chứng lại trực tiếp tại
> <https://developers.google.com/search/docs/essentials/spam-policies> trước khi dùng cho khách hàng.
> Các link trên là phân tích của bên thứ ba, được đối chiếu chéo nhiều nguồn, không phải văn bản gốc của Google.
