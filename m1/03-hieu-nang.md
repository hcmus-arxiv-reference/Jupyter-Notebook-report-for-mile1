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

Benchmark cuối chạy **trên một máy Google Colab CPU, tuần tự qua cả 25.000 ID**
của năm Range, bằng code đã ghép xong trên nhánh `main` của repo code. Một phiên
Colab không đủ dài cho cả lượt, nên lượt chạy được chia thành nhiều **đoạn chạy**
(segment):

1. Mỗi đoạn chạy crawler bên trong harness `src.benchmark`. Harness lấy mẫu RAM
   của **cả cây tiến trình** mỗi 1 giây và dung lượng thư mục dữ liệu mỗi 5 giây
   (`psutil`), ghi dần ra CSV, nên số liệu vẫn còn dù phiên bị ngắt đột ngột.
2. Hết phiên, toàn bộ thư mục dữ liệu và checkpoint được nén, kèm sha256, rồi
   lưu lên Google Drive. Phiên sau khôi phục từ bản này và chạy tiếp
   (notebook `notebooks/colab_m1_selftest.ipynb`).
3. `src.merge_benchmarks` gộp các đoạn lại. Thời gian chạy là **tổng thời gian
   các đoạn thực sự chạy**, không tính khoảng nghỉ giữa hai phiên. Thời gian
   crawler chủ động chờ (cooldown) được tách riêng.

Thời gian ở đây chủ yếu là **thời gian chờ theo giới hạn truy cập**, không phải
thời gian tính toán. Mỗi request tới arXiv phải cách nhau ít nhất 3,1 giây.

```{code-cell} python
:tags: [remove-input]
n_ids = 5000 * N_RANGES
vpp = total("expected_versions") / total("discovered")
requests = n_ids * vpp + n_ids / 50          # source mỗi Version + discovery theo lô 50 ID
lower_bound_h = requests * 3.1 / 3600
md(f"**Ước lượng trước khi chạy** (không phải số đo): với trung bình {so(vpp, 2)} Version mỗi "
   f"Publication (lấy từ snapshot ở trang trước), {so(n_ids)} ID cần khoảng {so(requests)} request "
   f"arXiv. Chỉ riêng khoảng cách tối thiểu 3,1 giây giữa các request đã chiếm "
   f"**≈ {so(lower_bound_h, 0)} giờ**, chưa tính thời gian tải và chờ khi bị HTTP 429.")
```

## Kết quả

```{code-cell} python
:tags: [remove-input]
if BENCHMARK is None:
    md("**Chưa có số đo.** Lượt benchmark cuối trên Colab chưa chạy xong. Bảng dưới đây "
       "liệt kê các chỉ số đề yêu cầu; trang này tự điền số khi có file "
       "`data/m1/benchmark/benchmark_total.json`.")
    table(pd.DataFrame({"Chỉ số đề yêu cầu": [
        "Tổng thời gian chạy", "Thời gian trung bình mỗi Publication", "Tổng thời gian Discovery",
        "RAM lớn nhất", "RAM trung bình", "Dung lượng đĩa lớn nhất", "Dung lượng output cuối"],
        "Giá trị": ["chưa đo"] * 7}))
else:
    b = BENCHMARK
    segments = pd.DataFrame(b["per_segment"])
    processed = segments["done_papers_at_end"].iloc[-1] - segments["done_papers_at_start"].iloc[0]
    rows = [("Số đoạn chạy", so(b["segments"])),
            ("Tổng thời gian chạy", f"{so(b['total_wall_hours'], 2)} giờ"),
            ("Trong đó crawler chủ động chờ (cooldown)",
             "—" if b["total_cooldown_seconds"] is None else f"{so(b['total_cooldown_seconds'] / 3600, 2)} giờ"),
            ("Publication xử lý trong lượt", so(processed)),
            ("Thời gian trung bình mỗi Publication",
             f"{so(b['total_wall_seconds'] / processed, 2)} giây" if processed else "—"),
            ("Tổng thời gian Discovery", f"{so(b['discovery_seconds'], 0)} giây" if b.get("discovery_seconds") else "chưa đo"),
            ("RAM lớn nhất (cả cây tiến trình)", f"{so(b['peak_rss_mb'], 1)} MB"),
            ("RAM trung bình", f"{so(b['avg_rss_mb'], 1)} MB"),
            ("Dung lượng đĩa lớn nhất", f"{so(b['peak_disk_mb'] / 1024, 2)} GB"),
            ("Dung lượng output cuối", f"{so(b['final_disk_mb'] / 1024, 2)} GB")]
    table(pd.DataFrame(rows, columns=["Chỉ số", "Giá trị"]))
    table(segments.rename(columns={"name": "Đoạn", "wall_seconds": "Thời gian (giây)", "peak_rss_mb": "RAM lớn nhất (MB)",
                                   "done_papers_at_start": "Xong lúc bắt đầu", "done_papers_at_end": "Xong lúc kết thúc",
                                   "cooldown_seconds": "Cooldown (giây)", "ended": "Kết thúc"}))
```

```{code-cell} python
:tags: [remove-input]
if SAMPLES is not None:
    s = SAMPLES.assign(gio=SAMPLES["t_seconds"] / 3600)
    show(px.line(s, x="gio", y="rss_mb", labels={"gio": "Thời gian chạy (giờ)", "rss_mb": "RAM (MB)"},
                 title="RAM của cả cây tiến trình theo thời gian"))
    show(px.line(s, x="gio", y="disk_mb", labels={"gio": "Thời gian chạy (giờ)", "disk_mb": "Đĩa (MB)"},
                 title="Dung lượng thư mục dữ liệu theo thời gian"))
```
