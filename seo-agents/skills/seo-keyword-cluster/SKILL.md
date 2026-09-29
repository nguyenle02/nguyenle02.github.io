---
name: seo-keyword-cluster
description: "Nghiên cứu và gom cụm từ khoá cho ptemagic.com (EN + VI, 6 cluster trụ cột). Nguồn: GSC API, export Ahrefs/Semrush, SERP. Trả về topic clusters có intent, funnel, và action (NEW/REFRESH/PUSH/DEFEND/CONSOLIDATE/PRUNE). Trigger: 'nghiên cứu từ khoá', 'keyword research', 'cluster', 'tìm chủ đề viết', 'content gap', 'striking distance'."
user-invocable: true
argument-hint: "[seed topic | --from-gsc]"
license: MIT
metadata:
  version: "1.0.0"
  category: seo
  depends_on_scripts: ["gsc_pull.py", "cluster_keywords.py"]
---

# Keyword Research & Clustering

## Nguồn dữ liệu — và thứ tự ưu tiên

| Hạng | Nguồn | Vì sao | Độ tin |
|---|---|---|---|
| 1 | **GSC của chính PTE Magic** | Bạn đã có demand thật, có vị trí thật, có CTR thật | cao nhất |
| 2 | GSC của **khách trước** (nếu cùng niche) | Demand đã kiểm chứng | cao |
| 3 | Ahrefs/Semrush export | Có volume + KD nhưng là **ước lượng** | trung bình |
| 4 | SERP thực tế (đọc top 5 kết quả) | Phát hiện intent thật, thứ Google coi là đủ tốt | cao cho intent |
| 5 | Hỏi đội sales/support/trainer | Câu hỏi thật của học viên | cao nhất cho **ý định** |
| 6 | Suggestions của LLM | Chỉ dùng để **mở rộng** danh sách, không dùng để chọn chủ đề | **thấp** |

```bash
python scripts/gsc_pull.py --days 90 --compare-previous --out data/gsc-90d.csv
python scripts/cluster_keywords.py --in data/gsc-90d.csv --out data/clusters.md \
    --csv-out data/clusters.csv
python scripts/cluster_keywords.py --in data/ahrefs-export.csv --out data/clusters-ahrefs.md
```

`cluster_keywords.py` tự nhận diện cột (GSC ↔ Ahrefs ↔ Semrush). Nó phân loại bằng **quy tắc
đọc được**, không bằng mô hình — bạn phải kiểm tra được vì sao một query bị gán `REFRESH`.

## Quy tắc chọn chủ đề (phần này không delegate được)

Một chủ đề chỉ đáng làm khi **đủ 3/4**:

1. **Có demand đo được** — impression GSC > 0, hoặc volume > 30, hoặc SERP top 5 có ≥2 trang
   chuyên biệt về đúng query đó (không phải bài tổng có nhắc 1 câu)
2. **PTE Magic có quyền viết khác biệt** — khớp 1 trong 4:
   dữ liệu chấm AI của 400.000+ học viên · 8.000+ câu hỏi theo format Pearson ·
   template trainer viết · trường hợp học viên có tên + điểm số
3. **Kết nối tới conversion** — dẫn tới `/sso/auth/register`, `/features`, hoặc khoá học
4. **Không bị C2 chặn** — `config → issues.open_decisions[I18N-ARCH]` đang mở; chủ đề chỉ-tiếng-Việt
   nên chờ chốt kiến trúc i18n

Không đủ 3/4 → để vào `data/backlog.md`, đừng viết.

## Bảng 6 cluster trụ cột

Chi tiết + trạng thái URL thật: `context/target-keywords.md`. Tóm tắt ưu tiên:

