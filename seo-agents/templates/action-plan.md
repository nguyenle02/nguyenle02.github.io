# Action Plan — {site} · {quarter}

Nguồn: `reports/{date}-audit.md` · Người duyệt: · Ngày:

## Quy tắc
- **Tối đa 8 việc.** Hơn 8 = không xong cái nào.
- Mỗi việc có: owner (tên người), deadline, **số đo trước**, **số đo sau**.
- Việc nào không đo được kết quả → không đưa vào plan.

## Bảng chính
| # | Việc | sev | Impact | Effort | Owner | Deadline | Đo trước | Đo sau | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | | critical | | | | | | | |

Sắp xếp theo **Impact ÷ Effort** (không theo severity — việc critical effort cao thường
xếp sau nhiều việc high effort thấp).

## Nhóm theo người làm

### Dev (cần sprint)
| # | Việc | File/config dự kiến | Validation |
|---|---|---|---|

### SEO/Editor (tự làm)
| # | Việc | Output | |

### Cần quyết định (founder/khách)
| # | Câu hỏi | Phương án A | Phương án B | Khuyến nghị | Hạn trả lời |
|---|---|---|---|---|---|

## Dependencies
```
(1) chốt i18n architecture
   └─> (2) hreflang  ─┐
   └─> (3) URL plan VI ├─> (6) content plan Q+1
   └─> (4) sitemap split┘
(5) sizes prop next/image  ──> (7) đo lại LCP sau 4 tuần
```
**Chạy việc phía dưới trước khi xong phía trên = làm lại.**

## Đo lường
| Chỉ số | Nguồn | Tần suất | Baseline | Mục tiêu |
|---|---|---|---|---|
| Non-brand click | GSC | tuần | | |
| `sign_up_free` từ organic | GA4 | tuần | | |
| URL top 10 (cluster {x}) | GSC | tháng | | |
| % URL CWV Good (mobile) | CrUX | tháng | | |
| AI citation rate (25 prompts) | `context/ai-citation-targets.md` | quý | | |
| Policy gate BLOCK count | `reports/policy-log.csv` | tháng | | |

## Không làm (có chủ đích)
| Đề xuất đã loại | Vì sao |
|---|---|
| | |

Mục này bắt buộc. Nó ngăn cùng một đề xuất quay lại mỗi tháng, và nó là bằng chứng
bạn đã cân nhắc rủi ro chính sách.

## Review
- [ ] Sau 2 tuần: các việc critical/dev đã merge?
- [ ] Sau 6 tuần: số đo "sau" đầu tiên (CrUX cần 28 ngày, đừng đo sớm hơn)
- [ ] Cuối quý: `drift.py compare` + `seo_audit.py` lại → sang quý mới
