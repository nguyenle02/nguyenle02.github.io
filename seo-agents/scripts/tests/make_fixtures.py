#!/usr/bin/env python3
"""Sinh fixture HTML mô phỏng ĐÚNG các pattern lỗi đã quan sát trên ptemagic.com.

Đây là fixture tổng hợp (synthetic) dùng để test script khi không có mạng.
KHÔNG phải HTML thật của ptemagic.com — HTML thật không truy cập được từ sandbox.
Mỗi fixture tái hiện một pattern đã xác nhận bằng crawl nội dung thật:

  home.html          nhiều H1 (biến thể mobile+desktop cùng trong DOM), /_next/image w=3840
  vi.html            lang=vi, khối testimonial lặp nguyên văn 2 lần
  blog-list.html     title lặp brand "PTE Magic - PTE Magic Blog", tiêu đề card KHÔNG phải link
  post-en.html       Article schema thiếu author + thiếu datePublished
  post-vi-root.html  bài tiếng Việt nằm trên path ROOT của domain EN → locale mismatch
  post-en-near.html  bản gần trùng của post-en.html (đổi nước, giữ nguyên vỏ) → doorway pattern
  no-canonical.html  trang thiếu canonical + thiếu meta description + thiếu alt

Chạy:  python scripts/tests/make_fixtures.py
Test:  python scripts/tests/run_selftest.py
"""
from __future__ import annotations

import json
import os
import pathlib

HERE = pathlib.Path(__file__).parent
FIX = HERE / "fixtures" / "ptemagic"
BASE = "https://ptemagic.com"

NAV = """<nav><a href="{b}/features">Features</a><a href="{b}/blogs">Blog</a>
<a href="{b}/contact-us">Contact</a><a href="{b}/sso/auth/login">Sign in</a></nav>"""

FOOTER = """<footer>
<a href="{b}/exam-structure-pte-academic">About PTE Academic</a>
<a href="{b}/exam-structure-pte-core">About PTE Core</a>
<a href="https://ptemagic.com.vn/">Vietnamese PTE Coaching</a>
<a href="https://ptemagic.com.au/">International PTE Coaching</a>
<a href="{b}/privacy-policy">Privacy Policy</a>
<a href="{b}/privacy-policy">Payment &amp; Refund Policy</a>
<a href="{b}/blogs?page=1&amp;categoryIds=18">PTE Speaking</a>
</footer>"""


def page(title, body, *, lang="en", canonical=None, desc=None, jsonld=None,
         hreflang=None, viewport=True, robots=None, og=True):
    head = [f'<meta charset="utf-8">']
    if viewport:
        head.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    head.append(f"<title>{title}</title>")
    if desc:
        head.append(f'<meta name="description" content="{desc}">')
    if robots:
        head.append(f'<meta name="robots" content="{robots}">')
    if canonical:
        head.append(f'<link rel="canonical" href="{canonical}">')
    if og:
        head.append(f'<meta property="og:title" content="{title}">')
        head.append(f'<meta property="og:image" content="{BASE}/og.png">')
    for hl, href in (hreflang or []):
        head.append(f'<link rel="alternate" hreflang="{hl}" href="{href}">')
    for block in (jsonld or []):
        head.append(f'<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>')
    return (f'<!doctype html><html lang="{lang}"><head>{"".join(head)}</head>'
            f'<body>{NAV.format(b=BASE)}<main>{body}</main>{FOOTER.format(b=BASE)}</body></html>')


def nextimg(path, alt="", w=3840, q=75, dims=False):
    d = ' width="1200" height="630"' if dims else ""
    a = f' alt="{alt}"' if alt else ""
    return f'<img src="{BASE}/_next/image?url=%2F{path}&w={w}&q={q}"{a}{d}>'


# --------------------------------------------------------------------------- #
PAGES: dict[str, dict] = {}

