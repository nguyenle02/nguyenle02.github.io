---
description: "Chạy full technical + on-page + i18n + schema + GEO audit cho một site (mặc định ptemagic.com), dispatch các sub-agent song song, xuất báo cáo có điểm số và action plan."
argument-hint: "[url] [--max-urls N] [--offline-dir DIR]"
allowed-tools: Bash(python scripts/*), Bash(gh *), Read, Write, Grep, Glob
---

Audit toàn diện: **$ARGUMENTS**

## Bước 0 — ngữ cảnh (bắt buộc)
Đọc: `config/ptemagic.yaml`, `QUY-TRINH-SEO-PTEMAGIC.md`, toàn bộ `context/`,
report mới nhất trong `reports/ptemagic/`.
Tóm tắt 5 dòng cho tôi: site · locales · KPI · open decisions đang mở · ngày audit trước.

## Bước 1 — bằng chứng (script, không phải mắt)
```bash
python scripts/seo_audit.py --site <url> --max-urls ${3:-300} \
    --config config/ptemagic.yaml --out reports/ptemagic/
python scripts/psi_cwv.py --config config/ptemagic.yaml --strategy both \
    --out reports/ptemagic/$(date +%F)-cwv.md   # bỏ qua nếu thiếu PSI_API_KEY
```
Không có mạng → `--offline-dir <dir>`. Nếu chạy offline, **ghi rõ trong report**
rằng head/headers/CrUX không đo được và **không chấm điểm tổng**.

## Bước 2 — dispatch song song (MỘT tin nhắn, nhiều agent)
`technical-auditor` · `performance-auditor` · `onpage-editor` ·
`schema-engineer` · `hreflang-engineer` · `geo-analyst`

Mỗi agent trả JSON theo schema riêng. **Loại mọi finding có confidence: low** khỏi
danh sách hành động, chuyển vào mục "cần verify" kèm lệnh verify.

## Bước 3 — tổng hợp
1. Khử trùng lặp theo `code` + `url`
2. Ghi đè bằng số liệu từ JSON — agent không được sửa số
3. Xếp Impact × Effort → `templates/action-plan.md`
4. **Tối đa 8 việc**, mỗi việc có owner (tên người) + deadline + số đo trước/sau
5. Ghi `reports/ptemagic/$(date +%F)-audit.md` + `-action-plan.md`

## Bước 4 — trả lời tôi
```
## Đã làm
## Phát hiện đáng tiền nhất (tối đa 3)
## Tôi không làm / không đề xuất, và vì sao
## Cần tôi quyết (tối đa 2 câu, có phương án A/B)
## Lệnh để tự tái hiện
```
Không khen, không "nhìn chung site ổn". Nếu site ổn thật thì nói 1 dòng và chỉ ra
3 thứ đang chặn tăng trưởng.
