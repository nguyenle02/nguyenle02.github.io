---
name: seo-geo-visibility
description: "GEO/AEO cho PTE Magic: làm cho nội dung dễ được trích dẫn trong AI Overviews, ChatGPT, Perplexity, Gemini. Kiểm AI crawler access, llms.txt, thực thể, citability scoring, theo dõi citation thật. Trigger: 'AI Overviews', 'ChatGPT có nhắc', 'GEO', 'AEO', 'LLM visibility', 'được trích dẫn', 'llms.txt', 'GPTBot'."
user-invocable: true
argument-hint: "<URL | 'audit' | 'prompts'>"
license: MIT
metadata:
  version: "1.0.0"
  category: geo
---

# GEO / AEO — được trích dẫn trong câu trả lời AI

## Vì sao skill này tồn tại (đây là thay đổi lớn nhất 2024→2026)

1. Người học PTE hỏi ChatGPT/Gemini "PTE Core khác PTE Academic thế nào", "cần bao nhiêu điểm
   cho y tá đăng ký hành nghề ở Úc" — **thay vì** google.
2. **Từ 15/05/2026**, Google định nghĩa lại spam: áp dụng cho cả việc
   *"manipulate generative AI responses in Google Search"*.
   SpamBrain quét nội dung để xét tư cách được trích trong AI.

Hai việc này cùng kéo về một kết luận: **tối ưu để được trích dẫn, nhưng không tối ưu chỉ để
được trích dẫn.**

> ### ⛔ Ranh giới
> Google nói rõ: trang được làm ra **để được AI trích dẫn mà không có lý do gì cho người đọc**
> = scaled content abuse. "Xếp hạng" giờ bao gồm "được trích dẫn".
> → Không tạo trang chỉ để trả lời 1 prompt. Tạo trang tốt cho người, rồi cấu trúc nó
> để máy trích được.

## Bước 1 — AI crawler: quyền truy cập có chủ đích

```bash
curl -s https://ptemagic.com/robots.txt
```
 robots.txt hiện tại:
```
User-Agent: *
Allow: /
Sitemap: https://ptemagic.com/sitemap.xml
```
Không có mục nào cho crawler AI. **Cho phép hết, không có chủ đích** — chấp nhận được,
nhưng nên là lựa chọn có ý thức.

| Bot | Dùng để | Khuyến nghị cho PTE Magic |
|---|---|---|
| `GPTBot` | ChatGPT **học** / huấn luyện | Cân nhắc — dữ liệu bài thi có giá trị huấn luyện |
| `OAI-SearchBot` | **Search** trong ChatGPT (không huấn luyện) | **CHO PHÉP** — đây là kênh cite |
| `ChatGPT-User` | Khi user yêu cầu fetch | Cho phép |
| `PerplexityBot` | lập chỉ mục cho tìm kiếm của Perplexity | **CHO PHÉP** |
| `ClaudeBot` / `Claude-User` | Anthropic | Cho phép |
| `Google-Extended` | Gemini / AI Overviews | **CHO PHÉP** nếu muốn vào AI Overviews |
| `Applebot-Extended` | Apple AI | Tuỳ chọn |
| `meta-externalagent`, `Bytespider`, `Amazonbot` | Meta/TikTok/Amazon | Thường chặn — ít giá trị, nhiều tải |

Cấu hình mẫu, tách bạch "cho tìm kiếm AI" vs "cho huấn luyện":
```
User-agent: GPTBot
Disallow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Bytespider
Disallow: /
User-agent: Amazonbot
Disallow: /

User-agent: *
Allow: /
Sitemap: https://ptemagic.com/sitemap.xml
```
Quyết định này là **của chủ doanh nghiệp**, không phải của SEO. Trình bày tradeoff rồi xin
quyết định bằng văn bản, đặc biệt nếu bạn làm cho khách — chặn GPTBot có nghĩa là ChatGPT
có thể không biết tới bạn; cho phép nghĩa là nội dung PTE (có thể có giá trị huấn luyện)
đi vào mô hình.

## Bước 2 — `llms.txt`

PTE Magic **chưa có** `/llms.txt`. Tiêu chuẩn còn non trẻ, lợi ích chưa được chứng minh,
nhưng chi phí ~15 phút và rủi ro ~0.

```markdown
# PTE Magic

> Nền tảng luyện thi PTE Academic & PTE Core dùng AI chấm điểm. 400.000+ học viên,
> 8.000+ câu hỏi theo format Pearson, báo cáo điểm tức thì cho từng kỹ năng.
> Pearson's Elite Partner 2025.

## Kỳ thi
- [PTE Academic structure](https://ptemagic.com/exam-structure-pte-academic): parts, tasks, timing, 10-90 scale
- [PTE Core structure](https://ptemagic.com/exam-structure-pte-core): Canadian migration format

## Điểm số
- [How PTE automated scoring works](https://ptemagic.com/how-does-pte-automated-scoring-work-a-complete-guide)
- [PTE score report: access & share](https://ptemagic.com/how-to-access-and-share-your-pte-score-report-easily)

## Luyện tập
- [PTE essay topics 2026: 60 questions](https://ptemagic.com/pte-essay-topics)
- [Free mock test](https://ptemagic.com/sso/auth/register)

## Tiếng Việt
- [Trang chủ VI](https://ptemagic.com/vi)

## Chính sách
- [Privacy](https://ptemagic.com/privacy-policy)

_Lưu ý: lệ phí và yêu cầu visa thay đổi; luôn kiểm tra với Pearson và cơ quan di trú nước sở tại._
```
Giữ 40–60 dòng. **KHÔNG** nhét toàn bộ 400+ URL — biến nó thành một danh bạ link vô dụng.

