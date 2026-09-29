# PTE Magic SEO Operating System

**Quy trình SEO chạy bằng Agent Skills — tối ưu thời gian, giữ chất lượng, không vi phạm chính sách Google.**

Bộ này được research từ 8 repo SEO agent/skill hàng đầu trên GitHub (tổng ~90.000 stars) rồi
viết lại riêng cho `ptemagic.com`. Xem [`RESEARCH-GITHUB-SEO-AGENTS.md`](RESEARCH-GITHUB-SEO-AGENTS.md)
để biết cái nào được lấy ý tưởng, cái nào bị loại và vì sao.

---

## 1. Nó giải quyết vấn đề gì

| Vấn đề cũ | Cách bộ này xử lý |
|---|---|
| Audit thủ công 1 site mất 1–2 ngày | `scripts/seo_audit.py` chạy 40+ check trong ~2 phút, xuất Markdown + JSON |
| Mỗi bài viết bắt đầu từ trang trắng | `context/` là "bộ nhớ" (brand voice, keyword map, internal link map) → brief sinh ra trong 15 phút |
| Không biết bài nào sắp rớt hạng | `scripts/gsc_pull.py` tự tìm "striking distance" (top 5–20) và content decay |
| Rủi ro bị Google phạt vì content AI hàng loạt | **Policy Gate** (`scripts/policy_gate.py`) chặn trước khi publish — xem mục 5 |
| Làm lại audit từ đầu mỗi tháng | `scripts/drift.py` lưu baseline, tháng sau chỉ diff |
| Site đa ngôn ngữ (.com / .com/vi / .com.vn / .com.au) rối hreflang | Skill `seo-i18n-hreflang` + check hreflang reciprocal trong audit |

**Kết quả thời gian dự kiến** (đo trên quy trình 1 người):

| Việc | Thủ công | Với bộ này | Tiết kiệm |
|---|---|---|---|
| Full technical audit | 8–12h | 1.5h (script 2ph + đọc & quyết định 1.5h) | ~85% |
| Keyword research + cluster 1 chủ đề | 4h | 1h | ~75% |
| 1 content brief chuẩn | 1.5h | 20ph | ~78% |
| 1 bài 1.500 từ (draft → sẵn sàng publish) | 6h | 2.5h (AI draft + người biên tập thật) | ~58% |
| Báo cáo tuần | 2h | 15ph | ~87% |
| **Tổng/tháng (8 bài + audit + report)** | **~90h** | **~38h** | **~58%** |

> Phần "người" không bị cắt: biên tập, kiểm chứng số liệu PTE, thêm trải nghiệm thật.
> Đó chính là thứ Google trả tiền — xem mục 5.

---

## 2. Cài đặt (5 phút)

```bash
cd seo-agents
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
cp .env.example .env          # điền key (không bắt buộc, script tự degrade)
bash install.sh --target claude --project-dir /path/to/ptemagic-repo
```

`install.sh` hỗ trợ nhiều runtime — nó copy `skills/` `agents/` `commands/` vào đúng chỗ:

| Runtime | Lệnh | Nơi ghi vào |
|---|---|---|
| Claude Code / Claude Cowork | `--target claude` | `<project>/.claude/{skills,agents,commands}` |
| Claude Code (toàn máy) | `--target global` | `~/.claude/{skills,agents,commands}` |
| OpenAI Codex CLI | `--target codex` | `~/.codex/skills` + `AGENTS.md` |
| Cursor | `--target cursor` | `<project>/.cursor/rules/seo.mdc` + `.cursor/skills/` |
| Windsurf | `--target windsurf` | `<project>/.windsurf/rules/seo.md` |
| GitHub Copilot | `--target copilot` | `<project>/.github/copilot-instructions.md` |
| Tất cả | `--target all` | |

Không dùng AI coding tool nào? Vẫn dùng được: `QUY-TRINH-SEO-PTEMAGIC.md` là SOP người-đọc-được,
và mọi script trong `scripts/` chạy standalone bằng CLI.

### Biến môi trường (tất cả đều optional)

