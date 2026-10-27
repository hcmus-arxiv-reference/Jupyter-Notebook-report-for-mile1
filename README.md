# Jupyter-notebook-for-mile-1

Báo cáo Jupyter Book cho **Milestone 1 — Data Crawling** của dự án *arXiv Reference Matching* (nhóm 3 KHDL24).
Đề bài: https://hcmus-cs-ta.github.io/lab-book/intro-ds/statement/crawling/

| Mục | Giá trị |
| --- | --- |
| Repo code (crawler) | `<điền link repo code công khai>` |
| Báo cáo (GitHub Pages) | `<điền link Pages>` |
| Nhóm trưởng | Nguyễn Thành Bảo |
| Deadline nộp M1 | `<điền từ Moodle>` — **không nhận nộp muộn** |

---

## 1. Repo này dùng để làm gì

Repo này **chỉ chứa báo cáo**. Mã crawler nằm ở repo code riêng. Báo cáo phải:

- giải thích cách crawler hoạt động và công cụ đã dùng;
- trình bày thống kê dữ liệu và hiệu năng bằng **hình/bảng sinh lúc build**, có tính tương tác ở một số hình;
- được đăng trên GitHub Pages và mở được khi chưa đăng nhập;
- là phần đầu của một book duy nhất; Milestone 2 sẽ thêm chương sau.

### Quy tắc bất biến

1. **Không đưa corpus thô** (`.tex`, `.bib`, archive, Parquet) vào repo này. Chỉ lưu số liệu tổng hợp nhỏ.
2. **Không crawl Internet khi build.** Notebook chỉ đọc file trong `data/stats/`.
3. **Không dán ảnh chụp** làm hình kết quả. Mọi hình/bảng sinh bằng code.
4. **Mọi con số trong văn bản lấy từ biến trong notebook**, không gõ tay.
5. Ghi rõ **tử số và mẫu số** cho mọi tỷ lệ. Không lấy số ID được giao làm số bài đã tải thành công.
6. Số liệu chưa hoàn tất phải ghi rõ thời điểm snapshot và phạm vi.

---

## 2. Cấu trúc repo đề xuất

```
.
├── README.md
├── myst.yml                  # cấu hình book (hoặc _config.yml + _toc.yml nếu dùng Jupyter Book 1)
├── requirements.txt          # pandas, plotly, ... (ghim phiên bản)
├── index.md                  # trang giới thiệu
├── 01-overview.ipynb         # thiết kế hệ thống, công cụ, API
├── 02-data-stats.ipynb       # thống kê dữ liệu
├── 03-performance.ipynb      # thời gian, RAM, đĩa
├── 04-limitations.md         # hạn chế, lỗi, việc còn lại
├── data/
│   └── stats/
│       ├── versions_<owner>.csv   # mỗi dòng một Version, mỗi thành viên một file
│       ├── runs_<owner>.csv       # mỗi dòng một lượt chạy
│       └── SCHEMA.md              # định nghĩa cột (mục 3)
├── scripts/
│   └── merge_stats.py        # gộp các file của 5 thành viên, kiểm tra schema
└── .github/workflows/        # build và deploy Pages
```

---

## 3. Hợp đồng số liệu (cả nhóm xuất cùng schema)

Đây là chỗ dễ lệch giữa các thành viên nhất. **Mỗi người xuất file theo đúng schema này từ repo code**, rồi bỏ vào `data/stats/`.

### `versions_<owner>.csv` (mỗi dòng một Version)

| Cột | Kiểu | Ý nghĩa |
| --- | --- | --- |
| `owner` | string | Người chạy |
| `arxiv_id` | string | ID gốc, không có `vN` (giữ ID kiểu cũ như `hep-th/9901001`) |
| `version` | int | 1, 2, … |
| `n_versions_expected` | int | Số Version theo discovery của API |
| `status` | string | `success` / `non_tex` / `unavailable` / `download_error` / `not_attempted` |
| `bytes_archive` | int, nullable | Kích thước archive tải về (**trước** khi bỏ hình) |
| `bytes_kept` | int, nullable | Tổng `.tex` + `.bib` giữ lại (**sau** khi bỏ hình) |
| `n_refs_total` | int, nullable | Số reference thu được từ Semantic Scholar |
| `n_refs_with_arxiv_id` | int, nullable | Số reference có ArXiv ID (thành dòng của bảng `references`) |
| `s2_status` | string | `ok` / `empty` / `rate_limited` / `error` / `not_attempted` |
| `t_download_s` | float, nullable | Giây tải + giải nén |
| `t_refs_s` | float, nullable | Giây gọi Semantic Scholar |

