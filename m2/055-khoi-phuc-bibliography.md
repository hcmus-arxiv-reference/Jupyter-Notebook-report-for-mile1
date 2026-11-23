---
title: Khôi phục bibliography
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
```

Đây là phần xử lý dữ liệu mà nhóm tự phát hiện và xử lý: không có trong đề, nhưng nếu bỏ qua thì bảng
`bibtex` mất phần lớn entry của khoảng một phần sáu số Version.

## Vấn đề

Đề Crawling yêu cầu chỉ giữ file `.tex` và `.bib` của mỗi Version. Nhưng arXiv biên dịch bằng file
`.bbl` đã dịch sẵn, nên nhiều tác giả chỉ nộp `.bbl`, hoặc nộp `.bib` mang tên khác với tên khai báo.
Những Version này vẫn có `\cite`, còn corpus M1 không có danh mục tham khảo nào để đọc. Key được cite
khi đó không có entry. Bước BibTeX ghi các key này vào `unresolved_keys` với lý do `missing_entry`
(hợp đồng dữ liệu mục 4.2), thay vì tạo entry giả.

Phân tích 985 key `missing_entry` trên bộ mẫu 100 Publication: 980 key nằm ở Version khai báo
`.bib`/`.bbl` mà corpus không có, 5 key là lỗi của tác giả, không key nào do Parser đọc sót.

## Cách làm

1. **Chỉ tải lại phần cần.** `scripts/recover_bibtex_sources.py --all` chạy bộ gom file của Parser trên
   từng Version. Chỉ Version có đường biên dịch khai báo bibliography mà thiếu file mới được tải lại
   archive gốc từ `export.arxiv.org` (cùng quy tắc lịch sự của M1).
2. **Kiểm chứng với M1.** Mọi file `.tex/.bib` trong receipt `source.json` của M1 phải khớp SHA-256 với
   archive tải lại. Archive đã đổi thì Version bị ghi `archive_mismatch`, không dùng.
3. **Sidecar, không sửa corpus.** Chỉ `.bib/.bbl` được chép ra thư mục riêng, kèm `manifest.json`
   (SHA-256 của receipt, archive và từng file). `raw/` của M1 giữ nguyên đúng như đề yêu cầu.
4. **Parser kiểm lại trước khi đọc.** `parse_range.py --supplement-dir` kiểm manifest, rồi mới bổ sung
   bibliography. Digest của sidecar nằm trong khóa checkpoint, nên kết quả có và không có sidecar không
   lẫn vào nhau; Version dùng sidecar mang mã `bibliography_recovered` trong log.
5. **Chạy được cả Range.** Có resume; Version lỗi (HTTP, mạng, archive không phải tar, Source/Structure
   từ chối) được ghi trạng thái rồi chạy tiếp, không dừng cả Range.

## Kết quả

Phân loại mọi Version TeX theo nguồn bibliography, bằng quét tĩnh bỏ qua comment
(`scripts/measure_bib_coverage.py`). "Khai báo nhưng thiếu" là Version có `\bibliography`,
`\addbibresource` hoặc `\input{….bbl}` mà không có `.bib` hay `\bibitem` nào trong corpus.

```{code-cell} python
:tags: [remove-input]
rows, tot = [], {"tex": 0, "missing": 0, "recovered": 0}
for m in MEMBER_ORDER:
    c = BIBCOV.get(m)
    if c is None:
        continue
    v = c["versions"]
    tot["tex"] += c["tex_versions"]; tot["missing"] += v["declared_missing"]
    tot["recovered"] += c["declared_missing_recovered"]
    rows.append({
        "Range": MEMBER_NAME[m],
        "Version TeX": so(c["tex_versions"]),
        "Khai báo nhưng thiếu": pt(v["declared_missing"], c["tex_versions"]),
        "Đã khôi phục": f"{so(c['declared_missing_recovered'])} ({pt(c['declared_missing_recovered'], v['declared_missing'])})",
    })
if rows:
    if len(rows) == len(MEMBER_ORDER):
        rows.append({"Range": "**Tổng**", "Version TeX": so(tot["tex"]),
                     "Khai báo nhưng thiếu": pt(tot["missing"], tot["tex"]),
                     "Đã khôi phục": f"{so(tot['recovered'])} ({pt(tot['recovered'], tot['missing'])})"})
    table(pd.DataFrame(rows))
else:
    md("*Chưa có `data/m2/bib_coverage/<member>.json`.*")
```

Trên bộ mẫu 100 Publication, cùng code Parser, chỉ khác có hay không có sidecar:

```{code-cell} python
:tags: [remove-input]
before, after = BIBCOV.get("sample_before"), METRICS.get("export")
if before is not None and after is not None and after.get("bibliography_supplement"):
    def row(label, key):
        return {"Chỉ số": label, "Không có sidecar": so(before[key]), "Có sidecar": so(after[key])}
    table(pd.DataFrame([
        row("Key cite không có entry (`missing_entry`)", "bibtex_unresolved_keys"),
        row("Entry trong bảng `bibtex`", "bibtex_entries_after_dedup"),
        row("Publication parse đủ mọi Version", "publications_succeeded"),
        row("Version lỗi", "versions_failed"),
    ]))
    md(f"Có {so(after['versions_bibliography_recovered'])} Version của bộ mẫu được bổ sung từ sidecar.")
else:
    md("*Chưa có số đo bộ mẫu có sidecar.*")
```

```{code-cell} python
:tags: [remove-input]
if RANGES:
    rec = sum(r["versions_bibliography_recovered"] for r in RANGES.values())
    keys = sum(r["bibtex_unresolved_keys"] for r in RANGES.values())
    md(f"Trên toàn bộ 5 Range, {so(rec)} Version đọc bibliography từ sidecar. Số này lớn hơn cột "
       "\"Đã khôi phục\" ở bảng trên vì bảng chỉ xét Version không có `.bib` nào, còn pipeline bổ sung "
       "cả Version có `.bib` nhưng thiếu đúng file được khai báo. Sau khôi phục còn "
       f"{so(keys)} key `missing_entry`, gồm key tác giả cite mà không khai báo và key của các Version "
       "không khôi phục được (mục dưới).")
```

## Giới hạn

- **Archive không khôi phục được.** arXiv trả lỗi, archive tải lại không còn khớp receipt M1, hoặc là
  nguồn một file (gzip, không có `.bbl`). Các Version này giữ nguyên kết quả không có sidecar.
- **Version mà Source/Structure đã từ chối** (`source_failed`), ví dụ không có hoặc có nhiều file gốc
  chưa review. Script không tải lại archive cho chúng, vì Parser vẫn ghi lỗi dù có bibliography.
- **Lỗi của tác giả.** Key được cite nhưng không có trong `.bib` đã nộp; đây là dữ liệu đúng như nguồn.
- **Chưa đo `missing_entry` trên toàn Range khi không có sidecar**; mức giảm trên toàn Range chỉ suy ra
  từ số Version khôi phục, còn số trước/sau đo trực tiếp chỉ có trên bộ mẫu.

Vì đề chỉ cho giữ `.tex/.bib`, `raw/` trên Hugging Face không đổi. Sidecar là dữ liệu đầu vào riêng
của M2, có provenance tới từng archive gốc.
