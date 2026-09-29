# Content Brief — {slug}

| | |
|---|---|
| Primary keyword | `{keyword}` |
| Locale | `en` \| `vi` |
| Intent | informational \| commercial \| transactional \| navigational |
| Funnel | TOFU \| MOFU \| BOFU |
| Loại trang | bài blog \| landing \| tool \| so sánh \| bản cập nhật |
| Cluster | {C1..C6, tham chiếu `context/target-keywords.md`} |
| Người viết | |
| Ước lượng | {phút} quen · {phút} mới |

## 1. Nhu cầu tìm kiếm (có số thì nói số, không có thì nói không có)
```
GSC (90d): {impressions} impr · {clicks} click · {avg position} pos  · nguồn: {file}, {date}
Ahrefs/Semrush: {volume} ±{range} · KD {n}  · HOẶC "CHƯA IMPORT"
```
**Không** bịa. Không có dữ liệu → `không đo được — đề xuất dựa trên SERP + dữ liệu nội bộ`.

## 2. SERP hiện tại (5 kết quả đầu, đọc THẬT)
| # | URL | Type | Từ | Có gì | **Thiếu gì** |
|---|---|---|---|---|---|

**Khoảng trống sẽ lấp:** {1–2 câu — nếu không tìm thấy → không viết bài mới}

## 3. Giá trị độc quyền (chọn ≥1 — bắt buộc, không được để trống)
- [ ] **Dữ liệu chấm AI** — dataset: {n bài}, {period}, {metric sẽ công bố}
- [ ] **Ngân hàng 8.000+ câu hỏi** — {phân bố/chủ đề sẽ phân tích}
- [ ] **Template do trainer viết** — {trainer nào, đã test trên bao nhiêu học viên}
- [ ] **Ca học viên có tên** — {tên, điểm trước→sau, đã xin phép: ☐}

Không tick được → **huỷ brief**. Đây là ranh giới giữa "AI-assisted có biên tập"
và "scaled content abuse".

## 4. Outline
| H2 | H3 | Trả lời câu hỏi nào | Độ dài ước lượng | Nguồn số liệu |
|---|---|---|---|---|

Ràng buộc: **mỗi H2 = một câu hỏi người dùng thật gõ**, không phải "Giới thiệu/Tổng quan/Kết luận".

## 5. Thực thể & thuật ngữ phải có
`Pearson` · `PTE Academic` · `PTE Core` · `communicative skills` · `enabling skills` ·
`10-90` · `Score Report` · {task names theo `references/pte-domain-glossary.md`}
→ Bài **VI**: giữ nguyên tên task tiếng Anh + giải thích bằng tiếng Việt.

## 6. Internal links
**Vào (≥3):** | từ URL | anchor |
**Ra (≥4):** | tới URL | anchor |
Nguồn: `context/internal-links-map.md`. **Không** bịa URL.

## 7. Meta
```
Title A ({n}/60):
Title B ({n}/60):
Title C ({n}/60):
Meta A ({n}/155):
Meta B ({n}/155):
```
Không lặp brand 2 lần (bài học: title `/blogs` = "PTE Magic - PTE Magic Blog").

## 8. Schema
`Article` (đủ `author` + `datePublished` + `dateModified`) · `BreadcrumbList` ·
`FAQPage` (≥3 Q&A có acceptedAnswer) · {`Course`+`Offer` nếu landing khoá học}

## 9. Tiêu chí chất lượng
- [ ] ≥{words} từ cho {type}
- [ ] Ảnh thật từ platform (không stock) + **mọi ảnh có `sizes` prop, không có w=3840**
- [ ] Mọi số liệu có **nguồn + ngày**
- [ ] Ngày updated hiển thị; nếu YMYL → ≤90 ngày
- [ ] Tác giả có tên + chức danh + URL profile
- [ ] Không "In today's fast-paced world" / "Tóm lại" / "điều quan trọng cần lưu ý"
- [ ] Không hứa hẹn kết quả
- [ ] Không khẳng định "đề thi thật" (xem `references/pte-domain-glossary.md`)
- [ ] Đã có **người thứ hai** đọc (bắt buộc nếu YMYL)

## 10. Policy pre-check — người viết tự khai
| Câu | ✓/✗ | Ghi chú |
|---|---|---|
| Đây là bản sao/ẩn-sao bài đã có, chỉ đổi nước/tháng/format? | | "có" → **dừng** |
| Có assertion về điểm/visa tôi không chắc? | | |
| Có số liệu không nguồn? | | |
| Có nhắc đề thi thật / leak / bản quyền Pearson? | | |
| Có nội dung bên thứ ba để hưởng traffic domain mình? | | |
| Chủ đề visa/học bổng/chi phí? | | "có" → YMYL → thêm author + ngày + nguồn chính phủ |

## 11. Cần người quyết / Rủi ro
- **Câu hỏi:** {một câu, phương án A/B}
- **Rủi ro nếu làm ẩu:** {chỉ ra `code` trong `policy_gate.py` sẽ bắn}
- **(VI) Cảnh báo:** `issues.I18N-ARCH` chưa chốt → URL có thể đổi. **Chưa publish.**
