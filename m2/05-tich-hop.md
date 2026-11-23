---
title: Tích hợp và số liệu
kernelspec:
  name: python3
  display_name: Python 3
---

```{code-cell} python
:tags: [remove-cell]
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists()) / "m2"))
from m2data import *
import plotly.express as px
```

```{code-cell} python
:tags: [remove-input]
draft("Minh")
```

## Thứ tự xử lý một Publication

1. Với từng Version, đổi `\cite{k}` theo `key_map` của Version đó.
2. Chuẩn hóa từng nút bằng `normalize`.
3. **Băm từ lá lên gốc:** lá băm theo `(kind, content)`; nút cấu trúc băm theo
   `(kind, content, danh sách id con theo thứ tự)`. `element_id = <publication key>#<kind>-<16 hex đầu sha256>`.
4. **Khử trùng lặp giữa các Version:** hợp Element của mọi Version, mỗi `element_id` một dòng.
   Hai cây con giống hệt sau chuẩn hóa nhận cùng `element_id`.
5. Sinh cạnh `hierarchy`: một dòng cho mỗi cạnh nút → cha của một Version.

Thứ tự anh em không nằm trong bảng; nó được giữ ở dữ liệu trung gian của M2.

## Log, checkpoint, bất biến

- **Log Version:** mỗi Version theo metadata có đúng một dòng, trạng thái `parsed`,
  `empty_non_tex`, `failed` hoặc `missing`. Version không có TeX vẫn có bản ghi rỗng.
- **Checkpoint:** bỏ qua Publication khi sha256 của input và phiên bản mọi module không đổi.
- **Bất biến trước khi ghi bảng:** mọi `parent_id` trỏ tới `element_id` có thật, mọi key trích
  dẫn có trong `key_map`, ba bảng qua `validate()` của schema chung.

## Bộ mẫu phát triển

Plan 100 Publication lấy ngẫu nhiên có seed, kèm lệnh tải từ Hugging Face. Mọi gói đo
`metrics/<gói>.json` trên cùng bộ mẫu này để số liệu so sánh được.

## Số liệu đề yêu cầu trên 5 Range

Chạy `scripts/parse_range.py --member <m> --supplement-dir … --roots configs/m2-reviewed-roots.json`
trên toàn bộ corpus M1 của từng Range, có sidecar bibliography (xem
[Khôi phục bibliography](05b-khoi-phuc-bibliography.md)) và các file gốc đã review.

```{code-cell} python
:tags: [remove-input]
if RANGES:
    rows, tot = [], {}
    keys = ["publications_total", "publications_succeeded", "versions_total_metadata", "versions_parsed",
            "versions_empty_non_tex", "versions_failed", "elements_before_dedup", "elements_after_dedup",
            "bibtex_entries_before_dedup", "bibtex_entries_after_dedup", "elapsed_seconds", "output_dir_size_mb"]
    for m, r in RANGES.items():
        for k in keys:
            tot[k] = tot.get(k, 0) + r[k]
        tot["peak_rss_mb"] = max(tot.get("peak_rss_mb", 0), r["peak_rss_mb"])
    def row(name, r):
        tex = r["versions_parsed"] + r["versions_failed"]
        return {
            "Range": name,
            "Publication parse đủ": pt(r["publications_succeeded"], r["publications_total"]),
            "Version TeX parse được": pt(r["versions_parsed"], tex),
            "Element trước → sau khử trùng lặp": f"{so(r['elements_before_dedup'])} → {so(r['elements_after_dedup'])}",
            "BibTeX entry trước → sau": f"{so(r['bibtex_entries_before_dedup'])} → {so(r['bibtex_entries_after_dedup'])}",
            "Thời gian (phút)": so(r["elapsed_seconds"] / 60),
            "RAM đỉnh (MB)": so(r["peak_rss_mb"]),
            "Đầu ra (MB)": so(r["output_dir_size_mb"]),
        }
    rows = [row(MEMBER_NAME[m], r) for m, r in RANGES.items()]
    if len(RANGES) == len(MEMBER_ORDER):
        rows.append(row("**Tổng**", tot))
    table(pd.DataFrame(rows))
    md(f"Độ phủ Version: mọi Version trong metadata đều có một dòng log; "
       f"{so(tot['versions_empty_non_tex'])} Version không có TeX được ghi bản ghi rỗng. "
       f"Thời gian tổng là tổng của các Range (cách tính thầy chốt cho M1). "
       f"Trung bình {so(tot['elapsed_seconds'] / tot['publications_total'], 2)} giây mỗi Publication.")
else:
    pending("ranges")
```

Số hiệu năng đo trên MacBook (Apple silicon, 24 GB RAM) ngày 23/11, chạy cục bộ, không phải
Google Colab; thời gian và RAM trên Colab CPU sẽ khác.

### Version lỗi theo lý do

Một Version lỗi có thể mang nhiều mã. Bảng đếm số Version có mỗi mã, cộng 5 Range.

```{code-cell} python
:tags: [remove-input]
if RANGES:
    from collections import Counter
    total = Counter()
    for r in RANGES.values():
        total.update(r["failed_version_issues"])
    failed = sum(r["versions_failed"] for r in RANGES.values())
    table(pd.DataFrame([{"Mã": f"`{code}`", "Ý nghĩa": ISSUE_LABEL.get(code, ""), "Version": so(n),
                         "Tỉ lệ trên Version lỗi": pt(n, failed)}
                        for code, n in total.most_common(8)]))
```

`ambiguous_root` là nhóm lớn nhất và giảm được bằng review file gốc, không cần sửa Parser.
Các nhóm còn lại là giới hạn của cách đọc tĩnh, xem [Hạn chế](06-han-che.md).
