#!/usr/bin/env bash
# jing-broll environment self-check.
# Adapted from gbro-collage-broll (MIT, (c) 2026 狗哥笔记).
# Exit 0 = checked dependencies ready; 1 = missing dependency; 2 = invalid option.
# This is a local dependency check, not an API/credit or renderer health check.

set -u

VENV_PY="${JING_BROLL_VENV:-$HOME/jing-broll-projects/.venv}/bin/python"
FAIL=0
REQUIRE_GEMINI=0
REQUIRE_FAL=0
REQUIRE_SAY=0

for option in "$@"; do
  case "$option" in
    --require-gemini) REQUIRE_GEMINI=1 ;;
    --require-fal) REQUIRE_FAL=1 ;;
    --require-say) REQUIRE_SAY=1 ;;
    --help)
      printf '%s\n' 'Usage: check_setup.sh [--require-gemini] [--require-fal] [--require-say]'
      printf '%s\n' 'No flags: check only ffmpeg/ffprobe and Python. Flags add selected backend dependencies.'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$option" >&2; exit 2 ;;
  esac
done

ok()   { printf 'PASS  %s\n' "$1"; }
bad()  { printf 'FAIL  %s\n' "$1"; FAIL=1; }
skip() { printf 'SKIP  %s\n' "$1"; }

# 1. GEMINI_API_KEY（注意:agent 会话环境是启动快照,刚写入 ~/.zshrc 的
#    key 需要在命令里显式 source 才可见）
if [ "$REQUIRE_GEMINI" -eq 1 ]; then
  if [ -n "${GEMINI_API_KEY:-}" ]; then
    ok "GEMINI_API_KEY 已设置"
  else
    bad "GEMINI_API_KEY 未设置：本次选择的 Gemini 后端需要既有凭据；配置变更需授权"
  fi
else
  skip "Gemini 未选择，不检查其凭据或 SDK"
fi

# 2. ffmpeg / ffprobe
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  ok "ffmpeg / ffprobe 可用"
else
  bad "ffmpeg / ffprobe 缺失（macOS: brew install ffmpeg；Debian/Ubuntu: sudo apt install ffmpeg）"
fi

# 3. Python >= 3.10
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  ok "python3 >= 3.10"
else
  bad "python3 缺失或版本低于 3.10"
fi

# 4. google-genai >= 2.10.0 reachable from some interpreter.
#    Accept either the shared venv or a plain python3 that already has it —
#    checking only the venv reports a false FAIL on hosts where the deps are
#    installed against the default interpreter.
has_genai() {
  [ -x "$1" ] || command -v "$1" >/dev/null 2>&1 || return 1
  "$1" - <<'PY' 2>/dev/null
import sys
from google import genai
parts = [int(x) for x in genai.__version__.split(".")[:2]]
sys.exit(0 if parts >= [2, 10] else 1)
PY
}

if [ "$REQUIRE_GEMINI" -eq 1 ]; then
  if has_genai "$VENV_PY"; then
    ok "共享 venv 就绪（google-genai >= 2.10.0）：$VENV_PY"
  elif has_genai python3; then
    ok "python3 已有 google-genai >= 2.10.0（未使用共享 venv）"
  else
    bad "google-genai 缺失或版本低于 2.10.0；仅所选 Gemini 路线受阻，安装或配置变更需授权"
  fi
fi

if [ "$REQUIRE_FAL" -eq 1 ]; then
  if [ -n "${FAL_KEY:-}" ]; then
    ok "FAL_KEY 已设置"
  else
    bad "FAL_KEY 未设置：本次选择的 fal 后端需要既有凭据；配置变更需授权"
  fi
  if [ -x "$VENV_PY" ] && "$VENV_PY" -c 'import httpx' 2>/dev/null; then
    ok "httpx 可用：$VENV_PY"
  elif command -v python3 >/dev/null 2>&1 && python3 -c 'import httpx' 2>/dev/null; then
    ok "httpx 可用：python3（未使用共享 venv）"
  else
    bad "httpx 缺失；所选 fal 路线需要此依赖，安装需授权"
  fi
else
  skip "fal 未选择，不检查其凭据或 SDK"
fi

if [ "$REQUIRE_SAY" -eq 1 ]; then
  if command -v say >/dev/null 2>&1; then
    ok "say 可用"
  else
    bad "say 不可用：本次选择的本机旁白路线受阻"
  fi
else
  skip "say 未选择"
fi

printf '%s\n' '范围：仅核心与显式选择的后端依赖；未验证 API 访问、额度、codex-image 或 HyperFrames 运行能力。'
exit $FAIL
