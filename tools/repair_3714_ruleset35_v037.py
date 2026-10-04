#!/usr/bin/env python3
"""Tag the verified 3714-turn O'Brien recording for v0.2.37 replay.

This is intentionally hash-locked. It does not rewrite RNG checkpoints.
It accepts either:
- the true historical recording stream (SHA-256 c095...); or
- the earlier two-byte diagnostic copy (SHA-256 6f646...), in which case the
  two diagnostic RNG payload edits are first restored to their historical
  values 183 and 56.

The only compatibility change written to the historical stream is header byte
13 bit 0x02 (OBRIEN_COMPAT_LEGACY_STRENGTH_PHASE).
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

TRUE_SHA = "c095b5dfa021cb6cc810e704defb07abae0834dca7906af41914e07aa127b0f0"
DIAGNOSTIC_SHA = "6f646658e910f07fa52f83d5edda354f039b64bf303abbe8176b1f9dd5edb021"
EXPECTED_SIZE = 20541
COMPAT_INDEX = 13
RULESET_INDEX = 14
COMPAT_DELAY_BASHIR_RETURN = 0x01
COMPAT_LEGACY_STRENGTH_PHASE = 0x02
RNG_2054_OFFSET = 11104
RNG_2055_OFFSET = 11109


def sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", nargs="?", type=Path)
    args = ap.parse_args()

    src = args.input.read_bytes()
    if len(src) != EXPECTED_SIZE:
        raise SystemExit(f"Refusing unexpected size {len(src)}; expected {EXPECTED_SIZE}.")

    initial_sha = sha256(src)
    b = bytearray(src)

    if initial_sha == DIAGNOSTIC_SHA:
        if (b[RNG_2054_OFFSET], b[RNG_2055_OFFSET]) != (105, 71):
            raise SystemExit("Diagnostic hash matched but expected edited RNG bytes were absent.")
        b[RNG_2054_OFFSET] = 183
        b[RNG_2055_OFFSET] = 56
        restored_sha = sha256(b)
        if restored_sha != TRUE_SHA:
            raise SystemExit(f"Historical checkpoint restoration produced unexpected SHA {restored_sha}.")
        print("Restored the two earlier diagnostic RNG payload edits.")
    elif initial_sha != TRUE_SHA:
        raise SystemExit(
            "Refusing an unrecognized recording.\n"
            f"SHA-256: {initial_sha}\n"
            "This repair is deliberately locked to the verified 3714-turn recording."
        )

    if b[RULESET_INDEX] != 35:
        raise SystemExit(f"Expected ruleset 35; found {b[RULESET_INDEX]}.")
    if (b[COMPAT_INDEX] & COMPAT_DELAY_BASHIR_RETURN) == 0:
        raise SystemExit("Expected existing Bashir-return compatibility bit 0x01.")

    b[COMPAT_INDEX] |= COMPAT_LEGACY_STRENGTH_PHASE

    out = args.output
    if out is None:
        out = args.input.with_name(args.input.stem + ".v037-repaired" + args.input.suffix)
    out.write_bytes(b)

    print(f"Input SHA-256:  {initial_sha}")
    print(f"Output SHA-256: {sha256(b)}")
    print(f"Compatibility byte: 0x{b[COMPAT_INDEX]:02x}")
    print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
