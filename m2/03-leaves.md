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

```{code-cell} python
:tags: [remove-input]
draft("Nghiêm")
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

Theo PR của Nghiêm (ngày 12/11, nhóm chưa review): bộ câu khó và phép kiểm "không mất chữ" đạt
trên fixture. Chưa có số đo trên bộ mẫu và chưa có bộ nhãn tay.

```{code-cell} python
:tags: [remove-input]
if "leaves" not in METRICS: pending("leaves")
```

Số liệu sẽ báo cáo: số lá theo loại, độ dài câu trung bình và trung vị, số Block không tách
được, thời gian.

## Quyết định cần ghi lại

- `enumerate` và `description` dùng chung `kind = "itemize"`, vì schema không có loại riêng.
- Môi trường nhiều dòng (`align`, `gather`) là một hay nhiều `formula`.
