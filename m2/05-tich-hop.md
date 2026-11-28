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
  `empty_non_tex` (chỉ có PDF/docx), `empty_unavailable` (arXiv trả 404/410), `failed` hoặc
  `missing` (chưa có source đã xác minh). Version không có TeX vẫn có bản ghi rỗng.
- **Checkpoint:** bỏ qua Publication khi sha256 của input và phiên bản mọi module không đổi.
- **Bất biến trước khi ghi bảng:** mọi `parent_id` trỏ tới `element_id` có thật, mọi key trích
  dẫn có trong `key_map`, ba bảng qua `validate()` của schema chung.

## Bộ mẫu phát triển

Plan 100 Publication lấy ngẫu nhiên có seed, kèm lệnh tải từ Hugging Face. Mọi gói đo
`metrics/<gói>.json` trên cùng bộ mẫu này để số liệu so sánh được.

## Số liệu đề yêu cầu trên 5 Range

Chạy `scripts/parse_range.py --member <m> --supplement-dir … --roots configs/m2-reviewed-roots.json`
trên toàn bộ corpus M1 của từng Range, có sidecar bibliography (xem
[Khôi phục bibliography](055-khoi-phuc-bibliography.md)) và các file gốc đã review.

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
        tot["peak_rss_children_mb"] = max(tot.get("peak_rss_children_mb", 0), r.get("peak_rss_children_mb", 0))
    def row(name, r):
        tex = r["versions_parsed"] + r["versions_failed"]
        return {
            "Range": name,
            "Publication parse đủ": pt(r["publications_succeeded"], r["publications_total"]),
            "Version TeX parse được": pt(r["versions_parsed"], tex),
            "Element trước → sau khử trùng lặp": f"{so(r['elements_before_dedup'])} → {so(r['elements_after_dedup'])}",
            "BibTeX entry trước → sau": f"{so(r['bibtex_entries_before_dedup'])} → {so(r['bibtex_entries_after_dedup'])}",
            "Thời gian (phút)": so(r["elapsed_seconds"] / 60),
            "RAM đỉnh tiến trình chính (MB)": so(r["peak_rss_mb"]),
            "RAM đỉnh một tiến trình con (MB)": so(r.get("peak_rss_children_mb", 0)),
            "Đầu ra (MB)": so(r["output_dir_size_mb"]),
        }
    rows = [row(MEMBER_NAME[m], r) for m, r in RANGES.items()]
    if len(RANGES) == len(MEMBER_ORDER):
        rows.append(row("Tổng", tot))
    table(pd.DataFrame(rows))
    md(f"Độ phủ Version: mọi Version trong metadata đều có một dòng log; "
       f"{so(tot['versions_empty_non_tex'])} Version không có TeX được ghi bản ghi rỗng. "
       f"Thời gian tổng là tổng thời gian chạy của các Range, cùng cách tính với M1. "
       f"Trung bình {so(tot['elapsed_seconds'] / tot['publications_total'], 2)} giây mỗi Publication.")
    short = {MEMBER_NAME[m]: r["publications_total"] for m, r in RANGES.items() if r["publications_total"] < 5000}
    if short:
        md("Mẫu số Publication là số Publication có file metadata trong corpus M1 của Range "
           "(`parse_range.py --member` chỉ lấy ID có metadata), nên có Range dưới 5.000: "
           + "; ".join(f"{k}: {so(v)}" for k, v in short.items()) + ".")
else:
    pending("ranges/<member>.json")
