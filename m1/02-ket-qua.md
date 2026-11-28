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
md(snapshot_scope() + ("" if len(SNAPSHOTS) == N_RANGES else " Range chưa có snapshot không được tính vào tử số hay mẫu số."))
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
table(counts_frame(), **{c: lambda v: so(v) for c in counts_frame().columns if c != "Range"})
```

```{code-cell} python
:tags: [remove-input]
status = pd.DataFrame([{"Range": name(m), "Trạng thái": k, "Số Version": s["counts"][k]}
                       for m, s in SNAPSHOTS.items()
                       for k in ("success", "non_tex", "unavailable", "download_error", "not_attempted")])
status["Trạng thái"] = status["Trạng thái"].map({"success": "TeX", "non_tex": "non_tex",
    "unavailable": "không tải được (404/410)", "download_error": "lỗi tải", "not_attempted": "chưa thử"})
show(px.bar(status, x="Range", y="Số Version", color="Trạng thái",
            title="Trạng thái source theo Version"))
```

```{code-cell} python
:tags: [remove-input]
versions = pd.DataFrame([{"Range": name(m), **row} for m, s in SNAPSHOTS.items()
                         for row in s["versions_distribution"]])
show(px.bar(versions, x="versions", y="publications", color="Range", barmode="group",
            labels={"versions": "Số Version của Publication", "publications": "Số Publication"},
            title="Phân bố số Version mỗi Publication"))
mean_versions = total("expected_versions") / total("discovered")
md(f"Trung bình mỗi Publication có **{so(mean_versions, 2)} Version** "
   f"({so(total('expected_versions'))} Version / {so(total('discovered'))} Publication).")
```

## Kích thước source

Đề yêu cầu kích thước trung bình mỗi bài **trước và sau** khi bỏ hình và các
file không phải `.tex`/`.bib`. Báo cáo tính theo hai đơn vị: **Publication**
(cộng mọi Version của bài) và **Version**. Cả hai bảng đo trên **cùng tập
Publication hoàn chỉnh** mà receipt `source.json` của mọi Version đều ghi kích
thước, nên cùng tổng số byte, chỉ khác mẫu số:

- *Archive tải về*: số byte nhận từ arXiv (đã nén).
- *Trước khi bỏ hình*: số byte sau giải nén, trước khi lọc file.
- *Sau khi bỏ hình*: tổng `.tex` và `.bib` được giữ lại.

```{code-cell} python
:tags: [remove-input]
rows = []
for m, s in SNAPSHOTS.items():
    st = s["storage"]
    after = st["complete_publication_retained_bytes"]
    sized = st.get("publications_with_before_size")
    rows.append({"Range": name(m),
                 "Publication có đủ số đo": so(sized) if sized else "không ghi lại",
                 "Archive tải về (TB/bài)": mb((st.get("complete_publication_downloaded_bytes") or {}).get("mean")),
                 "Trước khi bỏ hình (TB/bài)": mb(st.get("before_extraction_bytes")),
                 "Sau khi bỏ hình (TB/bài)": mb(after["mean"]),
                 "Trung vị sau": mb(after["median"]), "Lớn nhất sau": mb(after["max"]),
                 "Giảm": "—" if st.get("size_reduction_fraction") is None
                         else f"{so(100 * st['size_reduction_fraction'], 1)}%"})
import plotly.graph_objects as go
sized = {m: s["storage"] for m, s in SNAPSHOTS.items() if s["storage"].get("before_extraction_bytes")}
if sized:
    labels = [name(m) for m in sized]
    before = [st["before_extraction_bytes"] / 1e6 for st in sized.values()]
    after = [st["complete_publication_retained_bytes"]["mean"] / 1e6 for st in sized.values()]
    cut = [st["size_reduction_fraction"] for st in sized.values()]
    fig = go.Figure([
        go.Bar(name="Trước khi bỏ hình", x=labels, y=before, marker_color=COLOR_BASE,
               text=[f"{so(v, 2)} MB" for v in before], textposition="outside",
               hovertemplate="%{x}<br>Trước: %{y:.2f} MB/bài<extra></extra>"),
        go.Bar(name="Sau khi bỏ hình", x=labels, y=after, marker_color=COLOR_MAIN,
               text=[f"{so(v, 2)} MB<br>−{so(100 * c, 1)}%" for v, c in zip(after, cut)],
               textposition="outside",
               hovertemplate="%{x}<br>Sau: %{y:.2f} MB/bài<extra></extra>")])
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08,
                      title=f"Bỏ hình giảm {so(100 * min(cut), 1)}–{so(100 * max(cut), 1)}% dung lượng mỗi Publication",
                      yaxis_title="MB trung bình mỗi Publication", legend=dict(orientation="h", y=-0.15),
                      height=420)
    fig.update_yaxes(range=[0, max(before) * 1.2])
    show(fig)
details("Chi tiết theo Publication", pd.DataFrame(rows))

rows = []
for m, s in SNAPSHOTS.items():
    st = s["storage"]
    sized = st.get("sized_version_after_bytes") or {}
    after = sized if sized.get("n") else (st.get("complete_version_retained_bytes") or {})
    get = lambda field: (st.get(field) or {}).get("mean")
    rows.append({"Range": name(m),
                 "Version có đủ số đo": so(sized["n"]) if sized.get("n") else "không ghi lại",
                 "Archive tải về (TB/Version)": mb(get("sized_version_downloaded_bytes")),
                 "Trước khi bỏ hình (TB/Version)": mb(get("sized_version_before_bytes")),
                 "Sau khi bỏ hình (TB/Version)": mb(after.get("mean")),
                 "Trung vị sau": mb(after.get("median")), "Lớn nhất sau": mb(after.get("max"))})
