---
title: So sánh pipeline của các thành viên
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

members = all_members()


def get(m, section, key):
    return m.get(section, {}).get(key)


def ratio(num, den, digits=1):
    return "—" if num is None or not den else pt(num, den, digits)
```

Ban đầu mỗi thành viên tự xây một pipeline và crawl Range của mình. Mục tiêu
là so sánh để chọn cách làm tốt nhất cho từng Stage, rồi ghép vào một Engine
chung. Trang này đặt kết quả của năm pipeline cạnh nhau. Mỗi dòng ghi kèm
**mức kiểm chứng**, vì các thành viên đếm bằng công cụ khác nhau.

```{code-cell} python
:tags: [remove-input]
table(pd.DataFrame([{"Mức kiểm chứng": k, "Ý nghĩa": v} for k, v in VERIFICATION.items()]))
md("Chỉ dòng ở mức `validated` được cộng vào số liệu nhóm ở trang *Kết quả thu thập*. "
   "Các dòng khác chỉ để tham khảo, không cộng gộp với nhau.")
```

## Kết quả theo thành viên

```{code-cell} python
:tags: [remove-input]
rows = []
for m in members:
    v = m["versions"]
    rows.append({
        "Thành viên": m["name"],
        "Range": f"{m['range']['first']} – {m['range']['last']}",
        "Mức kiểm chứng": m["verification"],
        "Có metadata": ratio(get(m, "publications", "with_metadata"), get(m, "publications", "assigned")),
        "Hoàn chỉnh": ratio(get(m, "publications", "complete"), get(m, "publications", "assigned")),
        "Version có TeX": ratio(v.get("tex"), v.get("expected")),
        "non-TeX": ratio(v.get("non_tex"), v.get("expected")),
        "404/410": ratio(v.get("unavailable"), v.get("expected")),
        "Lỗi khác": ratio(v.get("other_error"), v.get("expected")),
        "Lấy S2 thành công": ratio(get(m, "references", "s2_success"), get(m, "publications", "with_metadata")),
        "Reference TB/bài": (so(get(m, "references", "raw_records") / get(m, "references", "s2_success"), 2)
                             if get(m, "references", "raw_records") and get(m, "references", "s2_success") else "—"),
    })
table(pd.DataFrame(rows))
```

```{code-cell} python
:tags: [remove-input]
notes = [f"- **{m['name']}**: {m['verification_note']}" for m in members if m.get("verification_note")]
notes += [f"- **{m['name']}**: {n}" for m in members for n in m.get("notes", [])]
md("\n".join(notes))
```

### Kích thước trước và sau khi bỏ hình

```{code-cell} python
:tags: [remove-input]
rows = []
for m in members:
    s, n = m["size"], get(m, "publications", "assigned")
    before, after = s.get("before_bytes_total"), s.get("after_bytes_total")
    rows.append({"Thành viên": m["name"],
                 "Trước (TB/bài)": f"{so(before / n / 1e6, 2)} MB" if before else "chưa đo",
                 "Sau (TB/bài)": f"{so(after / n / 1e6, 2)} MB" if after else "chưa đo",
                 "Giảm": f"{so(100 * (1 - after / before), 2)}%" if before and after else "—",
                 "Ghi chú": "làm tròn từ file tóm tắt" if s.get("rounded") else ""})
table(pd.DataFrame(rows))
md("Trung bình ở đây chia cho 5.000 ID được giao để các dòng cùng mẫu số; vì vậy nó "
   "khác trung bình *trên Publication hoàn chỉnh* ở trang Kết quả thu thập.")
```

### Hiệu năng đã ghi nhận

Các lượt chạy dưới đây khác nhau về máy, mạng, mức song song và chính sách
nghỉ khi lỗi, nên **không so sánh trực tiếp được** và không thay cho benchmark
trên Colab ở trang *Hiệu năng*.

```{code-cell} python
:tags: [remove-input]
rows = []
for m in members:
    p = m["performance"]
    if p.get("wall_seconds"):
        rows.append({"Thành viên": m["name"], "Môi trường": p["environment"],
                     "Tổng thời gian": f"{so(p['wall_seconds'] / 3600, 2)} giờ",
                     "Giây / ID": so(p["wall_seconds"] / get(m, "publications", "assigned"), 1),
                     "RAM đỉnh": f"{so(p['peak_rss_mib'], 1)} MiB" if p.get("peak_rss_mib") else "—",
                     "RAM TB": f"{so(p['avg_rss_mib'], 1)} MiB" if p.get("avg_rss_mib") else "—",
                     "Ghi chú": p.get("note") or ""})
if rows:
    table(pd.DataFrame(rows))
else:
    md("Chưa thành viên nào có số đo hiệu năng.")
```

## Cách làm theo từng Stage

```{code-cell} python
:tags: [remove-input]
stages = [("discovery", "Discovery"), ("source", "Source fetch"), ("references", "References"),
          ("retry", "Retry"), ("resume", "Resume / Manifest"), ("storage", "Lưu trữ / Export")]
table(pd.DataFrame([{"Stage": label, **{m["name"]: m["pipeline"].get(key) or "—" for m in members}}
                    for key, label in stages]))
```

Từ bảng này, Engine chung giữ lại:

- **Discovery theo lô 50 ID**, hỏi lại từng ID khi lô lỗi. Cả năm pipeline đều
  truy vấn metadata theo lô.
- **Tải tiếp file bị cắt bằng HTTP Range**, lấy từ pipeline của Liễu.
- **Một luồng S2 chạy song song với tải source**, giúp tận dụng thời gian chờ
  giữa các request arXiv mà không tăng số kết nối tới arXiv.
- **Resume theo manifest và checksum**, không chỉ dựa vào file đánh dấu `done`.
- **Layout file + Parquet** cho mọi Range, để Parser và validator dùng chung.

## Giới hạn truy cập

Đề yêu cầu chỉ một kết nối tới arXiv tại một thời điểm, các request cách nhau
ít nhất 3 giây, và tuân thủ hạn mức của Semantic Scholar. Một pipeline đã chạy
ba notebook tải source song song, dùng ba API key Semantic Scholar cùng lúc,
và thử lại lỗi 429/5xx không giới hạn số vòng. Cách làm này rút ngắn thời gian
nhưng không giữ được điều kiện một kết nối tới arXiv tại một thời điểm, và có thể
vượt hạn mức của Semantic Scholar. Vì vậy nhóm không đưa cách làm này vào Engine
chung, và thời gian chạy của nó trong bảng hiệu năng ở trên không phản ánh tốc
độ khi tuân thủ giới hạn.
