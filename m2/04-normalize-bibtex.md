---
title: Normalize và BibTeX
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
draft("Hải")
```

## Normalize

`normalize(kind, raw)` là hàm thuần, đưa nội dung về dạng so sánh được giữa các Version:

| `kind` | Chuẩn hóa |
|---|---|
| `sentence` | bỏ lệnh định dạng vô nghĩa; toán inline về `$…$`; gom khoảng trắng |
| `formula` | mọi dạng toán khối về `\begin{equation}…\end{equation}` |
| `figure` | bỏ `\centering`, `[htpb]`, `\toprule`, `\midrule`, …; giữ `\caption`, `\label`, `\includegraphics` |

Hai tính chất được kiểm trên mọi fixture:

- **Idempotent:** `normalize(k, normalize(k, x)) == normalize(k, x)`.
- Hai chuỗi chỉ khác khoảng trắng hoặc lệnh định dạng cho cùng output.

Danh sách lệnh bị bỏ nằm trong một bảng hằng số có ghi nguồn. `normalize` không đổi `\cite`;
việc đổi key thuộc bước Tích hợp và làm trước khi chuẩn hóa.

## BibTeX

Với mỗi Publication, bước này nhận `BibSource` của **mọi** Version và trả về `BibResult`:

1. **Đọc `.bib`** (thư viện `bibtexparser`, không phải mô hình học máy), xử lý `@string` và
   `crossref`.
2. **`\bibitem` → entry** bằng regex: năm, DOI, URL, arXiv ID, tiêu đề.
3. **Khử trùng lặp giữa các Version:** hai entry là một khi trùng DOI, hoặc trùng arXiv ID, hoặc
   trùng tiêu đề đã chuẩn hóa và năm. Các trường được hợp lại, xung đột ghi vào log.
4. **Chọn key tất định:** key của Version mới nhất có entry đó; hòa thì lấy key nhỏ nhất theo
   thứ tự từ điển.
5. **`key_map`:** ánh xạ key gốc của từng Version sang key đã chọn, dùng để đổi `\cite` ở bước
   Tích hợp.

## Kết quả sơ bộ trên bộ mẫu

```{code-cell} python
:tags: [remove-input]
b = BIBTEX
md(f"Nguồn: {b['source']}. Bộ mẫu {b['publications']} Publication, seed {b['seed']}, commit `{b['commit']}`.")
table(pd.DataFrame([
    {"Chỉ số": "Entry trước khử trùng lặp", "Giá trị": so(b["entries_before"])},
    {"Chỉ số": "Entry sau khử trùng lặp", "Giá trị": so(b["entries_after"])},
    {"Chỉ số": "Publication đã xử lý", "Giá trị": pt(b["publications_processed"], b["publications"])},
    {"Chỉ số": "Publication chưa qua validate_D", "Giá trị": pt(b["validate_D_failed_publications"], b["publications_processed"])},
    {"Chỉ số": "Key được trích dẫn chưa phân giải", "Giá trị": so(b["unresolved_keys"])},
    {"Chỉ số": "Version lỗi gom source", "Giá trị": pt(b["versions_source_error"], b["versions"])},
]))
big = sum(p["entries_before"] for p in b["largest_publications"])
names = " và ".join(f"`{p['arxiv_id']}`" for p in b["largest_publications"])
md(f"**Số trước khử trùng lặp bị chi phối bởi hai Publication:** {names} chiếm "
   f"{pt(big, b['entries_before'])} entry, vì mỗi Version kèm một file `.bib` dùng chung rất lớn "
   "mà bài chỉ trích dẫn một phần nhỏ.")
```

## Quyết định còn mở

Phạm vi xuất bảng `bibtex`:

1. chỉ entry được trích dẫn trên đường biên dịch (tính cả `\nocite` và entry cha qua `crossref`);
2. mọi entry của các file `.bib` được khai báo.

Phương án 1 tránh đưa danh mục thư viện chưa dùng vào bước Matching; phương án 2 không bỏ sót
key khi bộ đọc `\cite` thiếu biến thể. Nhóm sẽ đối chiếu độ phủ key trên bộ mẫu rồi chốt.

```{code-cell} python
:tags: [remove-input]
if "bibtex" not in METRICS: pending("bibtex")
```
