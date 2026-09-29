---
name: seo-schema-markup
description: "Thiết kế, sinh và kiểm JSON-LD cho ptemagic.com: Organization, WebSite+SearchAction, Article, BlogPosting, FAQPage, BreadcrumbList, Course, Event, VideoObject, SoftwareApplication. Trigger: 'schema', 'structured data', 'JSON-LD', 'rich result', 'FAQ schema', 'breadcrumb', 'thêm markup'."
user-invocable: true
argument-hint: "<URL | 'generate' <loại trang>>"
license: MIT
metadata:
  version: "1.0.0"
  category: schema
---

# Structured Data — PTE Magic

## Nguyên tắc

1. **`mainEntityOfPage` là URL canonical của trang**, không phải URL đang xem
2. Schema phải **khớp nội dung nhìn thấy được**. Markup mô tả thứ không có trên trang =
   vi phạm (và với `FAQPage` thì từng bị Manual Action).
3. Một khối JSON-LD `<script type="application/ld+json">` trong `<head>`, không phải ba khối rời.
4. validate bằng [Rich Results Test](https://search.google.com/test/rich-results) +
   [schema.org validator](https://validator.schema.org) **trước** khi báo "đã xong"
5. Không kỳ vọng rich result — schema giúp máy hiểu thực thể; nó **không** phải yếu tố xếp hạng trực tiếp

## Script

```bash
python scripts/seo_audit.py --site <url> --only-url <URL>     # codes: JSONLD_*, ARTICLE_*, FAQ_*, ORG_SCHEMA_MISSING, BREADCRUMB_SCHEMA_MISSING
```

## Ma trận trang → schema

| Trang | Schema bắt buộc | Tuỳ chọn |
|---|---|---|
| `ptemagic.com/` + `/vi` | `Organization` (hoặc `EducationalOrganization`) + `WebSite` | `ProfessionalService`, `FAQPage` |
| `/features` | `WebPage`, `ItemList` của tính năng | `SoftwareApplication` (mobile/web) |
| `/exam-structure-pte-academic`, `-core` | `WebPage` + `BreadcrumbList` | `HowTo` (chỉ nếu đúng 5.3), `VideoObject` |
| `/blogs` | `CollectionPage` + `BreadcrumbList` + `ItemList` | `FAQPage` (trang này **có** FAQ) |
| Bài blog | `Article`/`BlogPosting` + `BreadcrumbList` | `FAQPage`, `HowTo`, `Quotation` |
| Khoá học / pricing | `Course` + `Offer` + `BreadcrumbList` | `AggregateRating` (**chỉ** nếu rating thật, hiển thị trên trang) |
| `/contact-us` | `Organization` + `ContactPoint` | `FAQPage` |
| Sự kiện ( hội thảo, webinar) | `Event` + `Organizer` | `Offer` |
| Trang tra điểm / tool | `WebApplication` + `BreadcrumbList` | `HowTo` |

## `Organization` — thứ PTE Magic đang không khai thác

Trang chủ hiện **không có** `Organization`/`EducationalOrganization`. Trong khi các giải thưởng
thật đang nằm trên trang **dưới dạng ảnh** — máy không đọc được ảnh giải thưởng.

```json
{
  "@context": "https://schema.org",
  "@type": "EducationalOrganization",
  "name": "PTE Magic",
  "alternateName": "PTE Magic Practice Platform",
  "url": "https://ptemagic.com/",
  "logo": {"@type":"ImageObject","url":"https://ptemagic.com/magic-landing-page-assets/brand-mark.svg"},
  "sameAs": [
    "https://www.facebook.com/...", "https://www.linkedin.com/company/...",
    "https://www.youtube.com/...", "https://www.pearsonpte.com/"
  ],
  "award": [
    "Pearson's Elite Partner 2025",
    "Promising Education Technology Award 2023 (Edu 4.0)",
    "Member, Vietnam–Australia EdTech Alliance",
    "Top 10 EdTechList, Bett Asia"
  ],
  "memberOf": "Vietnam – Australia EdTech Alliance",
  "slogan": "Better Practice. Better Results."
}
```

**Cảnh báo khi khai:**
- `foundingDate`, `numberOfEmployees`, `aggregateRating` → **chỉ khai khi dữ liệu đó thật và
  hiển thị trên trang**. `aggregateRating` bịa là loại Manual Action kinh điển.
- `award` phải đối chiếu được. Trên `/vi` có "Top 20 thương hiệu giáo dục 2023"
  (`golden-brand.png`) nhưng bản EN **không có** → hoặc thêm vào EN, hoặc không khai ở EN.
- `sameAs` phải trỏ hồ sơ **chính chủ** do bạn kiểm soát (kênh social thật, không phải trang
  tổng hợp hồ sơ).

## `Article` — PTE Magic đang thiếu author & datePublished

`seo_audit.py` báo `ARTICLE_NO_AUTHOR` và `ARTICLE_NO_DATE`.

```json
{
  "@type": "Article",
  "headline": "<≤110 ký tự>",
  "description": "<meta description>",
  "image": ["https://ptemagic.com/...webp"],
  "datePublished": "2026-09-02T18:00:50+00:00",
  "dateModified":  "2026-09-25T09:00:00+00:00",
  "author": [{"@type":"Person","name":"Trần Minh Anh",
              "jobTitle":"PTE Trainer","url":"https://ptemagic.com/team/tran-minh-anh",
              "sameAs":["https://www.linkedin.com/in/..."]}],
  "reviewer": [{"@type":"Person","name":"Nguyễn Thu Hà","jobTitle":"Head of Training"}],
  "publisher": {"@type":"EducationalOrganization","name":"PTE Magic",
                "logo":{"@type":"ImageObject","url":"..."}},
  "mainEntityOfPage": {"@type":"WebPage","@id":"https://ptemagic.com/pte-essay-topics"},
  "inLanguage": "en",
  "isAccessibleForFree": true
}
```

Ba thứ đáng thêm mà đối thủ hiếm khi có: `reviewer` (trainer duyệt — quyền tác giả
tầng 3 của E-E-A-T) và `inLanguage` (`en` / `vi`, khớp với `lang=`).

`dateModified` phải **là ngày sửa thật**. `lastmod` trong sitemap của PTE Magic hiện
= thời điểm build (xem audit H1) — đừng nhân bản lỗi đó vào schema.

## `FAQPage` — điều kiện cứng

Trang `/blogs` có 8 mục FAQ nhưng render dưới dạng accordion và không có schema
(`FAQ_MISSING_ANSWER` xuất hiện khi Question thiếu `acceptedAnswer`).

```json
{"@type":"FAQPage","mainEntity":[
  {"@type":"Question","name":"What is the difference between PTE Academic and PTE Core?",
   "acceptedAnswer":{"@type":"Answer","text":"PTE Academic serves study and migration for
     Australia/NZ/UK; PTE Core is accepted for Canadian economic immigration streams.
     Both are 10–90 scored and reported within about 48 hours."}}
]}
```

- Mỗi Question **phải** có `acceptedAnswer.text`. Chỉ có tên → không đủ điều kiện rich result
  (và là hành vi bị Google xử lý từ 2019: markup mô tả nội dung không có trên trang)
- `text` là câu trả lời **đầy đủ**, không phải teaser. Ngắn: 40–80 từ
- Câu hỏi phải là câu người dùng thật gõ. `How long is the score valid?` → nên viết
  `How long is a PTE score valid?` (chính nó cũng giúp được trích trong AI Overview)
- **Không** lặp 1 bộ FAQ cho mọi trang → `policy_gate.py` sẽ bắt near-duplicate
- Từ 2019, FAQ rich result chủ yếu dành cho site **nhà nước/y tế**; với site thương mại
  lợi ích thật nằm ở việc được trích dẫn trong câu trả lời AI, không ở ngôi sao trên SERP

## `Course` + `Offer` cho trang khoá học

```json
{"@type":"Course","name":"PTE Magic Academic Course",
 "description":"...","provider":{"@type":"EducationalOrganization","name":"PTE Magic"},
 "educationalLevel":"PTE Academic 65+","inLanguage":["en","vi"],
 "hasCourseInstance":{"@type":"CourseInstance","courseMode":"Online",
   "courseWorkload":"PT4H"},
 "offers":{"@type":"Offer","price":"0","priceCurrency":"USD","category":"Free trial",
           "url":"https://ptemagic.com/sso/auth/register"}}
```
Chỉ khai `offers` khi giá đó **hiển thị trên trang**. Không khai giá "từ $0" rồi dẫn tới
checkout $200 — vừa là trải nghiệm tệ vừa là hành vi bị xử lý dưới nhóm hành vi quảng cáo sai lệch.

## `SoftwareApplication` cho app luyện thi

`operatingSystem`, `applicationCategory":"EducationalApplication",` `offers`. Nếu có
`aggregateRating` → **phải** là rating có thật, có đếm được, hiển thị trên trang.
Không có → bỏ thuộc tính.

## Kiểm tra cuối

- [ ] JSON parse được (`JSONLD_PARSE_ERROR` = 0)
- [ ] Rich Results Test: pass, không warning nào có chữ "Missing field"
- [ ] `url`/`@id` là **tuyệt đối**, đúng scheme (`https`), không trailing slash lung tung
- [ ] Ảnh trong `logo`/`image` truy cập được trực tiếp (không cần referer)
- [ ] `inLanguage` khớp `lang=` của `<html>` — PTE Magic có trang `lang="en"` nhưng nội dung
      tiếng Việt (audit H2/C2)
- [ ] Trang app (`/sso/*`, `/dashboard/*`) **không** có `Article` schema
- [ ] Schema tự động sinh (Next.js `generateMetadata` / headless CMS) — sửa ở nguồn, không sửa
      từng file, nếu không lần build sau sẽ mất
