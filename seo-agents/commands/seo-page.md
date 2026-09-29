---
description: "Audit sâu MỘT URL của ptemagic.com: on-page, schema, ảnh, CWV, chính sách. Dùng cho bài sắp đăng hoặc bài đang rank kém."
argument-hint: "<url hoặc path file draft>"
allowed-tools: Bash(python scripts/*), Read, Write, Edit, Grep, Glob
---

Phân tích 1 trang: **$1**

1. `python scripts/seo_audit.py --site <url> --only-url <url>` (hoặc `--offline-dir` cho draft)
2. Đọc `context/brand-voice.md` + `context/seo-guidelines.md`
3. Chẩn đoán **trước** khi sửa — 4 nhóm: không impression / impression cao CTR thấp /
   position 11–20 / rank tốt không convert. Nói rõ trang này thuộc nhóm nào và vì sao.
4. So top 5 SERP: H2 nào của họ mà trang này chưa trả lời?
5. Giao `onpage-editor` sửa theo `code`; `schema-engineer` nếu có `JSONLD_*`/`ARTICLE_*`;
   `performance-auditor` nếu có `NEXT_IMAGE_OVERSIZED_W`.
6. **Bắt buộc trước khi báo "sẵn sàng publish":**
   `python scripts/policy_gate.py --file <draft> --corpus published/`

Output: chẩn đoán · đã sửa (trước/sau) · **không sửa vì** · cần dev/CMS làm gì ·
kết quả policy gate. Không có policy gate result = bài chưa sẵn sàng, nói thẳng.
