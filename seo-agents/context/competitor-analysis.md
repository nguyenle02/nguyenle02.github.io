# Competitor Analysis — PTE Magic

> **Trạng thái dữ liệu: DANH SÁCH ỨNG VIÊN — CHƯA VERIFY.**
> `config/ptemagic.yaml → competitors.verification_status = "unverified_candidate_list"`.
> Agent **không** được coi file này là sự thật. Verify bằng Ahrefs
> (Organic competitors của `ptemagic.com`) hoặc Similarweb trước khi trích dẫn cho khách.

## Cách verify (30 phút, làm 1 lần)

```bash
# Ahrefs (cần token)
.venv/bin/python -c "
import os,requests,json
for ep in ['refdomains-history','organic-competitors','pages-top']:
    r=requests.get('https://api.ahrefs.com/v3/site-explorer/'+ep,
      params={'target':'ptemagic.com','mode':'subdomains','limit':20},
      headers={'Authorization':'Bearer '+os.environ['AHREFS_API_TOKEN']})
    print(ep, r.status_code, r.text[:400])"
# hoặc: Ahrefs UI → Site Explorer → ptemagic.com → Organic search → Competitors → export CSV
#      vào data/competitors.csv
```

Sau khi verify: cập nhật `verification_status: "verified"` + ngày, rồi **mới** dùng để ra quyết định.

## Khung phân tích (điền sau khi có data)

| Đối thủ | Traffic hữu cơ | Số URL | Blog mới/tháng | Content depth | Platform (mock test) | **Họ mạnh** | **Họ thiếu** |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Giả thuyết ban đầu (CẦN KIỂM CHỨNG — không dùng làm kết luận)

| Đối thủ | Vai trò giả định | Cách kiểm |
|---|---|---|
| **E2Language** | Strongest content authority, học viện lâu năm | organic gap cho query task-level |
| **Alfa PTE** | platform AI scoring, đối thủ trực tiếp nhất | so sánh **tính năng**, không so traffic |
| **Gurully** | platform + cộng đồng, mạnh ở Ấn Độ | ai link tới họ? |
| **APEUni** | app-first, cộng đồng lớn | họ có LLMO/AI-citable content không |
| **Language Academy** | SEO content dày, India | Cannibalisation query task |

**PTE Magic có thể dẫn về:** 400.000+ học viên · Pearson **Elite Partner** (rất hiếm) ·
đội sáng lập VN hiểu thí sinh VN · 8.000+ câu hỏi đã phân loại.

## Khoảng trống để nhắm

| Loại gap | Cách tìm | Vì sao |
|---|---|---|
| **Content gap** | Ahrefs Content Gap (≥3 trang top 10, PTE Magic không) | nhanh nhất |
| **Format gap** | họ toàn bài text → **tool** (score calculator) | tool được trích & link |
| **Locale gap** | bản dịch VI/AU của nội dung EN top | PTE Magic đã có 2 bản |
| **Data gap** | thống kê từ 400.000 học viên | **không ai copy được** |
| **Trust gap** | giải thưởng/partnership không nêu | đã có, không khai |
| **AI-citation gap** | AI trả lời mà không cite ai | `context/ai-citation-targets.md` |

**Data gap là lớn nhất.** Vài nghìn bài "PTE tips" không cạnh tranh được với
1 báo cáo *"PTE score reality: 400,000 attempts"* dựa trên dữ liệu thật.

## Không làm khi soi đối thủ

| ❌ | |
|---|---|
| Copy outline đối thủ sát tới mức đổi vài từ | `NEAR_DUPLICATE` (BLOCK) |
| "Họ làm X nên mình làm X" không qua bộ lọc value-add | scaled content abuse |
| Theo đối thủ sang query ngoài niche (loan, coupon, jobs) | site reputation abuse |
| So sánh "nhiều câu hỏi nhất" | assertion không có nguồn |
| Scrape SERP hàng loạt cho "AI rewrite" | vừa vi phạm TOS vừa cho ra scaled content |

## Theo dõi

| Chỉ số | Cadence | Nguồn |
|---|---|---|
| Traffic hữu cơ của 5 đối thủ | quý | Ahrefs |
| Content gap còn lại | quý | Ahrefs |
| Đối thủ được AI cite (25 prompt) | quý | `context/ai-citation-targets.md` |
| Đối thủ có feature mới | quý | `/features` của họ |
| **Đối thủ bị penalty** | sau spam update | traffic curve tụt + không có update nội dung |

Cột cuối có giá nhất: khi một đối thủ rơi sau spam update, hãy xem **chính xác** họ đã làm gì
và tự hỏi site mình có đang làm thế không.