# 1. Trang chủ EN — nhiều H1, ảnh w=3840, có Organization schema
body_home = f"""
<h1>Better Practice. Better Results.</h1>
<h1>Better Practice.</h1>
<h1>Better Results.</h1>
<h1>With PTE Magic Platform.</h1>
<p>Join 400,000+ students who trust PTE Magic to achieve their dream Pearson Test of English
scores for migration, study, or work abroad.</p>
<a href="{BASE}/sso/auth/register">Start for FREE</a>
{nextimg('magic-landing-page-assets/result-screen.png', 'Result Screen')}
<h2>Trusted by Thousands of PTE Test-Takers Worldwide</h2>
<h2>Trusted by Thousands of PTE Test-Takers Worldwide</h2>
<h3>400,000+ students</h3><h3>200+ partner institutions</h3>
<h3>60+ countries served</h3><h3>8,000+ exam-style questions</h3>
<h2>Why Choose the PTE Magic Platform?</h2>
<h4>Practice Question Bank with Answer Keys</h4>
<h4>Mock Tests with Full Score Reports</h4>
<h4>AI-Scored Speaking Practice</h4>
<h4>AI-Scored Writing Analysis</h4>
<h4>High-Scoring Exam Tips</h4>
{nextimg('magic-landing-page-assets/working-girl.png', 'PTE Test-Takers Worldwide')}
{nextimg('magic-landing-page-assets/edutech-reward.png', 'Promising Education Technology Award 2023')}
<h2>Real Students. Real Results</h2>
<blockquote>I had taken the PTE three times and kept falling short in speaking.
PTE Magic mock tests helped me score 83 overall.</blockquote>
<h6>Ravi - India</h6>
"""
PAGES["home.html"] = {
    "url": f"{BASE}/",
    "html": page("PTE Magic Practice App: Real PTE Online Mock Tests with AI Scores", body_home,
                 desc="Practice for PTE Academic and PTE Core with AI-scored mock tests, "
                      "8,000+ exam-style questions and instant feedback. Join 400,000+ students.",
                 jsonld=[{"@context": "https://schema.org", "@type": "Organization",
                          "name": "PTE Magic", "url": BASE,
                          "award": "Pearson Elite Partner 2025"}]),
}

# 2. Trang chủ VI — testimonial lặp 2 lần nguyên văn
TESTIMONIAL_VI = """<blockquote>PTE Magic có phần chấm điểm AI và feedback chi tiết giúp mình nhận ra
lỗi chính tả, ngữ pháp và cách triển khai ý chưa hợp lý. Sau 2 tháng luyện tập liên tục với mock
test và tài liệu hướng dẫn, mình đạt 68 overall, đúng như mục tiêu để hoàn tất hồ sơ định cư.</blockquote>
<h6>Thảo Nguyên</h6>
<blockquote>Mục tiêu của mình là đạt đủ điểm để nộp hồ sơ Working Holiday Visa. Mình được bạn bè
giới thiệu PTE Magic và thực sự bất ngờ vì lượng đề thi thật rất nhiều, lại có thi thử không giới
hạn. Khi đi thi thật mình không còn bỡ ngỡ và đã đạt Overall 40.</blockquote>
<h6>Tấn Thịnh</h6>
<blockquote>Khi chuyển sang PTE Magic platform, mình thấy tự tin hơn vì có AI chấm chi tiết từng
kỹ năng. Hai dạng bài mình lo nhất là RS và WFD. Mock test nhiều lần giúp mình quen với áp lực
phòng thi và mình đạt 89 overall.</blockquote>
<h6>Phương Quỳnh</h6>"""

body_vi = f"""
<h1>Nền tảng luyện thi PTE</h1>
<h1>hàng đầu chuẩn Pearson dành cho người Việt</h1>
<p>Được tin tưởng bởi 400,000+ học viên từ 60+ quốc gia để chinh phục kỳ thi PTE Academic và Core.</p>
<a href="{BASE}/sso/auth/register">Bắt đầu MIỄN PHÍ</a>
{nextimg('magic-landing-page-assets/result-screen-2.png', 'Result screen')}
<h2>Thành tựu nổi bật</h2>
<h4>Ngân hàng đề thi phong phú cho PTE Academic và PTE Core</h4>
<p>Kho đề thi đa dạng với hàng nghìn câu hỏi cập nhật sát với đề thi thực tế, giúp học viên làm
quen với cấu trúc và độ khó của kỳ thi PTE.</p>
<h4>Chấm điểm tức thì, phân tích chi tiết từng kỹ năng</h4>
<p>Hệ thống AI hiện đại cung cấp kết quả chấm điểm ngay lập tức, kèm phân tích chuyên sâu cho
Speaking và Writing.</p>
<h2>Học viên nói gì về PTE Magic?</h2>
{TESTIMONIAL_VI}
{TESTIMONIAL_VI}
{nextimg('magic-landing-page-assets/question-list-graphic.png', 'Question List PTE Magic')}
"""
PAGES["vi.html"] = {
    "url": f"{BASE}/vi",
    "html": page("Ứng dụng luyện thi PTE Magic: Đề thi thử PTE Online thực tế với điểm AI",
                 body_vi, lang="vi",
                 desc="Luyện thi PTE Academic và PTE Core với đề thi thử chấm điểm bằng AI, "
                      "hơn 8.000 câu hỏi sát đề thật. Hơn 400.000 học viên đã tin dùng.",
                 jsonld=[{"@context": "https://schema.org", "@type": "Organization",
                          "name": "PTE Magic", "url": BASE}]),
}

