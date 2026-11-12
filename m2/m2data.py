"""Đọc số liệu Milestone 2 cho các trang báo cáo.

Chỉ đọc file trong ``data/m2/``; không gọi mạng, không đọc corpus. File chưa có thì
giá trị là ``None`` và trang ghi "chưa có số liệu" thay vì lỗi build.

- ``source_range_bao.json``: trạng thái M2.1 và Structure trên Range Bảo qua các lượt đo.
- ``bibtex_sample.json``: số liệu BibTeX trên bộ mẫu 100 Publication (thành viên tự báo cáo).
- ``progress.json``: trạng thái từng gói việc tại ngày ghi trong file.
- ``metrics/<gói>.json`` (chưa có): số liệu nghiệm thu do lệnh đo của từng gói ghi ra.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
sys.path.insert(0, str(ROOT / "m1"))
from m1data import _load, md, pd, pt, show, so, table  # noqa: E402,F401  (dùng lại định dạng của M1)

DATA2 = ROOT / "data" / "m2"


def load(name):
    """Nội dung ``data/m2/<name>`` hoặc ``None`` khi file chưa có."""
    path = DATA2 / name
    return _load(path) if path.exists() else None


SOURCE = load("source_range_bao.json")
BIBTEX = load("bibtex_sample.json")
PROGRESS = load("progress.json")
METRICS = {p.stem: _load(p) for p in sorted((DATA2 / "metrics").glob("*.json"))}


def tex_versions(run):
    """Mẫu số của tỉ lệ ``ready``: Version có TeX (không tính ``empty_non_tex``)."""
    return run["ready"] + run["needs_review"] + run["error"]


def draft(owner, due="28/11/2026"):
    """Ghi chú đầu trang cho phần còn là bản sơ lược."""
    md(f"> **Bản sơ lược ngày {PROGRESS['as_of'][8:]}/{PROGRESS['as_of'][5:7]}.** {owner} hoàn thiện "
       f"phần phương pháp trước {due}. Số liệu đánh dấu *sơ bộ* sẽ được thay bằng số đo nghiệm thu.")


def pending(name):
    """Câu báo thiếu số liệu nghiệm thu của một gói."""
    md(f"*Chưa có `data/m2/metrics/{name}.json`. Phần này sẽ sinh bảng và hình khi file có mặt.*")
