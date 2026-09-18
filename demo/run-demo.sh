#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAVE="$ROOT/demo/OBrien_3727turn_longsave_backup.broguesave"
BIN="${BROGUE_BIN:-$ROOT/bin/brogue}"

python3 "$ROOT/demo/materialize_save.py"

if [[ ! -x "$BIN" ]]; then
  cat >&2 <<'EOF'
No Brogue binary found at bin/brogue.

For the intended O'Brien v0.2.28 demo build:
  python3 apply_obrien_mod_v0_2_28.py
  make -B
  ./demo/run-demo.sh

Or set BROGUE_BIN=/absolute/path/to/brogue.
EOF
  exit 2
fi

RUNTIME="${TMPDIR:-/tmp}/obrien-3727-historical-demo-${USER:-user}.broguesave"
cp "$SAVE" "$RUNTIME"

echo "Historical demo source remains untouched:"
echo "  $SAVE"
echo "Runtime copy:"
echo "  $RUNTIME"
echo
echo "NOTE: this is the original forensic save, not a repaired save."
echo "Current clean v0.2.28 is expected to expose the historical replay/OOS problem."

cd "$(dirname "$BIN")"
exec "./$(basename "$BIN")" -o "$RUNTIME"