# 3. Trang danh sách blog — title lặp brand, card title không phải link
CARDS = ""
for slug, title, alt in [
    ("pte-exam-pattern", "PTE Exam Pattern 2026: Full Test Structure", "PTE Accepted Countries for Nurses 2026"),
    ("list-of-pte-accepted-countries-for-nurses", "PTE Accepted Countries for Nurses 2026", "How to Access and Share Your PTE Score"),
    ("how-to-access-and-share-your-pte-score-report-easily", "How to Access &amp; Share Your PTE Score", "PTE Home B1, A2 and A1"),
    ("pte-home-a1-a2-b1-tests-everything-you-need-to-know", "PTE Home B1, A2 and A1: Format, Pass Mark", "Why PTE Is Growing"),
    ("why-pte-is-becoming-more-popular-among-test-takers-worldwide", "Why PTE Is Growing in Popularity", "PTE Time Management"),
    ("time-management-tips-for-pte-exam-maximize-every-minute", "PTE Time Management: Tips per Section", "Common PTE Mistakes"),
    ("common-mistakes-in-pte-and-how-to-avoid-them", "Common PTE Mistakes and How to Avoid", "How to Stay Calm"),
    ("how-not-to-be-nervous-on-your-pte-test-date", "How to Stay Calm on PTE Test Day", "Essay Topics"),
]:
    CARDS += (f"<h5>{title}</h5>"
              f'<a href="{BASE}/{slug}">{nextimg("cms-thumb.webp", alt, w=3840)}</a>'
              f'<a href="{BASE}/blogs?page=1">Read more</a>')

FAQ = "".join(
    f'<h5>{q}</h5><p>{a}</p>' for q, a in [
        ("What is the difference between PTE Academic and PTE Core?",
         "PTE Academic is for study and migration; PTE Core is for Canadian economic migration."),
        ("What is PTE exam structure and duration?", "About 2 hours across Speaking, Writing, Reading, Listening."),
        ("How is the PTE exam scored?", "Automated scoring on a 10-90 scale across communicative skills."),
        ("How long is a PTE score valid?", "Two years from the test date."),
        ("How much does the PTE exam cost?", "Fees vary by country; check Pearson for current pricing."),
    ])

PAGES["blog-list.html"] = {
    "url": f"{BASE}/blogs",
    "html": page("PTE Magic - PTE Magic Blog",
                 f"<h1>PTE Magic Blog:</h1><h1>Your Roadmap to PTE Success</h1>"
                 f"<p>Dive into the best study resources, time-saving tips and updates for the PTE exam.</p>"
                 f"<h2>Featured Articles</h2><h4>PTE Essay Topics 2026: 60 Questions</h4>"
                 f"<h2>Latest Articles</h2>{CARDS}<h2>Frequently Asked Questions</h2>{FAQ}",
                 desc="PTE Magic blog.",
                 jsonld=[{"@context": "https://schema.org", "@type": "CollectionPage",
                          "name": "PTE Magic Blog"}]),
}

