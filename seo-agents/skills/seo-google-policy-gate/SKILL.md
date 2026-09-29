---
name: seo-google-policy-gate
description: "Cổng kiểm tra CHÍNH SÁCH GOOGLE trước khi publish cho PTE Magic (và cho khách hàng). Chấm 12 nhóm rủi ro: scaled content abuse, keyword stuffing, doorway, cloaking, hidden text, link spam, site reputation abuse, expired domain abuse, YMYL/E-E-A-T, deceptive claims, AI boilerplate. Trả về PASS / WARN / BLOCK và KHÔNG cho publish khi BLOCK. Trigger: 'check chính sách', 'bài này ổn chưa', 'trước khi đăng', 'policy gate', 'có bị phạt không', 'review bài', 'pre-publish'."
user-invocable: true
argument-hint: "<file.md | file.html | URL>"
license: MIT
metadata:
  version: "1.0.0"
  category: governance
  blocking: true
  depends_on_scripts: ["policy_gate.py"]
---

# Policy Gate — bước không được bỏ qua

## Vì sao nó đứng riêng, không nằm trong "tối ưu"

8 repo SEO-agent hàng đầu trên GitHub (research 2026-09-29, ~90.000 stars) **tất cả đều tối ưu,
không repo nào từ chối**. Skill audit tìm ra 40 thứ nên cải thiện; không skill nào nói
"đừng publish bài này".

Với người làm dịch vụ, chỗ mất tiền thật không nằm ở việc thiếu tối ưu — mà ở việc đăng
một bài khiến site của khách tụt 60% và bạn phải giải trình. Gate này sinh ra cho việc đó.

## Lệnh

```bash
# 1 bài, có so trùng lặp với nội dung đã publish
python scripts/policy_gate.py --file drafts/pte-core-email.md --corpus published/ \
    --config config/ptemagic.yaml --out reports/policy/pte-core-email.md \
    --log reports/policy-log.csv

# exit code để dùng trong CI / pre-commit hook
python scripts/policy_gate.py --file <draft> --corpus published/ ; echo $?
#   0 = PASS · 10 = WARN · 20 = BLOCK · 2 = lỗi chạy
```

`--corpus` **bắt buộc** khi làm cho khách:_near-duplicate chỉ phát hiện được khi có gì để so.
Corpus tốt nhất = export toàn bộ bài đã publish (WordPress REST, hoặc CMS export).

## 12 nhóm kiểm tra

| # | Code | Chính sách Google | Mức | Ngưỡng mặc định |
|---|---|---|---|---|
| 1 | `NEAR_DUPLICATE` | **Scaled content abuse** | BLOCK | Jaccard 5-gram ≥ 0.70 vs corpus |
| 2 | `NEAR_DUPLICATE_WARN` | Scaled content abuse | WARN | ≥ 0.50 |
| 3 | `TEMPLATE_SHELL` | **Doorway pages** | BLOCK | ≥8 URL chung ≥85% khung heading **và** thân khác <30% |
| 4 | `KEYWORD_STUFFING` / `HEADING_KEYWORD_STUFFED` | **Keyword stuffing** | BLOCK | exact-match density >3.5% (>5.6% nếu bài <500 từ) · keyword ở >60% heading |
| 5 | `HIDDEN_TEXT` | **Hidden text & link abuse** | BLOCK | text ẩn bằng CSS **và** chứa keyword |
| 6 | `CLOAKING_BOT_SNIFFING` / `CLOAKING_NOSCRIPT_MISMATCH` | **Cloaking** | BLOCK / WARN | phân nhánh theo UA; `<noscript>` khác hẳn bản visible |
| 7 | `ANCHOR_OVER_OPTIMIZED` | **Link spam** | BLOCK | ≥40% anchor ra ngoài là commercial exact-match |
| 8 | `PAID_LINK_MISSING_REL` | **Link spam** | BLOCK | link có `utm_`/`affiliate`/`partner=` mà thiếu `rel="sponsored"` |
| 9 | `SITE_REPUTATION_ABUSE` | **Site reputation abuse** | BLOCK | thuật ngữ ngoài lĩnh vực nằm ở **title/heading** |
| 10 | `EXPIRED_DOMAIN_REUSE` | **Expired domain abuse** | WARN | config khai `domain_history.acquired_expired: true` |
| 11 | `YMYL_MISSING_EVIDENCE` (gom `YMYL_NO_AUTHOR`/`_NO_DATE`/`_STALE`/`_NO_OFFICIAL_SOURCE`) | **E-E-A-T / Helpful content** | BLOCK | YMYL mà thiếu 1 trong: author · ngày ≤90 ngày · link nguồn chính thức |
| 12 | `GUARANTEE_CLAIM` | **Deceptive content** | BLOCK | "cam kết đậu", "chắc chắn đạt", "đảm bảo 100%", "bao đậu" |
| + | `AI_BOILERPLATE` · `NO_VALUE_ADD` · `THIN_CONTENT` · `OFF_TOPIC_TERMS_IN_BODY` | Helpful content | WARN | heuristic, cần người quyết |

