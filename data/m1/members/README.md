# Số liệu tự báo cáo của từng thành viên

Mỗi thành viên một file `<github-username>.json`, theo mẫu `_template.json`.
Trang *So sánh pipeline của các thành viên* đọc các file này lúc build. File có
tên bắt đầu bằng `_` bị bỏ qua.

Các file này mô tả **pipeline ban đầu** của từng thành viên. Snapshot của Engine
chung (`data/m1/snapshots/`, lượt Colab) là tầng riêng cho các trang Kết quả,
Hiệu năng, Hạn chế; hai tầng không thay thế hay cộng gộp với nhau. Bảo dùng Engine
chung từ đầu, nên `NTBao-coder.json` được đóng băng từ snapshot ngày 25/10/2026 của
corpus crawl bằng Mac.

`range.segments` (tùy chọn) ghi Range nhiều Đoạn, ví dụ Range của Minh.

## Quy ước

- Mọi trường số cho phép `null`. **Không đo thật thì để `null`, không ước lượng.**
- Kích thước ghi bằng **byte** (`*_bytes*`), RAM và disk bằng **MiB** (`*_mib`).
  Nếu chỉ có số đã làm tròn (ví dụ "50,69 GB") thì đặt `size.rounded = true`.
- `verification` chọn **một** trong:
  - `validated`: đã chạy `report_m1` hoặc validator của nhóm.
  - `self_checked`: tự kiểm manifest/checksum và đọc Parquet theo schema.
  - `file_check`: chỉ kiểm trạng thái và việc file có tồn tại.
  - `download_state`: chỉ biết archive tải thành công.
  - `none`: chưa có số.
- `versions`: `tex` + `non_tex` + `unavailable` (404/410) + `other_error`
  phải bằng `expected` khi đủ số. `archive_downloaded` chỉ dùng khi chưa tách
  được TeX và non-TeX.
- `references.s2_success` tính trên Publication có metadata; danh sách rỗng hợp
  lệ vẫn là thành công và được đếm riêng ở `empty`.
- `performance.wall_seconds` là tổng thời gian các lượt thật sự chạy, ghi rõ môi
  trường và mức song song trong `environment`.

## Tin nhắn gửi nhóm

> Mình đã đưa phần so sánh pipeline vào báo cáo M1. Mỗi người kiểm tra file
> `data/m1/members/<github-username>.json` của mình trong repo báo cáo (mình điền
> từ file summary của các bạn) và bổ sung số còn thiếu theo quy ước trong
> `data/m1/members/README.md`. Cần gấp nhất:
>
> - **Hải**: chạy `python -m scripts.report_m1` trên thư mục `merged/` để lên mức
>   `validated`.
> - **Liễu**: tổng `bytes_before` / `bytes_after` dạng byte (không làm tròn) và
>   `stats/benchmark_total.json`.
> - **Minh**: tổng hợp mọi `status.json` (số Version có TeX, non-TeX, kích thước
>   trước/sau), số liệu S2, và `last_september_id`.
> - **Nghiêm**: `outputs/summary.json` và `stats/benchmark.json`.
>
> Không đo được thì để `null`, đừng ước lượng. Hạn: <ngày>.
