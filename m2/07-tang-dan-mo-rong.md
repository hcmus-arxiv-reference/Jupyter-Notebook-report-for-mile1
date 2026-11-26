---
title: Xử lý tăng dần, tái lập và mở rộng
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
PERF = load("performance.json")
```

Crawl một Range mất nhiều giờ, nên Parser không thể đợi crawl xong mới bắt đầu. Trang này trả lời
ba câu hỏi: trong lúc dữ liệu còn đang về thì nhóm xử lý phần đã có như thế nào, thiết kế nào giúp
chạy lại ra đúng kết quả cũ, và dữ liệu mới về có làm hỏng phần đã xử lý hay không.

## Trong lúc chờ crawl

**Phát triển trên bộ mẫu.** Parser được viết và đo trên một plan 100 Publication lấy ngẫu nhiên có
seed (`configs/m2-sample-100.json`) từ phần corpus đã crawl xong. Mỗi gói (gom source, khung mục, lá,
chuẩn hóa, BibTeX) có fixture tự viết và số đo riêng trên cùng bộ mẫu, nên các thành viên làm song
song mà không phải chờ Range đầy đủ.

**Chạy Parser trên corpus đang được ghi.** Có ba cơ chế để M2 đọc an toàn khi crawler vẫn đang chạy:

1. Crawler ghi mỗi Version vào một thư mục tạm, rồi đổi tên thư mục một lần khi đã đủ file và
   receipt `source.json`. Parser không bao giờ thấy một Version ghi dở.
2. Parser chỉ nhận **Version đã xác minh**: receipt hợp lệ, danh sách và checksum file `.tex/.bib`
   khớp. Version chưa về hoặc không khớp được ghi `missing` trong log, không bị đoán.
3. **Checkpoint theo nội dung đầu vào.** Mỗi Publication có `done.json`, khóa bằng sha256 của
   metadata, receipt của mọi Version, phiên bản từng module và các đầu vào phụ (sidecar
   bibliography, root đã review). Lần chạy sau chỉ parse lại những Publication có khóa đổi,
   tức là bài mới, bài có thêm Version, hoặc bài chịu ảnh hưởng của module vừa sửa.

Vì vậy nhóm có thể chạy M2 nhiều lần trong lúc crawl. Mỗi lần chỉ tốn thời gian cho phần mới về.

```{code-cell} python
:tags: [remove-input]
if PERF and "incremental" in PERF:
    inc = PERF["incremental"]
    md(f"**Thử nghiệm trên Range {MEMBER_NAME[PERF['range']]}.** Lần 1 chạy nửa đầu Range "
       f"({so(inc['half_publications'])} Publication, giả lập crawl mới xong một nửa), mất "
       f"{so(inc['half_seconds'] / 60, 1)} phút. Lần 2 chạy toàn Range: "
       f"{so(inc['resumed'])} Publication dùng lại checkpoint, chỉ {so(inc['parsed'])} bài được parse, "
       f"mất {so(inc['full_seconds'] / 60, 1)} phút. Ba bảng của lần 2 "
       + ("**giống từng byte**" if inc["identical"] else "**khác**")
       + " với bảng của một lần chạy toàn Range từ đầu.")
else:
    md("*Chưa có `data/m2/performance.json`.*")
```

## Dữ liệu mới có làm hỏng cấu trúc đã có không

| Thay đổi | Ảnh hưởng tới bảng đã xuất | Vì sao |
|---|---|---|
| Thêm Publication mới | Chỉ thêm dòng của bài đó | `element_id` gồm publication key và hash cây con, không phụ thuộc bài khác hay thứ tự chạy |
| Thêm Version mới của một bài | Bài đó được parse lại. Element giống hệt Version cũ giữ nguyên `element_id`; chỉ thêm Element và cạnh mới | Khử trùng lặp theo nội dung sau chuẩn hóa |
| Thay đổi thứ tự, chia lô, số tiến trình | Không đổi gì | Bảng gộp theo thứ tự arXiv ID từ kết quả từng Publication |
| Sửa code một module | Mọi bài được parse lại, vì phiên bản module nằm trong khóa checkpoint | Không có bảng nào trộn kết quả của code cũ và code mới |
| Sửa luật parse (ví dụ chọn file gốc, ADR 0005) | `element_id` của các Version bị ảnh hưởng thay đổi; M3 phải dùng bảng mới | Hash phản ánh nội dung cây, nên cây khác thì id khác |

Kết quả của mỗi Publication được kiểm bất biến trước khi gộp: mọi `parent_id` trỏ tới
`element_id` có thật, mọi key trích dẫn có trong `key_map`, các dòng qua `validate()` của schema
chung. Publication vi phạm được ghi `publication_error` trong log và không có dòng nào trong bảng,
nên dữ liệu mới lỗi không làm hỏng phần còn lại.

Các tính chất trên có test chạy được trong repo (`tests/test_parse_pipeline_inputs.py`):

- chạy song song ra bảng giống chạy tuần tự;
- Version về sau chỉ làm parse lại đúng Publication đó, các bài khác dùng lại checkpoint, và
  `element_id` cũ được giữ.

## Song song hóa theo Publication

Mỗi Publication độc lập và có checkpoint riêng, nên `run_batch` chia các Publication cho nhiều tiến
trình (`scripts/parse_range.py --workers N`, `0` là dùng mọi CPU). Kết quả được gộp theo thứ tự ID,
nên bảng xuất ra giống hệt bản tuần tự.

```{code-cell} python
:tags: [remove-input]
if PERF:
    seq = PERF["sequential"]
    rows = [{"Cách chạy": "Tuần tự (1 tiến trình)", "Thời gian (phút)": so(seq["seconds"] / 60, 1),
             "Tăng tốc": "1,0×", "RAM tiến trình chính (MB)": so(seq["peak_rss_mb"]),
             "RAM tiến trình con lớn nhất (MB)": "–", "Bảng giống bản tuần tự": "–"}]
    for run in PERF["parallel"]:
        rows.append({"Cách chạy": f"{run['workers']} tiến trình",
                     "Thời gian (phút)": so(run["seconds"] / 60, 1),
                     "Tăng tốc": f"{so(seq['seconds'] / run['seconds'], 1)}×",
                     "RAM tiến trình chính (MB)": so(run["peak_rss_mb"]),
                     "RAM tiến trình con lớn nhất (MB)": so(run["peak_rss_children_mb"]),
                     "Bảng giống bản tuần tự": "có" if run["identical"] else "không"})
    table(pd.DataFrame(rows))
    md(f"Đo trên {PERF['machine']} ngày {PERF['as_of']}, Range {MEMBER_NAME[PERF['range']]} "
       f"({so(PERF['publications'])} Publication). RAM đỉnh toàn máy có thể tới RAM tiến trình chính "
       "cộng số tiến trình nhân RAM tiến trình con lớn nhất.")
