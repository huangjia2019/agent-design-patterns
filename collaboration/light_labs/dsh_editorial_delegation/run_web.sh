#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DSH_SOURCE:-}" ]]; then
  echo "Set DSH_SOURCE to a DeepSeek Harness source checkout." >&2
  exit 2
fi

if [[ ! -f "$DSH_SOURCE/package.json" ]]; then
  echo "DSH_SOURCE does not look like a DeepSeek Harness checkout: $DSH_SOURCE" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/cordis.patch.yml.template"
PLUGIN_DIR="$DSH_SOURCE/scratch-plugin/editorial-delegation"
PLUGIN_FILE="$PLUGIN_DIR/brief_gate.ts"
GENERATED="$(mktemp "${TMPDIR:-/tmp}/dsh-editorial-XXXXXX.yml")"

cleanup() {
  rm -f "$GENERATED"
  rm -f "$PLUGIN_FILE"
  rmdir "$PLUGIN_DIR" 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "$PLUGIN_DIR"
install -m 0644 "$SCRIPT_DIR/brief_gate.ts" "$PLUGIN_FILE"
sed "s|__BRIEF_GATE_PLUGIN__|$PLUGIN_FILE|g" "$TEMPLATE" > "$GENERATED"

echo "Generated dsh overlay: $GENERATED"
cd "$DSH_SOURCE"
if [[ "${1:-}" == "--dump-config" ]]; then
  corepack pnpm dsh --profile web --patch "$GENERATED" --dump-config
  exit 0
fi
corepack pnpm dsh web --patch "$GENERATED"
