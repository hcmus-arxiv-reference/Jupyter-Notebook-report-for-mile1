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

## Bibliography sau khôi phục

Phần bibliography mà M1 lọc mất đã được khôi phục có kiểm chứng (xem
[Khôi phục bibliography](05b-khoi-phuc-bibliography.md)). Còn lại khoảng 7–10% Version "khai báo
nhưng thiếu" không khôi phục được, cùng các key tác giả cite mà không có trong `.bib`.

## Việc còn mở

- Đã chạy M2 trên cả 5 Range (xem [Tích hợp](05-tich-hop.md)). Còn 1.963 Version `ambiguous_root`
  cần review file gốc.
- Chưa có bộ nhãn tay 30 bài để đo độ đúng cấp mục và ranh giới câu.
- Bảng `bibtex` chỉ giữ entry được cite (C12, chốt 20/11; xem [Normalize và BibTeX](04-normalize-bibtex.md)).
