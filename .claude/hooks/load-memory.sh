#!/usr/bin/env bash
# SessionStart hook：把 .claude/memory/ 目录下所有 .md 文件的内容
# 拼接起来，作为 additionalContext 自动注入给 Claude。
# 这样就不用每次开新 session 手动提醒 Claude 去读记忆文件了。

set -euo pipefail

MEMORY_DIR="$(dirname "$0")/../memory"

# 没有 memory 目录或目录是空的，直接安静退出，不影响正常启动
if [ ! -d "$MEMORY_DIR" ]; then
  exit 0
fi

# 排除模板示例文件本身，避免每次都把模板说明也注入进去
FILES=$(find "$MEMORY_DIR" -maxdepth 1 -name "*.md" ! -name "EXAMPLE_*" | sort)

if [ -z "$FILES" ]; then
  exit 0
fi

CONTENT="以下是这个项目积累的经验教训（来自 .claude/memory/），请在整个 session 中遵守：\n\n"

for f in $FILES; do
  CONTENT="${CONTENT}---\n$(cat "$f")\n\n"
done

# 用 jq 安全地把内容编码进 JSON 字符串，避免换行/引号破坏 JSON 格式
if command -v jq >/dev/null 2>&1; then
  printf '%s' "$CONTENT" | jq -Rs '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: .}}'
else
  # 没装 jq 的兜底方案：用 python 做同样的事
  printf '%s' "$CONTENT" | python3 -c '
import json, sys
content = sys.stdin.read()
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": content}}))
'
fi
