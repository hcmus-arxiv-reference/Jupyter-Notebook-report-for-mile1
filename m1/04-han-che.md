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
        md(f"Đã thử lại riêng {so(t['requested'])} Publication còn thiếu của {name(m)} "
           f"(mất {so(t['elapsed_seconds'], 1)} giây). Kết quả: source ({src}), Reference ({ref}); "
           f"phục hồi thêm được **{so(t['recovered_publications'])} Publication**.")
```

## Độ phủ Version theo thời gian

Số Version kỳ vọng là số Version arXiv báo **tại lúc crawl**. arXiv vẫn nhận
Version mới sau đó, nên số này chỉ đúng tới ngày snapshot. Bảng dưới đối chiếu
với danh sách Version tra lại trên arXiv API.

```{code-cell} python
:tags: [remove-input]
if ARXIV_VERSIONS:
    ref = ARXIV_VERSIONS["members"]
    day = ARXIV_VERSIONS["queried_at"][:10]
    rows = [{"Range": name(m), "Ngày snapshot": s["snapshot_at"][:10],
             "Version kỳ vọng lúc crawl": s["counts"]["expected_versions"],
             f"Version trên arXiv ngày {day}": ref[MEMBER_NAMES[m][0]]["versions"],
             "Chênh lệch": ref[MEMBER_NAMES[m][0]]["versions"] - s["counts"]["expected_versions"]}
            for m, s in SNAPSHOTS.items() if MEMBER_NAMES.get(m, ("",))[0] in ref]
    if rows:
        table(pd.DataFrame(rows), **{c: so for c in rows[0] if c not in ("Range", "Ngày snapshot")})
        md("Chênh lệch dương là Version arXiv nhận sau ngày crawl. Lượt crawl trên Colab "
           "(trang Hiệu năng) lấy lại danh sách Version tại thời điểm chạy.")
```

## Hạn chế

```{code-cell} python
:tags: [remove-input]
missing = N_RANGES - len(SNAPSHOTS)
items = []
if missing:
    items.append(f"Mới có snapshot của {len(SNAPSHOTS)}/{N_RANGES} Range. Các Range còn lại đang "
                 "được crawl lại bằng Engine chung trên Colab; trước đó chúng được crawl bằng "
                 "pipeline riêng của từng thành viên (trang *So sánh pipeline*), không cộng vào "
                 "số liệu nhóm.")
old = [name(m) for m, s in SNAPSHOTS.items() if not s["benchmark"].get("total_wall_seconds")]
if old:
    items.append(f"Corpus hiện có của {', '.join(old)} được tích lũy qua nhiều lượt chạy và nhiều "
                 "commit, nên thời gian crawl của nó không dùng làm benchmark.")
nosize = [name(m) for m, s in SNAPSHOTS.items() if s["storage"].get("before_extraction_bytes") is None]
if nosize:
    items.append(f"Kích thước *trước* khi bỏ hình chưa được ghi cho corpus của {', '.join(nosize)}.")
items += [
    "Trước tag `m1-bench-v2`, truy vấn lô Discovery không gửi `max_results`, nên arXiv API chỉ "
    "trả 10 entry mặc định cho lô 50 ID; 40 ID còn lại được hỏi lại từng cái (khoảng 41 request "
    "mỗi lô thay vì 1). Dữ liệu không sai, chỉ tốn thêm thời gian; corpus crawl trước đó chịu "
    "lỗi này, lượt benchmark trên Colab thì không.",
    "Thời gian một lô Discovery được tính cho Publication kích hoạt lô, nên thời gian lớn nhất "
    "mỗi Publication thường rơi vào bài đầu lô.",
    "Source được lưu riêng theo từng Version, chưa khử trùng lặp giữa các Version. Ví dụ bài "
    "lớn nhất sau khi lọc (2508.04349, 6 Version) có 4 Version đều kèm file `anthology.bib` "
    "khoảng 42 MB của template ACL. File này đúng là `.bib` nên được giữ lại theo yêu cầu đề; "
    "khử trùng lặp nội dung thuộc Milestone 2.",
    "Dung lượng đĩa là tổng kích thước logic của file, lấy mẫu mỗi 5 giây; không phải số block "
    "thực tế trên đĩa, và đỉnh giữa hai lần lấy mẫu có thể bị bỏ sót.",
]
md("\n".join(f"- {x}" for x in items))
```
