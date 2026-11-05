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


# ---- Tầng tự báo cáo: data/m1/members/<github-username>.json ----

MEMBERS = {p.stem: json.loads(p.read_text(encoding="utf-8"))
           for p in sorted((DATA / "members").glob("*.json")) if not p.stem.startswith("_")}

VERIFICATION = {
    "validated": "Đã kiểm bằng report_m1/validator của nhóm",
    "self_checked": "Thành viên tự kiểm manifest/checksum và schema",
    "file_check": "Chỉ kiểm trạng thái và sự hiện diện file",
    "download_state": "Chỉ biết archive tải thành công",
    "none": "Chưa có số liệu",
}
SNAPSHOT_NAMES = {"bao": ("NTBao-coder", "Bảo")}


def snapshot_as_member(key, snap):
    """Đưa một snapshot đã kiểm chứng về cùng dạng với members/*.json."""
    c, st, r = snap["counts"], snap["storage"], snap["references"]
    github, name = SNAPSHOT_NAMES.get(key, (key, key))
    return {"member": github, "name": name, "range": snap["range"], "verification": "validated",
            "publications": {"assigned": c["assigned"], "with_metadata": c["discovered"], "complete": c["complete"]},
            "versions": {"expected": c["expected_versions"], "tex": c["success"], "non_tex": c["non_tex"],
                         "unavailable": c["unavailable"], "other_error": c["download_error"] + c["not_attempted"],
                         "archive_downloaded": None},
            "references": {"s2_success": c["references_success"], "empty": r["successfully_empty_publications"],
                           "raw_records": r["all_records"], "with_arxiv_id": r["with_arxiv_before_dedup"]},
            "size": {"before_bytes_total": st.get("before_extraction_bytes"),
                     "after_bytes_total": st["retained_tex_bib_bytes"],
                     "after_mean_bytes_complete": st["complete_publication_retained_bytes"]["mean"], "rounded": False},
            "performance": {"environment": None, "wall_seconds": None, "peak_rss_mib": None, "avg_rss_mib": None,
                            "final_disk_mib": None, "note": snap["benchmark"]["testbed"]},
            "pipeline": {"discovery": "Lô 50 ID, hỏi lại từng ID khi lô lỗi",
                         "source": "Tuần tự, 1 kết nối arXiv, cách ≥ 3,1 giây",
                         "references": "1 luồng S2 song song với source, 1,1 giây/request (có key)",
                         "retry": "Retry-After hoặc bảng backoff có jitter, số lần thử có giới hạn",
                         "resume": "Theo manifest và checksum từng Version",
                         "storage": "Layout src/crawl/ + manifest JSONL; Parquet"}}


def all_members():
    """Tầng kiểm chứng (snapshot) trước, rồi tầng tự báo cáo; một thành viên chỉ xuất hiện một lần."""
    rows = {m["member"]: m for m in (snapshot_as_member(k, s) for k, s in SNAPSHOTS.items())}
    for key, data in MEMBERS.items():
        rows.setdefault(key, data)
    return list(rows.values())
