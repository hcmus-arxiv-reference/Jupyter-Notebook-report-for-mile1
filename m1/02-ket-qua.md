---
title: Kết quả thu thập
kernelspec:
  name: python3
  display_name: Python 3
---

```{code-cell} python
:tags: [remove-cell]
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists()) / "m1"))
from m1data import *
import plotly.express as px
```

```{code-cell} python
:tags: [remove-input]
md(snapshot_scope() + " Range chưa có snapshot không được tính vào tử số hay mẫu số.")
```

## Publication và Version

Một Publication **hoàn chỉnh** khi mọi Version của nó đều có source đã xác minh
(TeX, hoặc bản ghi rỗng nếu là `non_tex`) và lấy được Reference từ Semantic Scholar.

```{code-cell} python
:tags: [remove-input]
md(f"- Publication tìm thấy trên arXiv: {pt(total('discovered'), total('assigned'))} ID được giao.\n"
   f"- **Publication hoàn chỉnh: {pt(total('complete'), total('assigned'))}** ID được giao.\n"
   f"- Version có source TeX: {pt(total('success'), total('expected_versions'))} Version kỳ vọng; "
   f"`non_tex` (chỉ có PDF/docx): {pt(total('non_tex'), total('expected_versions'))}; "
   f"không tải được: {pt(total('unavailable') + total('download_error'), total('expected_versions'))}.")
table(counts_frame(), **{c: lambda v: so(v) for c in counts_frame().columns if c not in ("Thành viên", "Range")})
```

```{code-cell} python
:tags: [remove-input]
status = pd.DataFrame([{"Thành viên": m, "Trạng thái": k, "Số Version": s["counts"][k]}
                       for m, s in SNAPSHOTS.items()
                       for k in ("success", "non_tex", "unavailable", "download_error", "not_attempted")])
status["Trạng thái"] = status["Trạng thái"].map({"success": "TeX", "non_tex": "non_tex",
    "unavailable": "không tải được (404/410)", "download_error": "lỗi tải", "not_attempted": "chưa thử"})
show(px.bar(status, x="Thành viên", y="Số Version", color="Trạng thái",
            title="Trạng thái source theo Version"))
```

```{code-cell} python
:tags: [remove-input]
versions = pd.DataFrame([{"Thành viên": m, **row} for m, s in SNAPSHOTS.items()
                         for row in s["versions_distribution"]])
show(px.bar(versions, x="versions", y="publications", color="Thành viên", barmode="group",
            labels={"versions": "Số Version của Publication", "publications": "Số Publication"},
            title="Phân bố số Version mỗi Publication"))
mean_versions = total("expected_versions") / total("discovered")
md(f"Trung bình mỗi Publication có **{so(mean_versions, 2)} Version** "
   f"({so(total('expected_versions'))} Version / {so(total('discovered'))} Publication).")
```

## Kích thước source

Đề yêu cầu kích thước trung bình mỗi bài **trước và sau** khi bỏ hình và các
file không phải `.tex`/`.bib`.

```{code-cell} python
:tags: [remove-input]
rows = []
for m, s in SNAPSHOTS.items():
    st = s["storage"]
    rows.append({"Thành viên": m,
                 "Trước khi bỏ hình (TB/bài)": st.get("before_extraction_bytes"),
                 "Sau khi bỏ hình (TB/bài, Publication hoàn chỉnh)": st["complete_publication_retained_bytes"]["mean"],
                 "Trung vị sau": st["complete_publication_retained_bytes"]["median"],
                 "Lớn nhất sau": st["complete_publication_retained_bytes"]["max"]})
mb = lambda v: "chưa đo" if v is None else f"{so(v / 1e6, 2)} MB"
table(pd.DataFrame(rows), **{c: mb for c in rows[0] if c != "Thành viên"})
missing = [m for m, s in SNAPSHOTS.items() if s["storage"].get("before_extraction_bytes") is None]
if missing:
    md(f"Corpus của {', '.join(missing)} được crawl khi Engine chưa ghi kích thước archive trước "
       "giải nén, nên cột *trước* còn trống. Số này sẽ được đo trong lượt benchmark cuối trên "
       "Colab (trang Hiệu năng), không ước lượng.")
```

```{code-cell} python
:tags: [remove-input]
smoke = pd.DataFrame([x for s in SNAPSHOTS.values() for x in s.get("smoke_samples", [])])
if not smoke.empty:
    md(f"Để tham khảo, {len(smoke)} bài trong smoke test có đủ cả hai số đo. Mẫu quá nhỏ "
       "nên không dùng làm trung bình của corpus:")
    smoke = smoke[["id", "n_versions", "bytes_before", "bytes_after"]].rename(columns={
        "id": "arXiv ID", "n_versions": "Version", "bytes_before": "Trước (byte)", "bytes_after": "Sau (byte)"})
    table(smoke, **{"Trước (byte)": so, "Sau (byte)": so})
```

## References

```{code-cell} python
:tags: [remove-input]
refs = {m: s["references"] for m, s in SNAPSHOTS.items()}
n_ok = sum(r["per_successful_publication"]["n"] for r in refs.values())
n_records = sum(r["per_successful_publication"]["sum"] for r in refs.values())
md(f"- Lấy Reference thành công: {pt(total('references_success'), total('discovered'))} Publication tìm thấy "
   f"(gồm {so(sum(r['successfully_empty_publications'] for r in refs.values()))} bài mà Semantic Scholar "
   "trả về danh sách rỗng hợp lệ).\n"
   f"- Trung bình **{so(n_records / n_ok, 1)} Reference mỗi Publication** "
   f"({so(n_records)} bản ghi / {so(n_ok)} Publication lấy thành công).\n"
   f"- Bản ghi có arXiv ID: {pt(sum(r['with_arxiv_before_dedup'] for r in refs.values()), n_records)}. "
   "Chỉ những bản ghi này trở thành dòng của bảng `references`.")
def khoang(h):
    lo, hi = h["lower"], h["upper_exclusive"]
    return f"≥ {lo}" if hi is None else (str(lo) if hi - lo == 1 else f"{lo}–{hi - 1}")
hist = pd.DataFrame([{"Thành viên": m, "Khoảng": khoang(h),
                      "Số Publication": h["count"]} for m, r in refs.items() for h in r["histogram"]])
show(px.bar(hist, x="Khoảng", y="Số Publication", color="Thành viên", barmode="group",
            labels={"Khoảng": "Số Reference của Publication"}, title="Phân bố số Reference mỗi Publication"))
```

## Kiểm tra bảng xuất ra

```{code-cell} python
:tags: [remove-input]
rows = []
for m, s in SNAPSHOTS.items():
    for name, t in s["checks"]["tables"].items():
        rows.append({"Thành viên": m, "Bảng": name, "Đọc được theo schema": "có" if t["valid"] else "không",
                     "Số dòng": t.get("rows"), "Khóa trùng": t.get("duplicate_keys"),
                     "ID ngoài Range": t.get("outside_range")})
table(pd.DataFrame(rows), **{"Số dòng": so, "Khóa trùng": so, "ID ngoài Range": so})
md(f"Snapshot được sinh sau khi kiểm tra lại checksum của "
   f"{so(sum(s['provenance']['verified_input_files'] for s in SNAPSHOTS.values()))} file đầu vào.")
```
