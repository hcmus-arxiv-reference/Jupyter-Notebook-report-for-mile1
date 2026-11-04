---
title: Lỗi còn lại và hạn chế
kernelspec:
  name: python3
  display_name: Python 3
---

```{code-cell} python
:tags: [remove-cell]
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists()) / "m1"))
from m1data import *
```

## Tác vụ chưa thành công

Mỗi tác vụ lỗi được ghi kèm ID, loại tác vụ, trạng thái và mã HTTP. Mã 404
chỉ phản ánh kết quả tại thời điểm crawl, không chứng minh source đã mất vĩnh
viễn. Vì vậy nó được ghi là `unavailable`/`error`, không bao giờ đổi thành
`non_tex` hay danh sách Reference rỗng.

```{code-cell} python
:tags: [remove-input]
failures = pd.DataFrame([{"Thành viên": m, **f} for m, s in SNAPSHOTS.items() for f in s["failures"]])
if failures.empty:
    md("Không có tác vụ lỗi trong các snapshot hiện có.")
else:
    kinds = {"discovery": "Discovery", "source": "Source fetch", "references": "References"}
    summary = (failures.assign(kind=failures["kind"].map(kinds), http_status=failures["http_status"].fillna("—"))
               .groupby(["Thành viên", "kind", "status", "http_status"]).size().reset_index(name="Số tác vụ")
               .rename(columns={"kind": "Stage", "status": "Trạng thái", "http_status": "HTTP"}))
    table(summary, **{"Số tác vụ": so})
```

```{code-cell} python
:tags: [remove-input]
for m, s in SNAPSHOTS.items():
    t = s.get("retry_trial")
    if t:
        src = ", ".join(f"{k}: {so(v)}" for k, v in t["source_outcomes"].items())
        ref = ", ".join(f"{k}: {so(v)}" for k, v in t["reference_outcomes"].items())
        md(f"Đã thử lại riêng {so(t['requested'])} Publication còn thiếu của {m} "
           f"(mất {so(t['elapsed_seconds'], 1)} giây). Kết quả: source ({src}), Reference ({ref}); "
           f"phục hồi thêm được **{so(t['recovered_publications'])} Publication**.")
```

## Hạn chế

```{code-cell} python
:tags: [remove-input]
missing = N_RANGES - len(SNAPSHOTS)
items = []
if missing:
    items.append(f"Mới có snapshot của {len(SNAPSHOTS)}/{N_RANGES} Range. Các Range còn lại được crawl "
                 "bằng những pipeline khác nhau trước khi nhóm hợp nhất Engine, nên phải chuyển về "
                 "layout chung và kiểm tra lại rồi mới đưa vào báo cáo.")
items += [
    "Corpus hiện có được tích lũy qua nhiều lượt chạy và nhiều commit, nên thời gian crawl của nó "
    "không dùng làm benchmark. Số hiệu năng chỉ lấy từ lượt chạy tuần tự trên Colab.",
    "Kích thước *trước* khi bỏ hình chưa được ghi cho corpus hiện có.",
    "Harness đo thời gian cả lượt, RAM và đĩa; thời gian riêng của Discovery cần lấy từ log của "
    "crawler, chưa có trong file benchmark.",
    "Dung lượng đĩa là tổng kích thước logic của file, không phải số block thực tế trên đĩa.",
]
md("\n".join(f"- {x}" for x in items))
```
