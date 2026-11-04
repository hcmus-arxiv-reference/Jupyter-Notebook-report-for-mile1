# Báo cáo arXiv Reference Matching (Jupyter Book 2)

Báo cáo của nhóm 3 KHDL24, build bằng [MyST / Jupyter Book 2](https://mystmd.org).
Code của dự án: <https://github.com/hcmus-arxiv-reference/arxiv-reference-matching>.

## Cấu trúc

```text
myst.yml                 # cấu hình sách và mục lục
index.md                 # trang đầu
m1/                      # Milestone 1
  01-phuong-phap.md      # nguồn dữ liệu, thiết kế crawler (chỉ văn bản)
  02-ket-qua.md          # thống kê corpus (code-cell)
  03-hieu-nang.md        # benchmark Colab (code-cell)
  04-han-che.md          # lỗi còn lại, hạn chế (code-cell)
  m1data.py              # đọc data/m1/ và hàm định dạng dùng chung
data/m1/
  snapshots/<member>.json             # output của scripts/report_m1.py, mỗi Range một file
  benchmark/benchmark_total.json      # output của src/merge_benchmarks.py (khi có)
  benchmark/benchmark_samples_all.csv
```

Trang có code là MyST Markdown notebook: các `{code-cell}` được chạy lúc build.
Mọi bảng, hình (Plotly, tương tác) và con số trong câu văn đều sinh từ `data/m1/`.

## Quy tắc

1. Chỉ commit số liệu tổng hợp nhỏ. Không commit `.tex`, `.bib`, archive, Parquet hay bí mật.
2. Build không gọi mạng; notebook chỉ đọc `data/m1/`.
3. Không gõ tay con số kết quả vào văn bản; viết trong code-cell.
4. Tỉ lệ luôn ghi kèm tử số và mẫu số (hàm `pt()`).

## Cập nhật số liệu

Từ repo code:

```sh
# Thống kê corpus của một Range
python -m scripts.report_m1 --cache data/crawl-smoke \
  --output ../Jupyter-Notebook-report-for-mile1/data/m1/snapshots/<member>.json

# Sau lượt benchmark tuần tự trên Colab
python -m src.merge_benchmarks --runs stats/runs --out stats
cp stats/benchmark_total.json stats/benchmark_samples_all.csv \
  ../Jupyter-Notebook-report-for-mile1/data/m1/benchmark/
```

## Build cục bộ

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
myst start --execute          # xem trực tiếp tại http://localhost:3000
myst build --html --execute   # ra _build/html/
```

Workflow `.github/workflows/deploy-book.yml` build lại ở mọi pull request và
deploy lên GitHub Pages khi push vào `main`. Trong repo Settings → Pages, chọn
nguồn là **GitHub Actions**.
