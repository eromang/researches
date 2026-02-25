#!/usr/bin/env python3
"""
live_dashboard_watcher.py

A lightweight companion script that watches a benchmark JSONL file and regenerates a
simple HTML dashboard periodically (near real-time), without touching the runner.

What it does
- Detects the latest run_id via results/LATEST_RUN_ID.txt (or uses --run-id)
- Reads the JSONL incrementally (robust to partial lines)
- Computes quick progress + basic aggregates (by model/temp/rep/condition, ok/error, latency)
- Writes a live HTML dashboard: results/<run_id>_live_dashboard.html
- Optional auto-open in browser, optional auto-refresh in the page

Usage
  python3 live_dashboard_watcher.py --outdir results
  python3 live_dashboard_watcher.py --outdir results --poll 10 --tail 400 --open

Tip
- Keep this running in a second terminal while the benchmark runs.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# -----------------------------
# Helpers
# -----------------------------

def safe_read_text(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except Exception:
        return None


def find_latest_run_id(outdir: Path) -> Optional[str]:
    txt = safe_read_text(outdir / "LATEST_RUN_ID.txt")
    if not txt:
        return None
    # Some shells accidentally append a '%' character in pasted output; guard it.
    return txt.replace("%", "").strip() or None


def parse_condition_from_prompt_id(prompt_id: str) -> str:
    # Expected: S01_China_Suspected, S12_Neutral, etc.
    if "_" not in prompt_id:
        return "UNKNOWN"
    return prompt_id.split("_", 1)[1]


def human_ms(ms: Optional[int]) -> str:
    if ms is None:
        return "-"
    if ms < 1000:
        return f"{ms} ms"
    s = ms / 1000.0
    if s < 60:
        return f"{s:.1f} s"
    m = int(s // 60)
    r = s - m * 60
    return f"{m}m {r:.0f}s"


def clamp_int(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


# -----------------------------
# Robust JSONL reader
# -----------------------------

@dataclass
class JSONLState:
    offset: int = 0  # byte offset
    seen: int = 0    # records processed


def read_jsonl_incremental(path: Path, state: JSONLState, max_records: int = 50000) -> Tuple[List[Dict[str, Any]], JSONLState]:
    """
    Incrementally read newly appended JSONL records from `path` starting at `state.offset`.
    Robust to partial final line and occasional JSON decode errors.
    """
    new_records: List[Dict[str, Any]] = []

    try:
        with path.open("rb") as f:
            f.seek(state.offset)
            chunk = f.read()
            if not chunk:
                return new_records, state

            text = chunk.decode("utf-8", errors="replace")
            lines = text.splitlines()

            # If the file doesn't end with newline, last line might be partial.
            # We'll only parse complete lines; keep the partial line for next round.
            ends_with_newline = text.endswith("\n") or text.endswith("\r\n")
            complete_lines = lines if ends_with_newline else lines[:-1]

            # Update offset: move forward by the bytes of the complete part.
            complete_text = "\n".join(complete_lines) + ("\n" if complete_lines else "")
            state.offset += len(complete_text.encode("utf-8", errors="replace"))

            for line in complete_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        new_records.append(obj)
                        state.seen += 1
                        if state.seen >= max_records:
                            break
                except json.JSONDecodeError:
                    # Ignore malformed line; next finalize pass can still handle full file.
                    continue

    except FileNotFoundError:
        return new_records, state

    return new_records, state


# -----------------------------
# Dashboard builder
# -----------------------------

def compute_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes quick aggregates from all records (not just tail).
    """
    totals = {
        "total": 0,
        "ok": 0,
        "error": 0,
    }
    by_model = defaultdict(lambda: {"total": 0, "ok": 0, "error": 0, "lat_ms_sum": 0, "lat_ms_n": 0})
    by_cond = defaultdict(lambda: {"total": 0, "ok": 0, "error": 0})
    by_temp = defaultdict(lambda: {"total": 0, "ok": 0, "error": 0})
    by_rep = defaultdict(lambda: {"total": 0, "ok": 0, "error": 0})

    for r in records:
        totals["total"] += 1
        ok = bool(r.get("ok", False))
        if ok:
            totals["ok"] += 1
        else:
            totals["error"] += 1

        model = str(r.get("model", "UNKNOWN"))
        temp = r.get("temperature", "UNKNOWN")
        rep = r.get("rep", "UNKNOWN")
        prompt_id = str(r.get("prompt_id", "UNKNOWN"))
        cond = str(r.get("condition") or parse_condition_from_prompt_id(prompt_id))

        bm = by_model[model]
        bm["total"] += 1
        bm["ok"] += 1 if ok else 0
        bm["error"] += 0 if ok else 1
        lat = r.get("latency_ms")
        if isinstance(lat, int):
            bm["lat_ms_sum"] += lat
            bm["lat_ms_n"] += 1

        bc = by_cond[cond]
        bc["total"] += 1
        bc["ok"] += 1 if ok else 0
        bc["error"] += 0 if ok else 1

        bt = by_temp[str(temp)]
        bt["total"] += 1
        bt["ok"] += 1 if ok else 0
        bt["error"] += 0 if ok else 1

        br = by_rep[str(rep)]
        br["total"] += 1
        br["ok"] += 1 if ok else 0
        br["error"] += 0 if ok else 1

    # Add avg latency per model
    for model, bm in by_model.items():
        bm["avg_latency_ms"] = int(bm["lat_ms_sum"] / bm["lat_ms_n"]) if bm["lat_ms_n"] else None

    return {
        "totals": totals,
        "by_model": dict(by_model),
        "by_condition": dict(by_cond),
        "by_temp": dict(by_temp),
        "by_rep": dict(by_rep),
    }


