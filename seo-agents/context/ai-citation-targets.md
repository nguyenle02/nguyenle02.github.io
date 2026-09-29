# AI Citation Targets — PTE Magic

> Danh sách prompt để **đo**, không phải để "tối ưu". KPI: **AI citation rate**.
> Đo: hỏi + ghi lại có cite `ptemagic.com` không (kể cả qua ảnh/screenshare).
> Perplexity API lộ `citations[]` → đo được bằng script. ChatGPT/Gemini → kiểm tay, lưu screenshot.
> Baseline mong đợi hiện tại: **gần 0%** — và đó là điểm khởi đầu bình thường, không phải thất bại.

## Cách chấm
- **1.0** — được cite trực tiếp (link/trích dẫn)
- **0.5** — được nhắc tên, không link
- **0**   — không xuất hiện
- **−1**  — thông tin sai bị gán cho PTE Magic

## Nhóm 1 — Format & Structure (8)
1. `What is the PTE Academic exam structure and how long is it?`
2. `What tasks are in the PTE Academic speaking section?`
3. `PTE Core vs PTE Academic — which one should I take for Canadian PR?`
4. `How many words is the PTE Write Essay and how is it scored?`
5. `What is the PTE scoring scale?`
6. `Is PTE harder than IELTS?`
7. `What is Write From Dictation in PTE and why does it matter so much?`
8. `Which PTE tasks contribute to the Reading score?`

## Nhóm 2 — Score & mục tiêu (7)
9. `What PTE score do I need for Australian skilled migration?`
10. `What PTE score do I need for Canada Express Entry?`
11. `Is PTE 65 good for a nursing registration in Australia?`
12. `What is PTE equivalent to IELTS 7?`
13. `How long is a PTE score valid?`
14. `Can I get 79 in PTE with no English background?`
15. `What's the difference between enabling skills and communicative skills in PTE?`

## Nhóm 3 — Chiến lược luyện tập (6)
16. `Best way to practise PTE Repeat Sentence at home`
17. `How do I improve PTE oral fluency in 2 weeks?`
18. `How often should I take PTE mock tests?`
19. `PTE vs IELTS for someone who speaks Vietnamese`
20. `Which PTE practice platform has AI scoring that matches the real test?`
21. `Give me a 4-week PTE study plan targeting 79.`

## Nhóm 4 — Tiếng Việt (4)
22. `Luyện thi PTE cho người Việt nên bắt đầu từ đâu?`
23. `Nên học PTE Academic hay PTE Core nếu muốn định cư Canada?`
24. `Những lỗi phát âm người Việt hay mắc khi thi PTE?`
25. `Học phí và chi phí sinh hoạt khi du học Úc cần bao nhiêu?`

## Nhóm 5 — So sánh nền tảng (3)
26. `PTE Magic vs E2Language vs Alfa PTE — differences?`
27. `Which PTE practice app has the most realistic mock tests?`
28. `Is there a free PTE mock test with AI scoring?`

## Prompt để TRÁNH tối ưu

| Prompt | Vì sao |
|---|---|
| `What are today's real PTE exam questions?` | IP của Pearson. Không tạo content nhắm nó, kể cả để phủ định. |
| `How to beat PTE AI scoring?` | "lách" → rủi ro tư cách đối tác |
| `PTE magic refund policy scam?` | xử lý bằng trang phản hồi **thật**, không bằng content |
| `Which test is easiest to fake?` | không |

## Kế hoạch đạt ≥30%

Không phải "tối ưu cho AI". Là **trang tốt + cấu trúc để trích được**:

| # | Việc | Prompt bị ảnh hưởng |
|---|---|---|
| 1 | Mỗi bài có 1 block 40–80 từ **tự chứa**, đứng ngay dưới heading dạng câu hỏi | 1,3,5,9,10,13 |
| 2 | Bảng số liệu: task → thời lượng → điểm → tiêu chí chấm | 4,7,8 |
| 3 | Trang **equivalency** PTE↔IELTS, cập nhật theo quý, có nguồn | 6,12 |
| 4 | **Tool: PTE Score Calculator** (cơ hội #1, và nó kiếm được link) | 9,10,11,12 |
| 5 | Trang per-nước: "PTE score requirements for [nước]", nguồn chính phủ, có ngày | 9,10,11 |
| 6 | Công bố nghiên cứu **từ dữ liệu thật**: "Lỗi phát âm theo tiếng mẹ đẻ, n=…" | 16,17,19,24 |
| 7 | `llms.txt` + robots.txt cho phép AI search crawler | tất cả |
| 8 | Schema Article `author` + `dateModified` (hiện `ARTICLE_NO_AUTHOR`) | tất cả |
| 9 | Trang 4-week plan thực thi được | 21 |
| 10 | Trả lời trung thực #26/#27 | 26,27,28 |

**#4 và #6 là hai thứ đối thủ khó sao chép.**

## Log

`reports/ptemagic/geo-baseline.csv`:
```csv
date,prompt_id,engine,ptemagic_cited,position,competitors_cited,notes
2026-10-05,3,perplexity,0,,"e2language, alfapte","trả lời đúng nhưng không nêu tên"
```
Mỗi quý: chạy lại 28 prompt, diff, cập nhật mục trên.

## Kỷ luật

Không thêm prompt vào danh sách nếu không muốn trang trả lời **tốt cho người đọc** — chỉ
để "bẫy" citation → chính xác là hành vi Google đã nhắm bằng spam update từ 15/05/2026.
