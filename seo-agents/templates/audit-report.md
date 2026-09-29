# SEO Audit — {site}

**Ngày:** {date} · **Người thực hiện:** {owner} · **Phạm vi:** {scope}
**Chế độ:** {live | offline} · **Số URL audit:** {n} · **Lệnh tái tạo:** `{bash}`

---

## 0. Giới hạn phương pháp  ← luôn giữ mục này

| Đã đo được | Không đo được |
|---|---|
| {list} | {list — vd: HTTP headers, CrUX field data, head tags nếu render proxy} |

Finding nào thuộc cột phải → **không** có trong báo cáo. Không suy đoán thay.

## 1. Điểm tổng quan

| Hạng mục | Điểm | Critical | High | Medium | Low |
|---|---|---|---|---|---|
| Technical | | | | | |
| On-page | | | | | |
| Content | | | | | |
| Performance (CWV) | | | | | |
| Schema | | | | | |
| i18n | | | | | |
| Images | | | | | |
| Links | | | | | |
| **Tổng** | | | | | |

Không có số đo thật → ghi `not measured`. **Không** chấm điểm trên không.

## 2. CRITICAL (chặn mọi thứ khác)
| # | Code | Mô tả | Số URL | Evidence (trích JSON) | Fix | Owner | Giờ |
|---|---|---|---|---|---|---|---|

## 3. HIGH  / 4. MEDIUM  / 5. LOW
*(cùng bảng; mục 5 được phép gộp thành 1 dòng/code)*

## 6. Đã kiểm tra và ổn
Giữ lại mục này — nó chứng minh bạn đã nhìn, và nó chặn đề xuất sửa thứ đang chạy tốt.
- ✅ {hạng mục} — {bằng chứng}

## 7. Cần verify nhưng không đủ dữ liệu
| Finding tạm | Vì sao chưa chắc | Lệnh để kiểm |
|---|---|---|

## 8. Tình hình chính sách (Spam Policies)
| Nhóm policy | Phát hiện | Mức | Chi tiết |
|---|---|---|---|
| Scaled content abuse | | | |
| Site reputation abuse | | | |
| Link spam | | | |
| Expired domain abuse | | | |
| Keyword stuffing | | | |
| Doorway / hidden text / cloaking | | | |

Nếu không phát hiện gì → ghi rõ "không phát hiện", đừng bỏ trống bảng.

## 9. Khuyến nghị, xếp theo Impact × Effort
→ chuyển vào `action-plan.md`

## 10. Ảnh chụp nhanh (5 URL quan trọng nhất)
```
URL: /
  title (52/60)   "…"
  meta  (148/155) "…"
  h1 count: 4  ← lỗi
  canonical: present, self
  hreflang: 0
  jsonld: Organization ✓  Article ✗  BreadcrumbList ✗
  imgs: 12, thiếu alt 3, w>1200: 12  ← lỗi
  words: 640  internal links: 9
```
