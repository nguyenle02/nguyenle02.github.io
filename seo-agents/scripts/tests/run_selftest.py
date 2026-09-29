#!/usr/bin/env python3
"""Self-test cho bộ script SEO.

Chạy KHÔNG cần mạng: sinh fixture → chạy audit → chạy policy gate → đối chiếu
với danh sách finding bắt buộc phải phát hiện được.

    python scripts/tests/run_selftest.py

Exit code 0 = tất cả PASS. Đây là thứ nên chạy sau mỗi lần sửa script.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
FIXDIR = os.path.join(HERE, "fixtures", "ptemagic")
PY = sys.executable

# (code phải xuất hiện, vì sao nó quan trọng với ptemagic.com)
AUDIT_EXPECTATIONS = [
    ("MULTIPLE_H1",                    "Trang chủ EN và /vi đang có nhiều H1 (biến thể mobile+desktop)"),
    ("NEXT_IMAGE_OVERSIZED_W",         "/_next/image đang request w=3840 cho cả thumbnail"),
    ("DUPLICATE_TEXT_BLOCK_IN_PAGE",   "/vi lặp nguyên khối testimonial 2 lần"),
    ("LOCALE_CONTENT_MISMATCH",        "Bài tiếng Việt nằm trên path root của domain EN"),
    ("LANG_MISMATCH",                  'lang="en" nhưng nội dung tiếng Việt'),
    ("NEAR_DUPLICATE_CONTENT",         "2 bài chung 1 vỏ, chỉ đổi tên quốc gia (doorway pattern)"),
    ("TITLE_BRAND_DUPLICATED",         "Title /blogs = 'PTE Magic - PTE Magic Blog'"),
    ("BLOG_TITLE_NOT_LINKED",          "Trên /blogs, tiêu đề bài viết không phải anchor"),
    ("CANONICAL_MISSING",              "Nhiều trang không có rel=canonical"),
    ("ARTICLE_NO_AUTHOR",              "Schema Article thiếu author → yếu E-E-A-T"),
    ("ARTICLE_NO_DATE",                "Schema Article thiếu datePublished"),
    ("FAQ_MISSING_ANSWER",             "FAQPage có Question thiếu acceptedAnswer"),
    ("ANCHOR_VAGUE",                   "Link 'Read more' không có giá trị anchor"),
    ("PAID_LINK_MISSING_REL",          "Link có utm_ nhưng thiếu rel=sponsored"),
    ("HREFLANG_ABSENT_SITEWIDE",       "Site đa ngôn ngữ nhưng không có hreflang"),
    ("IMG_ALT_MISSING",                "Ảnh thiếu alt"),
    ("VIEWPORT_MISSING",               "Thiếu meta viewport"),
    ("THIN_CONTENT",                   "Trang quá mỏng"),
]

POLICY_EXPECTATIONS = [
    ("NEAR_DUPLICATE",       "Bài mới giống bài đã publish ≥70%"),
    ("TEMPLATE_SHELL",       "Nhiều URL dùng chung 1 vỏ"),
    ("KEYWORD_STUFFING",     "Mật độ exact-match vượt ngưỡng"),
    ("YMYL_MISSING_EVIDENCE","Nội dung visa/định cư thiếu author/ngày/nguồn"),
    ("HIDDEN_TEXT",          "Text ẩn chứa keyword"),
    ("ANCHOR_OVER_OPTIMIZED","Anchor ra ngoài nhồi exact-match"),
]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def section(title):
    print(f"\n{'═'*72}\n{title}\n{'═'*72}")


def main() -> int:
    failures: list[str] = []

    # ---- 0. fixtures ----
    section("0. Sinh fixture")
    r = run([PY, os.path.join(HERE, "make_fixtures.py")])
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("✗ không sinh được fixture"); return 2

    # ---- 1. seo_audit ----
    section("1. scripts/seo_audit.py (chế độ offline)")
    outdir = tempfile.mkdtemp(prefix="seo-selftest-")
    r = run([PY, os.path.join(SCRIPTS, "seo_audit.py"),
             "--offline-dir", FIXDIR, "--out", outdir, "--delay", "0",
             "--config", os.path.join(ROOT, "config", "ptemagic.yaml")])
    sys.stderr.write(r.stderr)
    json_path = os.path.join(outdir, sorted(os.listdir(outdir))[0]) if os.listdir(outdir) else None
    jsons = [f for f in os.listdir(outdir) if f.endswith(".json")]
    if not jsons:
        print("✗ audit không sinh JSON"); return 2
    data = json.load(open(os.path.join(outdir, jsons[0]), encoding="utf-8"))
    codes = data["by_code"]
    print(f"Điểm: {data['score']}/100 · {data['pages_audited']} trang · "
          f"{len(data['findings'])} finding · {len(codes)} loại code\n")
    for code, why in AUDIT_EXPECTATIONS:
        ok = codes.get(code, 0) > 0
        print(f"  {'✓' if ok else '✗'} {code:32s} n={codes.get(code,0):2d}  {why}")
        if not ok:
            failures.append(f"audit không phát hiện {code} ({why})")

    # ---- 2. policy_gate ----
    section("2. scripts/policy_gate.py")
    gate_root = tempfile.mkdtemp(prefix="seo-gate-")
    cases = _write_policy_cases(gate_root)
    for name, (case_dir, expect_codes, expect_verdict) in cases.items():
        target = os.path.join(case_dir, "file.md")
        corpus = os.path.join(case_dir, "corpus")
        r = run([PY, os.path.join(SCRIPTS, "policy_gate.py"),
                 "--file", target, "--corpus", corpus, "--json"])
        try:
            res = json.loads(r.stdout)
        except Exception:
            print(f"  ✗ {name}: không parse được output\n{r.stdout[:400]}{r.stderr[:600]}")
            failures.append(f"policy_gate crash trên {name}")
            continue
        got = {c["code"] for c in res["checks"]}
        verdict = res["verdict"]
        ok = expect_codes <= got and verdict == expect_verdict
        print(f"  {'✓' if ok else '✗'} {name:22s} verdict={verdict:5s} (muốn {expect_verdict:5s})  "
              f"codes={sorted(got) if got else '[]'}")
        if not ok:
            failures.append(f"policy_gate {name}: verdict={verdict} (muốn {expect_verdict}), "
                            f"thiếu {sorted(expect_codes - got)}, thừa-block "
                            f"{sorted(c for c in got - expect_codes if c in BLOCK_CODES)}")

    for code, why in POLICY_EXPECTATIONS:
        r2 = run([PY, "-c",
                  f"import sys;sys.path.insert(0,{SCRIPTS!r});"
                  f"import policy_gate as pg;print({code!r} in pg.ALL_CHECK_CODES)"])
        ok = r2.stdout.strip() == "True"
        print(f"  {'✓' if ok else '✗'} registry có {code:24s} {why}")
        if not ok:
            failures.append(f"policy_gate thiếu check {code}")

    # ---- 3. cluster_keywords ----
    section("3. scripts/cluster_keywords.py")
    csv_path = os.path.join(outdir, "gsc-sample.csv")
    open(csv_path, "w", encoding="utf-8").write(_SAMPLE_GSC)
    r = run([PY, os.path.join(SCRIPTS, "cluster_keywords.py"),
             "--in", csv_path, "--out", os.path.join(outdir, "clusters.md")])
    ok = r.returncode == 0 and os.path.exists(os.path.join(outdir, "clusters.md"))
    md = open(os.path.join(outdir, "clusters.md"), encoding="utf-8").read() if ok else ""
    checks = [("NEW", "đề xuất tạo bài mới"), ("REFRESH", "đề xuất refresh bài top 5-20"),
              ("C5", "nhận ra cluster PTE Core"), ("BOFU", "phân loại funnel")]
    for needle, why in checks:
        good = needle in md
        print(f"  {'✓' if good else '✗'} output chứa {needle:10s} {why}")
        if not good:
            failures.append(f"cluster_keywords output thiếu {needle}")
    if r.stderr.strip():
        print("   stderr:", r.stderr.strip()[:300])

    # ---- 4. drift ----
    section("4. scripts/drift.py")
    base = os.path.join(outdir, "baseline.json")
    r1 = run([PY, os.path.join(SCRIPTS, "drift.py"), "baseline",
              "--offline-dir", FIXDIR, "--baseline", base, "--delay", "0"])
    r2 = run([PY, os.path.join(SCRIPTS, "drift.py"), "compare",
              "--offline-dir", FIXDIR, "--baseline", base, "--out", outdir, "--delay", "0"])
    ok = r1.returncode == 0 and r2.returncode == 0
    print(f"  {'✓' if ok else '✗'} baseline + compare chạy không lỗi")
    if not ok:
        failures.append("drift.py lỗi: " + (r1.stderr or r2.stderr)[:300])
        print((r1.stderr + r2.stderr)[:600])

    # ---- tổng kết ----
    section("KẾT QUẢ")
    if failures:
        print(f"✗ {len(failures)} FAIL:")
        for f in failures:
            print("   -", f)
        return 1
    print("✓ TẤT CẢ PASS")
    return 0


BLOCK_CODES = {
    "NEAR_DUPLICATE", "TEMPLATE_SHELL", "KEYWORD_STUFFING", "HEADING_KEYWORD_STUFFED",
    "HIDDEN_TEXT", "CLOAKING_BOT_SNIFFING", "ANCHOR_OVER_OPTIMIZED", "PAID_LINK_MISSING_REL",
    "SITE_REPUTATION_ABUSE", "EXPIRED_DOMAIN_REUSE", "GUARANTEE_CLAIM",
    "YMYL_NO_AUTHOR", "YMYL_NO_DATE", "YMYL_STALE", "YMYL_NO_OFFICIAL_SOURCE",
    "YMYL_MISSING_EVIDENCE",
}


def _write_case(root: str, name: str, file_md: str, corpus: dict[str, str]):
    """Mỗi case là 1 thư mục cách ly: file.md + corpus/*.md (nội dung ĐÃ publish)."""
    d = os.path.join(root, name)
    os.makedirs(os.path.join(d, "corpus"), exist_ok=True)
    open(os.path.join(d, "file.md"), "w", encoding="utf-8").write(file_md)
    for fname, content in corpus.items():
        open(os.path.join(d, "corpus", fname), "w", encoding="utf-8").write(content)
    return d


def _write_policy_cases(root: str) -> dict[str, tuple[str, set[str], str]]:
    """Trả về {tên case: (thư mục, tập code bắt buộc, verdict bắt buộc)}."""
    cases: dict[str, tuple[str, set[str], str]] = {}

    # -- 1. Bài đạt chuẩn: author + ngày + số liệu độc quyền + nguồn chính thức --------------
    good = """---
title: "PTE Core Write Email: Template và 5 lỗi mất điểm"
primary_keyword: "PTE Core write email"
author: "Trần Minh Anh"
author_url: "https://ptemagic.com/team/tran-minh-anh"
date_published: "2026-09-20"
date_modified: "2026-09-25"
---

# PTE Core Write Email: Template và 5 lỗi mất điểm

Bài này dựa trên 1.240 bài email luyện tập đã được chấm bằng hệ thống AI của PTE Magic
trong tháng 8 năm 2026, cộng với phản hồi trực tiếp từ trainer Nguyễn Thu Hà. Chúng tôi
không suy ra từ tài liệu công khai mà đo trên chính dữ liệu luyện tập của học viên.

## Format mà Pearson yêu cầu

Task này cho bạn 20 phút và yêu cầu 50 đến 120 từ. Đề bài mô tả một tình huống giao tiếp
hàng ngày kèm ba gạch đầu dòng bắt buộc phải phủ đủ. Theo hướng dẫn chính thức của
Pearson, bài thi được chấm trên bốn tiêu chí: Content, Form, Grammar và Vocabulary.

## 5 lỗi học viên Việt Nam hay mắc nhất

Số liệu dưới đây lấy từ bộ chấm AI của PTE Magic trên 1.240 bài, không phải ước lượng.

1. Viết vượt 120 từ. 34 phần trăm bài luyện tập vượt giới hạn và bị trừ điểm Form.
2. Thiếu câu chào mở đầu. 22 phần trăm bài đi thẳng vào nội dung.
3. Dùng giọng quá trang trọng cho một tình huống thân mật với bạn bè.
4. Phủ thiếu một trong ba gạch đầu dòng mà đề bài đưa ra.
5. Không có câu kết, khiến bài dừng lại đột ngột giữa chừng.

Lỗi thứ tư là lỗi nặng nhất vì nó trừ trực tiếp vào Content, tiêu chí duy nhất có thể
kéo cả bài về 0. Trong số 1.240 bài chúng tôi phân tích, 19 phần trăm mất điểm Content
chỉ vì bỏ sót đúng một gạch đầu dòng.

## Template do trainer viết, có giải thích từng câu

Dear Sir or Madam,

I am writing to ask about the part-time library position advertised on your website last
Monday. I am a second-year student and I am available on weekday evenings.

Câu mở đầu nêu đúng mục đích trong một câu, không vòng vo. Câu thứ hai trả lời gạch đầu
dòng về thời gian. Trainer Hà chọn cấu trúc này vì nó giữ được dưới 120 từ mà vẫn phủ đủ
ba ý, dựa trên 214 bài đạt điểm Form tối đa trong tập dữ liệu.

## Vì sao template học thuộc lòng vẫn bị trừ điểm

Chúng tôi so sánh hai nhóm: nhóm dùng template nguyên văn và nhóm dùng template nhưng
thay chi tiết theo đề. Nhóm thứ hai có điểm Content trung bình cao hơn 2,4 trên thang 10
trong tập 1.240 bài nói trên. Lý do là Pearson chấm Content theo mức phủ đúng các gạch
đầu dòng của đề, không chấm theo độ trôi chảy của câu mở đầu.

## Nguồn tham khảo

- Hướng dẫn chính thức của Pearson: https://www.pearsonpte.com
- Dữ liệu chấm AI nội bộ PTE Magic, tháng 8 năm 2026, n = 1240 bài luyện tập

Reviewed by: Trần Minh Anh (Trainer PTE, 6 năm kinh nghiệm) · 2026-09-25
"""
    d = _write_case(root, "01-good", good, {})
    cases["01-good (bài đạt chuẩn)"] = (d, set(), "PASS")

    # -- 2. Near-duplicate: cùng vỏ, đổi 1 biến thể ------------------------------------------
    dup = good.replace("PTE Core Write Email", "PTE Core Write Summary").replace(
        "Write Email và yêu cầu", "Write Summary").replace(
        "bài email luyện tập", "bài summary luyện tập")
    d = _write_case(root, "02-near-duplicate", dup, {"published-write-email.md": good})
    cases["02-near-duplicate"] = (d, {"NEAR_DUPLICATE"}, "BLOCK")

    # -- 3. Keyword stuffing ------------------------------------------------------------------
    stuffed = """---
title: "pte mock test online miễn phí tốt nhất"
primary_keyword: "pte mock test"
author: "SEO Team"
date_published: "2026-09-01"
date_modified: "2026-09-01"
---

# pte mock test

Làm pte mock test miễn phí. pte mock test online giúp bạn đạt điểm cao trong kỳ thi.
pte mock test là cách tốt nhất để luyện tập. Hãy thử pte mock test ngay hôm nay.
pte mock test pte mock test pte mock test online miễn phí tốt nhất.

## pte mock test speaking

pte mock test speaking được chấm bằng AI hoàn toàn miễn phí. Thử pte mock test speaking.

## pte mock test writing

pte mock test writing có phản hồi chi tiết từng tiêu chí. Làm pte mock test writing ngay.

## pte mock test reading

pte mock test reading theo đúng format Pearson. pte mock test reading miễn phí 100 phần trăm.

## pte mock test listening

pte mock test listening có 8000 câu hỏi. Làm pte mock test listening online.
"""
    d = _write_case(root, "03-keyword-stuffing", stuffed, {})
    cases["03-keyword-stuffing"] = (d, {"KEYWORD_STUFFING"}, "BLOCK")

    # -- 4. YMYL thiếu evidence + cam kết kết quả ---------------------------------------------
    ymyl = """---
title: "Cách xin visa định cư Úc diện tay nghề 2026"
primary_keyword: "visa định cư Úc diện tay nghề"
---

# Cách xin visa định cư Úc diện tay nghề 2026

Bạn cần đạt điểm PTE 79 để được cộng 20 điểm trong hệ thống tính điểm di trú. Hồ sơ nộp
qua SkillSelect và chờ thư mời. Visa 189 và visa 190 có yêu cầu khác nhau về bảo lãnh
bang. Chi phí sinh hoạt tại Úc khoảng 25.000 AUD một năm cho một du học sinh.

Bạn chắc chắn sẽ đậu visa nếu làm đúng các bước sau đây. Chúng tôi cam kết đậu 100 phần
trăm cho học viên đăng ký khoá luyện thi. Hãy nộp hồ sơ ngay trong tháng này để kịp chỉ
tiêu của năm tài khoá.

## Các bước nộp hồ sơ

Bước một là thẩm định tay nghề. Bước hai là đạt điểm tiếng Anh. Bước ba là nộp Expression
of Interest. Bước bốn là chờ thư mời và nộp hồ sơ chính thức.
"""
    d = _write_case(root, "04-ymyl-missing-evidence", ymyl, {})
    cases["04-ymyl-missing-evidence"] = (d, {"YMYL_MISSING_EVIDENCE", "GUARANTEE_CLAIM"}, "BLOCK")

    # -- 5. Hidden text + anchor over-optimised + link thiếu rel -------------------------------
    hidden = """---
title: "PTE Listening: chiến thuật từng dạng câu hỏi"
primary_keyword: "pte listening"
author: "Lê Duy Nguyên"
date_published: "2026-09-10"
date_modified: "2026-09-20"
---

# PTE Listening: chiến thuật từng dạng câu hỏi

<span style="color:#ffffff;font-size:0px">pte listening tips pte listening practice test
free pte mock test online cheap pte course discount code pte listening answers</span>

Phần Listening của bài thi PTE gồm tám dạng câu hỏi khác nhau, mỗi dạng có cách tính điểm
và áp lực thời gian riêng. Nội dung dưới đây dựa trên phân tích 800 bài luyện tập của học
viên PTE Magic trong quý 2 năm 2026, và chúng tôi đo được dạng Highlight Correct Summary
là dạng mất điểm nhiều nhất với 41 phần trăm lượt trả lời sai.

## Liên kết tham khảo

<a href="https://spam-partner.example/buy">best pte mock test online</a>
<a href="https://spam-partner.example/coupon">cheap pte course discount</a>
<a href="https://spam-partner.example/deal">pte practice test free download</a>
<a href="https://www.pearsonpte.com/pte-academic/test-format">Pearson official PTE test format</a>
"""
    d = _write_case(root, "05-hidden-text-anchors", hidden, {})
    cases["05-hidden-text-anchors"] = (d, {"HIDDEN_TEXT", "ANCHOR_OVER_OPTIMIZED"}, "BLOCK")

    # -- 6. Site reputation abuse: nội dung ngoài lĩnh vực -------------------------------------
    offtopic = """---
title: "Mã giảm giá Shopee và cách săn deal casino online"
primary_keyword: "mã giảm giá"
author: "Cộng tác viên"
date_published: "2026-09-15"
---

# Mã giảm giá Shopee và cách săn deal

Dưới đây là tổng hợp coupon code và mã giảm giá mới nhất. Ngoài ra bạn có thể tham khảo
các chương trình khuyến mãi casino và cá độ thể thao với tỷ lệ cược hấp dẫn. Chúng tôi
cũng có link vay nóng nhanh trong ngày với thủ tục đơn giản.

## Danh sách mã

Mã giảm giá 50 phần trăm cho đơn hàng đầu tiên. Coupon code áp dụng cho toàn bộ ngành hàng.
"""
    d = _write_case(root, "06-site-reputation-abuse", offtopic, {})
    cases["06-site-reputation-abuse"] = (d, {"SITE_REPUTATION_ABUSE"}, "BLOCK")

    # -- 7. Template shell: 9 URL chung 1 vỏ, thân gần như giống nhau ---------------------------
    shell_tpl = """---
title: "Cách du học {country} 2026: yêu cầu, chi phí, học bổng"
primary_keyword: "du học {country}"
author: "PTE Magic Content"
date_published: "2026-09-01"
date_modified: "2026-09-01"
---

# Cách du học {country} 2026

Du học {country} cần ba thứ: điểm tiếng Anh, hồ sơ tài chính và thư mời nhập học. Bài
viết này tóm tắt yêu cầu cơ bản cho {country} trong năm 2026.

## Yêu cầu tiếng Anh

Bạn cần chứng chỉ tiếng Anh còn hiệu lực. Nhiều trường tại {country} chấp nhận kết quả
thi PTE Academic với mức điểm phù hợp từng bậc học.

## Hồ sơ tài chính

Chuẩn bị sổ tiết kiệm và giấy tờ chứng minh thu nhập của người bảo lãnh theo yêu cầu của
cơ quan xét duyệt hồ sơ tại {country}.

## Thư mời nhập học

Nộp hồ sơ cho trường và chờ thư mời. Thời gian xử lý khác nhau tuỳ trường và tuỳ ngành.

## Học bổng

Có nhiều loại học bổng dành cho sinh viên quốc tế tại {country}, từ bán phần đến toàn phần.

## Kết luận

Chuẩn bị sớm giúp bạn chủ động hơn khi du học {country}.
"""
    countries = ["Úc", "Canada", "New Zealand", "Anh", "Mỹ", "Đức", "Hà Lan", "Singapore", "Ireland"]
    target = shell_tpl.replace("{country}", countries[0])
    corpus = {f"study-in-{i}.md": shell_tpl.replace("{country}", c)
              for i, c in enumerate(countries[1:], start=1)}
    d = _write_case(root, "07-template-shell", target, corpus)
    cases["07-template-shell (doorway)"] = (d, {"TEMPLATE_SHELL"}, "BLOCK")

    # -- 8. Chỉ WARN: bài ổn nhưng thiếu tín hiệu giá trị độc quyền ------------------------------
    warnish = """---
title: "PTE Speaking: giới thiệu tổng quan phần thi nói"
primary_keyword: "pte speaking"
author: "PTE Magic Content"
date_published: "2026-09-18"
date_modified: "2026-09-18"
---

# PTE Speaking: giới thiệu tổng quan phần thi nói

Phần thi nói của bài PTE Academic đánh giá khả năng phát âm và độ trôi chảy của thí sinh
thông qua nhiều dạng câu hỏi khác nhau. Thí sinh sẽ trả lời trực tiếp vào micro và hệ
thống chấm điểm tự động sẽ phân tích câu trả lời.

## Các dạng câu hỏi trong phần thi nói

Phần thi nói bao gồm Read Aloud, Repeat Sentence, Describe Image, Re-tell Lecture và
Answer Short Question. Mỗi dạng có một cách tiếp cận riêng và yêu cầu kỹ năng khác nhau.

## Cách tính điểm

Điểm phần nói được tính dựa trên hai tiêu chí là phát âm và độ trôi chảy. Hai tiêu chí
này cũng đóng góp vào điểm tổng của kỹ năng Speaking trong bảng điểm cuối cùng.

## Lời khuyên chung

Hãy luyện tập đều đặn mỗi ngày để cải thiện phản xạ. Giữ tốc độ nói ổn định và tránh
ngập ngừng quá lâu giữa các câu trả lời.

## Tổng kết

Phần thi nói là một phần quan trọng của bài thi và cần được chuẩn bị kỹ lưỡng trước khi
bạn bước vào phòng thi chính thức.
"""
    d = _write_case(root, "08-warn-only", warnish, {})
    cases["08-warn-only (thiếu value-add)"] = (d, {"NO_VALUE_ADD"}, "WARN")

    return cases


_SAMPLE_GSC = """query,page,country,device,clicks,impressions,ctr,position
pte core vs pte academic,https://ptemagic.com/exam-structure-pte-core,VN,mobile,12,840,0.014,11.2
pte core writing email,https://ptemagic.com/cau-truc-mau-dap-an-va-meo-thi-pte-core-writing-email,VN,mobile,5,210,0.024,18.4
pte repeat sentence practice,https://ptemagic.com/blogs,AU,mobile,0,690,0.0,42.1
pte write from dictation tips,https://ptemagic.com/blogs,IN,mobile,0,510,0.0,38.7
pte exam pattern,https://ptemagic.com/pte-exam-pattern,IN,mobile,145,2600,0.056,4.2
pte essay topics,https://ptemagic.com/pte-essay-topics,US,desktop,88,1900,0.046,3.1
pte score to ielts,https://ptemagic.com/how-does-pte-automated-scoring-work-a-complete-guide,VN,mobile,3,420,0.007,22.5
pte mock test online free,https://ptemagic.com/features,VN,mobile,21,1100,0.019,9.8
pte magic,https://ptemagic.com/,VN,mobile,610,1400,0.436,1.2
pte magic login,https://ptemagic.com/sso/auth/login,VN,mobile,240,600,0.4,1.0
study in australia for international students,https://ptemagic.com/how-to-study-in-australia-as-an-international-student,AU,mobile,9,300,0.03,14.2
pte accepted countries for nurses,https://ptemagic.com/list-of-pte-accepted-countries-for-nurses,PH,mobile,17,780,0.022,7.4
how long is pte score valid,,VN,mobile,0,260,0.0,61.0
pte retell lecture template,,IN,mobile,0,390,0.0,74.5
pte home b1,,GB,mobile,1,95,0.011,29.3
"""


if __name__ == "__main__":
    sys.exit(main())
