#!/usr/bin/env bash
# =============================================================================
# install.sh — Cài bộ SEO skill/agent vào runtime bạn dùng.
#
# Pattern đa runtime học từ Bhanunamikaze/Agentic-SEO-Skill (MIT), viết lại.
#
#   bash install.sh --target claude  --project-dir /path/to/ptemagic
#   bash install.sh --target global
#   bash install.sh --target all     --project-dir /path/to/ptemagic
#   bash install.sh --target cursor  --project-dir .
#   bash install.sh --list
#   bash install.sh --uninstall --target claude --project-dir .
#
# Không copy code của repo nào khác — chỉ copy nội dung thư mục này.
# =============================================================================
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="claude"
PROJECT_DIR=""
MODE="copy"          # copy | symlink
FORCE=0
DRY=0

usage() {
  sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)       TARGET="$2"; shift 2 ;;
    --project-dir)  PROJECT_DIR="$2"; shift 2 ;;
    --symlink)      MODE="symlink"; shift ;;
    --force)        FORCE=1; shift ;;
    --dry-run)      DRY=1; shift ;;
    --uninstall)    TARGET="${TARGET:-claude}"; UNINSTALL=1; shift ;;
    --list|-l)      echo "Targets: claude global codex cursor windsurf copilot cline continue all"; exit 0 ;;
    -h|--help)      usage ;;
    *) echo "Không hiểu tham số: $1" >&2; usage ;;
  esac
done

log()  { printf '\033[0;35m[install]\033[0m %s\n' "$*"; }
ok()   { printf '\033[0;32m   ✓\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m   !\033[0m %s\n' "$*"; }
die()  { printf '\033[0;31m   ✗\033[0m %s\n' "$*" >&2; exit 1; }

run() { if [[ $DRY -eq 1 ]]; then echo "   [dry-run] $*"; else eval "$@"; fi; }

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
place() {  # place <src> <dst>
  local src="$1" dst="$2"
  if [[ -e "$dst" && $FORCE -eq 0 ]]; then
    warn "đã tồn tại, bỏ qua (dùng --force để ghi đè): $dst"
    return 0
  fi
  run "mkdir -p \"$(dirname "$dst")\""
  if [[ "$MODE" == "symlink" ]]; then
    run "rm -rf \"$dst\" && ln -s \"$src\" \"$dst\""
  else
    if [[ -d "$src" ]]; then
      run "rm -rf \"$dst\" && cp -R \"$src\" \"$dst\" && find \"$dst\" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true"
    else
      run "cp \"$src\" \"$dst\""
    fi
  fi
  ok "$(basename "$dst")"
}

install_set() {  # install_set <base_dir>
  local base="$1"
  # Lần cài đầu tiên thư mục .claude/.cursor chưa tồn tại — phải tự tạo, không được bỏ qua.
  run "mkdir -p \"$base\""
  log "→ $base"
  place "$SRC_DIR/skills"   "$base/skills/ptemagic-seo"
  place "$SRC_DIR/agents"   "$base/agents/ptemagic-seo"
  place "$SRC_DIR/commands" "$base/commands/ptemagic-seo"
}

require_project_dir() {
  [[ -n "$PROJECT_DIR" ]] || die "cần --project-dir cho target '$TARGET'"
  [[ -d "$PROJECT_DIR" ]] || die "--project-dir không tồn tại: $PROJECT_DIR"
  PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
}

# --------------------------------------------------------------------------- #
# Uninstall
# --------------------------------------------------------------------------- #
if [[ "${UNINSTALL:-0}" -eq 1 ]]; then
  log "Gỡ cài đặt (target=$TARGET)"
  case "$TARGET" in
    claude) require_project_dir; for d in skills agents commands; do
              run "rm -rf \"$PROJECT_DIR/.claude/$d/ptemagic-seo\""; done ;;
    global) for d in skills agents commands; do run "rm -rf \"$HOME/.claude/$d/ptemagic-seo\""; done ;;
    *) warn "uninstall chưa hỗ trợ target '$TARGET' — xoá tay theo đường dẫn in ở trên" ;;
  esac
  ok "đã gỡ"
  exit 0
fi

# --------------------------------------------------------------------------- #
# Install
# --------------------------------------------------------------------------- #
echo
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║   PTE Magic SEO Operating System — installer                     ║"
echo "║   source: $SRC_DIR"
echo "║   target: $TARGET · mode: $MODE · dry-run: $DRY"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo

