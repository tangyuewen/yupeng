# -*- coding: utf-8 -*-
"""
指标计算：基于鱼盆趋势模型（均线趋势观测）。
所有函数均为纯计算，不触碰网络。

核心指标：
  - MA20      : 收盘价 20 日简单移动平均（临界值基准）
  - 偏离率    : (最新收盘 - MA20) / MA20，排序依据
  - 穿越日期  : 最近一次收盘价上穿/下穿 MA20 的日期（状态转变时间）
  - 区间涨幅  : 最新收盘 / 穿越当日收盘 - 1
  - 当日涨幅  : 最新收盘 / 前一日收盘 - 1
"""
from __future__ import annotations
import numpy as np
import pandas as pd

MA_WINDOW = 20


def compute_metrics(dates, closes, window: int = MA_WINDOW) -> dict:
    """
    输入：dates(list[str])、closes(list[float])，按时间升序。
    返回单标的指标字典。
    """
    s = pd.Series(closes, dtype="float64").reset_index(drop=True)
    if len(s) < 2:
        raise ValueError("历史数据不足，无法计算")
    ma = s.rolling(window).mean()
    last_close = float(s.iloc[-1])
    prev_close = float(s.iloc[-2])
    last_ma = float(ma.iloc[-1])

    dev = (last_close - last_ma) / last_ma if last_ma else 0.0
    day_chg = (last_close / prev_close - 1) if prev_close else 0.0

    # 找最近一次穿越（收盘相对 MA20 的符号翻转）
    diff = s - ma
    sign = np.sign(diff)
    cross = sign.diff().fillna(0.0)
    idxs = cross[cross != 0].index.tolist()
    if idxs:
        last = int(idxs[-1])
        direction = "up" if cross.iloc[last] > 0 else "down"
        cross_date = str(dates[last])
        cross_close = float(s.iloc[last])
    else:
        # 全程未穿越：取首个交易日，方向按当前位置
        direction = "up" if sign.iloc[-1] > 0 else "down"
        cross_date = str(dates[0])
        cross_close = float(s.iloc[0])

    interval_ret = (last_close / cross_close - 1) if cross_close else 0.0

    return {
        "ma20": last_ma,
        "dev": dev,
        "cross_date": cross_date,        # 状态转变时间
        "direction": direction,           # up=原YES(偏强) / down=原NO(偏弱)
        "interval_ret": interval_ret,     # 区间涨幅
        "day_chg": day_chg,               # 当日涨幅
        "last_close": last_close,
    }


def rank_rows(rows: list[dict]) -> list[dict]:
    """
    按偏离率绝对值降序排名？—— 鱼盆模型按偏离率(可正可负)从高到低排序，
    即偏离率越大越靠前（最强）。返回带 `rank` 字段的行。
    """
    ranked = sorted(rows, key=lambda r: r["dev"], reverse=True)
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i
    return ranked


def rank_change(current: list[dict], previous: list[dict] | None) -> None:
    """
    计算排序变化：current/previous 均为已带 rank 的行。
    本日名次 - 上日名次 为正表示名次上升(↑)。结果写入 current 行的 `rank_chg`。
    若无上一日快照，rank_chg = 0。
    """
    if not previous:
        for r in current:
            r["rank_chg"] = 0
        return
    prev_rank = {r["code"]: r["rank"] for r in previous}
    for r in current:
        p = prev_rank.get(r["code"])
        # 名次上升(↑)为正：上一日名次 - 当日名次
        r["rank_chg"] = (p - r["rank"]) if p is not None else 0
