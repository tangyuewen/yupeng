#!/usr/bin/env bash
#
# 一键推送到 GitHub（在你本机 / 有 GitHub 访问权限的终端运行，不要在沙箱内跑）
# 用法:
#   ./push_to_github.sh            # 交互式：在 github.com 建空仓库后自动推送
#   ./push_to_github.sh --create   # 若已装 gh 且已登录，自动建仓库并推送
#
# 前置:
#   1) 在 github.com 用 moonnightlab 账户新建一个【空】仓库 moving-average-monitor
#      （或用 `gh repo create moving-average-monitor --public`）
#   2) 本机已配置 GitHub 凭证（gh auth login / git credential / SSH key 均可）
#
set -e

REPO="moving-average-monitor"
OWNER="moonnightlab"
REMOTE="https://github.com/${OWNER}/${REPO}.git"
BRANCH="main"

cd "$(dirname "$0")"

echo "==> 当前分支: $(git branch --show-current 2>/dev/null || echo '未知')"
echo "==> 提交记录:"
git log --oneline -3 2>/dev/null || true

# 若用户选择自动建仓库
if [ "${1:-}" = "--create" ]; then
  if command -v gh >/dev/null 2>&1; then
    echo "==> 用 gh 创建仓库 ${OWNER}/${REPO} ..."
    gh repo create "${OWNER}/${REPO}" --public --description "鱼盆趋势模型 · 均线趋势观测工具（参考 OG-Wang 实现）" 2>&1 || echo "(仓库可能已存在，继续推送)"
  else
    echo "未检测到 gh CLI，请手动在 github.com 新建空仓库 ${REPO} 后重试。"
    exit 1
  fi
fi

# 设置远程并推送
git remote remove origin 2>/dev/null || true
git remote add origin "${REMOTE}"
echo "==> 推送 ${BRANCH} 到 ${REMOTE} ..."
git push -u origin "${BRANCH}"

echo
echo "✅ 完成！仓库地址: https://github.com/${OWNER}/${REPO}"