details("Chi tiết theo Version", pd.DataFrame(rows))
missing = [name(m) for m, s in SNAPSHOTS.items() if s["storage"].get("before_extraction_bytes") is None]
if missing:
    md(f"Range {', '.join(missing)} được crawl bằng phiên bản Engine trước khi có bước ghi kích thước "
       "archive, nên không có số *trước giải nén*; nhóm không ước lượng số này. Cột *sau* vẫn tính "
       "trên mọi Publication hoàn chỉnh của các Range đó.")
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

Semantic Scholar trả về một **danh sách trích dẫn** cho mỗi Publication, gồm cả
bài không có arXiv ID. **Reference** chỉ là các dòng có arXiv ID, khử trùng lặp
theo `ref_arxiv_id` trong cùng Publication (định nghĩa trong `CONTEXT.md`).
Báo cáo ghi cả hai số để không lẫn với nhau.

```{code-cell} python
:tags: [remove-input]
refs = {m: s["references"] for m, s in SNAPSHOTS.items()}
n_ok = sum(r["per_successful_publication"]["n"] for r in refs.values())
n_rows = sum(r["per_successful_publication"]["sum"] for r in refs.values())
n_arxiv = sum(r["with_arxiv_before_dedup"] for r in refs.values())
n_unique = sum(r["unique_arxiv_pairs"] for r in refs.values())
n_table = sum(s["checks"]["tables"]["references"].get("rows") or 0 for s in SNAPSHOTS.values())
dedup = ("không có dòng trùng nào" if n_unique == n_arxiv
         else f"còn {so(n_unique)} Reference sau khi bỏ {so(n_arxiv - n_unique)} dòng trùng")
md(f"- Lấy danh sách trích dẫn thành công: {pt(total('references_success'), total('discovered'))} "
   f"Publication tìm thấy (gồm {so(sum(r['successfully_empty_publications'] for r in refs.values()))} "
   "bài mà Semantic Scholar trả về danh sách rỗng hợp lệ).\n"
   f"- Trung bình **{so(n_unique / n_ok, 1)} Reference mỗi Publication** "
   f"({so(n_unique)} Reference / {so(n_ok)} Publication lấy thành công).\n"
   f"- Trung bình {so(n_rows / n_ok, 1)} dòng trích dẫn S2 mỗi Publication ({so(n_rows)} dòng), "
   f"trong đó {pt(n_arxiv, n_rows)} có arXiv ID; khử trùng lặp theo `ref_arxiv_id` thì {dedup}.\n"
   f"- Bảng `references` có {so(n_table)} dòng, ít hơn {so(n_unique)} Reference ở trên vì Export chỉ "
   "ghi Reference của các Publication có dòng trong bảng `papers` (xem mục kiểm tra bảng bên dưới).")
def khoang(h):
    lo, hi = h["lower"], h["upper_exclusive"]
    return f"≥ {lo}" if hi is None else (str(lo) if hi - lo == 1 else f"{lo}–{hi - 1}")
hist = pd.DataFrame([{"Range": name(m), "Khoảng": khoang(h),
                      "Số Publication": h["count"]} for m, r in refs.items() for h in r["histogram"]])
show(px.bar(hist, x="Khoảng", y="Số Publication", color="Range", barmode="group",
            labels={"Khoảng": "Số dòng trích dẫn S2 của Publication"},
            title="Phân bố độ dài danh sách trích dẫn S2 mỗi Publication"))
```

## Kiểm tra bảng xuất ra

```{code-cell} python
:tags: [remove-input]
rows = []
for m, s in SNAPSHOTS.items():
    for table_name, t in s["checks"]["tables"].items():
        rows.append({"Range": name(m), "Bảng": table_name, "Đọc được theo schema": "có" if t["valid"] else "không",
                     "Số dòng": t.get("rows"), "Khóa trùng": t.get("duplicate_keys"),
                     "ID ngoài Range": t.get("outside_range")})
bad = [r for r in rows if r["Đọc được theo schema"] != "có" or r["Khóa trùng"] or r["ID ngoài Range"]]
md(f"**{len(rows) - len(bad)}/{len(rows)} bảng** đọc được theo schema, không có khóa trùng và không có ID ngoài Range.")
details("Chi tiết từng bảng", pd.DataFrame(rows), **{"Số dòng": so, "Khóa trùng": so, "ID ngoài Range": so})
n_papers = sum(s["checks"]["tables"]["papers"].get("rows") or 0 for s in SNAPSHOTS.values())
extra = n_papers - total("complete")
md("Số dòng ở bảng này đếm trên các bảng `papers`/`references` đã nộp lên Hugging Face "
   f"(`tables/<Range>/`). Bảng `papers` có {so(n_papers)} dòng"
   + (f": ngoài {so(total('complete'))} Publication hoàn chỉnh còn {so(extra)} Publication có metadata "
      "hợp lệ nhưng chưa hoàn chỉnh theo snapshot (ví dụ một Version tải lỗi, hoặc snapshot tạo trước "
      "quy tắc S2 không có bài). Các Publication này giữ dòng `papers`/`references` để M2 vẫn parse "
      "các Version đã có, nhưng không có file thô chưa xác minh trên Hugging Face." if extra > 0 else ".") )
md(f"Snapshot được sinh sau khi kiểm tra lại checksum của "
   f"{so(sum(s['provenance']['verified_input_files'] for s in SNAPSHOTS.values()))} file đầu vào.")
```
