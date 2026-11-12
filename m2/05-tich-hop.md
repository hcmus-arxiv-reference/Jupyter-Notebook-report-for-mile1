---
title: Tích hợp và số liệu
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
draft("Minh")
```

## Thứ tự xử lý một Publication

1. Với từng Version, đổi `\cite{k}` theo `key_map` của Version đó.
2. Chuẩn hóa từng nút bằng `normalize`.
3. **Băm từ lá lên gốc:** lá băm theo `(kind, content)`; nút cấu trúc băm theo
   `(kind, content, danh sách id con theo thứ tự)`. `element_id = <publication key>#<kind>-<16 hex đầu sha256>`.
4. **Khử trùng lặp giữa các Version:** hợp Element của mọi Version, mỗi `element_id` một dòng.
   Hai cây con giống hệt sau chuẩn hóa nhận cùng `element_id`.
5. Sinh cạnh `hierarchy`: một dòng cho mỗi cạnh nút → cha của một Version.

Thứ tự anh em không nằm trong bảng; nó được giữ ở dữ liệu trung gian của M2.

## Log, checkpoint, bất biến

- **Log Version:** mỗi Version theo metadata có đúng một dòng, trạng thái `parsed`,
  `empty_non_tex`, `failed` hoặc `missing`. Version không có TeX vẫn có bản ghi rỗng.
- **Checkpoint:** bỏ qua Publication khi sha256 của input và phiên bản mọi module không đổi.
- **Bất biến trước khi ghi bảng:** mọi `parent_id` trỏ tới `element_id` có thật, mọi key trích
  dẫn có trong `key_map`, ba bảng qua `validate()` của schema chung.

## Bộ mẫu phát triển

Plan 100 Publication lấy ngẫu nhiên có seed, kèm lệnh tải từ Hugging Face. Mọi gói đo
`metrics/<gói>.json` trên cùng bộ mẫu này để số liệu so sánh được.

## Số liệu đề yêu cầu

```{code-cell} python
:tags: [remove-input]
e = METRICS.get("export", {})
table(pd.DataFrame([{"Chỉ số": label, "Giá trị": e.get(key, "chưa đo")} for label, key in [
    ("Tỉ lệ parse thành công", "success_rate"), ("Độ phủ Version", "version_coverage"),
    ("Số Element trước khử trùng lặp", "elements_before"), ("Số Element sau khử trùng lặp", "elements_after"),
    ("Số BibTeX entry trước khử trùng lặp", "entries_before"), ("Số BibTeX entry sau khử trùng lặp", "entries_after"),
    ("Thời gian tổng và trung bình mỗi Publication", "seconds"), ("RAM đỉnh", "peak_rss_mb"),
    ("Dung lượng đầu ra", "output_mb")]]))
if not e: pending("export")
```

Hiệu năng đo trên Google Colab CPU bằng cùng harness `src.benchmark` của Milestone 1.