def render_table_kv(title: str, rows: List[Tuple[str, str]]) -> str:
    tr = "\n".join(
        f"<tr><td class='k'>{html.escape(k)}</td><td class='v'>{html.escape(v)}</td></tr>"
        for k, v in rows
    )
    return f"""
    <div class="card">
      <div class="card-title">{html.escape(title)}</div>
      <table class="kv">{tr}</table>
    </div>
    """


def render_agg_table(title: str, data: Dict[str, Dict[str, Any]], key_label: str) -> str:
    # data: key -> metrics
    keys = sorted(data.keys())
    trs = []
    for k in keys:
        d = data[k]
        ok = d.get("ok", 0)
        err = d.get("error", 0)
        total = d.get("total", 0)
        ok_rate = (ok / total * 100.0) if total else 0.0
        extra = ""
        if "avg_latency_ms" in d:
            extra = f"<td>{html.escape(human_ms(d.get('avg_latency_ms')))}</td>"
        trs.append(
            f"<tr>"
            f"<td>{html.escape(str(k))}</td>"
            f"<td>{total}</td>"
            f"<td>{ok}</td>"
            f"<td>{err}</td>"
            f"<td>{ok_rate:.1f}%</td>"
            f"{extra}"
            f"</tr>"
        )

    latency_header = "<th>Avg latency</th>" if any("avg_latency_ms" in v for v in data.values()) else ""
    latency_col = ""  # handled per row

    return f"""
    <div class="card">
      <div class="card-title">{html.escape(title)}</div>
      <table class="agg">
        <thead>
          <tr>
            <th>{html.escape(key_label)}</th>
            <th>Total</th>
            <th>OK</th>
            <th>Error</th>
            <th>OK rate</th>
            {latency_header}
          </tr>
        </thead>
        <tbody>
          {''.join(trs)}
        </tbody>
      </table>
    </div>
    """