case "$TARGET" in
  claude|cowork)
    require_project_dir
    install_set "$PROJECT_DIR/.claude"
    place "$SRC_DIR/config"   "$PROJECT_DIR/.claude/ptemagic-seo-config"
    place "$SRC_DIR/context"  "$PROJECT_DIR/.claude/ptemagic-seo-context"
    place "$SRC_DIR/scripts"  "$PROJECT_DIR/.claude/ptemagic-seo-scripts"
    place "$SRC_DIR/references" "$PROJECT_DIR/.claude/ptemagic-seo-references"
    place "$SRC_DIR/templates"  "$PROJECT_DIR/.claude/ptemagic-seo-templates"
    place "$SRC_DIR/QUY-TRINH-SEO-PTEMAGIC.md" "$PROJECT_DIR/.claude/SEO-SOP.md"
    ;;

  global)
    install_set "$HOME/.claude"
    place "$SRC_DIR/config"  "$HOME/.claude/ptemagic-seo-config"
    place "$SRC_DIR/context" "$HOME/.claude/ptemagic-seo-context"
    place "$SRC_DIR/scripts" "$HOME/.claude/ptemagic-seo-scripts"
    ;;

  codex)
    install_set "$HOME/.codex"
    AGENTS_MD="${PROJECT_DIR:-.}/AGENTS.md"
    if [[ -f "$AGENTS_MD" ]]; then
      warn "AGENTS.md đã tồn tại — không ghi đè. Tự dán nội dung SEO-SOP.md vào."
    else
      { echo "# Agent instructions"; echo
        echo "## SEO"; echo
        echo "Đọc \`.codex/skills/ptemagic-seo/\` trước khi làm bất cứ việc SEO nào."
        echo "Quy trình chuẩn: \`$SRC_DIR/QUY-TRINH-SEO-PTEMAGIC.md\`."
        echo "KHÔNG publish nội dung nào chưa qua \`scripts/policy_gate.py\`."
      } > "$AGENTS_MD"
      ok "AGENTS.md"
    fi
    ;;

  cursor)
    require_project_dir
    place "$SRC_DIR/skills"  "$PROJECT_DIR/.cursor/skills/ptemagic-seo"
    place "$SRC_DIR/scripts" "$PROJECT_DIR/.cursor/ptemagic-seo-scripts"
    MDC="$PROJECT_DIR/.cursor/rules/ptemagic-seo.mdc"
    run "mkdir -p \"$(dirname "$MDC")\""
    {
      echo "---"
      echo "description: Quy trình SEO cho ptemagic.com — skill, agent, script và policy gate"
      echo "alwaysApply: false"
      echo "globs: "
      echo "---"
      echo
      echo "# SEO operating rules (ptemagic.com)"
      echo
      cat "$SRC_DIR/QUY-TRINH-SEO-PTEMAGIC.md"
      echo
      echo "## Skill có sẵn"
      echo
      for f in "$SRC_DIR"/skills/*/SKILL.md; do
        [[ -f "$f" ]] || continue
        name="$(basename "$(dirname "$f")")"
        desc="$(awk '/^description:/{sub(/^description:[ ]*/,""); print; exit}' "$f")"
        echo "- **\`$name\`** — ${desc:0:220}"
      done
    } > "$MDC"
    ok ".cursor/rules/ptemagic-seo.mdc"
    ;;

  windsurf)
    require_project_dir
    place "$SRC_DIR/skills" "$PROJECT_DIR/.windsurf/skills/ptemagic-seo"
    place "$SRC_DIR/scripts" "$PROJECT_DIR/.windsurf/ptemagic-seo-scripts"
    WF="$PROJECT_DIR/.windsurf/rules/ptemagic-seo.md"
    run "mkdir -p \"$(dirname "$WF")\""
    run "cp \"$SRC_DIR/QUY-TRINH-SEO-PTEMAGIC.md\" \"$WF\""
    ok ".windsurf/rules/ptemagic-seo.md"
    ;;

  copilot)
    require_project_dir
    place "$SRC_DIR/skills" "$PROJECT_DIR/.github/skills/ptemagic-seo"
    place "$SRC_DIR/scripts" "$PROJECT_DIR/.github/ptemagic-seo-scripts"
    CI="$PROJECT_DIR/.github/copilot-instructions.md"
    if [[ -f "$CI" && $FORCE -eq 0 ]]; then
      warn "copilot-instructions.md đã tồn tại — không ghi đè (--force để ghi đè)"
    else
      {
        echo "# Repository instructions"
        echo
        echo "## SEO (ptemagic.com)"
        echo
        echo "Toàn bộ quy trình: \`.github/skills/ptemagic-seo/\` và SOP dưới đây."
        echo
        cat "$SRC_DIR/QUY-TRINH-SEO-PTEMAGIC.md"
      } > "$CI"
      ok ".github/copilot-instructions.md"
    fi
    ;;

  cline)
    require_project_dir
    place "$SRC_DIR/skills" "$PROJECT_DIR/.cline/skills/ptemagic-seo"
    CR="$PROJECT_DIR/.clinerules"
    [[ -f "$CR" && $FORCE -eq 0 ]] && warn ".clinerules đã tồn tại — bỏ qua" \
      || { run "cp \"$SRC_DIR/QUY-TRINH-SEO-PTEMAGIC.md\" \"$CR\""; ok ".clinerules"; }
    ;;

  continue)
    require_project_dir
    place "$SRC_DIR/skills" "$PROJECT_DIR/.continue/skills/ptemagic-seo"
    run "mkdir -p \"$PROJECT_DIR/.continue/prompts\""
    run "cp \"$SRC_DIR/QUY-TRINH-SEO-PTEMAGIC.md\" \"$PROJECT_DIR/.continue/prompts/seo.md\""
    ok ".continue/prompts/seo.md"
    ;;

  all)
    require_project_dir
    for t in claude cursor windsurf copilot; do
      echo
      "$0" --target "$t" --project-dir "$PROJECT_DIR" --mode "$MODE" \
           $([[ $FORCE -eq 1 ]] && echo --force) $([[ $DRY -eq 1 ]] && echo --dry-run) || true
    done
    echo
    "$0" --target codex --project-dir "$PROJECT_DIR" $([[ $DRY -eq 1 ]] && echo --dry-run) || true
    ;;

  *) die "target không hợp lệ: $TARGET (chọn: claude global codex cursor windsurf copilot cline continue all)" ;;
esac

echo
log "Xong. Việc tiếp theo:"
echo "  1. cd $SRC_DIR && python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt"
echo "  2. cp .env.example .env   # điền PSI_API_KEY + GSC service account"
echo "  3. .venv/bin/python scripts/tests/run_selftest.py    # xác nhận toolchain chạy được"
echo "  4. .venv/bin/python scripts/seo_audit.py --site https://ptemagic.com --max-urls 100"
echo
echo "  Trong agent: gõ  /seo-audit https://ptemagic.com"
echo
