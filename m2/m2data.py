"""Đọc số liệu Milestone 2 cho các trang báo cáo.

Chỉ đọc file trong ``data/m2/``; không gọi mạng, không đọc corpus. File chưa có thì
giá trị là ``None`` và trang ghi "chưa có số liệu" thay vì lỗi build.

- ``source_range_bao.json``: trạng thái M2.1 và Structure trên Range 2508.02872–2508.07871 qua các lượt đo
  trong lúc phát triển.
- ``bibtex_sample.json``: số liệu BibTeX trên bộ mẫu 100 Publication, đo trong lúc phát triển.
- ``metrics/<gói>.json``: số liệu nghiệm thu do lệnh đo của từng gói ghi ra
  (``export.json``: ``scripts/parse_range.py`` trên bộ mẫu 100 Publication).
- ``bib_coverage/<member>.json``: nguồn bibliography của từng Version TeX trước/sau khôi phục
  (``scripts/measure_bib_coverage.py``); ``bib_coverage/sample_before.json`` là metrics export của
  bộ mẫu khi chưa dùng sidecar, để so với ``metrics/export.json``.
- ``ranges/<member>.json``: metrics của ``scripts/parse_range.py --member`` trên toàn Range (có sidecar
  và root đã review), thêm ``version_status`` và ``failed_version_issues`` đếm từ ``log/versions.jsonl``.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
sys.path.insert(0, str(ROOT / "m1"))
from m1data import COLOR_BASE, COLOR_MAIN, COLOR_SECOND, _load, details, md, pd, pt, show, so, table  # noqa: E402,F401  (dùng lại định dạng của M1)

DATA2 = ROOT / "data" / "m2"


def load(name):
    """Nội dung ``data/m2/<name>`` hoặc ``None`` khi file chưa có."""
    path = DATA2 / name
    return _load(path) if path.exists() else None


SOURCE = load("source_range_bao.json")
LEAVES = load("leaves_ranges.json")
BIBTEX = load("bibtex_sample.json")
METRICS = {p.stem: _load(p) for p in sorted((DATA2 / "metrics").glob("*.json"))}
BIBCOV = {p.stem: _load(p) for p in sorted((DATA2 / "bib_coverage").glob("*.json"))}
MEMBER_ORDER = ["bao", "minh", "nghiem", "hai", "lieu"]
# Báo cáo gọi Range theo dải arXiv ID, không theo tên người chạy (cùng nhãn với chương M1).
MEMBER_NAME = {"bao": "2508.02872–2508.07871", "minh": "2409.18594–2410.03024",
               "nghiem": "2409.08594–2409.13593", "hai": "2412.08848–2412.13847",
               "lieu": "2410.08025–2410.13024"}
RANGES = {m: _load(DATA2 / "ranges" / f"{m}.json") for m in MEMBER_ORDER
          if (DATA2 / "ranges" / f"{m}.json").exists()}
ISSUE_LABEL = {
    "ambiguous_root": "nhiều file gốc, chưa chọn được",
    "parse_error": "lỗi khi dựng cây",
    "include_error": "`\\input` không đọc được (tên động, ra ngoài thư mục, vòng lặp)",
    "missing_content": "thiếu file mục sau `\\begin{document}`",
    "root_selected_by_title": "file gốc chọn theo tiêu đề (kèm lỗi khác)",
    "unsupported_conditional": "lệnh điều kiện chưa hỗ trợ",
    "unclosed_conditional": "lệnh điều kiện không đóng",
    "invalid_syntax": "cú pháp TeX hỏng",
    "publication_error": "lỗi cấp Publication",
    "missing_root": "không có file gốc",
}


def tex_versions(run):
    """Mẫu số của tỉ lệ ``ready``: Version có TeX (không tính ``empty_non_tex``)."""
    return run["ready"] + run["needs_review"] + run["error"]


def pending(path):
    """Câu báo thiếu file số liệu ``data/m2/<path>``."""
    md(f"*Chưa có `data/m2/{path}`. Phần này sẽ sinh bảng và hình khi file có mặt.*")