| Cluster | Trạng thái | Ưu tiên |
|---|---|---|
| C1 PTE format & structure | có trang tĩnh, thiếu trang so sánh Academic vs Core | 2 |
| C2 Task-level tips & templates | **dày cho PTE Core, mỏng cho PTE Academic**; RS/WFD trống | 1 |
| C3 Score & scoring | có bài scoring, thiếu score calculator + IELTS conversion | 3 |
| C4 Study abroad 4 nước | ~27 URL, rủi ro doorway + YMYL | 5 (audit trước) |
| C5 PTE Core (Canada) | đang có đà, đối thủ mỏng | 1 |
| C6 Brand & platform | ổn, cần bảo vệ sitelink | 4 |

## Cảnh báo khi làm việc với PTE Magic

**Không làm những việc sau, kể cả khi số liệu hấp dẫn:**

| ❌ | Vì sao |
|---|---|
| Nhắm "pte real questions 2026", "đề thi thật hôm nay", "pte exam leak" | Bản quyền Pearson + rủi ro pháp lý. Bài `/pte-essay-topics` hiện viết **đúng**: tự nhận là "practice prompts written in the style PTE uses… not copied from live tests". Giữ chuẩn đó. |
| Gom "best pte app", "pte vs ielts which easier" thành bài dìm đối thủ | Không vi phạm spam policy nhưng vi phạm 5.1 (đánh giá sai lệch) và làm xấu brand với cả người đọc lẫn Pearson |
| Tạo N bài theo biến thể `pte <task> tips <year>` | Đây là công thức scaled content abuse + doorway. `policy_gate.py` sẽ `TEMPLATE_SHELL` BLOCK khi ≥8 URL chung vỏ |
| Chọn chủ đề chỉ vì volume cao | PTE Magic cần `sign_up_free`, không cần traffic tò mò |
| Nhắm "free pte mock test" làm money keyword cho trang trả phí | Mismatch intent → tụt CTR + bounce; Google đọc được tín hiệu này |

## Format output bắt buộc

```markdown
# Cluster: <tên> (<id>)
Demand đã đo:  <impression GSC / volume + nguồn>  ← hoặc "CHƯA ĐO ĐƯỢC"
Intent:        <informational|commercial|transactional|navigational> — <bằng chứng SERP>
Funnel:        <TOFU|MOFU|BOFU>
Vì sao PTE Magic thắng được: <1 trong 4 quyền lợi độc quyền>

## Trang hiện có
| URL | Pos | Impr | Click | Vấn đề |
|---|---|---|---|---|

## Đề xuất
| # | Action | URL/slug mới | Primary KW | Secondary KW | Priority | Giờ |
|---|---|---|---|---|---|---|

## Cannibalisation cần xử lý
<cặp URL> — <pos mỗi bên> — <gộp hay tách, và vì sao>

## Không làm
<chủ đề đã cân nhắc và loại + lý do>
```

Mục **"Không làm"** là bắt buộc. Nó tiết kiệm cho bạn cuộc tranh luận lặp lại mỗi tháng,
và nó là bằng chứng bạn đã cân nhắc rủi ro chính sách trước khi làm — thứ nên đưa cho khách xem.

## Handling đa ngôn ngữ

EN và VI **không phải** bản dịch của nhau về từ khoá. `pte core writing email` (EN) và
`cách viết email pte core` (VI) có intent, độ cạnh tranh và SERP khác hẳn.

- Không bao giờ dịch keyword list từ EN sang VI và giả định volume tương đương
- Chạy `cluster_keywords.py` RIÊNG cho từng locale (`--out data/clusters-vi.md`)
- Với bài VI: keyword tiếng Việt; **giữ nguyên thuật ngữ cố định** (PTE Core, Write From
  Dictation, Repeat Sentence, Describe Image) — học viên Việt Nam tìm các thuật ngữ này bằng tiếng Anh
- `config/ptemagic.yaml → issues.I18N-ARCH` đang MỞ: mọi quy hoạch URL tiếng Việt chỉ là
  kế hoạch tạm. Ghi chú điều đó vào mọi output VI.
