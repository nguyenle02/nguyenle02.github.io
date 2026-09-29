---
description: "So sánh trạng thái hiện tại của site với baseline đã lưu — phát hiện regression sau deploy trong 5 phút thay vì 3 tuần sau khi traffic tụt."
argument-hint: "[baseline | compare | history] [url]"
allowed-tools: Bash(python scripts/drift.py*), Read, Write
---

Drift: **$ARGUMENTS**

```bash
python scripts/drift.py baseline --site <url> --max-urls 300    # sau mỗi audit quý
python scripts/drift.py compare  --site <url> --out reports/ptemagic/
python scripts/drift.py history  --site <url>
```

Báo cáo **chỉ nói về thứ ĐÃ thay đổi**, không lặp lại danh sách lỗi cũ.

Phân loại khi trình bày:
- **Regression (critical)** — `canonical_changed/missing`, `jsonld_type_removed`,
  `hreflang_removed`, `noindex_added`, `status_changed`, `page_disappeared`
  → nếu xuất hiện ngay sau deploy: **báo dev trong ngày**, đề xuất revert.
- **Cố ý** — `title_changed`, `word_count_gain`, `jsonld_type_added`
  → xác nhận có trong action plan không; nếu có → chạy `baseline` lại để lần sau không báo.
- **Cảnh giác** — `oversized_images_added`, `html_size_surge`, `internal_links_drop`,
  `h1_count_changed`

Không kết luận "đã sửa xong" hay "ổn rồi" nếu không có baseline cũ để so.
Nếu compare sạch sau một deploy lớn → nói rõ: *hoặc deploy sạch, hoặc baseline đã cũ;
kiểm tra ngày của baseline.*
