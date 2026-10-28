---
exports:
  - format: pdf
---

# Báo cáo arXiv Reference Matching

Đây là Jupyter Book có khả năng tái lập cho Milestone 1 — thu thập dữ liệu.
Nội dung văn bản Markdown và notebook được gộp thành một session MyST trước khi
build. Các code cell được thực thi trong lúc build và chỉ đọc dữ liệu tổng hợp
đã commit trong `data/`; quy trình không crawl Internet.

## Chạy cục bộ

```{code-block} bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/merge_sessions.py
myst build --html --execute --force
```

Kết quả HTML nằm trong `_build/html/`. Để xuất PDF, chạy:

```{code-block} bash
myst build --pdf --execute --force
```

Lệnh `merge_sessions.py` tự tìm các file `.md` và `.ipynb` trong các thư mục
`chapters/` và `docs/`, giữ nguyên thứ tự chữ cái, rồi chuyển notebook thành
MyST với các `{code-cell}` có thể thực thi. Có thể truyền danh sách file riêng:

```{code-block} bash
python scripts/merge_sessions.py \
  chapters/m1_crawling_report.ipynb docs/method.md \
  --output _generated/session.md
```

Notebook cũng có thể được đưa trực tiếp vào `project.toc` nếu muốn giữ mỗi
notebook là một trang riêng thay vì gộp thành một session.

## Môi trường trực tuyến

Repository có workflow GitHub Pages để build và deploy HTML sau mỗi lần push
vào `main`. Người đọc có thể mở notebook trên web; code cell đã được chạy và
output được sinh từ dữ liệu trong repository. PDF được lưu như artifact của
workflow build để tải xuống.

Notebook gốc có thể chạy tương tác trên
[Google Colab](https://colab.research.google.com/github/hcmus-arxiv-reference/Jupyter-Notebook-report-for-mile1/blob/main/chapters/m1_crawling_report.ipynb)
hoặc [Binder](https://mybinder.org/v2/gh/hcmus-arxiv-reference/Jupyter-Notebook-report-for-mile1/main).
Hai môi trường này đọc cùng `requirements.txt`; việc chạy lại vẫn không được
phép crawl Internet.

Để chạy lại cell tương tác, mở notebook gốc trong JupyterLab/Colab và cài
`requirements.txt`. Không đưa corpus thô, credentials hoặc dữ liệu cá nhân vào
repository.