## Bước 3 — Citability: 8 đặc điểm làm nội dung dễ được trích

`references/eeat-checklist.md` có checklist chấm 0-100.

| # | Đặc điểm | Áp dụng cho PTE Magic |
|---|---|---|
| 1 | **Câu trả lời tự chứa, 40–80 từ, ngay dưới heading dạng câu hỏi** | "PTE Core khác PTE Academic ở đâu?" → trả lời trong 2 câu đầu của section |
| 2 | **Số cụ thể + ngày** | "Part 1: 54–67 phút, gồm 5 task type" — không phải "khoảng một tiếng" |
| 3 | **Bảng khi có so sánh** | Bảng so sánh Academic/Core hiện **đã tốt** trên `/pte-essay-topics` — nhân bản pattern này |
| 4 | **Định nghĩa thuật ngữ** | `enabling skills`, `communicative skills`, `Skill Enabling scores` — giải thích trong 1 câu |
| 5 | **Nguồn sơ cấp được nêu tên** | "theo hướng dẫn PTE Academic chính thức của Pearson" ← **bài `/pte-essay-topics` đã làm đúng cái này** |
| 6 | **Không nước đôi** | "nhiều người cho rằng…" = không trích được. Khẳng định hoặc không nói |
| 7 | **Tác giả có chức danh** | Trainer, không phải "PTE Magic Team" |
| 8 | **Cập nhật** | "Tháng 9/2026" ở đầu bài với nội dung đổi theo năm |

**Ghi nhận:** `/pte-essay-topics` đang viết **tốt** theo 8 tiêu chí này (bảng, số trait,
điểm từng trait, tuyên bố rõ ràng về xuất xứ đề). Vấn đề không nằm ở chất lượng nội dung đó — mà ở chỗ **nó là ngoại lệ**, chưa phải chuẩn của cả site.

## Bước 4 — Đo citation thật (không đoán)

```bash
python scripts/gsc_pull.py --days 90 --out data/gsc-90d.csv
python scripts/psi_cwv.py --url https://ptemagic.com/pte-essay-topics
```

Đo citation bằng danh sách prompt trong `context/ai-citation-targets.md`:
```bash
for q in $(cut -d, -f2 context/ai-citation-targets.md | head -12); do
  echo "── $q"
  curl -s "https://api.perplexity.ai/..." -d "{\"model\":\"sonar\",\"messages\":[{\"role\":\"user\",\"content\":\"$q\"}]}" \
    | jq -r '.citations[]?' | grep -E 'ptemagic|pearson|reddit|quora' | sed 's/^/   /'
done
```
(Perplexity Sonar API trả `citations` — là chỗ đáng tiền nhất để đo. Các API khác không lộ
nguồn, phải đọc tay.)

Ghi vào `reports/ptemagic/geo-baseline.csv`:
```
date,prompt,engine,ptemagic_cited,position,competitors_cited
```

KPI: **AI citation rate** = % prompt mà PTE Magic được cite (target: ≥30% trong 2 quý
cho 25 prompt trong `context/ai-citation-targets.md`).

## Bước 5 — những việc không làm

| ❌ | Vì sao |
|---|---|
| "Tối ưu cho AI" bằng cách viết lại toàn bộ site thành Q&A 40 từ | Mất nội dung cho người đọc, và vi phạm 5.2 |
| Thêm `x AI-friendly` meta / "please cite us" | Không có thẻ nào như vậy |
| Nhồi "According to PTE Magic" vào mọi câu | Nhồi từ khoá đội lốt trích dẫn |
| Đăng 500 bài "Prompt X → Answer Y" | **Đúng định nghĩa** scaled content abuse để được cite |
| Che giấu nội dung cho AI khác với cho người dùng | Cloaking |
| Chặn `Google-Extended` rồi kỳ vọng xuất hiện trong AI Overviews | Không hoạt động được như vậy |

## Báo cáo cho khách — nói thẳng tradeoff

> "Nếu khách muốn traffic từ ChatGPT/AI Overviews, cần **mở** access cho các AI crawler tìm
> kiếm, và đánh đổi là nội dung có thể được tham chiếu. Không có cách nào 'tối ưu cho AI'
> mà vẫn chặn AI."

Khách nào muốn cả hai → đề xuất `OAI-SearchBot`/`PerplexityBot` cho phép, `GPTBot` chặn.
Đó là **lựa chọn khả thi và giải thích được** — đừng im lặng chọn hộ họ.