## Đọc verdict

### `BLOCK` — không publish, không thương lượng

```bash
# sửa NỘI DUNG, rồi chạy lại:
python scripts/policy_gate.py --file <draft> --corpus published/
```

**Không được làm để "qua gate":**
- Chèn 3 câu random để giảm Jaccard xuống 0.69
- Bớt 1 lần lặp keyword để density từ 3.7% xuống 3.4%
- Đổi `best pte mock test online` thành `top pte mock test online`
- Xoá `color:#fff` nhưng vẫn để text ngoài DOM cho bot

Mỗi mánh đó để lại cùng hành vi mà Google phạt, chỉ không bị script bắt. Gate là **lưới an toàn**,
không phải tấm khiên. Nếu phải nghĩ cách lách, nghĩa là **bài chưa đáng đăng**.

### `WARN` — publish được, nhưng phải ghi lại

WARN có chủ đích: heuristic, cần phán đoán người. Quy trình:
1. Đọc lý do, quyết định bằng judgment nghề nghiệp
2. Ghi 1 dòng vào `reports/policy-log.csv` (tự động khi dùng `--log`)
3. Nếu làm cho khách: **nói cho khách biết WARN đó**. Đây là lúc bạn chứng minh mình
   hiểu chính sách chứ không chỉ chạy tool.

### `PASS` — vẫn cần người đọc

PASS = "không phát hiện pattern vi phạm đã biết". Không phải "bài hay".
Editor vẫn phải đọc to một lượt, vẫn phải verify số liệu.

## Khi nào gate báo sai — và cách sửa script

| Tình huống | Hệ quả | Xử lý |
|---|---|---|
| Corpus rỗng / thiếu | Near-duplicate không phát hiện được gì | **Luôn luôn** truyền `--corpus`. Không có corpus thì gate chỉ check được 8/12 nhóm |
| Corpus là markdown thuần, bài cần check là HTML | So sánh lệch vì HTML có nav/footer | Dùng `--format` đúng, hoặc export corpus cùng format |
| Bài dịch thuật legitimately giống bản gốc | Jaccard cao → BLOCK oan | Bài dịch phải là **bản dịch**, không phải bản thứ hai → hreflang chứ không phải bài mới. Đúng ra phải BLOCK |
| Bài 180 từ trùng thuật ngữ chuyên ngành | Density cao oan | Đã nới: <500 từ → ngưỡng ×1.6. Vẫn sai thì `--config` chỉnh |
| Anchor "Pearson official practice" | Không commercial → không flag | OK |
| Trang accordion có text ẩn vì UX | Không flag (vì không chứa keyword) | **Đúng** — Google nói rõ accordion/tooltip vì usability thì ổn |

