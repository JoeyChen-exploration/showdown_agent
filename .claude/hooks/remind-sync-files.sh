#!/bin/bash
# Stop hook：每轮结束前提醒 Claude 检查相关文件是否需要同步更新。
# 通过 stop_hook_active 防止无限循环：提醒只触发一次，Claude 完成自检后即可正常结束。

input=$(cat)
active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)

if [ "$active" = "true" ]; then
  exit 0
fi

cat <<'EOF'
{"decision":"block","reason":"自动同步检查：如果本轮修改过任何文件，请 view 项目中所有相关文件（CLAUDE.md、.claude/memory/、维护日志等），检查是否需要同步更新，需要则一并更新后再结束；如果本轮没有改动文件或同步已完成，直接结束即可，不要重复此检查。"}
EOF
