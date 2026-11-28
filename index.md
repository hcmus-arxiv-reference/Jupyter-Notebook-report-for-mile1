---
title: Báo cáo arXiv Reference Matching
---

Báo cáo của nhóm 3 KHDL24 cho đồ án Nhập môn Khoa học Dữ liệu (HCMUS). Phần
**Milestone 1** trình bày cách nhóm thu thập source LaTeX, metadata và
Reference của các bài arXiv trong Range được giao. Phần này gồm thống kê dữ liệu
và hiệu năng crawler, đúng các yêu cầu trong
[đề Crawling](https://hcmus-cs-ta.github.io/lab-book/intro-ds/statement/crawling/).

- Code: <https://github.com/hcmus-arxiv-reference/arxiv-reference-matching>
- Mã nguồn của báo cáo: <https://github.com/hcmus-arxiv-reference/Jupyter-Notebook-report-for-mile1>

Mọi bảng, hình và con số trong báo cáo được tính lúc build từ số liệu tổng hợp
trong `data/m1/` và `data/m2/`. Báo cáo không chứa source LaTeX, nội dung Reference hay thông
tin đăng nhập, và quá trình build không gọi mạng.

Phần **Milestone 2** trình bày Parser: cấu trúc chương trình, phương pháp của từng bước, số liệu
trên cả 5 Range và hiệu năng, theo các yêu cầu trong
[đề Parsing](https://hcmus-cs-ta.github.io/lab-book/intro-ds/statement/parsing/).

## Luồng dữ liệu

:::{figure} images/pipeline-m1-m3.svg
:label: fig-pipeline-m1-m3
:alt: Sơ đồ luồng dữ liệu: arXiv và Semantic Scholar vào Engine crawl, tạo corpus thô và bảng papers, references; Parser M2 tạo elements, hierarchy, bibtex; mô hình Matching tạo predictions; sáu bảng của năm Range được gộp thành dataset Hugging Face.

Luồng dữ liệu từ M1 đến M3. Mỗi thành viên chạy cùng codebase trên Range của mình; bước cuối
gộp 6 bảng của 5 Range thành dataset nộp. Sơ đồ vẽ theo code ở commit `f1972ad` của repo code.
:::

## Thành viên

| Thành viên | GitHub | Range được giao | Phần phụ trách chính |
|---|---|---|---|
| Nguyễn Thành Bảo (nhóm trưởng) | `NTBao-coder` | 2508.02872–2508.07871 | Engine crawler chung, tích hợp Parser, khôi phục bibliography, dataset Hugging Face, Jupyter Book |
| Võ Nhật Liệu | `langtucod0n` | 2410.08025–2410.13024 | Parser: gom source và khung mục; mô hình xếp hạng M3 |
| Hồ Hữu Nghiêm | `hohuunghiem` | 2409.08594–2409.13593 | Parser: tách lá (câu, công thức, hình); matcher tự động và chia tập M3 |
| Đỗ Ngọc Hải | `ngochai06` | 2412.08848–2412.13847 | Parser: chuẩn hóa và BibTeX |
| Ngô Hoàng Minh | `nhminh107` | 2409.18594–2410.03024 | Parser: kiểu dữ liệu giữa các bước, xuất bảng, batch; đặc trưng hierarchy M3 |

Ở Milestone 1, mỗi thành viên tự xây một pipeline và crawl Range của mình, rồi nhóm ghép các
cách làm tốt nhất vào một Engine chung (trang *So sánh pipeline của các thành viên*). Các trang
sau gọi Range theo dải arXiv ID; bảng trên cho biết Range nào thuộc về ai.
