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
| Snapshot metadata arXiv trên Kaggle (`Cornell-University/arxiv`, file `arxiv-metadata-oai-snapshot.json`) | Discovery: title, authors, `journal-ref`, danh sách Version và ngày từng Version | Đọc offline, không gửi request tới arXiv |
| arXiv API `export.arxiv.org/api/query` | Discovery dự phòng, chỉ cho ID không có trong snapshot | Hai request arXiv cách nhau ít nhất 3,1 giây (đề yêu cầu ≥ 3 giây); chỉ một kết nối tại một thời điểm |
| arXiv source `export.arxiv.org/src/{id}v{n}` | Tải source của từng Version | Dùng chung bộ điều tiết với API ở trên; User-Agent mô tả dự án kèm email liên hệ |
| Semantic Scholar Graph API `POST /paper/batch` | Lấy danh sách trích dẫn của 100 Publication trong một request | Cách nhau 1,1 giây khi có API key (3,1 giây nếu không có); bộ điều tiết riêng, không dùng chung với arXiv |
| Semantic Scholar Graph API `GET /paper/arXiv:{id}/references` | Lấy lại danh sách trích dẫn của một Publication theo từng trang, khi kết quả lô có thể bị cắt (≥ 1.000 dòng), hoặc khi lô lỗi mà không phải do bị giới hạn (429/5xx) | Cùng bộ điều tiết với `/paper/batch` |

Nhóm không dùng OAI-PMH. Lúc đầu Discovery gọi arXiv API theo lô 50 ID (tag
`m1-bench-v2`). Trong lượt chạy thử trên Colab ngày 15/11/2026, `/api/query` trả
HTTP 429 cho 43/55 lô, trong khi `/src/` vẫn tải đều. Từ `m1-bench-v3`, Discovery
đọc metadata từ snapshot của arXiv trên Kaggle (`src/crawl/snapshot.py`). Cách
này bớt khoảng 973 request arXiv mỗi Range (100 lô Discovery cộng các request tra
ngày Version). Snapshot gốc nặng 4–5 GB, nên `scripts/extract_snapshot.py` trích
trước các ID của 5 Range ra một file nhỏ. Mỗi lượt crawl đọc file trích này. ID nào
không có trong snapshot vẫn được hỏi qua arXiv API như trước.

**Mốc phủ Version.** Header của file trích ghi sha256 của file snapshot gốc và
`latest_update_date`, tức ngày cập nhật mới nhất trong snapshot. Đây là ngày chốt
danh sách Version của lượt crawl: Version mà arXiv nhận sau ngày này không có trong
dữ liệu. File trích trên Hugging Face mà notebook Colab của 5 Range tải về được tạo ngày 15/11/2026, có
`latest_update_date` là **13/11/2026** và chứa đủ 25.000/25.000 ID (không ID nào phải
hỏi qua API). Notebook Colab ghi ngày này cùng sha256 vào `run.json` của mỗi lượt, để
đối chiếu với timestamp lúc crawl. Mục *Độ phủ Version theo thời gian* ở trang
*Lỗi còn lại và hạn chế* so số Version này với danh sách tra lại trên arXiv.

**Cách tính 3,1 giây.** Bộ điều tiết (`_send` trong `src/crawl/http_client.py`) tính
khoảng cách từ lúc **bắt đầu** request trước, không phải từ lúc tải xong. Như vậy
hai request tới arXiv luôn bắt đầu cách nhau ít nhất 3,1 giây. Mỗi lúc vẫn chỉ
có một kết nối, vì request sau chỉ bắt đầu khi request trước đã xong. Với archive lớn,
thời gian tải đã dài hơn 3,1 giây, nên request sau có thể gửi ngay khi tải xong.
Giảng viên khuyên tính từ lúc tải xong để ít bị HTTP 429 hơn. Nhóm giữ cách tính hiện
tại vì hai lý do. Thứ nhất, lỗi 429 ở `/src/` đã có cơ chế chờ lùi xử lý (mục *Xử lý lỗi*
bên dưới). Thứ hai, số lần 429 khi tải source của từng Range được ghi lại ở trang
*Hiệu năng*, nên đánh giá được lựa chọn này bằng số liệu.

Range của bốn thành viên nằm gọn trong một tháng. Range thứ năm vắt qua tháng
9 và tháng 10/2024, nên được ghi thành hai **Đoạn** tường minh trong
`configs/ranges.toml`. Nhờ vậy crawler không cần hỏi arXiv ID cuối của tháng.

## Công cụ và thư viện