### `runs_<owner>.csv` (mỗi dòng một lượt chạy)

| Cột | Ý nghĩa |
| --- | --- |
| `owner`, `run_id`, `commit` | Định danh lượt chạy và commit crawler |
| `started_at`, `finished_at` | Thời gian bắt đầu và kết thúc (ISO) |
| `t_discovery_s` | Tổng thời gian entry discovery |
| `t_wall_s` | Wall time đầu-cuối |
| `n_publications_processed` | Số Publication thực xử lý |
| `ram_peak_mb`, `ram_mean_mb` | RAM tối đa và trung bình (cả tiến trình con) |
| `disk_peak_mb`, `output_mb` | Đĩa tối đa và dung lượng đầu ra cuối |
| `environment` | Ví dụ `colab-cpu` hoặc `local` (ghi rõ) |
| `is_resume` | `true` nếu là lượt chạy tiếp, không gộp vào benchmark mới |

### Định nghĩa chỉ số (viết cố định để mọi người tính giống nhau)

| Chỉ số | Công thức |
| --- | --- |
| Tỷ lệ Version thành công | Version `success` / tổng Version dự kiến |
| Độ phủ Version | (`success` + `non_tex` đã xác minh) / tổng Version dự kiến |
| Kích thước trung bình trước/sau bỏ hình | trung bình `bytes_archive` và `bytes_kept` trên Version `success` |
| Reference trung bình mỗi bài | trung bình `n_refs_total` trên Publication có `s2_status` là `ok` hoặc `empty` |
| Tỷ lệ thành công crawl reference | Version có `s2_status = ok` / Version đã thử gọi S2 |

---

## 4. Nội dung báo cáo cần viết

| Chương | Phải có | Nguồn dữ liệu |
| --- | --- | --- |
| **1. Tổng quan và thiết kế** | Sơ đồ quy trình discovery → download → extract → reference → ghi bảng; công cụ và API đã dùng (arXiv API, `export.arxiv.org/src`, Semantic Scholar, thư viện HTTP); lý do chọn; tuân thủ giới hạn tốc độ (3 giây giữa các request arXiv, 1 request/giây với Semantic Scholar) | Viết tay, tham chiếu code |
| **2. Thống kê dữ liệu** | Số Publication/Version thành công và tỷ lệ; phân bố `status`; số Version mỗi bài; kích thước trung bình trước/sau bỏ hình; số reference trung bình; tỷ lệ thành công crawl reference | `versions_*.csv` |
| **3. Hiệu năng** | Thời gian một bài, trung bình mỗi bài, tổng entry discovery; RAM tối đa/trung bình; đĩa tối đa; dung lượng đầu ra. Đo trên **Colab CPU**; hệ thống nhiều chương trình thì tính wall time đầu-cuối và RAM tổng | `runs_*.csv` |
| **4. Hạn chế** | Version không có TeX, lỗi tải, lỗi S2, dữ liệu chưa hoàn tất, thời điểm snapshot, giới hạn công cụ đo | Viết tay + số từ CSV |

Mỗi chương nên có **ít nhất một hình tương tác** (ví dụ Plotly: phân bố trạng thái, histogram kích thước, boxplot thời gian) và một bảng tổng hợp theo thành viên cộng một dòng tổng của nhóm.

---

## 5. Việc cần làm

### Giai đoạn 0 — Nền tảng (làm ngay)
- [ ] Xác nhận deadline trên Moodle và ghi vào bảng đầu README.
- [ ] Xác nhận công cụ build mà môn khuyến nghị (Jupyter Book 2 / MyST hay Jupyter Book 1) và dùng đúng một loại.
- [ ] Tạo khung book, deploy **một trang rỗng** lên GitHub Pages để phát hiện sớm lỗi cấu hình (`BASE_URL`, quyền Pages, workflow).
- [ ] Ghim phiên bản trong `requirements.txt`; build thử trên môi trường sạch.