# 4. Bài viết EN — Article schema thiếu author/datePublished, FAQ thiếu acceptedAnswer
ESSAY_SECTIONS = [
    ("PTE Write Essay at a glance",
     "Write Essay is the final task of Part 1 Speaking and Writing. You get 20 minutes to plan, "
     "write and check a single essay of 200 to 300 words. Pearson scores it against seven traits "
     "worth 15 points in total: Content (3), Formal Requirement (2), Development Structure and "
     "Coherence (2), Grammar (2), General Linguistic Range (2), Vocabulary Range (2) and Spelling (2)."),
    ("Why Content is the trait that decides your mark",
     "Content is the only trait worth three points and it is the only trait that can zero the whole "
     "essay. An essay that is very short, very long, not in English, or written entirely in capitals "
     "scores zero automatically. Answering the question actually asked beats writing beautifully "
     "about something adjacent, so spend the first two minutes deciding what the prompt really wants."),
    ("The five PTE essay topic types",
     "Pearson describes the prompts as problem and solution statements, arguments for and against a "
     "position, and agree or disagree propositions. In practice two more shapes appear often enough "
     "to prepare for: advantages and disadvantages, and discuss both views. Each shape wants a "
     "different essay skeleton and using the wrong skeleton is the most common way to lose Content marks."),
    ("Agree or disagree prompts",
     "Some people believe university education should be free for all citizens. Working from home is "
     "more productive than working in an office. Governments should invest in public transport rather "
     "than build new roads. Take one clear position and defend it; do not sit on the fence."),
    ("Advantages and disadvantages prompts",
     "More and more people are choosing to live alone. Many companies offer unpaid internships. "
     "Online learning is replacing classroom teaching at many universities. Give both sides real "
     "weight, then say which one is larger and why."),
    ("Problem and solution prompts",
     "Traffic congestion is worsening in most large cities. Plastic waste in the oceans continues to "
     "increase. Housing has become unaffordable for young people. Answer in two parts: name the "
     "causes first, then propose specific measurable actions."),
    ("Discuss both views prompts",
     "Some people think exams are the best way to assess students while others prefer continuous "
     "assessment. Some argue governments should fund the arts while others say public money should go "
     "to essential services. Present both views and then give your own opinion, because omitting the "
     "opinion costs Content marks."),
    ("A full model answer",
     "The prompt asks whether social media has done more harm than good to society. The model answer "
     "opens by taking a clear position, spends one paragraph on the harm, one on the benefit, and a "
     "short conclusion that restates which side is heavier. It runs 268 words and uses four linking "
     "devices without repeating the same connector."),
    ("How PTE Magic scores your essay",
     "The platform returns feedback on grammar, spelling, vocabulary, cohesion and content relevance "
     "immediately after submission, mapped to the same traits Pearson uses. That mapping is built "
     "from analysis of practice essays written by learners who later sat the real test."),
    ("Common mistakes that cost marks",
     "Writing over 300 words, copying phrases from the prompt verbatim, using a memorised template "
     "that does not answer the question, and leaving no time to check spelling. Spelling errors are "
     "scored twice, once under Spelling and again under Vocabulary Range."),
    ("A 20 minute timing plan",
     "Two minutes to analyse the prompt and choose a position. Three minutes to outline three "
     "paragraphs. Twelve minutes to write. Three minutes to check spelling, subject verb agreement "
     "and word count. Practising this split is worth more than learning another template."),
    ("Where to practise next",
     "Start with the agree or disagree shape because it is the most common, then move to discuss both "
     "views which learners find hardest. Full length mock tests on the platform time all four skills "
     "in sequence so the essay does not feel isolated."),
]


def essay_body(country=None):
    """Vỏ bài viết. `country` mô phỏng pattern doorway: đổi 1 từ khoá, giữ nguyên toàn bộ vỏ."""
    out = ["<h1>PTE Essay Topics 2026: 60 Questions</h1>",
           "<p>PTE gives you one essay, 20 minutes and 200 to 300 words. The prompts recycle a small "
           "number of shapes rather than a fixed list of topics, so the fastest way to prepare is to "
           "practise the shapes. Below are 60 practice prompts sorted into the five shapes PTE "
           "actually uses, one full model answer, and the trait by trait breakdown that decides your mark.</p>"]
    for h2, para in ESSAY_SECTIONS:
        text = para
        if country:
            text = text.replace("PTE Write Essay at a glance", f"PTE Write Essay at a glance ({country})")
        out.append(f"<h2>{h2}</h2><p>{text}</p>")
    if country:
        out.append(f"<h2>Essay requirements for {country}</h2>"
                   f"<p>Learners applying to {country} should confirm the score their institution or "
                   f"visa category requires before booking, because requirements differ by programme.</p>")
    out.append(f'<a href="{BASE}/pte-exam-pattern">PTE exam pattern and full test structure</a>')
    out.append(f'<a href="{BASE}/features">Explore PTE Magic features</a>')
    out.append(f'<a href="{BASE}/how-does-pte-automated-scoring-work-a-complete-guide">How PTE automated scoring works</a>')
    out.append(f'<a href="{BASE}/time-management-tips-for-pte-exam-maximize-every-minute">Read more</a>')
    out.append('<a href="https://partner.example.com/?utm_source=ptemagic">Pearson partner</a>')
    out.append(nextimg("cms-thumb.webp", "PTE Essay Topics 2026"))
    return "\n".join(out)


