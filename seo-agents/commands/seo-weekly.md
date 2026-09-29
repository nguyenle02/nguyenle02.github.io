---
description: "Báo cáo SEO tuần cho ptemagic.com — non-brand click, delta theo locale, striking distance, content decay, CWV, và 3 việc cần làm."
argument-hint: "[--days N]"
allowed-tools: Bash(python scripts/*), Read, Write, Grep, Glob
---

Weekly report — tuần của **$ARGUMENTS**

```bash
python scripts/gsc_pull.py --days ${1:-28} --compare-previous --out data/gsc-weekly.csv
python scripts/cluster_keywords.py --in data/gsc-weekly.csv --out data/weekly-clusters.md
python scripts/drift.py compare --site https://ptemagic.com
python scripts/psi_cwv.py --url https://ptemagic.com/ --strategy mobile
```

Viết `reports/ptemagic/$(date +%F)-weekly.md` theo `templates/weekly-report.md`,
**tối đa 1 trang**:

1. **KPI**: non-brand click + `sign_up_free`. Tổng click chỉ là tham khảo.
2. Delta vs tuần trước, **tách EN / VI**
3. Top 5 query tăng · top 5 giảm
4. **Striking distance** (pos 5–15, impression cao) → với mỗi cái: URL, cần gì, ai làm
5. **Content decay** (click giảm ≥30%) → nguyên nhân: tụt vị trí / nội dung cũ / đối thủ mới / update
6. **3 việc cho tuần này** + owner

Kỷ luật:
- Mọi số có **nguồn + ngày**. Không có → `not measured`.
- Không ngoại suy, không dự báo, không tô vẽ. Giảm 8% = "giảm 8%".
- Nếu `gsc_pull.py` fail (thiếu credentials) → in lỗi, **dừng**, không viết report suông.
- `drift.py compare` có critical → đặt nó **lên đầu** báo cáo, trên mọi thứ khác.

Nếu không có gì đáng nói, viết 3 dòng rồi kết luận "không có hành động".
Không sản xuất 4 trang để trông bận rộn.