Phát hiện gate báo sai? Sửa `scripts/policy_gate.py` + thêm case vào
`scripts/tests/run_selftest.py`, rồi commit. Gate mà báo sai thì người ta sẽ tắt nó.

## Trường hợp đặc thù PTE Magic (dễ vấp nhất)

### 1. 32 bài "study in <nước>" — `TEMPLATE_SHELL`

4 nước × 8 chủ đề (định dạng, việc làm, chỗ ở, visa, học bổng, trường, chi phí, việc part-time)
= 32 bài cùng một cái vỏ.

`policy_gate.py --corpus` sẽ BLOCK. **Không phải** vì Google phạt "có nội dung cho 4 nước"
— mà vì *hàng chục bài trông gần như nhau, chỉ khác tên nước*.

- **Nếu làm được** khác biệt thật (học phí của trường A, yêu cầu thật của cơ quan di trú nước đó,
  số liệu học viên thật) → không phải doorway, gate sẽ PASS (vì thân khác nhau).
- **Nếu không** → gộp thành 1 bài có bảng so sánh + 301 các bài còn lại.
  Gộp đúng cách thường tăng cả traffic lẫn vị trí.

### 2. Nội dung visa/định cư = YMYL → `YMYL_MISSING_EVIDENCE`

Bài về điểm số cho y tá, học bổng, chi phí, hồ sơ thường trú **phải** có:
`author` có chức danh + URL profile · ngày cập nhật ≤90 ngày · link tới
`homeaffairs.gov.au` / `canada.ca` / `immigration.govt.nz` / `gov.uk` / `pearsonpte.com`.

Và **không được** viết "bạn chắc chắn sẽ đậu nếu làm đúng các bước". Xem `GUARANTEE_CLAIM`.

### 3. "Đề thi thật" — `OFF_TOPIC` + rủi ro pháp lý Pearson

Bài `/pte-essay-topics` hiện **xử lý đúng**, giữ làm mẫu:
> "These are practice prompts written in the style and register PTE uses. They are not
> copied from live tests — no one outside Pearson has the live item bank."

Bản dịch Việt phải giữ nguyên câu này. **Không** đổi thành "đề thi thật 2026" cho hút click.
Câu đó là thứ bảo vệ cả khách lẫn bạn.

### 4. Guest post từ đối tác du học

Blog cho đối tác đăng bài = **có thể** site reputation abuse, **có thể** hoàn toàn ổn.
Tiêu chí của Google là *ý định*: nội dung có nằm trên domain đó vì relevance biên tập,
hay vì sức mạnh domain?

Yêu cầu tối thiểu:
- [ ] chủ đề **thuộc lĩnh vực** PTE / du học / định cư / luyện thi tiếng Anh
- [ ] có **editorial review** ghi lại được (ai duyệt, ngày nào)
- [ ] disclose rõ: "Bài do <đối tác> cung cấp, PTE Magic không được trả tiền để đăng"
- [ ] **không** có link trả phí trong bài. Nếu có → `rel="sponsored"` + disclosure riêng
- [ ] **không** dùng làm hạ tầng link cho đối tác (nếu 5 đối tác × 20 bài link về site họ
      = đó là **link scheme**, dù content có tốt)

Không đủ 5 → từ chối, giải thích bằng 1 đoạn. Khách sẽ tôn trọng bạn hơn.

## Việc của bạn khi gate BLOCK

1. Đọc **evidence** (script in ra bằng chứng, không chỉ kết luận)
2. Mở 1 file trong nhóm bị so trùng, đọc cạnh bài mới, tự hỏi: *"nếu mình là người dùng,
   có cần 2 trang này không?"*
3. Nếu **cần cả hai** → script sai → sửa script + thêm test case
4. Nếu **không cần** → hợp nhất, hoặc viết lại với góc độ thật sự khác, hoặc **huỷ bài**

Bước 4 có nghĩa là đôi khi câu trả lời đúng là "tuần này không publish gì mới".
Đó là một kết quả tốt.
