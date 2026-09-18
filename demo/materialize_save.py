#!/usr/bin/env python3
"""Reconstruct the embedded 3727-turn O'Brien historical save exactly."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "OBrien_3727turn_longsave_backup.broguesave"
EXPECTED_SIZE = 20507
EXPECTED_SHA256 = "dadc44db70a6b029e7be9dee422acc96d9a6b9063837c897305c335ee444b76d"
EXPECTED_SEED = 436566627
EXPECTED_TURNS = 3727
EXPECTED_LEVEL_CHANGES = 14


def main() -> int:
    parts = sorted(ROOT.glob("save.b64.part*"))
    if [p.name for p in parts] != [f"save.b64.part{i:02d}" for i in range(7)]:
        raise SystemExit("embedded save parts are missing or unexpectedly named")

    encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
    data = base64.b64decode(encoded, validate=True)

    digest = hashlib.sha256(data).hexdigest()
    if len(data) != EXPECTED_SIZE:
        raise SystemExit(f"size mismatch: got {len(data)}, expected {EXPECTED_SIZE}")
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"SHA-256 mismatch: got {digest}")

    if data[:9] != b"CE 1.15.1":
        raise SystemExit("recording version header mismatch")
    if data[15] != 0xB0:
        raise SystemExit(f"variant/mode byte mismatch: got 0x{data[15]:02x}, expected 0xb0")

    seed = int.from_bytes(data[16:24], "big")
    turns = int.from_bytes(data[24:28], "big")
    level_changes = int.from_bytes(data[28:32], "big")
    recorded_length = int.from_bytes(data[32:36], "big")
    if seed != EXPECTED_SEED:
        raise SystemExit(f"seed mismatch: got {seed}")
    if turns != EXPECTED_TURNS:
        raise SystemExit(f"turn count mismatch: got {turns}")
    if level_changes != EXPECTED_LEVEL_CHANGES:
        raise SystemExit(f"level-change count mismatch: got {level_changes}")
    if recorded_length != EXPECTED_SIZE:
        raise SystemExit(f"recorded length mismatch: got {recorded_length}")

    OUTPUT.write_bytes(data)
    print(f"materialized: {OUTPUT}")
    print(f"size={len(data)} sha256={digest}")
    print(
        f"header: seed={seed} turns={turns} "
        f"levelChanges={level_changes} variantByte=0x{data[15]:02x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
