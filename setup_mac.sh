#!/usr/bin/env bash
set -euo pipefail

echo "[*] Creating skeleton..."
mkdir -p docs .cursor/rules

echo "[*] Done. Copy PRD/rules if not present and run:"
echo "tm parse prd ./docs/PRD.md -o ./tasks.json"
echo "cursor agent --apply=ask --rules --mcp"