PAGES["post-en.html"] = {
    "url": f"{BASE}/pte-essay-topics",
    "html": page("PTE Essay Topics 2026: 60 Questions | PTE Magic", essay_body(),
                 desc="60 PTE essay topics grouped by the five prompt types, plus a full model answer "
                      "and the seven traits Pearson scores. Write Essay is 20 minutes, 200-300 words.",
                 jsonld=[
                     {"@context": "https://schema.org", "@type": "Article",
                      "headline": "PTE Essay Topics 2026: 60 Questions",
                      "image": f"{BASE}/og.png"},
                     {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                         {"@type": "Question", "name": "How many PTE essay topics are there?"},
                         {"@type": "Question", "name": "How long is the PTE essay?",
                          "acceptedAnswer": {"@type": "Answer", "text": "20 minutes for 200-300 words."}}]}]),
}

# 6. Bản GẦN TRÙNG: đúng pattern doorway page — đổi 1 từ khoá quốc gia, giữ nguyên toàn bộ vỏ.
PAGES["post-en-near.html"] = {
    "url": f"{BASE}/pte-essay-topics-canada",
    "html": page("PTE Essay Topics for Canada 2026: 60 Questions | PTE Magic",
                 essay_body(country="Canada"),
                 desc="60 PTE essay topics for Canada grouped by the five prompt types, with a model "
                      "answer and the seven traits Pearson scores.",
                 canonical=f"{BASE}/pte-essay-topics-canada",
                 jsonld=[{"@context": "https://schema.org", "@type": "Article",
                          "headline": "PTE Essay Topics for Canada 2026: 60 Questions"}]),
}

# 5. Bài TIẾNG VIỆT nằm trên path ROOT của domain EN → locale mismatch (lỗi thật đã phát hiện)
VN_BODY = """<h1>Những thay đổi về điểm thi PTE quan trọng năm 2024</h1>
<p>Pearson đã công bố một số thay đổi về cách tính điểm kỳ thi PTE Academic trong năm 2024.
Học viên cần nắm rõ để chuẩn bị hồ sơ du học và định cư chính xác hơn.</p>
<h2>Thay đổi về thang điểm</h2>
<p>Thang điểm PTE vẫn giữ từ 10 đến 90, tuy nhiên cách quy đổi giữa các kỹ năng có điều chỉnh.
Điều này ảnh hưởng trực tiếp tới điểm overall mà học viên đạt được.</p>
<h2>Ảnh hưởng tới hồ sơ định cư Úc</h2>
<p>Bộ Nội vụ Úc yêu cầu điểm PTE tương đương IELTS cho từng diện visa. Học viên nên kiểm tra
yêu cầu mới nhất trên trang chính thức của cơ quan di trú trước khi nộp hồ sơ.</p>
<h2>Lời khuyên từ trainer PTE Magic</h2>
<p>Hãy luyện đề thi thử có chấm điểm AI để biết chính xác vị trí của mình, sau đó tập trung
vào kỹ năng yếu nhất thay vì học dàn trải cả bốn kỹ năng.</p>
<h2>Câu hỏi thường gặp</h2>
<p>Điểm PTE có giá trị trong bao lâu? Kết quả thi PTE có hiệu lực hai năm kể từ ngày thi.</p>
"""
PAGES["post-vi-root.html"] = {
    "url": f"{BASE}/nhung-thay-doi-ve-diem-thi-pte-quan-trong-nam-2024",
    "html": page("Những thay đổi về điểm thi PTE quan trọng năm 2024 | PTE Magic", VN_BODY,
                 lang="en",  # <-- cố ý SAI: lang=en nhưng nội dung tiếng Việt (pattern thật cần phát hiện)
                 desc="Cập nhật những thay đổi về điểm thi PTE năm 2024 và ảnh hưởng tới hồ sơ du học.",
                 jsonld=[{"@context": "https://schema.org", "@type": "Article",
                          "headline": "Những thay đổi về điểm thi PTE quan trọng năm 2024"}]),
}

# 7. Trang thiếu gần hết on-page cơ bản
PAGES["no-canonical.html"] = {
    "url": f"{BASE}/features",
    "html": page("Features",
                 "<h2>Tính năng</h2>" + nextimg("feature-1.png") + nextimg("feature-2.png")
                 + "<a href=''>empty</a><p>AI scoring, mock tests and question bank.</p>",
                 viewport=False, og=False),
}


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    manifest = []
    for fname, spec in PAGES.items():
        (FIX / fname).write_text(spec["html"], encoding="utf-8")
        manifest.append({"url": spec["url"], "file": fname, "status": 200,
                         "headers": {"content-type": "text/html; charset=utf-8",
                                     "strict-transport-security": "max-age=31536000"}})
        print(f"  {fname:22s} {len(spec['html'])//1024:3d}KB  {spec['url']}")
    (FIX / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ {len(manifest)} fixture tại {FIX}")


if __name__ == "__main__":
    main()
