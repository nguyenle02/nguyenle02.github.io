---
description: "Chạy cổng kiểm tra chính sách Google trước khi publish. BLOCK = không đăng. Dùng cho MỌI bài, kể cả bài cũ khi refresh."
argument-hint: "<file.md|file.html> [--corpus DIR] [--batch DIR]"
allowed-tools: Bash(python scripts/policy_gate.py*), Read, Write, Grep, Glob
---

Policy check: **$1**

## Bắt buộc
```bash
python scripts/policy_gate.py --file "$1" --corpus ${2:-published/} \
    --config config/ptemagic.yaml --out reports/policy/$(basename "$1" | sed 's/\..*//').md \
    --log reports/policy-log.csv
```

**Thiếu `--corpus` thì nói rõ:** chỉ check được 8/12 nhóm, không phát hiện near-duplicate
→ gate **chưa pass**.

## Khi BLOCK
1. Đọc `evidence`, không chỉ `message`
2. **Mở nội dung thật để xác minh.** Script có thể đúng hoặc sai.
3. Script đúng → soạn bản sửa cụ thể (thêm section nào, gộp URL nào, bỏ assertion nào)
4. Script sai → đề xuất ngưỡng mới + **thêm case vào `scripts/tests/run_selftest.py`** + commit
5. Chạy lại tới khi PASS/WARN

## Cấm tuyệt đối
- Tư vấn cách **lách** gate (chèn câu ngẫu nhiên giảm Jaccard, đổi 1 từ trong anchor,
  bỏ CSS hidden nhưng vẫn để text ngoài DOM).
- Bỏ qua vì "gấp" / "khách đồng ý rồi".
- Tự duyệt bài do bạn viết ở phiên trước mà không nói rõ đó là self-check.
  Bài YMYL → **đề nghị người thứ hai**.

## Output
```
VERDICT: BLOCK | WARN | PASS
Đã chặn:  | code | chính sách | bằng chứng | bản sửa |
Đã chấp nhận có ghi chú: | code | lý do | người quyết định |
Không check được: ...
```
PASS ≠ "bài hay". Sau PASS vẫn phải có người đọc to một lượt và verify mọi số liệu.
Nếu verdict WARN/PASS, thêm dòng vào cuối file nguồn:
`Reviewed by: <tên> · <ngày> · Policy Gate: <verdict>`
