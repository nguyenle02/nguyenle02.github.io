# Core Web Vitals 2026 — ngưỡng & playbook cho Next.js

## Ngưỡng (p75, field data)

| Metric | 🟢 Good | 🟡 Needs improvement | 🔴 Poor |
|---|---|---|---|
| **LCP** | ≤ 2.5s | 2.5–4.0s | > 4.0s |
| **INP** | ≤ 200ms | 200–500ms | > 500ms |
| **CLS** | ≤ 0.10 | 0.10–0.25 | > 0.25 |
| TTFB (tham khảo, không phải CWV) | ≤ 800ms | 800–1800ms | > 1800ms |

**INP thay FID từ 12/03/2024.** FID bị loại khỏi Chrome CrUX API & PageSpeed Insights
ngày 09/09/2024; Lighthouse chưa bao giờ báo FID.
→ **Không** dùng FID trong bất kỳ output nào.

**Field vs Lab**
- **Field (CrUX)** = Chrome thật, p75, 28 ngày → **đây là thứ Google dùng**
- **Lab (Lighthouse)** = một máy, mô phỏng, giá trị chẩn đoán. Không phải KPI.
- Không có CrUX data (thiếu sample) → lab là proxy, và nói rõ nó là proxy.

KPI đúng: **% URL có cả LCP + INP + CLS = `GOOD` trên mobile** (mục tiêu ≥75%).
**Không** phải "điểm Lighthouse 90".

## Đo

```bash
export PSI_API_KEY=...     # không có key → quota ≈ 0, bạn sẽ gặp 429
python scripts/psi_cwv.py --url https://ptemagic.com/ --strategy both \
    --out reports/ptemagic/cwv.md --json-out data/cwv.json
python scripts/psi_cwv.py --config config/ptemagic.yaml    # đo 6 URL ưu tiên trong config
```

## Chẩn đoán Next.js — PTE Magic cụ thể

### LCP
| Nghi can | Bằng chứng | Fix |
|---|---|---|
| **`/_next/image` request `w=3840`** | đã quan sát trên hero, logo giải thưởng **và thumbnail card** của `/blogs` | `sizes` prop; kiểm tra `deviceSizes` trong `next.config.js` |
| Hero `priority` chưa bật | `prioritize-lcp-image` audit | `<Image priority>` cho ảnh LCP |
| Ảnh từ origin khác | `url=https%3A%2F%2Fcms.ptemagic.com%2Fwp-content%2F…` | 2 origin + 1 hop. cache-control, cân nhắc copy về cùng origin |
| HTML lớn trước khi paint | `html_bytes` từ `drift.py` | cắt payload |
| Font chặn render | `font-display` audit | `next/font` + `display:'swap'` + preload |

### CLS
- **Ảnh không có `width`/`height`** → `IMG_NO_DIMENSIONS`
- **Carousel render nội dung trùng** → trên `/vi`, cùng 3 testimonial xuất hiện **2 lần**;
  nhân bản node để làm loop vô hạn → giữ 1 bản, hoặc `aria-hidden` + CSS,
  hoặc nhân bản ở phía client
- **Nav sticky trên hero** → `top-nav` luôn là nguồn shift trên trang chủ EdTech
- Banner cookie/modal → reserve space

### INP
- Hydration lớn: `unused-javascript`, `dom-size`, `total-blocking-time`
- 400+ trang × carousel + analytics + chat widget
- Rủi ro cao nhất: trang có nhiều `useState` ở gốc. Ưu tiên `useTransition`, defer widget,
  `next/dynamic` + `ssr:false` cho phần không phải nội dung

## Playbook theo metric (thứ tự hiệu quả/giờ tốt nhất cho PTE Magic)

1. **Sửa `sizes` cho `next/image`** — ảnh hưởng **toàn bộ** site, một thay đổi component.
   Đây là fix số 1. Effort ~0.5 ngày.
2. `priority` + `fetchpriority="high"` cho ảnh LCP; **không** lazy nó
3. `next/font` (tự preload + `size-adjust`)
4. Ảnh trên **fold** tự host/inline; ngoài fold → `loading="lazy"`
5. Deferred script: analytics/chat/FB pixel sau khi idle (`next/script` `strategy="afterInteractive"`)
6. Cache-control + CDN policy cho `/_next/image` — hiện mỗi request có thể đang
   tới WordPress origin
7. Cache SSR/ISR cho `/blogs` và listing theo category
8. Cắt DOM: đừng render cả 2 biến thể mobile+desktop (vấn đề H1/carousel)
9. `content-visibility: auto` cho section thấp

## Định nghĩa "xong"

Không phải "điểm Lighthouse tăng". Là:
- [ ] số URL `GOOD` trên cả 3 metric **tăng** so với baseline
- [ ] kết quả **giữ nguyên** ≥4 tuần (CrUX 28 ngày → cần độ trễ)
- [ ] `drift.py compare` không có regression mới
- [ ] đo **trên 3G/4G thật, Android**, không chỉ trên máy dev

## Anti-pattern

| ❌ | Vì sao |
|---|---|
| Đuổi điểm Lighthouse 100 | đó là **lab**; bạn có thể đạt 100 bằng cách bỏ nội dung mà CrUX vẫn `POOR` |
| lazy-load ảnh LCP | làm LCP **tệ hơn** |
| Preload mọi thứ | cạnh tranh băng thông, kéo LCP xuống |
| AMP / "reduced-motion page" | đổi trải nghiệm lấy điểm số |
| Chặn JS 3 giây để có CLS đẹp | INP/CTR sẽ trả giá |
| Sửa 12 thứ rồi đo 1 lần | không quy được gì cho gì. **Một nhóm fix → một lần đo → commit** |