def render_tail_table(tail: List[Dict[str, Any]]) -> str:
    trs = []
    for r in tail:
        model = str(r.get("model", ""))
        temp = str(r.get("temperature", ""))
        rep = str(r.get("rep", ""))
        prompt_id = str(r.get("prompt_id", ""))
        cond = str(r.get("condition") or parse_condition_from_prompt_id(prompt_id))
        ok = bool(r.get("ok", False))
        lat = r.get("latency_ms")
        out_len = r.get("output_len_chars") or r.get("output_chars") or r.get("output_length") or ""
        reason = str(r.get("flag_reason", "") or r.get("error", "") or "")

        trs.append(
            "<tr>"
            f"<td>{html.escape(model)}</td>"
            f"<td>{html.escape(temp)}</td>"
            f"<td>{html.escape(rep)}</td>"
            f"<td>{html.escape(cond)}</td>"
            f"<td class='mono'>{html.escape(prompt_id)}</td>"
            f"<td class='{ 'ok' if ok else 'err' }'>{'OK' if ok else 'ERR'}</td>"
            f"<td>{html.escape(human_ms(lat) if isinstance(lat, int) else '-')}</td>"
            f"<td>{html.escape(str(out_len))}</td>"
            f"<td class='mono'>{html.escape(reason[:120])}</td>"
            "</tr>"
        )

    return f"""
    <div class="card">
      <div class="card-title">Latest records (tail)</div>
      <table class="tail">
        <thead>
          <tr>
            <th>Model</th><th>T</th><th>Rep</th><th>Condition</th>
            <th>Prompt ID</th><th>Status</th><th>Latency</th><th>Out chars</th><th>Note</th>
          </tr>
        </thead>
        <tbody>
          {''.join(trs)}
        </tbody>
      </table>
      <div class="hint">Tip: this is a lightweight live view. Use your runner’s finalized dashboard for deep qualitative review.</div>
    </div>
    """