```

Song song hóa không miễn phí. Mỗi tiến trình con gửi kết quả của nó (hàng triệu dòng Element
và cạnh) về tiến trình chính, rồi tiến trình chính mới gộp bảng. Việc đóng gói và giải nén này làm
tổng thời gian CPU tăng:

```{code-cell} python
:tags: [remove-input]
two = next(r for r in PERF["parallel"] if r["workers"] == 2)
seq = PERF["sequential"]["seconds"]
md(f"với 2 tiến trình, tổng thời gian CPU là {so(two['cpu_seconds'])} giây, trong khi bản tuần tự "
   f"(một nhân) chạy hết {so(seq)} giây; thời gian thực chỉ giảm từ {so(seq)} xuống "
   f"{so(two['seconds'])} giây.")
```

Vì vậy, với 2 tiến trình, mức tăng tốc gần như không đáng kể. Colab CPU chỉ có 2 vCPU và
khoảng 12 GB RAM, nên trên Colab nhóm chạy tuần tự (`--workers 1`). Song song hóa chỉ có lợi trên
máy nhiều nhân.

Lợi ích lớn hơn đến từ chạy tăng dần: phần đã parse không phải chạy lại, bất kể máy có bao nhiêu
nhân. Version lỗi vẫn được lưu checkpoint cùng mã lý do. Riêng Publication gặp lỗi ở cấp
Publication (`publication_error`) thì không được lưu, nên được thử lại ở lần chạy sau; đây là lý do
số bài dùng lại checkpoint ít hơn số bài của lần 1.

## Rà soát pipeline theo sáu tầng

Rà soát không dừng ở việc tìm lỗi trong code. Câu hỏi chính là bảng đầu ra có còn đúng nghĩa của
mã nguồn LaTeX đầu vào hay không.

| Tầng | Pipeline đang có | Bằng chứng | Còn thiếu |
|---|---|---|---|
| Kiến trúc | Mỗi Stage là một module có interface nhỏ (gom source, khung mục, lá, chuẩn hóa, BibTeX, xuất bảng); bản sửa của mỗi lỗi chỉ nằm trong một module | Hai bản sửa gần nhất (môi trường toán, chọn file gốc) đều chỉ đổi một file | Hàm điều phối `parse_publication` có quá nhiều tham số |
| Parse đúng | Chỉ theo đường biên dịch từ `\documentclass`; không tách câu ở toán, viết tắt, URL, số thập phân | Test fixture cho từng gói; kiểm ngẫu nhiên 30 Version chọn file gốc | Chưa có bộ nhãn tay để đo độ đúng cấp mục và ranh giới câu |
| Kiểm dữ liệu | Receipt và checksum ở đầu vào; bất biến `parent_id`, `key_map`, schema ở đầu ra | `validate()` chạy trước mỗi lần ghi bảng | — |
| Xử lý lỗi | Lỗi của một Version được ghi kèm mã lý do và không dừng cả lô; Version không có TeX vẫn có bản ghi rỗng | `log/versions.jsonl`: mọi Version trong metadata có đúng một dòng | Parser tất định nên không cần retry; chạy lại thì dùng checkpoint |
| Hiệu năng | Checkpoint, chạy tăng dần, song song theo Publication | Bảng ở mục trên | Kết quả cả Range vẫn được giữ trong RAM tới bước gộp cuối |
| Kiểm thử | Unit test từng gói, test tích hợp `run_batch`, so từng byte giữa các lần chạy | Bộ test trong repo; bảng chạy lại giống từng byte | Chưa có regression test trên toàn bộ dữ liệu thật |
