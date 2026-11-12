---
title: Tổng quan Parser
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

## Mục tiêu

Milestone 2 nhận `.tex/.bib` của mọi Version đã thu thập ở Milestone 1 và xuất ba bảng theo
[đề Parsing](https://hcmus-cs-ta.github.io/lab-book/intro-ds/statement/parsing/):

| Bảng | Một dòng là | Khóa chính |
|---|---|---|
| `elements` | một Element phân biệt của một Publication, nội dung đã chuẩn hóa | `element_id` |
| `hierarchy` | một cạnh nút → cha trong một Version | `(arxiv_id, version, element_id, parent_id)` |
| `bibtex` | một BibTeX entry đã khử trùng lặp | `(arxiv_id, citation_key)` |

Parser không dùng LLM hay mô hình pretrained. Mọi bước là code tất định: cùng input cho cùng
output từng byte.

## Cấu trúc chương trình

Parser gồm năm bước, nối với nhau qua năm điểm giao có kiểu dữ liệu và hàm kiểm tra riêng
(`src/parse/types.py`, `validate_A` … `validate_D`).

```{mermaid}
flowchart LR
  V[Thư mục Version] --> A["[A] SourceBundle"]
  A --> B["[B] StructureTree"]
  A --> Bp["[B'] BibSource"]
  B --> C["[C] LeafTree"]
  Bp --> D["[D] BibResult"]
  C --> E["[E] elements, hierarchy, bibtex"]
  D --> E
  N["normalize()"] --> E
```

| Bước | Việc | Điểm giao ra | Trang |
|---|---|---|---|
| M2.1 Source | chọn file gốc, gộp `\input`/`\include` theo đường biên dịch | [A] `SourceBundle` | [Source và Structure](02-source-structure.md) |
| M2.2 Structure | dựng khung mục, bỏ References, tách nguồn danh mục tham khảo | [B] `StructureTree`, [B'] `BibSource` | [Source và Structure](02-source-structure.md) |
| M2.3 Leaves | tách Block thành câu, công thức khối, hình, danh sách | [C] `LeafTree` | [Leaves](03-leaves.md) |
| M2.4 Normalize, BibTeX | chuẩn hóa nội dung; gom và khử trùng lặp BibTeX entry | `normalize()`, [D] `BibResult` | [Normalize và BibTeX](04-normalize-bibtex.md) |
| M2.5 Integration | đổi key trích dẫn, băm `element_id`, khử trùng lặp giữa các Version, xuất bảng | [E] ba bảng, log, metrics | [Tích hợp và số liệu](05-tich-hop.md) |

## Cách kiểm thử

Mỗi bước được kiểm độc lập bằng **golden fixture** ở `tests/fixtures/m2/<case>/`: một bộ `.tex`
tự viết kèm output mong đợi tại từng điểm giao. Test của một bước nạp golden của điểm giao trước
nó, chạy code, so với golden của điểm giao sau nó, rồi gọi hàm `validate_*`. Nhờ vậy các bước
phát triển song song mà không phải chờ nhau. Golden được viết tay và review trước khi viết code.

## Trạng thái

```{code-cell} python
:tags: [remove-input]
md(f"Trạng thái các gói việc tại ngày **{PROGRESS['as_of']}**:")
table(pd.DataFrame([{"Gói": p["package"], "Bước": p["steps"], "Người viết": p["owner"],
                     "Trạng thái": p["state"], "Số liệu": p["measured"]} for p in PROGRESS["packages"]]))
```

Số liệu trong các trang sau đọc từ `data/m2/` lúc build. Con số ghi *sơ bộ* là số đo trong lúc
phát triển; số nghiệm thu sẽ lấy từ `metrics/<gói>.json` của từng gói, đo trên bộ mẫu 100
Publication và trên toàn Range.