| Biến | Dùng cho | Không có thì sao |
|---|---|---|
| `GOOGLE_APPLICATION_CREDENTIALS` | Search Console, GA4 | bỏ qua phần GSC, vẫn audit được HTML |
| `GSC_SITE_URL` | property GSC (vd `sc-domain:ptemagic.com`) | dùng default trong `config/ptemagic.yaml` |
| `PSI_API_KEY` | PageSpeed Insights / CrUX | bị quota ẩn danh rất thấp → nên có (free) |
| `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD` | SERP API, keyword volume | dùng GSC + CSV export từ Ahrefs thay thế |
| `AHREFS_API_TOKEN` | backlink audit | export CSV tay rồi đưa vào `data/` |

---

## 3. Cấu trúc

```
seo-agents/
├── QUY-TRINH-SEO-PTEMAGIC.md      ← SOP 7 giai đoạn + time budget + Definition of Done
├── RESEARCH-GITHUB-SEO-AGENTS.md  ← báo cáo research GitHub (có link nguồn)
├── install.sh                     ← cài đa runtime
├── config/ptemagic.yaml           ← hồ sơ site: domain, locale, đối thủ, seed keyword
├── context/                       ← "bộ nhớ" nạp vào mọi agent (pattern của seomachine)
│   ├── brand-voice.md             ├── target-keywords.md
│   ├── internal-links-map.md      ├── competitor-analysis.md
│   ├── seo-guidelines.md          └── ai-citation-targets.md
├── skills/                        ← 11 SKILL.md (kiến thức + quy trình, agent tự nạp)
├── agents/                        ← 11 sub-agent (vai trò chuyên biệt, chạy song song)
├── commands/                      ← 6 slash command (điểm vào cho người dùng)
├── scripts/                       ← code deterministic (kết quả tái lập được, không do LLM đoán)
├── references/                    ← chính sách Google, ngưỡng CWV, checklist E-E-A-T
├── templates/                     ← audit report, brief, action plan, weekly report
├── reports/ptemagic/              ← output thật, có ngày tháng
└── data/                          ← CSV export (GSC, Ahrefs) — gitignored
```

**Nguyên tắc thiết kế quan trọng nhất:** mọi thứ *đo được* thì để Python làm, mọi thứ *cần phán đoán*
thì để agent làm, mọi thứ *rủi ro chính sách* thì phải qua Policy Gate. LLM không được tự bịa số liệu
audit — nó chỉ được đọc JSON do script sinh ra.

---

## 4. Dùng hàng ngày

```bash
# Audit toàn site (lần đầu + mỗi quý)
/seo-audit https://ptemagic.com

# Audit 1 URL sắp publish
/seo-page https://ptemagic.com/pte-essay-topics

# Sinh brief cho chủ đề mới
/seo-brief "PTE Core writing email template"

# Kiểm tra chính sách Google TRƯỚC khi publish (bắt buộc)
/seo-policy-check drafts/pte-core-email.md

# Báo cáo tuần
/seo-weekly

# So với baseline tháng trước
/seo-drift
```

Chạy script trực tiếp không cần agent:

```bash
python scripts/seo_audit.py --site https://ptemagic.com --max-urls 300 --out reports/ptemagic/
python scripts/gsc_pull.py --days 90 --out data/gsc-90d.csv
python scripts/cluster_keywords.py --in data/gsc-90d.csv --out data/clusters.md
python scripts/policy_gate.py --file drafts/bai-viet.md --corpus published/
python scripts/drift.py baseline --site https://ptemagic.com
python scripts/drift.py compare  --site https://ptemagic.com
```

---

## 5. Policy Gate — vì sao nó nằm giữa quy trình

Đây là phần khác biệt nhất so với các repo GitHub mình research: **đa số skill chỉ tối ưu, rất ít skill chặn.**

`scripts/policy_gate.py` + agent `policy-reviewer` kiểm 12 nhóm rủi ro, map 1-1 với
Google Spam Policies (cập nhật 15/05/2026 — chính sách spam giờ áp dụng cả cho
AI Overviews và AI Mode, không chỉ 10 link xanh). Chi tiết đầy đủ:
[`references/google-spam-policies.md`](references/google-spam-policies.md).

Ba mức phán quyết:

