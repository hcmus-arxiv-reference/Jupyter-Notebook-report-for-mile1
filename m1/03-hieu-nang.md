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
import json
import plotly.express as px
```

## Cách đo

Một phiên Colab giới hạn khoảng 12 giờ, không đủ để chạy tuần tự cả 25.000 ID, nên
giảng viên cho phép chia theo Range. Mỗi thành viên chạy **Range của mình trên một
phiên Google Colab CPU riêng**,
bằng notebook `notebooks/colab_m1_selftest.ipynb` của repo code và Engine `src/crawl/`.
Tag của repo code mà từng Range dùng ghi ở bảng commit trong mục Kết quả. Trong mỗi phiên, crawler chỉ mở một kết
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
md("Ước lượng này giả sử Discovery gọi arXiv API như ở `m1-bench-v2`. Từ `m1-bench-v3`, metadata và "
   "ngày Version lấy từ snapshot (trang *Phương pháp thu thập*), nên lượt chạy thật chỉ còn request "
   "tải source, cộng request API cho các ID không có trong snapshot.")
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
    md(f"**Chưa có số đo.** Chưa Range nào có kết quả benchmark trên Colab. "
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
    if len(measured) == N_RANGES:
        total_md = (f"**Tổng thời gian chạy của hệ thống là tổng thời gian các Range: {hours(sum(walls))}**, "
                    "tương đương chạy end-to-end tuần tự trên một máy. ")
    else:
        total_md = (f"Tổng thời gian của {len(measured)} Range đã đo là {hours(sum(walls))}; con số này "
                    f"**chưa phải** tổng thời gian của hệ thống vì còn {N_RANGES - len(measured)} Range chưa đo. ")
    md(f"Đã có số đo của **{len(measured)}/{N_RANGES} Range**. " + total_md +
       f"Để tham khảo, Range lâu nhất mất {hours(max(walls))}. "
       "Thời gian TB mỗi Publication tính trên `timings.jsonl` (tổng mọi lần ghé thăm Publication "
       "đó); thời gian chia đều cho 5.000 ID được giao là "
       + ", ".join(f"{name(m)}: {secs(b['wall_seconds_per_assigned_publication'], 2)}"
                   for m, b in measured.items()) + ".")
```

```{code-cell} python
:tags: [remove-input]
if measured:
    import plotly.graph_objects as go
    order = sorted(measured, key=lambda m: measured[m]["total_wall_seconds"])
    labels = [name(m) for m in order]
    wall = [measured[m]["total_wall_seconds"] / 3600 for m in order]
    # Từ m1-bench-v3, request arXiv chỉ còn tải source: một request mỗi Version.
    floor = [min(SNAPSHOTS[m]["counts"]["expected_versions"] * 3.1 / 3600, w) for m, w in zip(order, wall)]
    rest = [w - f for w, f in zip(wall, floor)]
    share = sum(floor) / sum(wall)
    fig = go.Figure([
        go.Bar(name="Chờ bắt buộc: số Version × 3,1 giây", y=labels, x=floor, orientation="h",
               marker_color=COLOR_MAIN, hovertemplate="%{y}<br>Chờ bắt buộc: %{x:.1f} giờ<extra></extra>"),
        go.Bar(name="Phần còn lại: tải archive lớn, chờ References, ghi file, chờ HTTP 429",
               y=labels, x=rest, orientation="h", marker_color=COLOR_SECOND,
               text=[f"{so(w, 1)} giờ" for w in wall], textposition="outside",
               hovertemplate="%{y}<br>Phần còn lại: %{x:.1f} giờ<extra></extra>")])
    fig.add_vrect(x0=7, x1=8, fillcolor="#8a8880", opacity=0.18, line_width=0)
    fig.add_annotation(x=7.5, y=1, xref="x", yref="paper", yanchor="bottom", showarrow=False,
                       text="trung vị năm trước: 7–8 giờ", font=dict(size=11, color="#52514e"))
    fig.update_traces(marker_line_color="white", marker_line_width=2)
    fig.update_layout(barmode="stack", bargap=0.35, height=380, legend_traceorder="normal",
                      title=(f"Mỗi Range mất {so(min(wall), 1)}–{so(max(wall), 1)} giờ; "
                             f"{so(100 * share)}% là thời gian chờ bắt buộc giữa các request arXiv"),
                      xaxis_title="Giờ chạy trên Colab CPU", legend=dict(orientation="h", y=-0.25))
    fig.update_xaxes(range=[0, max(wall) * 1.15])
    show(fig, top=80)
    backoff = sum(b["http"]["backoff_seconds"] for b in BENCHMARKS.values())
    md(f"Phần màu xanh là giới hạn dưới không thể rút ngắn: mỗi Version cần một request tải source, và "
       f"hai request phải cách nhau ít nhất 3,1 giây. Thời gian chờ lùi khi bị HTTP 429 lúc tải source "
       f"của cả 5 Range chỉ {so(backoff / 60, 1)} phút, nên gần như toàn bộ phần màu cam là thời gian tải "
       "những archive lớn hơn mức 3,1 giây cho phép, cộng thời gian chờ References ở cuối mỗi Publication. "
       "Dải xám là mức thời gian giảng viên nêu cho các nhóm năm trước, chỉ để tham khảo.")
```

