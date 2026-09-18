#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAVE="$ROOT/demo/OBrien_3727turn_longsave_backup.broguesave"
BIN="${BROGUE_BIN:-$ROOT/bin/brogue}"

python3 "$ROOT/demo/materialize_save.py"

if [[ ! -x "$BIN" ]]; then
  cat >&2 <<'EOF'
No Brogue binary found at bin/brogue.

For the intended O'Brien v0.2.29 demo build:
  python3 apply_obrien_mod_v0_2_29.py
  make -B
  ./demo/run-demo.sh

Or set BROGUE_BIN=/absolute/path/to/brogue.
EOF
  exit 2
fi

RUNTIME="${TMPDIR:-/tmp}/obrien-3727-repaired-demo-${USER:-user}.broguesave"
python3 "$ROOT/repair_legacy_obrien_save.py" "$SAVE" --output "$RUNTIME"

echo "Historical forensic source remains untouched:"
echo "  $SAVE"
echo "Repaired disposable runtime copy:"
echo "  $RUNTIME"
echo
echo "The runtime copy inserts only the 41 historically omitted input events"
echo "(37 Call Security C events + 4 Power Cell target choices)."

cd "$(dirname "$BIN")"
exec "./$(basename "$BIN")" -o "$RUNTIME"
