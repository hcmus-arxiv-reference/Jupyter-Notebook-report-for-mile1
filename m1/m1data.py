"""Đọc số liệu tổng hợp của Milestone 1 cho các trang báo cáo.

Chỉ đọc file trong ``data/m1/``; không gọi mạng, không đọc corpus thô.

- ``snapshots/<member>.json``: snapshot ``scripts/report_m1.py`` của từng Range (tầng
  kiểm chứng, Engine chung). Trang Kết quả, Hiệu năng, Hạn chế đọc tầng này.
- ``benchmark/<member>/benchmark_total.json`` và ``benchmark_samples_all.csv``: số đo
  ``src.merge_benchmarks`` của lượt Colab cùng Range.
- ``members/<github>.json``: số liệu tự báo cáo của pipeline ban đầu từng thành viên.
  Chỉ trang So sánh pipeline đọc tầng này; hai tầng không cộng gộp với nhau.
- ``arxiv_versions.json``: số Version hiện có trên arXiv của từng Range, để đối chiếu.
"""
from __future__ import annotations

import json
from pathlib import Path

import markdown as _markdown
import pandas as pd
import plotly.io as pio
from IPython.display import HTML, display

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
DATA = ROOT / "data" / "m1"

# Khóa snapshot (tham số MEMBER của notebook Colab) -> (GitHub username, tên hiển thị).
MEMBER_NAMES = {"bao": ("NTBao-coder", "Bảo"), "minh": ("nhminh107", "Minh"),
                "nghiem": ("hohuunghiem", "Nghiêm"), "hai": ("ngochai06", "Hải"),
                "lieu": ("langtucod0n", "Liễu")}
N_RANGES = len(MEMBER_NAMES)  # số Range được giao cho nhóm


def name(key):
    """Tên hiển thị của một khóa snapshot."""
    return MEMBER_NAMES.get(key, (key, key))[1]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


SNAPSHOTS = {p.stem: _load(p) for p in sorted((DATA / "snapshots").glob("*.json"))}
if not SNAPSHOTS:
    raise FileNotFoundError(f"Không có snapshot nào trong {DATA / 'snapshots'}")
for _member, _snap in SNAPSHOTS.items():
    if _snap.get("format") != 1:
        raise ValueError(f"{_member}: chỉ hỗ trợ snapshot format 1")

BENCHMARKS = {p.parent.name: _load(p) for p in sorted((DATA / "benchmark").glob("*/benchmark_total.json"))}
_samples = [pd.read_csv(p).assign(member=p.parent.name)
            for p in sorted((DATA / "benchmark").glob("*/benchmark_samples_all.csv"))]
SAMPLES = pd.concat(_samples, ignore_index=True) if _samples else None

_ARXIV = DATA / "arxiv_versions.json"
ARXIV_VERSIONS = _load(_ARXIV) if _ARXIV.exists() else None


def so(value, digits=0):
    """Định dạng số kiểu Việt Nam: 12.345 và 3,14."""
    if value is None:
        return "chưa có"
    text = f"{value:,.{digits}f}"
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def pt(numerator, denominator, digits=1):
    """Tỉ lệ kèm tử số và mẫu số, ví dụ ``4.941 / 5.000 (98,8%)``."""
    if not denominator:
        return f"{so(numerator)} / {so(denominator)}"
    return f"{so(numerator)} / {so(denominator)} ({so(100 * numerator / denominator, digits)}%)"


def mb(value, digits=2):
    """Byte -> MB thập phân (10^6), ``chưa đo`` khi thiếu."""
    return "chưa đo" if value is None else f"{so(value / 1e6, digits)} MB"


def md(text):
    """Hiển thị Markdown đã chuyển sang HTML.

    Trang MyST in output ``text/markdown`` của kernel thành văn bản thô (còn nguyên
    ``**`` và dấu backtick), nên phải tự chuyển sang HTML.
    """
    display(HTML(_markdown.markdown(text)))


def show(fig):
    """Hiển thị hình Plotly tương tác trong trang HTML."""
    fig.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=50, b=40))
    display(HTML(pio.to_html(fig, include_plotlyjs="cdn", full_html=False)))


def table(df, **formats):
    """Bảng HTML không có cột index; mọi chuỗi được escape (giữ ``<id>``, ``v<n>``)."""
    style = df.style.format(na_rep="—", escape="html").hide(axis="index")
    if formats:
        style = style.format(formats, na_rep="—", escape="html")
    display(style)


def range_text(rng):
    """Range dạng ``a – b``; Range nhiều Đoạn ghi từng Đoạn."""
    if rng.get("segments"):
        return "; ".join(f"{a} – {b}" for a, b in rng["segments"])
    return f"{rng['first']} – {rng['last']}"


def counts_frame():
    """Một dòng mỗi Range có snapshot, cộng dòng tổng."""
    rows = []
    for member, snap in SNAPSHOTS.items():
        c = snap["counts"]
        rows.append({"Thành viên": name(member), "Range": range_text(snap["range"]),
                     "ID được giao": c["assigned"], "Publication tìm thấy": c["discovered"],
                     "Publication hoàn chỉnh": c["complete"], "Version kỳ vọng": c["expected_versions"],
                     "Version có TeX": c["success"], "Version non-TeX": c["non_tex"],
                     "Version không tải được": c["unavailable"] + c["download_error"] + c["not_attempted"],
                     "References thành công": c["references_success"]})
    df = pd.DataFrame(rows)
    if len(df) > 1:
        total = df.drop(columns=["Thành viên", "Range"]).sum()
        df = pd.concat([df, pd.DataFrame([{"Thành viên": "Tổng", "Range": "", **total}])], ignore_index=True)
    return df


def total(key):
    return sum(s["counts"][key] for s in SNAPSHOTS.values())


def snapshot_scope():
    members = ", ".join(name(m) for m in SNAPSHOTS)
    times = ", ".join(f"{name(m)}: {s['snapshot_at'][:10]}" for m, s in SNAPSHOTS.items())
    return (f"Số liệu lấy từ **{len(SNAPSHOTS)}/{N_RANGES} Range** đã có snapshot ({members}). "
            f"Ngày snapshot (UTC): {times}.")


def revision_lookups(snap):
    """Số request tra ngày Version: Version 2..k-1 mỗi Publication (Version k có sẵn trong lô)."""
    return sum(max(row["versions"] - 2, 0) * row["publications"] for row in snap["versions_distribution"])


# ---- Tầng tự báo cáo: data/m1/members/<github-username>.json ----

MEMBERS = {p.stem: _load(p) for p in sorted((DATA / "members").glob("*.json")) if not p.stem.startswith("_")}

VERIFICATION = {
    "validated": "Đã kiểm bằng report_m1/validator của nhóm",
    "self_checked": "Thành viên tự kiểm manifest/checksum và schema",
    "file_check": "Chỉ kiểm trạng thái và sự hiện diện file",
    "download_state": "Chỉ biết archive tải thành công",
    "none": "Chưa có số liệu",
}


def all_members():
    """Pipeline ban đầu của các thành viên, theo thứ tự Range."""
    return sorted(MEMBERS.values(), key=lambda m: m["range"]["first"])
