---
description: "Sinh content brief 1 trang (tối đa) cho một chủ đề, SERP-driven, có value-add bắt buộc, internal links, schema và policy pre-check."
argument-hint: "<chủ đề> [--locale en|vi] [--type informational|landing|tool|comparison]"
allowed-tools: Bash(python scripts/*), Read, Write, Glob, Grep
---

Brief cho: **$1**

1. Nạp `context/target-keywords.md`, `context/brand-voice.md`, `context/internal-links-map.md`,
   `references/eeat-checklist.md`
2. Demand: chạy `gsc_pull.py` nếu có credentials; nếu không → `không đo được`. **Không bịa volume.**
3. Đọc top 5 SERP **thật**, lập bảng: format · độ dài · có gì · **thiếu gì**
4. **Không tìm thấy gap → trả về đề xuất refresh URL hiện có, không viết brief.**
   Đây là output tốt, không phải thất bại.
5. Chọn ≥1 value-add từ 4 tài sản độc quyền (dữ liệu chấm AI / 8.000 câu hỏi /
   template trainer / case học viên có tên). Không chọn được → **từ chối viết brief**.
6. Đủ 11 mục theo `templates/content-brief.md` → ghi `plans/<locale>-<slug>-brief.md`
7. Nếu `--locale vi`: brief **riêng** (query khác, ví dụ khác, CTA khác) + dòng cảnh báo
   `issues.I18N-ARCH` chưa chốt → chưa publish.

Cuối brief: 6 câu policy pre-check cho người viết tick, ước lượng phút,
và rủi ro policy nếu làm ẩu (chỉ rõ `code` trong `policy_gate.py`).