```{code-cell} python
:tags: [remove-input]
if BENCHMARKS:
    TAGS = {"be9e7f9": "m1-bench-v2", "b0c2ff1": "m1-bench-v3", "6f00b0e": "m1-bench-v4", "4c734ce": "m1-bench-v5"}
    table(pd.DataFrame([{"Range": name(m), "Tag": TAGS.get(b["commit"][:7], "—"), "Commit": f"`{b['commit'][:7]}`",
                         "Số phiên Colab": so(b["sessions"]),
                         "Discovery": hours(b["discovery_seconds"]),
                         "HTTP 429 khi tải source": so(b["http"]["http_429"]),
                         "Thời gian chờ lùi (giây)": so(b["http"]["backoff_seconds"])}
                        for m, b in BENCHMARKS.items()]))
    md("Các Range chạy bằng `m1-bench-v4` hoặc `m1-bench-v5`. Cả hai đều lấy metadata từ snapshot "
       "arXiv nên Discovery chỉ mất khoảng một phút.")
    old_path = DATA / "history" / "nghiem-m1-bench-v2.json"
    if old_path.exists():
        old = json.loads(old_path.read_text(encoding="utf-8"))
        new = BENCHMARKS.get("nghiem", {})
        md(f"Range {name('nghiem')} lúc đầu chạy bằng `m1-bench-v2`, khi Discovery còn gọi arXiv API: "
           f"lượt đó mất {hours(old['total_wall_seconds'])} qua {so(old['segments'])} đoạn chạy, riêng "
           f"Discovery {hours(old['discovery_seconds'])}, và gặp {so(old['http']['http_429'])} lần HTTP 429 "
           f"khi tải source. Range này đã được chạy lại bằng `m1-bench-v5` "
           f"({hours(new.get('total_wall_seconds'))}, {so(new.get('segments'))} đoạn chạy); "
           "các bảng trên dùng số của lượt chạy lại. File tổng của lượt cũ giữ ở "
           "`data/m1/history/` để đối chiếu.")
    md("Từ `m1-bench-v2` tới `m1-bench-v4`, Engine đổi những điểm ảnh hưởng tới tốc độ: Discovery đọc "
       "metadata snapshot của arXiv thay vì gọi API, lô Discovery bị HTTP 429 được thử lại cả lô, và "
       "references được lấy theo lô qua `/paper/batch` của Semantic Scholar trên một luồng riêng, không "
       "chặn luồng tải từ arXiv. `m1-bench-v5` chỉ khác `m1-bench-v4` ở cách ghi Version mà arXiv trả "
       "HTTP 404 (thành bản ghi rỗng, quy tắc C11), không đổi tốc độ. Vì vậy chênh lệch giữa các Range "
       "chạy v4 và v5 đến từ dữ liệu của Range (số Version, kích thước archive) và số lần bị HTTP 429, "
       "không phải từ phiên bản Engine.")
```

```{code-cell} python
:tags: [remove-input]
for m, b in BENCHMARKS.items():
    segments = pd.DataFrame(b["per_segment"])
    if segments.empty:
        continue
    details(f"Các đoạn chạy của Range {name(m)}", segments.drop(columns=["cooldown_seconds"], errors="ignore").rename(columns={
        "name": "Đoạn", "wall_seconds": "Thời gian (giây)", "peak_rss_mb": "RAM lớn nhất (MiB)",
        "done_papers_at_start": "Xong lúc bắt đầu", "done_papers_at_end": "Xong lúc kết thúc",
        "ended": "Kết thúc"}), **{"Thời gian (giây)": so, "RAM lớn nhất (MiB)": lambda v: so(v, 1),
                                  "Xong lúc bắt đầu": so, "Xong lúc kết thúc": so})
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
