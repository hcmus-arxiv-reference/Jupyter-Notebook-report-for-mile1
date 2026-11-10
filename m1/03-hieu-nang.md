---
title: Hiệu năng
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
import plotly.express as px
```

## Cách đo

Một phiên Colab giới hạn khoảng 12 giờ, không đủ để chạy tuần tự cả 25.000 ID, nên
giảng viên cho phép chia theo Range. Mỗi thành viên chạy **Range của mình trên một
phiên Google Colab CPU riêng**,
bằng cùng một code: notebook `notebooks/colab_m1_selftest.ipynb` của repo code ở
tag `m1-bench-v2`, Engine `src/crawl/`. Trong mỗi phiên, crawler chỉ mở một kết
nối tới arXiv tại một thời điểm. Một phiên Colab không đủ dài cho cả Range, nên
lượt chạy được chia thành nhiều **đoạn chạy** (segment):

1. Mỗi đoạn chạy crawler bên trong harness `src.benchmark`. Harness lấy mẫu RAM
   của **cả cây tiến trình** mỗi 1 giây và dung lượng thư mục dữ liệu mỗi 5 giây
   (`psutil`), ghi dần ra CSV, nên số liệu vẫn còn dù phiên bị ngắt đột ngột.
2. Hết mỗi đoạn, thư mục dữ liệu được nén thành checkpoint trên Google Drive.
   Phiên sau khôi phục từ checkpoint và chạy tiếp; notebook kiểm tra mọi phiên
   dùng cùng một commit.
3. `src.merge_benchmarks` gộp các đoạn. **Tổng thời gian** là tổng thời gian
   các đoạn thực sự chạy, không tính khoảng nghỉ giữa hai phiên. Thời gian chờ
   theo giới hạn truy cập và chờ khi gặp HTTP 429 nằm trong tổng thời gian này.
4. Crawler ghi `manifests/timings.jsonl`: thời gian xử lý từng Publication, kể
   cả Discovery, tải source mọi Version và chờ References. Thời gian của một lô
   Discovery được tính cho Publication kích hoạt lô đó.

Thời gian ở đây chủ yếu là **thời gian chờ theo giới hạn truy cập**, không phải
thời gian tính toán: mỗi request tới arXiv phải cách nhau ít nhất 3,1 giây.

```{code-cell} python
:tags: [remove-input]
rows = []
for m, s in SNAPSHOTS.items():
    versions, lookups = s["counts"]["expected_versions"], revision_lookups(s)
    batches = -(-s["counts"]["assigned"] // 50)
    n = versions + batches + lookups
    rows.append({"Range": name(m), "Tải source (1/Version)": versions, "Lô Discovery (50 ID)": batches,
                 "Tra ngày Version": lookups, "Tổng request arXiv": n, "Giờ tối thiểu": n * 3.1 / 3600})
est = pd.DataFrame(rows)
md("**Ước lượng trước khi chạy** (không phải số đo). Số request arXiv của mỗi Range bằng số "
   "Version (tải source) cộng số lô Discovery, cộng số request tra ngày của Version 2 tới "
   "Version áp chót (Version cuối đã có trong kết quả lô). Chỉ riêng khoảng cách tối thiểu "
   "3,1 giây giữa các request đã cho thời gian dưới đây, chưa tính thời gian tải và chờ khi "
   "bị HTTP 429:")
table(est, **{c: so for c in est.columns if c not in ("Range", "Giờ tối thiểu")},
      **{"Giờ tối thiểu": lambda v: so(v, 1)})
```

## Kết quả

```{code-cell} python
:tags: [remove-input]
def hours(seconds):
    return "chưa đo" if seconds is None else f"{so(seconds / 3600, 2)} giờ"

def mib(value):
    return "chưa đo" if value is None else f"{so(value / 2**20, 1)} MiB"

def gib(value):
    return "chưa đo" if value is None else f"{so(value / 2**30, 2)} GiB"

def secs(value, digits=1):
    return "chưa đo" if value is None else f"{so(value, digits)} giây"

measured = {m: s["benchmark"] for m, s in SNAPSHOTS.items() if s["benchmark"].get("total_wall_seconds")}
METRICS = ["Testbed", "Số đoạn chạy", "Tổng thời gian chạy", "Publication có thời gian đo",
           "Thời gian TB xử lý một Publication", "Trung vị / lớn nhất mỗi Publication",
           "Tổng thời gian Discovery", "RAM lớn nhất (cả cây tiến trình)", "RAM trung bình",
           "Dung lượng đĩa lớn nhất", "Dung lượng output cuối"]
if not measured:
    md(f"**Chưa có số đo.** Chưa Range nào nộp kết quả benchmark trên Colab (hạn 17/11/2026). "
       "Bảng dưới liệt kê các chỉ số đề yêu cầu; trang này tự điền số khi có snapshot "
       "kèm khối `benchmark`.")
    table(pd.DataFrame({"Chỉ số đề yêu cầu": METRICS[2:], "Giá trị": ["chưa đo"] * (len(METRICS) - 2)}))
else:
    cols = {}
    for m, b in measured.items():
        per = b["seconds_per_publication"]
        cols[name(m)] = [b["testbed"], so(b["segments"]), hours(b["total_wall_seconds"]),
                         pt(b["publications_timed"], SNAPSHOTS[m]["counts"]["assigned"]),
                         secs(b["mean_seconds_per_publication"]),
                         f"{secs(per['median'])} / {secs(per['max'], 0)}",
                         hours(b["discovery_seconds"]), mib(b["peak_rss_bytes"]), mib(b["mean_rss_bytes"]),
                         gib(b["peak_disk_bytes"]), gib(b.get("final_disk_bytes"))]
    table(pd.DataFrame({"Chỉ số": METRICS, **cols}))
    walls = [b["total_wall_seconds"] for b in measured.values()]
    md(f"Đã có số đo của **{len(measured)}/{N_RANGES} Range**. **Tổng thời gian chạy của hệ thống "
       f"là tổng thời gian các Range: {hours(sum(walls))}**, tương đương chạy end-to-end tuần tự "
       f"trên một máy. Để tham khảo, Range lâu nhất mất {hours(max(walls))}. "
       "Thời gian TB mỗi Publication tính trên `timings.jsonl` (tổng mọi lần ghé thăm Publication "
       "đó); thời gian chia đều cho 5.000 ID được giao là "
       + ", ".join(f"{name(m)}: {secs(b['wall_seconds_per_assigned_publication'], 2)}"
                   for m, b in measured.items()) + ".")
```

```{code-cell} python
:tags: [remove-input]
for m, b in BENCHMARKS.items():
    segments = pd.DataFrame(b["per_segment"])
    if segments.empty:
        continue
    md(f"Các đoạn chạy của Range {name(m)}:")
    table(segments.drop(columns=["cooldown_seconds"], errors="ignore").rename(columns={
        "name": "Đoạn", "wall_seconds": "Thời gian (giây)", "peak_rss_mb": "RAM lớn nhất (MiB)",
        "done_papers_at_start": "Xong lúc bắt đầu", "done_papers_at_end": "Xong lúc kết thúc",
        "ended": "Kết thúc"}))
```

```{code-cell} python
:tags: [remove-input]
if SAMPLES is not None:
    s = SAMPLES.assign(gio=SAMPLES["t_seconds"] / 3600, **{"Range": SAMPLES["member"].map(name)})
    show(px.line(s, x="gio", y="rss_mb", color="Range",
                 labels={"gio": "Thời gian chạy (giờ)", "rss_mb": "RAM (MiB)"},
                 title="RAM của cả cây tiến trình theo thời gian"))
    show(px.line(s, x="gio", y="disk_mb", color="Range",
                 labels={"gio": "Thời gian chạy (giờ)", "disk_mb": "Đĩa (MiB)"},
                 title="Dung lượng thư mục dữ liệu theo thời gian"))
```
