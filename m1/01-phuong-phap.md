---
title: Phương pháp thu thập
---

Mỗi thành viên được giao một **Range** gồm 5.000 arXiv ID. Với mỗi bài
(**Publication**) trong Range, nhóm phải lấy đủ mọi phiên bản (**Version**),
gồm source LaTeX, metadata và metadata của các bài được trích dẫn
(**Reference**). Toàn bộ code nằm ở
[repo arxiv-reference-matching](https://github.com/hcmus-arxiv-reference/arxiv-reference-matching).
Các thuật ngữ in đậm dùng đúng nghĩa trong file `CONTEXT.md` của repo đó.

## Nguồn dữ liệu và giới hạn truy cập

| Nguồn | Dùng để | Giới hạn nhóm tuân thủ |
|---|---|---|
| arXiv API `export.arxiv.org/api/query` | Tìm Publication, đọc metadata và danh sách Version | Hai request arXiv cách nhau ít nhất 3,1 giây (đề yêu cầu ≥ 3 giây); chỉ một kết nối tại một thời điểm |
| arXiv source `export.arxiv.org/src/{id}v{n}` | Tải source của từng Version | Dùng chung bộ điều tiết với API ở trên; User-Agent mô tả dự án kèm email liên hệ |
| Semantic Scholar Graph API `paper/arXiv:{id}/references` | Lấy Reference, có phân trang | Cách nhau 1,1 giây khi có API key (3,1 giây nếu không có); bộ điều tiết riêng, không dùng chung với arXiv |

Nhóm không dùng OAI-PMH hay bộ dữ liệu Kaggle. Đề không yêu cầu harvest toàn bộ
kho, mà mỗi Range chỉ có 5.000 ID liên tiếp. Truy vấn API theo lô cho tập ID
cố định này vừa đủ nhanh, vừa trả về đúng danh sách Version tại thời điểm crawl.

Range của bốn thành viên nằm gọn trong một tháng. Range thứ năm vắt qua tháng
9 và tháng 10/2024, nên được ghi thành hai **Đoạn** tường minh trong
`configs/ranges.toml`. Nhờ vậy crawler không cần hỏi arXiv ID cuối của tháng.

## Thiết kế crawler

Crawler là một **Engine** duy nhất trong `src/crawl/`
([ADR 0001](https://github.com/hcmus-arxiv-reference/arxiv-reference-matching/blob/main/docs/adr/0001-src-crawl-la-khung-duy-nhat.md)).
Engine chia thành các **Stage**, mỗi Stage có một interface riêng
([ADR 0003](https://github.com/hcmus-arxiv-reference/arxiv-reference-matching/blob/main/docs/adr/0003-crawl-library-boundaries.md)):

```{mermaid}
flowchart LR
  R[Runner<br/>chạy toàn Range, nhiều lượt] --> D[Discovery<br/>metadata + danh sách Version]
  D --> S[Source fetch<br/>tải và giải nén từng Version]
  D --> F[References<br/>Semantic Scholar, phân trang]
  S --> M[(Manifest<br/>trạng thái + checksum)]
  F --> M
  M --> E[Export<br/>bảng papers, references]
```

- **Discovery** truy vấn metadata theo lô 50 ID. ID nào thiếu hoặc lỗi trong lô thì
  được hỏi lại riêng, nên không có bài nào bị coi là không tồn tại chỉ vì lô bị lỗi.
- **Source fetch** tải archive của từng Version, chỉ giữ `.tex` và `.bib`, không
  sửa nội dung file (các lệnh `figure`, `\includegraphics` vẫn còn nguyên cho
  Milestone 2). Version chỉ có PDF hoặc docx được ghi trạng thái `non_tex` với
  bản ghi rỗng, không bị loại khỏi dữ liệu.
- **References** chạy song song với Source fetch, trên một luồng riêng. Chỉ
  luồng chính được ghi Manifest.
- **Export** đọc lại cache đã xác minh rồi ghi hai bảng Parquet theo schema của
  đề: `papers` và `references`. Bảng `references` chỉ chứa Reference có arXiv ID.

### Tổ chức dữ liệu

File trên đĩa là nguồn dữ liệu gốc; Parquet chỉ là bảng xuất ra
([ADR 0002](https://github.com/hcmus-arxiv-reference/arxiv-reference-matching/blob/main/docs/adr/0002-file-la-nguon-du-lieu-goc.md)):

```text
<data-dir>/
├── raw/<publication-key>/v<n>/     # .tex/.bib của từng Version + receipt checksum
├── metadata/                       # metadata của Publication và từng Version
├── references/                     # phản hồi Semantic Scholar
├── manifests/crawl.jsonl           # trạng thái từng tác vụ, dùng để resume
└── tables/{papers,references}.parquet
```

Nhóm đã cân nhắc SQLite và một cơ sở dữ liệu SQL, nhưng chọn file, vì ba lý do:
cách tổ chức này đúng như đề gợi ý (mỗi bài một thư mục); Parser ở Milestone 2
đọc thẳng `.tex`; và đo dung lượng bằng `du` trên Colab rất đơn giản.

### Xử lý lỗi và chạy tiếp

| Tình huống | Cách xử lý |
|---|---|
| HTTP 429 / 5xx | Theo `Retry-After` nếu có, không thì chờ theo bảng backoff có jitter; giới hạn số lần thử |
| Kết nối bị cắt giữa chừng | Gửi lại với header `Range: bytes=<đã nhận>-` để tải tiếp, không tải lại từ đầu |
| HTTP 404 / 410 | Ghi `unavailable`, không đổi thành `non_tex` hay danh sách rỗng |
| Archive hỏng hoặc quá giới hạn kích thước | Ghi lỗi cho riêng Version đó, Range vẫn chạy tiếp |
| Chạy lại | Bỏ qua Version đã có checksum khớp; chỉ tải lại phần thiếu hoặc hỏng |

Trong smoke test ngày 03/11/2026, một file bị cắt ở byte 3.145.728 đã được tải
tiếp từ đúng vị trí đó. Khi chạy lại y hệt, crawler không gửi request nào và
checksum của mọi file trong cache không đổi
([biên bản](https://github.com/hcmus-arxiv-reference/arxiv-reference-matching/blob/main/docs/m1-smoke-2026-11-03.md)).

## Tái lập báo cáo

Các trang sau chỉ đọc số liệu tổng hợp trong `data/m1/` của repo báo cáo. Số
liệu này do `scripts/report_m1.py` (thống kê corpus) và `src/merge_benchmarks.py`
(hiệu năng) trong repo code sinh ra. Mọi bảng, hình và con số trong câu văn
được tính lúc build sách. Quá trình build không gọi mạng.
