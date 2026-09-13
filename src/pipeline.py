# -*- coding: utf-8 -*-
"""
编排层：读配置 → 并发取数 → 计算 → 排序 → 存快照。
"""
from __future__ import annotations
import copy
import datetime as _dt
import json
import os
import shutil

from . import compute, datasource, snapshot

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _today() -> str:
    return _dt.datetime.today().strftime("%Y-%m-%d")


def _load_watchlist() -> dict:
    path = os.path.join(_BASE, "config", "watchlist.json")
    example = os.path.join(_BASE, "config", "watchlist.example.json")
    if not os.path.exists(path) and os.path.exists(example):
        shutil.copyfile(example, path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_prev_snapshot(grp: str, date_str: str) -> list[dict] | None:
    """加载早于 date_str 的最近一个同组快照，用于排序变化对比。"""
    for d in snapshot.latest_dates(grp):
        if d < date_str:
            return snapshot.load(d, grp)
    return None


def run(snap_date: str | None = None, today_mode: bool = False, full: bool = False) -> dict:
    """
    执行一次全量计算并落盘。
    snap_date : 指定快照日期（默认为今天）；today_mode 暂不跨源对齐，直接取各源最新。
    返回 {snap_date, groups:{grp: rows}}。
    """
    wl = _load_watchlist()
    the_date = snap_date or _today()
    result: dict = {"snap_date": the_date, "groups": {}}

    for grp, items in wl.items():
        entries = copy.deepcopy(items)
        data = datasource.fetch_all(entries, max_workers=8)

        rows: list[dict] = []
        for e in entries:
            code = e["code"]
            d = data.get(code, {})
            row = {
                "rank": 0, "code": code, "name": e["name"],
                "asset": e.get("asset", ""), "error": d.get("error"),
            }
            if d.get("error") or not d.get("dates"):
                rows.append(row)
                continue
            try:
                m = compute.compute_metrics(d["dates"], d["closes"])
            except Exception as ex:  # noqa: BLE001
                row["error"] = f"计算失败:{ex}"
                rows.append(row)
                continue
            row.update({
                "day_chg": m["day_chg"],
                "last_close": m["last_close"],
                "ma20": m["ma20"],
                "dev": m["dev"],
                "cross_date": m["cross_date"],
                "direction": m["direction"],
                "interval_ret": m["interval_ret"],
            })
            rows.append(row)

        ok = [r for r in rows if not r.get("error")]
        bad = [r for r in rows if r.get("error")]
        ok = compute.rank_rows(ok)
        compute.rank_change(ok, _load_prev_snapshot(grp, the_date))

        final_rows = ok + bad
        snapshot.save(the_date, grp, final_rows)
        result["groups"][grp] = final_rows

    return result