- **`PASS`** — publish được
- **`WARN`** — publish được nhưng phải ghi chú lý do vào báo cáo
- **`BLOCK`** — không publish. Sửa rồi chạy lại.

Mặc định `BLOCK` khi gặp:

1. Trang mới giống ≥ 70% (Jaccard trên 5-gram) với trang đã có trong corpus → *scaled content abuse*
2. Cùng một "vỏ template" lặp cho ≥ 8 URL mà phần thân khác nhau < 30% → *doorway pages*
3. Mật độ exact-match keyword > 3.5% hoặc keyword xuất hiện trong > 60% heading → *keyword stuffing*
4. Anchor text ra ngoài có ≥ 40% là exact-match commercial keyword → *link spam*
5. Link trả tiền/tài trợ không có `rel="sponsored"` → *link spam*
6. Có text ẩn (màu trùng nền, `font-size:0`, `clip-path`, off-screen) chứa keyword → *hidden text*
7. Redirect theo user-agent / Googlebot thấy nội dung khác người dùng → *cloaking*
8. Không có author + không có ngày + không có nguồn trích dẫn, mà nội dung thuộc nhóm YMYL
   (visa, định cư, tài chính du học) → *thiếu E-E-A-T*
9. Content bên thứ ba đặt trên domain PTE Magic để mượn authority mà không liên quan PTE/du học
   → *site reputation abuse*
10. Mua domain hết hạn có reputation cũ rồi đổi sang nội dung không liên quan → *expired domain abuse*

### Về PBN — nói thẳng

Kinh nghiệm của bạn là xây PBN (250+ site). **PBN là link spam theo chính sách Google hiện hành**
và SpamBrain ngày càng phát hiện được network-level signals. Bộ này **không** có skill nào tự động
hoá PBN, và Policy Gate sẽ `BLOCK` anchor text/link pattern dạng đó.

Thay vào đó `skills/seo-offpage-compliant/` triển khai các cách xây authority không vi phạm:
digital PR theo dữ liệu gốc (vd công bố thống kê điểm PTE của 400.000 học viên — asset PTE Magic
đang có thật), unlinked mention reclamation, guest post có liên quan thật sự về chủ đề du học,
và listing chính thức của Pearson/đối tác giáo dục. Đây là thứ vừa bền vừa bán được cho khách.

---

## 6. Trạng thái audit khởi đầu

Đã chạy audit thật trên `ptemagic.com` ngày 2026-09-29 (xem
[`reports/ptemagic/2026-09-29-audit-khoi-dau.md`](reports/ptemagic/2026-09-29-audit-khoi-dau.md)).
Tóm tắt: 4 lỗi Critical, 7 lỗi High. Đáng chú ý nhất:

- Ảnh hero/thumbnail đều gọi `/_next/image?...&w=3840` → LCP mobile gần như chắc chắn > 4s
- Trang chủ và `/vi` có **nhiều H1** và **khối testimonial bị lặp nguyên văn 2 lần** trong DOM
- Bài tiếng Việt nằm trên path root của domain tiếng Anh (`/nhung-thay-doi-ve-diem-thi-pte-...`)
  → không khớp mô hình `/vi/` của các trang tĩnh, dễ vỡ hreflang
- `lastmod` trong sitemap = thời điểm build (`2026-09-29T03:35:53.482Z` cho toàn bộ trang chính)
  → Google sẽ bỏ qua tín hiệu lastmod
- Footer: "Privacy Policy" và "Payment & Refund Policy" trỏ về **cùng một URL** `/privacy-policy`

---

## 7. Ghi chú

- Repo này là GitHub Pages site (CV). Thư mục `seo-agents/` có `.nojekyll` để Jekyll không build nó.
  Nếu không muốn public, chuyển thư mục này sang repo riêng (private) — cấu trúc không đổi.
- `data/`, `reports/*.json`, `.env`, `.venv/` đã nằm trong `.gitignore`.
- License các repo nguồn tham khảo: MIT / Apache-2.0. Bộ này viết lại từ đầu, không copy code,
  ghi công nguồn trong `RESEARCH-GITHUB-SEO-AGENTS.md`.
