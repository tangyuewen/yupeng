# -*- coding: utf-8 -*-
"""
数据源路由层。
优先使用 akshare（覆盖 A股/中证/港股/美股/行业/贵金属），境外指数用 yfinance 兜底。
返回统一结构：{dates:[...], closes:[...], error:None} 或 {error:"..."}。

说明：本模块依赖外部网络与第三方接口，接口名随 akshare 版本可能变动。
若某个资产取数失败，会在 error 字段记录原因，pipeline 会跳过并标灰，不影响其余标的。
"""
from __future__ import annotations
import datetime as _dt
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

try:
    import akshare as ak
except Exception:  # pragma: no cover
    ak = None

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None


def _today() -> str:
    return _dt.datetime.today().strftime("%Y%m%d")


def _start() -> str:
    return (_dt.datetime.today() - _dt.timedelta(days=420)).strftime("%Y%m%d")


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """把不同接口的列名统一成 date / close。"""
    if df is None or len(df) == 0:
        raise ValueError("返回空数据")
    date_col = next((c for c in df.columns if "日期" in str(c) or str(c).lower() == "date"), None)
    close_col = next((c for c in df.columns if "收盘" in str(c) or str(c).lower() == "close"), None)
    if date_col is None or close_col is None:
        raise ValueError(f"无法识别列名: {list(df.columns)}")
    out = df[[date_col, close_col]].copy()
    out.columns = ["date", "close"]
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna()
    return out


def _yf(symbol: str) -> pd.DataFrame:
    if yf is None:
        raise RuntimeError("未安装 yfinance")
    t = yf.Ticker(symbol)
    df = t.history(period="1y", auto_adjust=False)
    if df is None or len(df) == 0:
        raise ValueError("yfinance 无数据")
    df = df.reset_index()[["Date", "Close"]]
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    df.columns = ["date", "close"]
    return df


def _fetch_by_asset(entry: dict) -> pd.DataFrame:
    asset = entry.get("asset", "cn_index")
    code = str(entry.get("code", ""))
    name = entry.get("name", "")
    start, end = _start(), _today()

    if ak is None:
        raise RuntimeError("未安装 akshare")

    if asset in ("cn_index", "cn_csindex"):
        df = ak.index_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end)
        return _normalize(df)

    if asset == "hk_index":
        df = ak.stock_hk_index_daily(symbol=code)
        return _normalize(df)

    if asset == "us_etf":
        try:
            df = ak.stock_us_daily(symbol=code, adjust="")
            return _normalize(df)
        except Exception:
            return _yf(entry.get("yahoo", code))

    if asset == "global_index":
        return _yf(entry.get("yahoo", code))

    if asset == "metal_spot":
        df = ak.futures_foreign_hist(symbol=entry.get("metal", "XAU"),
                                     start_date=start, end_date=end)
        return _normalize(df)

    if asset == "ths_industry":
        df = ak.stock_board_industry_index_ths(symbol=name)
        return _normalize(df)

    raise ValueError(f"未知资产类型: {asset}")


def fetch_entry(entry: dict) -> dict:
    """取单个标的日线，返回标准化结构。"""
    try:
        df = _fetch_by_asset(entry)
        return {
            "dates": df["date"].tolist(),
            "closes": df["close"].astype(float).tolist(),
            "error": None,
        }
    except Exception as e:  # noqa: BLE001
        return {"dates": [], "closes": [], "error": f"{type(e).__name__}: {e}"[:200]}


def fetch_all(entries: list[dict], max_workers: int = 8) -> dict[str, dict]:
    """并发取数，返回 {code: result}。"""
    out: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(fetch_entry, e): e for e in entries}
        for fut, e in futures.items():
            out[e["code"]] = fut.result()
    return out
