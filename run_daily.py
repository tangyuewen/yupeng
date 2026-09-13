# -*- coding: utf-8 -*-
"""
定时跑数脚本：挂到系统定时任务（任务计划程序 / cron），每个交易日执行一次。
用法：python run_daily.py
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src import pipeline


def main():
    print("[moving-average-monitor] 开始计算...")
    res = pipeline.run(today_mode=False)
    print("快照日期:", res["snap_date"])
    for grp, rows in res["groups"].items():
        ok = sum(1 for r in rows if not r.get("error"))
        err = len(rows) - ok
        print(f"  - {grp}: 成功 {ok} / 失败 {err}")
    print("完成。")


if __name__ == "__main__":
    main()