def build_html(run_id: str, jsonl_path: Path, stats: Dict[str, Any], tail: List[Dict[str, Any]], refresh_sec: int) -> str:
    totals = stats["totals"]
    total = totals["total"]
    ok = totals["ok"]
    err = totals["error"]
    ok_rate = (ok / total * 100.0) if total else 0.0

    meta_refresh = f"<meta http-equiv='refresh' content='{refresh_sec}'>" if refresh_sec > 0 else ""

    head = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  {meta_refresh}
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Live Dashboard – {html.escape(run_id)}</title>
  <style>
    body {{ font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 24px; background: #0b0f14; color: #e6edf3; }}
    .top {{ display:flex; gap:16px; flex-wrap: wrap; align-items: stretch; }}
    .card {{ background: #111826; border: 1px solid #223045; border-radius: 12px; padding: 14px 14px 10px; box-shadow: 0 2px 12px rgba(0,0,0,.25); }}
    .card-title {{ font-weight: 650; margin-bottom: 10px; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
    .kv {{ border-collapse: collapse; width: 100%; }}
    .kv td {{ padding: 6px 8px; border-top: 1px solid #1e2a3d; vertical-align: top; }}
    .kv td.k {{ color: #9fb3c8; width: 180px; }}
    .kv td.v {{ color: #e6edf3; }}
    table.agg, table.tail {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    table.agg th, table.agg td, table.tail th, table.tail td {{ padding: 7px 8px; border-top: 1px solid #1e2a3d; text-align: left; }}
    table.agg th, table.tail th {{ color: #c7d7ea; font-weight: 650; }}
    .ok {{ color: #39d98a; font-weight: 700; }}
    .err {{ color: #ff5c7a; font-weight: 700; }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 14px; margin-top: 14px; }}
    .hint {{ margin-top: 8px; color: #9fb3c8; font-size: 12px; }}
    .small {{ color: #9fb3c8; font-size: 12px; }}
    a {{ color: #7aa2ff; }}
  </style>
</head>
<body>
  <div class="mono small">Live view for: <b>{html.escape(run_id)}</b> — source: {html.escape(str(jsonl_path))}</div>
  <h1 style="margin: 10px 0 18px;">EU LLM Benchmark – Live Dashboard</h1>
"""

    top_cards = f"""
  <div class="top">
    {render_table_kv("Progress", [
        ("Records (total)", str(total)),
        ("OK", str(ok)),
        ("Error", str(err)),
        ("OK rate", f"{ok_rate:.1f}%"),
        ("Last updated", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
    ])}
  </div>
"""

    grids = f"""
  <div class="grid">
    {render_agg_table("By model", stats["by_model"], "Model")}
    {render_agg_table("By condition", stats["by_condition"], "Condition")}
    {render_agg_table("By temperature", stats["by_temp"], "T")}
    {render_agg_table("By repetition", stats["by_rep"], "Rep")}
  </div>
"""

    tail_html = render_tail_table(tail)

    footer = """
</body>
</html>
"""

    return head + top_cards + grids + tail_html + footer


# -----------------------------
# Main loop
# -----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Watch a benchmark JSONL and regenerate a lightweight live HTML dashboard.")
    ap.add_argument("--outdir", default="results", help="Results directory (default: results)")
    ap.add_argument("--run-id", default=None, help="Run ID to watch (default: read outdir/LATEST_RUN_ID.txt)")
    ap.add_argument("--poll", type=int, default=10, help="Polling interval in seconds (default: 10)")
    ap.add_argument("--tail", type=int, default=200, help="Tail size (number of latest records to show) (default: 200)")
    ap.add_argument("--refresh", type=int, default=10, help="HTML meta refresh seconds (0 disables) (default: 10)")
    ap.add_argument("--open", action="store_true", help="Auto-open dashboard in browser (macOS: open / Linux: xdg-open / Win: start)")
    ap.add_argument("--once", action="store_true", help="Generate once and exit (no watch loop)")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    run_id = args.run_id or find_latest_run_id(outdir)
    if not run_id:
        print(f"[ERR] Could not determine run_id. Provide --run-id or ensure {outdir/'LATEST_RUN_ID.txt'} exists.", file=sys.stderr)
        return 2

    jsonl_path = outdir / f"{run_id}.jsonl"
    if not jsonl_path.exists():
        print(f"[ERR] JSONL not found: {jsonl_path}", file=sys.stderr)
        return 2

    html_path = outdir / f"{run_id}_live_dashboard.html"
    poll = clamp_int(args.poll, 1, 3600)
    tail_n = clamp_int(args.tail, 20, 5000)
    refresh = clamp_int(args.refresh, 0, 3600)

    state = JSONLState(offset=0, seen=0)
    all_records: List[Dict[str, Any]] = []

    def write_dashboard() -> None:
        stats = compute_stats(all_records)
        tail = all_records[-tail_n:] if tail_n > 0 else []
        page = build_html(run_id=run_id, jsonl_path=jsonl_path, stats=stats, tail=tail, refresh_sec=refresh)
        html_path.write_text(page, encoding="utf-8")
        print(f"[OK] Wrote: {html_path} (records={stats['totals']['total']})")

    # Initial load (read whole file once via incremental reader loop)
    # Read until no more new records available at start.
    while True:
        new, state = read_jsonl_incremental(jsonl_path, state)
        if not new:
            break
        all_records.extend(new)

    write_dashboard()

    if args.open:
        cmd = None
        if sys.platform.startswith("darwin"):
            cmd = ["open", str(html_path)]
        elif os.name == "nt":
            cmd = ["cmd", "/c", "start", "", str(html_path)]
        else:
            cmd = ["xdg-open", str(html_path)]
        try:
            import subprocess
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    if args.once:
        return 0

    last_size = jsonl_path.stat().st_size
    last_mtime = jsonl_path.stat().st_mtime

    print(f"[WATCH] run_id={run_id} poll={poll}s tail={tail_n} refresh={refresh}s")
    print(f"[WATCH] reading {jsonl_path}")

    while True:
        try:
            st = jsonl_path.stat()
            changed = (st.st_size != last_size) or (st.st_mtime != last_mtime)
            if changed:
                last_size, last_mtime = st.st_size, st.st_mtime
                new, state = read_jsonl_incremental(jsonl_path, state)
                if new:
                    all_records.extend(new)
                write_dashboard()
            time.sleep(poll)
        except KeyboardInterrupt:
            print("\n[STOP] watcher stopped.")
            return 0
        except FileNotFoundError:
            print("[WARN] JSONL disappeared; waiting…", file=sys.stderr)
            time.sleep(poll)
        except Exception as e:
            print(f"[WARN] watcher error: {e}", file=sys.stderr)
            time.sleep(poll)


if __name__ == "__main__":
    raise SystemExit(main())