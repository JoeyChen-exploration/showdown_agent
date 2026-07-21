#!/usr/bin/env bash
# PreToolUse hook（matcher: Edit|Write|MultiEdit）
# 如果当前 git 分支是 main/master，拦截对仓库内文件的改动，提示先开 feature branch。
# 仓库外的文件（比如 ~/.claude/ 全局配置、/tmp）不归本仓库的分支纪律管，放行。
# 不是 git 仓库、或者拿不到分支名/文件路径时，安静放行（避免误伤）。

set -euo pipefail

if ! command -v git >/dev/null 2>&1; then
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  exit 0
fi

INPUT=$(cat)

# 目标文件路径：只管仓库内的文件。拿不到路径时保守起见仍然拦截（宁可误报）。
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys
try:
    print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))
except Exception:
    pass" 2>/dev/null || true)

if [ -n "$FILE_PATH" ]; then
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
  case "$FILE_PATH" in
    "$REPO_ROOT"/*) ;;               # 仓库内 → 继续检查分支
    *) exit 0 ;;                     # 仓库外 → 放行
  esac
fi

BRANCH=$(git branch --show-current 2>/dev/null || true)

if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "拦截：当前在 $BRANCH 分支上，不允许直接改动仓库内文件。" >&2
  echo "请先开一个 issue（如果适用），再用 git checkout -b 开一个新分支，再继续。" >&2
  exit 2
fi

exit 0
