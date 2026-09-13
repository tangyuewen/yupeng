# -*- coding: utf-8 -*-
"""
快照持久化（SQLite）。
只存每日计算结果（几十行/天），用于历史回看与排序变化，底层行情不落盘。
"""
from __future__ import annotations
import datetime as _dt
import json
import os
import sqlite3

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BASE, "data", "snapshots.db")


def _con():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """CREATE TABLE IF NOT EXISTS snapshots(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snap_date TEXT,
            grp TEXT,
            payload TEXT,
            created TEXT
        )"""
    )
    return con


def save(snap_date: str, grp: str, rows: list[dict]) -> None:
    con = _con()
    con.execute("DELETE FROM snapshots WHERE snap_date=? AND grp=?", (snap_date, grp))
    con.execute(
        "INSERT INTO snapshots(snap_date,grp,payload,created) VALUES(?,?,?,?)",
        (snap_date, grp, json.dumps(rows, ensure_ascii=False), _dt.datetime.now().isoformat()),
    )
    con.commit()
    con.close()


def load(snap_date: str, grp: str) -> list[dict] | None:
    con = _con()
    r = con.execute(
        "SELECT payload FROM snapshots WHERE snap_date=? AND grp=? ORDER BY id DESC LIMIT 1",
        (snap_date, grp),
    ).fetchone()
    con.close()
    return json.loads(r[0]) if r else None


def latest_dates(grp: str) -> list[str]:
    """该组所有有快照的日期（降序）。"""
    con = _con()
    rows = con.execute(
        "SELECT DISTINCT snap_date FROM snapshots WHERE grp=? ORDER BY snap_date DESC", (grp,)
    ).fetchall()
    con.close()
    return [x[0] for x in rows]


def available_dates() -> list[str]:
    con = _con()
    rows = con.execute(
        "SELECT DISTINCT snap_date FROM snapshots ORDER BY snap_date DESC"
    ).fetchall()
    con.close()
    return [x[0] for x in rows]
