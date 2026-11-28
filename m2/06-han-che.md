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

Số đếm dưới đây cộng trên 5 Range, lấy từ log của lượt chạy cuối (xem [Tích hợp](05-tich-hop.md)).
Một Version lỗi có thể mang nhiều mã.

```{code-cell} python
:tags: [remove-input]
from collections import Counter
by = Counter()
for r in RANGES.values():
    by.update(r["failed_version_issues"])
failed = sum(r["versions_failed"] for r in RANGES.values())
md(f"- **Điều kiện chỉ biết khi biên dịch.** {so(by['unsupported_conditional'] + by['unclosed_conditional'])} "
   "Version dùng lệnh điều kiện mà bộ gom chưa đánh giá được hoặc không đóng; Parser đọc tĩnh, không chạy TeX.\n"
   f"- **Thiếu file mục.** {so(by['missing_content'])} Version gọi một file mục sau `\\begin{{document}}` "
   "mà file không có trong source; Parser báo lỗi thay vì parse thiếu mục.\n"
   f"- **`\\input` không đọc được.** {so(by['include_error'])} Version có tên file động, đường dẫn ra ngoài "
   "thư mục Version hoặc vòng lặp include.\n"
   f"- **Nhiều ứng viên file gốc.** {so(by['ambiguous_root'])} Version còn nhiều file `\\documentclass` sau "
   "luật chọn theo tiêu đề và tên file.\n"
   f"- **Lỗi khi dựng cây hoặc cú pháp TeX hỏng.** {so(by['parse_error'] + by['invalid_syntax'])} Version.\n\n"
   f"Tổng cộng {so(failed)} Version lỗi, mỗi Version có một dòng log kèm mã lý do.")
```

Parser không parse được 100% Version TeX trên dữ liệu thật. Không Version nào bị bỏ qua im lặng.

## Bibliography sau khôi phục

```{code-cell} python
:tags: [remove-input]
cov = [c for m, c in BIBCOV.items() if m in MEMBER_ORDER]
missing = sum(c["versions"]["declared_missing"] for c in cov)
recovered = sum(c["declared_missing_recovered"] for c in cov)
md("Phần bibliography mà M1 lọc mất đã được khôi phục có kiểm chứng (xem "
   "[Khôi phục bibliography](055-khoi-phuc-bibliography.md)). "
   f"Trong số Version \"khai báo nhưng thiếu\", còn {pt(missing - recovered, missing)} không khôi phục "
   "được, cùng các key tác giả cite "
   "mà không có trong `.bib`.")
```

## Việc còn mở

- Lệnh điều kiện không tính được khi đọc tĩnh (`\if1\blind`, `\ifdefined`) giữ văn bản của cả hai
  nhánh, nên một số câu chứa văn bản mà bản PDF không in. Chỉ nhánh chắc chắn tắt (`\iffalse`, `\ifnum`
  với hai số cụ thể) được bỏ.
- Các Version `ambiguous_root` còn lại là trường hợp luật chọn file gốc không cho kết quả duy nhất,
  ví dụ `Manuscript1.tex` với `Manuscript2.tex`.
- Thời gian và RAM của M2 đo trên MacBook, chưa có lượt đo trên Google Colab CPU.
- Độ đúng cấp mục mới đo trên 30 Version duyệt tay trước ADR 0005 (98,3% heading, trang
  [Source và Structure](02-source-structure.md)), chưa đo lại. Chưa có nhãn tay để đo ranh giới câu.
- Bảng `bibtex` chỉ giữ entry được cite (C12, chốt 20/11; xem [Normalize và BibTeX](04-normalize-bibtex.md)).