### Giai đoạn 1 — Chốt số liệu
- [ ] Hoàn thiện `data/stats/SCHEMA.md` theo mục 3 và gửi cả nhóm.
- [ ] Mỗi thành viên viết/chạy script xuất `versions_<owner>.csv` và `runs_<owner>.csv` từ manifest/receipt của Range mình (không từ file Parquet chưa hoàn tất).
- [ ] Viết `scripts/merge_stats.py`: gộp, kiểm tra cột/kiểu/trùng khóa `(owner, arxiv_id, version)`, báo lỗi theo người sở hữu.
- [ ] Đối soát: số Version trên đĩa so với `n_versions_expected` từ API.

### Giai đoạn 2 — Notebook
- [ ] `01-overview.ipynb`: sơ đồ quy trình, công cụ, tham số cấu hình.
- [ ] `02-data-stats.ipynb`: toàn bộ chỉ số mục 3, mỗi chỉ số kèm tử số/mẫu số và bảng theo thành viên.
- [ ] `03-performance.ipynb`: đọc `runs_*.csv`, tách lượt chạy mới và lượt resume.
- [ ] `04-limitations.md`: hạn chế và danh sách lỗi theo loại.
- [ ] Kiểm tra mọi số trong văn bản lấy từ biến, không gõ tay.

### Giai đoạn 3 — Benchmark chính thức
- [ ] Bổ sung phép đo RAM trung bình và RAM tiến trình con trong repo code (hiện `metrics.py` chưa đo).
- [ ] Chạy benchmark trên Colab CPU, ghi commit, cấu hình, môi trường.
- [ ] Cập nhật `runs_*.csv`, build lại, kiểm tra hình/bảng.

### Giai đoạn 4 — Đóng gói và nộp
- [ ] Build sạch từ đầu trên máy khác (clone mới, cài, build).
- [ ] Mở link Pages bằng cửa sổ ẩn danh; kiểm tra không mất style, link và hình tương tác hoạt động.
- [ ] Ghi mã commit cuối của cả hai repo.
- [ ] Dán hai link (repo code, báo cáo) lên Moodle **trước deadline một khoảng dự phòng**.

---

## 6. Chạy cục bộ

Lệnh dưới đây giả định dùng MyST (Jupyter Book 2). Nếu nhóm chọn công cụ khác, thay bằng lệnh tương ứng và cập nhật mục này.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/merge_stats.py        # kiểm tra và gộp số liệu
myst build --html                    # build book
```

Triển khai: bật GitHub Pages với nguồn là GitHub Actions và đặt workflow build rồi publish. Với project site, cần đặt đúng `BASE_URL` theo tên repo, nếu sai thì trang sẽ mất style.

---

## 7. Tiêu chí hoàn thành (Definition of Done)

- [ ] Link Pages mở được khi chưa đăng nhập.
- [ ] Đủ nội dung bắt buộc của đề: cách hoạt động, công cụ, số bài thành công và tỷ lệ, kích thước trước/sau bỏ hình, reference trung bình, tỷ lệ thành công reference, thời gian, bộ nhớ.
- [ ] Mọi hình/bảng sinh lúc build, có ít nhất vài hình tương tác.
- [ ] Mọi tỷ lệ có tử số và mẫu số; thời điểm snapshot được ghi.
- [ ] Hiệu năng ghi rõ môi trường đo (Colab CPU) và phạm vi.
- [ ] Repo không chứa corpus, Parquet hay bí mật.
- [ ] Người ngoài nhóm clone sạch và build được theo README.

---

## 8. Mở rộng cho Milestone 2

Chương M2 sẽ thêm vào cùng book: thuật toán parsing, thống kê dedup Element/BibTeX, tỷ lệ parse thành công, benchmark Parser. Giữ cấu trúc `data/stats/` theo từng milestone (ví dụ `data/stats/m2/`) để không lẫn số liệu.
