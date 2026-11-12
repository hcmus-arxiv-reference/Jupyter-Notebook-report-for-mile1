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

## Việc còn mở

- Bước Tích hợp (`export`, `pipeline`) chưa có code, nên chưa có ba bảng và chưa có số liệu
  đề yêu cầu.
- Chưa có bộ nhãn tay 30 bài để đo độ đúng cấp mục và ranh giới câu.
- Chưa chốt phạm vi xuất bảng `bibtex` (xem [Normalize và BibTeX](04-normalize-bibtex.md)).
- Số liệu hiện tại đo trên Range Bảo và một bộ mẫu; chưa chạy trên cả năm Range.
