# 均线趋势观测 · 鱼盆趋势模型

每个交易日生成两张趋势观测表（**宽基/风格趋势模型** + **板块轮动模型**），按 **20 日均线偏离率** 从高到低排序，
观察各标的相对其 20 日均线的强弱与趋势状态切换。界面与配色参照同花顺「趋势模型」风格。

> 仅供市场历史风格趋势观察，**不构成任何投资建议**。

## 参考来源

本项目的指标定义、配色与界面风格参考自 [@OG-Wang](https://github.com/OG-Wang) 的鱼盆趋势模型实现
[`moving-average-monitor`](https://github.com/OG-Wang/moving-average-monitor)，在此致谢。
本仓库为其思路的独立改写版：数据源改为以 `akshare` 为主、`yfinance` 兜底，计算与界面逻辑自实现，更轻量易改。

## 核心逻辑

- **临界值**：以 20 日均线（MA20）为基准，可按回测数据动态调整（如科创50在15日线附近表现更好）。
- **偏离率** = (最新收盘 − MA20) / MA20，**按此值从高到低排序**（含正负）。
- **状态转变时间**：最近一次收盘价上穿 / 下穿 MA20 的日期（即原模型 YES↔NO 的切换点）。
- **区间涨幅** = 最新收盘 / 穿越当日收盘 − 1。
- **当日涨幅** = 最新收盘 / 前一日收盘 − 1。
- **排序变化** = 上一交易日名次 − 当日名次（正 = 名次上升 ↑）。

## 指标与配色

| 列 | 含义 |
|---|---|
| 排序 | 按偏离率降序，1 = 短期最强 |
| 代码 / 名称 | 标的 |
| 涨幅% | 当日涨跌幅（红涨绿跌） |
| 现价 / 20日均线 | 最新收盘与 MA20 |
| 偏离率 | 强弱核心指标，红(高)→绿(低)渐变 |
| 趋势 | ↑偏强 / ↓偏弱；`↔` 表示当日刚穿越均线 |
| 状态转变时间 | 最近一次穿越 MA20 的日期 |
| 区间涨幅% | 穿越以来的累计涨跌 |
| 排序变化 | ↑走强 / ↓走弱 |

- 🔴 **红底** = 偏离率 > 0（收盘价在 MA20 上方，原 YES）
- 🟢 **绿底** = 偏离率 < 0（收盘价在 MA20 下方，原 NO）
- 🟡 **黄底整行** = 当日发生状态转变（刚穿越均线），需重点观察

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行 Web 界面
python -m src.app
# 或： python src/app.py
```

浏览器打开 `http://127.0.0.1:5000`。

- 首次运行会自动从 `config/watchlist.example.json` 复制出 `config/watchlist.json`（个人配置，不入库）。
- 结果页点 **「获取数据(全量)」** 联网计算并生成首份观测表；之后可用「智能补缺」读库优先（约 10–20 秒）。
- 「不等美股收盘」：勾选后直接取各源最新日，A股/港股收盘后即可看当日数据（美股显示昨日收盘）。

## 监控清单

`config/watchlist.json` 中按 `broad`（宽基/风格）、`sector`（板块轮动）两组维护标的。每条：

```json
{"name": "沪深300", "code": "000300", "asset": "cn_index"}
```

`asset` 取值与对应取数源：

| asset | 说明 | 取数源 |
|---|---|---|
| `cn_index` / `cn_csindex` | A股 / 中证指数 | akshare `index_zh_a_hist` |
| `hk_index` | 港股指数 | akshare `stock_hk_index_daily` |
| `us_etf` | 美股 ETF | akshare `stock_us_daily` → yfinance 兜底 |
| `global_index` | 海外指数（韩/台/日/德/英） | yfinance（需本地代理） |
| `metal_spot` | 现货金银 | akshare `futures_foreign_hist` |
| `ths_industry` | 同花顺行业/概念 | akshare `stock_board_industry_index_ths` |

> 境外指数走 yfinance，在国内需本地代理（Clash 等，默认 `http://127.0.0.1:7890`）。不用境外标的时是否开代理不影响其余标的。

## 推送到 GitHub

> 本仓库由 AI 在受限沙箱中生成；沙箱无外网出口，故推送需在本机（已连 GitHub 的终端）执行。

1. 在 github.com 用 **moonnightlab** 账户新建一个【空】仓库 `moving-average-monitor`
   （或本地已装 `gh` 并执行 `gh repo create moonnightlab/moving-average-monitor --public`）。
2. 在本仓库目录下运行一键脚本：

```bash
chmod +x push_to_github.sh
./push_to_github.sh            # 仓库已手动建好时
# 或（gh 已登录）： ./push_to_github.sh --create
```

脚本会自动设置远程并 `git push -u origin main`。

## 每日自动更新（可选）

把 `run_daily.py` 挂到系统定时任务（Windows 任务计划程序 / Linux cron），每个交易日（美股收盘后最稳）执行一次：

```bash
python run_daily.py
```

## 文件结构

```
moving-average-monitor/
├── README.md
├── requirements.txt
├── run_daily.py / run_daily.bat      # 定时跑数
├── start_ui.bat                      # 双击启动界面
├── push_to_github.sh                 # 一键推送到 GitHub（本机执行）
├── config/
│   └── watchlist.example.json        # 监控清单示例（个人配置 watchlist.json 不入库）
├── src/
│   ├── compute.py                    # 指标计算（MA20/偏离率/穿越点/区间涨幅/排序）
│   ├── datasource.py                 # 数据源路由（akshare 为主，yfinance 兜底）
│   ├── snapshot.py                   # SQLite 快照持久化
│   ├── pipeline.py                   # 编排：取数→计算→排序→落库
│   ├── app.py                        # Flask 界面（结果页 / 配置页）
│   └── templates/                    # base / result / config
└── data/                             # 运行时生成（.gitignore，不入库）
```

## 免责声明

所有数据、计算与排序仅用于市场风格趋势的客观观察，不含任何买卖建议。投资有风险，决策需独立判断、自负盈亏。
