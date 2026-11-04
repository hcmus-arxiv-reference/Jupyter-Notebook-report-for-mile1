"""Đọc số liệu tổng hợp của Milestone 1 cho các trang báo cáo.

Chỉ đọc file trong ``data/m1/``; không gọi mạng, không đọc corpus thô.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.io as pio
from IPython.display import HTML, Markdown, display

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
DATA = ROOT / "data" / "m1"

SNAPSHOTS = {p.stem: json.loads(p.read_text(encoding="utf-8"))
             for p in sorted((DATA / "snapshots").glob("*.json"))}
if not SNAPSHOTS:
    raise FileNotFoundError(f"Không có snapshot nào trong {DATA / 'snapshots'}")
for _member, _snap in SNAPSHOTS.items():
    if _snap.get("format") != 1:
        raise ValueError(f"{_member}: chỉ hỗ trợ snapshot format 1")

_BENCH = DATA / "benchmark" / "benchmark_total.json"
BENCHMARK = json.loads(_BENCH.read_text(encoding="utf-8")) if _BENCH.exists() else None
_SAMPLES = DATA / "benchmark" / "benchmark_samples_all.csv"
SAMPLES = pd.read_csv(_SAMPLES) if _SAMPLES.exists() else None

N_RANGES = 5  # số Range được giao cho nhóm


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


def md(text):
    display(Markdown(text))


def show(fig):
    """Hiển thị hình Plotly tương tác trong trang HTML."""
    fig.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=50, b=40))
    display(HTML(pio.to_html(fig, include_plotlyjs="cdn", full_html=False)))


def table(df, **formats):
    display(df.style.format(formats, na_rep="—").hide(axis="index"))


def counts_frame():
    """Một dòng mỗi thành viên có snapshot, cộng dòng tổng."""
    rows = []
    for member, snap in SNAPSHOTS.items():
        c = snap["counts"]
        rows.append({"Thành viên": member, "Range": f"{snap['range']['first']} – {snap['range']['last']}",
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
    members = ", ".join(SNAPSHOTS)
    times = ", ".join(f"{m}: {s['snapshot_at'][:10]}" for m, s in SNAPSHOTS.items())
    return (f"Số liệu lấy từ **{len(SNAPSHOTS)}/{N_RANGES} Range** đã có snapshot ({members}). "
            f"Ngày snapshot (UTC): {times}.")
