---
title: Hạn chế và việc còn mở
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

## Hạn chế đã biết

```{code-cell} python
:tags: [remove-input]
last = SOURCE["runs"][-1]
by = {i["code"]: i["versions"] for i in last["issue_versions"]}
md(f"- **Corpus chỉ có `.tex/.bib`.** {so(by['missing_bbl'])} Version gọi file `.bbl` không được lưu, "
   "nên danh mục tham khảo dạng `\\bibitem` của các Version này không đọc được.\n"
   f"- **Điều kiện chỉ biết khi biên dịch.** {so(by['unsupported_conditional'])} Version dùng lệnh điều kiện "
   "mà bộ gom chưa đánh giá được; Parser đọc tĩnh, không chạy TeX.\n"
   f"- **File được gọi nhưng không có.** {so(by['include_error'])} Version `\\input` tới file vắng mặt trong corpus.\n"
   f"- **Nhiều ứng viên file gốc.** {so(by['ambiguous_root'])} Version chưa được chọn file gốc tự động.")
```

Parser không đạt 100% `ready` trên dữ liệu thật. Mọi Version vẫn có một dòng trong log kèm mã
lý do; không Version nào bị bỏ qua im lặng.

## Bibliography bị lọc ở M1 và phần khôi phục

Đề Crawling yêu cầu chỉ giữ file `.tex` và `.bib` của mỗi Version. Khi biên dịch bằng BibTeX,
arXiv dùng file `.bbl` đã dịch sẵn, nên nhiều tác giả chỉ nộp `.bbl` mà không nộp `.bib`.
Những Version này vẫn có `\cite`, nhưng corpus M1 không còn danh mục tham khảo nào để đọc.
Key được cite khi đó không có entry. Bước BibTeX ghi các key này vào `unresolved_keys` với lý do
`missing_entry` (hợp đồng dữ liệu mục 4.2), thay vì tạo entry giả.

Để lấy lại phần đã mất mà không sửa corpus M1, `scripts/recover_bibtex_sources.py` chỉ tải lại
archive gốc từ `export.arxiv.org` cho những Version khai báo bibliography nhưng không có file.
Script đối chiếu mọi file `.tex/.bib` trong receipt M1 với archive, rồi chép riêng `.bib/.bbl` vào
một thư mục sidecar kèm `manifest.json` (SHA-256 của receipt, archive và từng file). Parser kiểm
lại các checksum này trước khi đọc sidecar (`--supplement-dir` của `scripts/parse_range.py`).

Bảng dưới phân loại mọi Version TeX theo nguồn bibliography, bằng quét tĩnh bỏ qua comment
(`scripts/measure_bib_coverage.py`). "Khai báo nhưng thiếu" là Version có `\bibliography`,
`\addbibresource` hoặc `\input{….bbl}` mà không có `.bib` hay `\bibitem` nào trong corpus.

```{code-cell} python
:tags: [remove-input]
rows = []
for m in MEMBER_ORDER:
    c = BIBCOV.get(m)
    if c is None:
        continue
    v = c["versions"]
    rows.append({
        "Range": MEMBER_NAME[m],
        "Version TeX": so(c["tex_versions"]),
        "Có .bib hoặc \\bibitem": pt(v["bib_or_bibitem"], c["tex_versions"]),
        "Khai báo nhưng thiếu": pt(v["declared_missing"], c["tex_versions"]),
        "Đã khôi phục": pt(c["declared_missing_recovered"], v["declared_missing"]),
        "Không có bibliography": so(v["no_bibliography"]),
    })
if rows:
    table(pd.DataFrame(rows))
    missing = [MEMBER_NAME[m] for m in MEMBER_ORDER if m not in BIBCOV]
    if missing:
        md("*Chưa có số liệu cho Range: " + ", ".join(missing) + ".*")
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
    md("*Chưa có số đo bộ mẫu có sidecar (`data/m2/metrics/export.json` với `bibliography_supplement`).*")
```

Phần còn thiếu sau khôi phục có ba nguồn:

- **Lỗi của tác giả.** Key được cite nhưng không có trong `.bib` đã nộp, ví dụ một key gõ sai.
  Đây là dữ liệu đúng như nguồn, không phải lỗi Parser.
- **Archive không khôi phục được.** arXiv trả lỗi, hoặc archive tải lại không còn khớp receipt M1
  (`recovery_report` trong file số liệu của từng Range). Các Version này giữ nguyên kết quả không
  có sidecar.
- **Version mà Source/Structure đã từ chối** (`source_failed` trong `recovery_report`), ví dụ không
  có file gốc chứa `\documentclass` hoặc có nhiều file gốc mà chưa review. Script không tải lại
  archive cho các Version này, vì Parser vẫn sẽ ghi lỗi cho chúng dù có bibliography.
- **Không có bibliography.** Một phần nhỏ Version không khai báo danh mục tham khảo nào, ví dụ
  bài ngắn hoặc bản chỉ có phụ lục.

Vì đề chỉ cho giữ `.tex/.bib`, `raw/` trên Hugging Face không đổi. Sidecar là dữ liệu đầu vào
riêng của M2, có provenance tới từng archive gốc.

## Việc còn mở

- Bước Tích hợp (`export`, `pipeline`) đã có code và số đo trên bộ mẫu; số liệu trên cả năm
  Range sẽ thay số bộ mẫu khi chạy xong.
- Chưa có bộ nhãn tay 30 bài để đo độ đúng cấp mục và ranh giới câu.
- Bảng `bibtex` chỉ giữ entry được cite (C12, chốt 20/11; xem [Normalize và BibTeX](04-normalize-bibtex.md)).
- Số liệu hiện tại đo trên Range Bảo và một bộ mẫu; chưa chạy trên cả năm Range.
