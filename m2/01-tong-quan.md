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

## Pipeline

Parser xử lý từng Publication qua hai cấp. **Cấp Version** dựng cây tài liệu và tách nguồn danh mục
tham khảo cho từng `v1`, `v2`, …. **Cấp Publication** gộp mọi Version: dựng BibTeX entry một lần,
chuẩn hóa, băm `element_id` rồi khử trùng lặp giữa các Version. Mọi Version, kể cả Version lỗi hoặc
không có TeX, đều có một dòng log kèm mã lý do.

```{mermaid}
flowchart TB
  RAW[("Corpus M1<br/>.tex/.bib + receipt source.json")]
  ROOT[/"Root đã review<br/>configs/m2-reviewed-roots.json"/]
  SIDE[/"Sidecar bibliography<br/>.bib/.bbl khôi phục + manifest"/]
  CK{"Checkpoint<br/>SHA-256 đầu vào + phiên bản module<br/>khớp lần chạy trước?"}

  subgraph VER["Mỗi Version"]
    direction TB
    VS{"Version đã xác minh?"}
    SRC["1 · Gom source<br/>chọn file gốc, theo input/include"]
    STR["2 · Khung mục<br/>section… , bỏ References<br/>+ tách nguồn bibliography"]
    SUP["Bổ sung bibliography<br/>từ sidecar đã kiểm SHA-256"]
    LEAF["3 · Lá<br/>câu, công thức khối, hình, item"]
  end

  subgraph PUB["Mỗi Publication"]
    direction TB
    BIB["4 · BibTeX<br/>gom mọi Version, khử trùng lặp entry"]
    EXP["5 · Tích hợp<br/>đổi key cite, chuẩn hóa,<br/>băm element_id, khử trùng lặp Version"]
    INV{"Bất biến<br/>trước khi ghi"}
  end

  OUT[("elements · hierarchy · bibtex")]
  LOG[["log từng Version · metrics"]]

  RAW --> CK
  CK -->|"khớp: dùng lại kết quả"| OUT
  CK -->|"không"| VS
  VS -->|"có TeX"| SRC --> STR --> SUP --> LEAF
  VS -->|"không TeX hoặc thiếu"| LOG
  ROOT -.-> SRC
  SIDE -.-> SUP
  LEAF --> EXP
  SUP --> BIB --> EXP --> INV --> OUT
  SRC -.->|"lỗi"| LOG
  STR -.->|"lỗi"| LOG
  INV -.-> LOG
```

| Bước | Cấp | Việc | Module, kiểu dữ liệu ra | Trang |
|---|---|---|---|---|
| Checkpoint | Publication | bỏ qua Publication khi đầu vào (corpus, sidecar, root review) và phiên bản module không đổi | `pipeline.py`, `done.json` | [Tích hợp](05-tich-hop.md) |
| 1 · Gom source | Version | kiểm receipt, chọn file gốc (hoặc dùng root đã review), gộp `\input`/`\include` theo đường biên dịch | `source.py`, `SourceBundle` | [Source và Structure](02-source-structure.md) |
| 2 · Khung mục | Version | `\section`…`\paragraph`, giữ Acknowledgements và phụ lục, bỏ References; tách nguồn bibliography, bổ sung từ sidecar | `structure.py`, `bibtex_input.py`; `StructureTree`, `BibSource` | [Source và Structure](02-source-structure.md) |
| 3 · Lá | Version | tách câu, công thức khối, hình (gồm bảng), mỗi `\item` là con của danh sách | `leaves.py`, `LeafTree` | [Leaves](03-leaves.md) |
| 4 · BibTeX | Publication | đọc `.bib`/`\bibitem` của mọi Version, khử trùng lặp entry, sinh `key_map` từng Version | `bibtex.py`, `BibResult` | [Normalize và BibTeX](04-normalize-bibtex.md) |
| 5 · Tích hợp | Publication | đổi `\cite` theo `key_map`, chuẩn hóa nội dung, băm `element_id` theo cây con, khử trùng lặp giữa các Version, kiểm bất biến, ghi bảng | `normalize.py`, `export.py` | [Normalize và BibTeX](04-normalize-bibtex.md), [Tích hợp](05-tich-hop.md) |

Giữa hai bước liền nhau là một kiểu dữ liệu có hàm kiểm tra riêng (`validate_A` … `validate_E` trong
`src/parse/types.py`). Bước nào trả dữ liệu sai thì Version dừng ở đó và được ghi lỗi, không truyền
dữ liệu hỏng sang bước sau.

## Cách kiểm thử

Mỗi bước được kiểm độc lập bằng **golden fixture** ở `tests/fixtures/m2/<case>/`: một bộ `.tex`
tự viết kèm output mong đợi tại từng điểm giao. Test của một bước nạp golden của điểm giao trước
nó, chạy code, so với golden của điểm giao sau nó, rồi gọi hàm `validate_*`. Nhờ vậy các bước
phát triển song song mà không phải chờ nhau. Golden được viết tay và review trước khi viết code.

Số liệu trong các trang sau đọc từ `data/m2/` lúc build: số đo trên cả 5 Range của nhóm và trên bộ
mẫu phát triển 100 Publication.