| Thành phần | Công cụ | Ghi chú |
|---|---|---|
| HTTP | `urllib.request` (thư viện chuẩn Python) | Không dùng `requests` hay gói `arxiv`; bộ điều tiết, retry và tải tiếp bằng header `Range` tự viết trong `src/crawl/http_client.py` |
| Đọc snapshot metadata | `json`, `gzip` | Đọc file trích (một file JSON nén gzip); đổi dấu TeX trong tên tác giả (`\'e`) sang Unicode như arXiv API |
| Đọc Atom của arXiv API | `xml.etree.ElementTree` | Chỉ dùng cho ID không có trong snapshot |
| Giải nén source | `tarfile`, `gzip`, `zipfile` | Chỉ giữ `.tex` và `.bib` |
| Bảng xuất ra | `pyarrow` (Parquet) | Schema tường minh trong `src/common/schema.py` |
| Khóa thư mục dữ liệu | `filelock` | Chặn hai crawler cùng ghi một thư mục |
| Cấu hình | `tomllib` (Range), `python-dotenv` (email liên hệ, API key) | Khóa bí mật không nằm trong repo |
| Đo hiệu năng | `psutil` | RAM của cả cây tiến trình, dung lượng thư mục dữ liệu |
| Kiểm thử | `pytest` | Chạy trên CI với Python 3.12 và 3.13 |

## Thiết kế crawler

Crawler là một **Engine** duy nhất trong `src/crawl/`
([ADR 0001](https://github.com/hcmus-arxiv-reference/arxiv-reference-matching/blob/main/docs/adr/0001-src-crawl-la-khung-duy-nhat.md)).
Engine chia thành các **Stage**, mỗi Stage có một interface riêng
([ADR 0003](https://github.com/hcmus-arxiv-reference/arxiv-reference-matching/blob/main/docs/adr/0003-crawl-library-boundaries.md)):

```{mermaid}
flowchart LR
  R[Runner<br/>chạy toàn Range, nhiều lượt] --> D[Discovery<br/>metadata + danh sách Version]
  D --> S[Source fetch<br/>tải và giải nén từng Version]
  D --> F[References<br/>Semantic Scholar /paper/batch<br/>luồng riêng]
  S --> M[(Manifest<br/>trạng thái + checksum)]
  F --> M
  M --> E[Export<br/>bảng papers, references]
```

- **Discovery** lấy metadata và danh sách Version từ snapshot. Riêng ID không có
  trong snapshot thì hỏi arXiv API theo lô 50 ID. ID nào thiếu hoặc lỗi trong lô thì
  được hỏi lại riêng, nên không có bài nào bị coi là không tồn tại chỉ vì lô bị lỗi.
- **Source fetch** tải archive của từng Version, chỉ giữ `.tex` và `.bib`, không
  sửa nội dung file (các lệnh `figure`, `\includegraphics` vẫn còn nguyên cho
  Milestone 2). Version chỉ có PDF hoặc docx được ghi trạng thái `non_tex` với
  bản ghi rỗng, không bị loại khỏi dữ liệu.
- **References** chạy song song với Source fetch, trên một luồng riêng. Luồng này
  gom 100 Publication vào một request `POST /paper/batch`. Publication nào có kết
  quả lô có thể đã bị cắt (từ 1.000 dòng trở lên) thì được lấy lại theo từng trang
  qua `/references`. Thời gian chờ Semantic Scholar vì vậy không chặn luồng tải từ
  arXiv. Chỉ luồng chính được ghi Manifest.
- `ref_submission_date` lấy từ trường `publicationDate` của Semantic Scholar, vì S2
  không có ngày nộp lên arXiv (giảng viên cho phép, hỏi đáp câu 19–20). Nếu trường
  này thiếu hoặc không phải ngày ISO thì giá trị là null; nhóm không tra thêm ngày
  `v1` trên arXiv (`src/common/references.py`).
- **Export** đọc lại cache đã xác minh rồi ghi hai bảng Parquet theo schema của
  đề: `papers` và `references`. Bảng `references` chỉ chứa Reference có arXiv ID.

### Tổ chức dữ liệu

File trên đĩa là nguồn dữ liệu gốc; Parquet chỉ là bảng xuất ra
([ADR 0002](https://github.com/hcmus-arxiv-reference/arxiv-reference-matching/blob/main/docs/adr/0002-file-la-nguon-du-lieu-goc.md)):

```text
<data-dir>/
├── raw/<publication-key>/v<n>/     # .tex/.bib của từng Version + receipt checksum
├── metadata/<publication-key>.json # metadata của Publication; ngày mỗi Version nằm trong revised_dates
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
