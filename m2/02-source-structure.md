---
title: Source và Structure
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
draft("Liễu")
```

## M2.1: gom source

Input là một thư mục Version đã xác minh. `assemble_source()` trả về `SourceBundle`:

1. **Chọn file gốc:** file `.tex` có `\documentclass`.
2. **Gộp theo đường biên dịch:** theo `\input`, `\include` đệ quy; tôn trọng `\includeonly`.
   File `.tex` không nằm trên đường biên dịch được liệt kê riêng và không đi vào cây.
3. **Lệnh trong comment là văn bản thường**, không mở file và không mở nút.
4. **Giữ vết nguồn gốc:** `spans` ánh xạ mọi đoạn của văn bản đã gộp về file và dòng gốc.
5. **Chẩn đoán có mã:** mỗi trường hợp chưa xử lý được ghi một `issue` (mã, mức độ, file, dòng).

Mỗi Version nhận một trong bốn trạng thái:

| Trạng thái | Ý nghĩa | Bước sau |
|---|---|---|
| `ready` | gom đủ, không có cảnh báo | đi tiếp |
| `needs_review` | gom được nhưng gặp cấu trúc chưa hỗ trợ | đi tiếp, chép mã cảnh báo vào log |
| `error` | không xác định được nguồn | ghi `failed` vào log |
| `empty_non_tex` | Version không có TeX | bản ghi rỗng, không sinh nút |

## M2.2: khung mục

`build_structure()` dựng `StructureTree` từ văn bản đã gộp:

- Chỉ thân `\begin{document}…\end{document}` đi vào cây; comment được thay bằng khoảng trắng để
  giữ vị trí.
- Nhận `\chapter`, `\section`, `\subsection`, `\subsubsection`, `\paragraph`, kể cả bản `*`.
- **Cấp tương đối:** nút con luôn sâu hơn nút cha. Bài nhảy cấp (có `\subsection` mà không có
  `\section`) không sinh nút rỗng để lấp chỗ.
- **Bỏ References** (theo tiêu đề và môi trường `thebibliography`); **giữ** Acknowledgements và
  Appendix.
- Phần thân giữa các heading được cắt thành `Block` nguyên khối (đoạn văn, môi trường, toán
  khối). Việc tách bên trong Block thuộc bước Leaves.

Cùng lúc, bước này tách `BibSource`: nội dung các `.bib` được gọi, các `\bibitem` nguyên văn và
danh sách key được `\cite`.

## Kết quả sơ bộ trên Range Bảo

```{code-cell} python
:tags: [remove-input]
runs = SOURCE["runs"]
rows = [{"Ngày đo": r["date"], "Commit": r["commit"], "ready": pt(r["ready"], tex_versions(r)),
         "needs_review": r["needs_review"], "error": r["error"], "empty_non_tex": r["empty_non_tex"],
         "Thời gian (giây)": r["seconds"]} for r in runs]
md(f"Phạm vi: {SOURCE['scope']}. Mẫu số của tỉ lệ `ready` là số Version có TeX.")
table(pd.DataFrame(rows), **{c: so for c in ("needs_review", "error", "empty_non_tex", "Thời gian (giây)")})
last = runs[-1]
need = round(SOURCE["target_ready_fraction"] * tex_versions(last)) - last["ready"]
md(f"Mục tiêu của nhóm là `ready` ≥ {so(100 * SOURCE['target_ready_fraction'])}% số Version TeX. "
   f"Lượt đo gần nhất còn thiếu **{so(need)} Version**.")
```

```{code-cell} python
:tags: [remove-input]
issues = pd.DataFrame(last["issue_versions"])
fig = px.bar(issues.sort_values("versions"), x="versions", y="code", color="severity", orientation="h",
             labels={"versions": "Số Version", "code": "Mã chẩn đoán", "severity": "Mức"},
             title=f"Version chưa ready theo mã chẩn đoán ({last['date']})")
show(fig)
md("Một Version có thể mang nhiều mã. `missing_bbl` và một phần `include_error` đến từ chính "
   "corpus: đề chỉ cho giữ `.tex/.bib`, nên file `.bbl` và file phụ không có mặt.")
```

```{code-cell} python
:tags: [remove-input]
md(f"**Structure:** trong {so(last['ready'])} Version `ready`, {pt(last['structure_validated'], last['ready'])} "
   f"dựng được cây qua `validate_B` và `validate_B_prime`; {so(last['structure_failed'])} Version chưa qua.")
```

## Việc còn lại

- Xử lý `unsupported_conditional`, quy tắc tự chọn file gốc khi có nhiều ứng viên, `include_error`.
- Độ đúng cấp mục trên 30 bài gán nhãn tay (mục tiêu ≥ 95% số heading).
- Kiểm trên dữ liệu thật: không bài nào lọt References vào cây.
- So sánh bộ quét tự viết với `pylatexenc` trên bộ mẫu.

```{code-cell} python
:tags: [remove-input]
if "structure" not in METRICS: pending("structure")
```