```

Số hiệu năng đo trên MacBook (Apple silicon, 24 GB RAM) ngày 27/11, chạy song song 6 tiến trình
(`--workers 6`, xem [Xử lý tăng dần và mở rộng](07-tang-dan-mo-rong.md)), không phải Google Colab CPU
như đề quy định cho benchmark; thời gian và RAM trên Colab sẽ khác. Tiến trình chính giữ kết quả của
mọi Publication để ghi bảng, nên RAM của nó lớn hơn RAM của từng tiến trình con parse Publication.

### Độ phủ Version của từng Publication

Độ phủ của một Publication là số Version đã xử lý chia cho số Version trong metadata. Version
"đã xử lý" là Version parse được, hoặc Version không có TeX nên được ghi bản ghi rỗng. Version
lỗi và Version không có source (`missing`) không được tính.

```{code-cell} python
:tags: [remove-input]
if RANGES:
    order = ["100%", "50–99%", "1–49%", "0%"]
    cov = pd.DataFrame([{"Range": MEMBER_NAME[m], "Độ phủ": k, "Số Publication": n}
                        for m, r in RANGES.items() for k, n in r["publication_coverage"].items()])
    show(px.bar(cov, x="Range", y="Số Publication", color="Độ phủ",
                category_orders={"Độ phủ": order}, title="Độ phủ Version của từng Publication"))
    pubs = sum(r["publications_total"] for r in RANGES.values())
    count = {k: sum(r["publication_coverage"][k] for r in RANGES.values()) for k in order}
    md(f"{pt(count['100%'], pubs)} Publication có mọi Version được xử lý; {so(count['50–99%'] + count['1–49%'])} Publication được xử lý một "
       f"phần; {so(count['0%'])} Publication không có Version nào xử lý được.")
    rows = []
    for k in ["1", "2", "3", "4", "5"]:
        n = sum(r["coverage_by_versions"].get(k, {}).get("publications", 0) for r in RANGES.values())
        full = sum(r["coverage_by_versions"].get(k, {}).get("full", 0) for r in RANGES.values())
        rows.append({"Số Version": "5 trở lên" if k == "5" else k, "Publication": so(n),
                     "Độ phủ 100%": pt(full, n)})
    table(pd.DataFrame(rows))
    md("Publication càng nhiều Version thì càng ít đạt độ phủ 100%, vì chỉ cần một Version lỗi là "
       "Publication không còn được tính là đủ.")
```

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

Trước ADR 0005, `ambiguous_root` là nhóm lớn nhất với 1.963 Version. Luật chọn file gốc theo tiêu đề
metadata, rồi theo tên file (`docs/adr/0005-mot-van-ban-chinh-moi-version.md` trong repo code) giải
được 1.373 Version và còn lại 590 Version trong lượt ngày 24/11. Mỗi lựa chọn theo luật được ghi `root_selected_by_title`
hoặc `root_selected_by_name` trong log nên kiểm tra lại được. Bảng trên Hugging Face được sinh từ
commit `f1972ad` của repo code, ngày 27/11.

So với lượt ngày 24/11 (commit `c813d20`), lượt này sửa ba nhóm lỗi tìm ra khi chạy lại riêng các
Version lỗi và đọc traceback:

- Các bước cùng đọc LaTeX nhưng mỗi bước tự xác định vùng có hiệu lực, nên lệch nhau. Ví dụ, một cite
  key có khoảng trắng bên trong được bước dựng cây coi là một key, nhưng bước BibTeX lại tách khác.
  Bộ kiểm tra giữa các bước chặn cứng các chỗ lệch này và loại cả Version. Nay vùng có hiệu lực đi
  chung một nguồn; cite key không có entry được ghi là chưa giải được thay vì loại Publication.
- Văn bản trong nhánh chắc chắn tắt (`\iffalse … \fi`) vẫn vào `elements`, kèm các `\cite` trong đó.
  Nay nhánh này được bỏ như comment.
- `\input` tới file không có (file của bản phân phối TeX như `epsf`, hình TikZ/PGF mà M1 không giữ)
  làm lỗi cả Version. Nay chỉ là cảnh báo. Riêng file mục được đọc sau `\begin{document}` mà
  không có thì vẫn là lỗi `missing_content`, để Version thiếu nguyên một mục không bị tính là parse được.

Kết quả: số Version parse được tăng từ 34.933 lên 36.256, số Version lỗi giảm từ 3.354 xuống 2.029.
Các nhóm còn lại là giới hạn của cách đọc tĩnh, xem [Hạn chế](06-han-che.md).
