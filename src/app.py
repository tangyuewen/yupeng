# -*- coding: utf-8 -*-
"""
Flask 界面：结果页(两张趋势观测表) + 配置页。
启动：python src/app.py  →  http://127.0.0.1:5000
"""
from __future__ import annotations
import os
import sys

# 确保项目根目录在 sys.path，兼容 `python src/app.py` 与 `python -m src.app`
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from flask import Flask, render_template, request, redirect, url_for

from src import pipeline, snapshot

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))

GROUP_TITLE = {
    "broad": "宽基/风格趋势模型",
    "sector": "板块轮动模型",
}


def _dev_bg(dev: float) -> str:
    if dev > 0:
        if dev >= 0.05:
            return "#e59a9a"
        if dev >= 0.01:
            return "#eeadad"
        if dev >= 0.003:
            return "#f3c6c6"
        return "#f8dede"
    if dev < 0:
        if dev <= -0.05:
            return "#7ebf6d"
        if dev <= -0.03:
            return "#93c47d"
        if dev <= -0.01:
            return "#b6d9a6"
        return "#d9ead3"
    return "#f1f1f1"


def _pct(x: float | None, signed: bool = True) -> str:
    if x is None:
        return "-"
    return (f"{x*100:+.2f}%" if signed else f"{x*100:.2f}%")


def _decorate(groups: dict, snap_date: str) -> dict:
    out = {}
    for grp, rows in groups.items():
        decorated = []
        for r in rows:
            if r.get("error"):
                r["dev_bg"] = "#ffffff"
                r["row_bg"] = None
                r["trend"] = "—"
                r["day_pct"] = "-"
                r["dev_pct"] = "-"
                r["interval_pct"] = "-"
                r["rank_chg_disp"] = "-"
                decorated.append(r)
                continue
            dev = r.get("dev", 0.0)
            is_cross = (r.get("cross_date") == snap_date)
            r["dev_bg"] = _dev_bg(dev)
            r["row_bg"] = "#fdf6cf" if is_cross else None
            arrow = "↑" if r.get("direction") == "up" else "↓"
            r["trend"] = arrow + ("↔" if is_cross else "")
            r["day_pct"] = _pct(r.get("day_chg"))
            r["dev_pct"] = _pct(dev)
            r["interval_pct"] = _pct(r.get("interval_ret"))
            rc = r.get("rank_chg", 0)
            r["rank_chg_disp"] = "0" if rc == 0 else (f"↑{rc}" if rc > 0 else f"↓{-rc}")
            decorated.append(r)
        out[grp] = decorated
    return out


@app.route("/")
def index():
    dates = snapshot.available_dates()
    date = request.args.get("date") or (dates[0] if dates else None)
    groups = {}
    if date:
        wl = pipeline._load_watchlist()
        for grp in wl:
            rows = snapshot.load(date, grp)
            if rows:
                groups[grp] = rows
        groups = _decorate(groups, date)
    return render_template(
        "result.html",
        date=date, groups=groups, dates=dates,
        group_title=GROUP_TITLE,
    )


@app.route("/run")
def run():
    mode = request.args.get("mode", "refresh")
    today_mode = request.args.get("today", "0") == "1"
    res = pipeline.run(today_mode=today_mode)
    return redirect(url_for("index", date=res["snap_date"]))


@app.route("/config")
def config():
    wl = pipeline._load_watchlist()
    return render_template("config.html", watchlist=wl, group_title=GROUP_TITLE)


@app.route("/api/guess", methods=["POST"])
def guess():
    """简单数据源猜测：指数代码→A股/中证；^ 开头→雅虎；其余→手动。"""
    code = (request.form.get("code") or "").strip()
    if code.startswith("^") or code in ("QQQ", "SPY"):
        asset, note = "global_index", "雅虎源（境外，需本地代理）"
    elif code.isdigit():
        asset, note = "cn_index", "A股/中证指数（akshare）"
    else:
        asset, note = "us_etf", "美股ETF（akshare/yfinance）"
    return {"asset": asset, "note": note}


def main():
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
