---
title: Leaves
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

## Việc của bước này

Input là `StructureTree`. Mỗi `Block` được thay bằng nút lá hoặc nút danh sách, cho ra `LeafTree`:

| Block | Kết quả |
|---|---|
| đoạn văn | các lá `sentence` |
| `equation`, `align`, `$$…$$`, `\[…\]`, … | lá `formula` |
| `figure`, `table` (kể cả bản `*`) | một lá `figure`, giữ nguyên cả môi trường |
| `itemize`, `enumerate`, `description` | nút `itemize`; mỗi `\item` là một nút `item` chứa lá |

## Tách câu

Dấu chấm trong LaTeX không phải lúc nào cũng kết câu. Bộ tách **không cắt** ở các vị trí sau:

- bên trong toán inline `$…$`, `\(…\)` và bên trong đối số `{…}` của lệnh;
- sau chữ viết tắt: `i.e.`, `e.g.`, `et al.`, `etc.`, `Fig.`, `Eq.`, `Sec.`, `Tab.`, `vs.`, `cf.`;
- trong URL và giữa số thập phân (`3.14`).

**Cách làm:** che các vùng không được cắt bằng ký tự giữ chỗ cùng độ dài, tìm ranh giới câu trên
chuỗi đã che, rồi cắt chuỗi gốc ở đúng các vị trí đó. Vị trí ký tự (`span`) nhờ vậy không lệch,
và mọi lá chỉ ngược về được dòng gốc.

## Phép kiểm

- **Bộ 40 câu khó** viết trước khi code: mỗi dòng gồm input và kết quả tách mong đợi.
- **Không mất chữ:** nối `raw` của các lá trong một Block (bỏ khoảng trắng) phải cho lại đúng
  Block đó.
- **Golden:** `hard-sentences`, `lists-figures-math`.
- **Ranh giới câu trên 30 bài gán nhãn tay:** mục tiêu ≥ 95%.

## Kết quả

Bộ câu khó và phép kiểm "không mất chữ" đạt trên golden fixture. Bảng dưới đếm Element theo loại
trong bảng `elements` của cả 5 Range (sau khử trùng lặp giữa các Version) và độ dài câu tính bằng số
từ (tách theo khoảng trắng, công thức inline tính là một từ).

```{code-cell} python
:tags: [remove-input]
if LEAVES:
    order = ["sentence", "formula", "figure", "item", "itemize", "section", "subsection", "subsubsection",
             "paragraph", "chapter", "document"]
    rows = []
    for m in MEMBER_ORDER:
        r = LEAVES["ranges"].get(m)
        if r is None:
            continue
        rows.append({"Range": MEMBER_NAME[m], **{k: so(r["by_kind"].get(k, 0)) for k in order[:4]},
                     "Câu: TB / trung vị / p95 (từ)": f"{so(r['sentence_words_mean'], 1)} / {so(r['sentence_words_median'])} / {so(r['sentence_words_p95'])}"})
    table(pd.DataFrame(rows))
    tot = {k: sum(r["by_kind"].get(k, 0) for r in LEAVES["ranges"].values()) for k in order}
    md("Tổng 5 Range: " + ", ".join(f"`{k}` {so(v)}" for k, v in tot.items() if v) + ".")
```

Chưa có bộ nhãn tay để đo độ đúng ranh giới câu; đây là việc còn mở ở trang Hạn chế.

## Quyết định đã chốt

- `enumerate` và `description` dùng chung `kind = "itemize"`, vì schema không có loại riêng.
- Một môi trường toán nhiều dòng (`align`, `gather`, `eqnarray`, …) là **một** lá `formula`.
  Bước chuẩn hóa đưa thân môi trường vào `aligned` hoặc `gathered` bên trong
  `\begin{equation}…\end{equation}`, giữ nguyên các dòng (`src/parse/normalize.py`).
