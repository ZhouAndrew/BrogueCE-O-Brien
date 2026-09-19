#!/usr/bin/env python3
"""Recover the exact 3727-turn historical O'Brien v0.2.28 save.

The historical v0.2.28 O'Brien input recorder omitted two classes of input:

1. Security Hologram toggle ('C') events. The action consumed a turn and emitted
   an RNG_CHECK, but obrienCallSecuritySpell() never recorded the initiating C.
   In this save those omissions appear as 37 RNG_CHECK records immediately
   following another RNG_CHECK.

2. Emergency Power Cell target selections. recordApplyItemCommand(cell)
   recorded "a" + the Power Cell inventory letter, but the nested target staff
   inventory letter was not recorded. Four target selections are missing in
   this exact historical save.

This tool restores only those missing input events. It does not alter, invent,
skip, or re-lock any recorded RNG_CHECK byte.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE_SHA256 = "dadc44db70a6b029e7be9dee422acc96d9a6b9063837c897305c335ee444b76d"
RECOVERED_SHA256 = "6ec2dd4a57b9dac8015b09cc84004ffd499d5e50a5ef59be162f3b7dae5138c0"
SOURCE_SIZE = 20507
RECOVERED_SIZE = 20630
HEADER_SIZE = 36
KEYSTROKE = 0
RNG_CHECK = 6

# These offsets are in the evolving byte stream after the 37 C events have
# been restored, and then after each preceding Power Cell target insertion.
# Every insertion point is asserted to be an RNG_CHECK that the clean engine
# was waiting to reach only after consuming the missing target key.
POWER_CELL_TARGETS = (
    (10336, "e", "turn 1922: Power Cell l -> staff e"),
    (15099, "f", "turn 2785: Power Cell m -> staff f"),
    (18329, "g", "turn 3326: Power Cell l -> staff g"),
    (18660, "e", "turn 3385: Power Cell n -> staff e"),
)


def sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def event_length(buf: bytes | bytearray, pos: int) -> int:
    event_type = buf[pos]
    if event_type == KEYSTROKE:
        return 3
    if event_type in (1, 2, 3, 4, 5):
        return 4
    if event_type == RNG_CHECK:
        return 2
    if event_type in (7, 8, 9):
        return 1
    raise ValueError(f"unknown event type {event_type} at byte {pos}")


def restore_missing_security_toggles(source: bytes) -> tuple[bytearray, int]:
    out = bytearray(source[:HEADER_SIZE])
    pos = HEADER_SIZE
    previous_type: int | None = None
    restored = 0

    while pos < len(source):
        event_type = source[pos]
        length = event_length(source, pos)

        if event_type == RNG_CHECK and previous_type == RNG_CHECK:
            out.extend((KEYSTROKE, ord("C"), 0))
            restored += 1

        out.extend(source[pos : pos + length])
        previous_type = event_type
        pos += length

    if restored != 37:
        raise ValueError(f"expected 37 omitted C events, found {restored}")
    return out, restored


def insert_power_cell_targets(buf: bytearray) -> None:
    for offset, key, label in POWER_CELL_TARGETS:
        if offset >= len(buf) or buf[offset] != RNG_CHECK:
            got = None if offset >= len(buf) else buf[offset]
            raise ValueError(
                f"{label}: expected RNG_CHECK at byte {offset}, got {got!r}"
            )
        buf[offset:offset] = bytes((KEYSTROKE, ord(key), 0))


def update_recorded_length(buf: bytearray) -> None:
    buf[32:36] = len(buf).to_bytes(4, "big")


def validate_header(buf: bytes | bytearray) -> None:
    if buf[:9] != b"CE 1.15.1":
        raise ValueError("unexpected Brogue recording version")
    if buf[15] != 0xB0:
        raise ValueError(f"unexpected variant/mode byte 0x{buf[15]:02x}")
    if int.from_bytes(buf[16:24], "big") != 436566627:
        raise ValueError("unexpected seed")
    if int.from_bytes(buf[24:28], "big") != 3727:
        raise ValueError("unexpected turn count")
    if int.from_bytes(buf[28:32], "big") != 14:
        raise ValueError("unexpected deepest level")
    if int.from_bytes(buf[32:36], "big") != len(buf):
        raise ValueError("header file length does not match actual length")


def recover(source: bytes) -> bytes:
    if len(source) != SOURCE_SIZE:
        raise ValueError(f"source size {len(source)} != {SOURCE_SIZE}")
    digest = sha256(source)
    if digest != SOURCE_SHA256:
        raise ValueError(f"source SHA-256 mismatch: {digest}")

    out, restored_c = restore_missing_security_toggles(source)
    insert_power_cell_targets(out)
    update_recorded_length(out)
    validate_header(out)

    if len(out) != RECOVERED_SIZE:
        raise ValueError(f"recovered size {len(out)} != {RECOVERED_SIZE}")
    recovered_digest = sha256(out)
    if recovered_digest != RECOVERED_SHA256:
        raise ValueError(
            f"recovered SHA-256 mismatch: {recovered_digest} != {RECOVERED_SHA256}"
        )

    print(f"restored Security Hologram C events: {restored_c}")
    print(f"restored Power Cell target events: {len(POWER_CELL_TARGETS)}")
    print(f"output size: {len(out)}")
    print(f"output SHA-256: {recovered_digest}")
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        nargs="?",
        default="demo/OBrien_3727turn_longsave_backup.broguesave",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="demo/OBrien_3727turn_recovered.broguesave",
    )
    args = parser.parse_args()

    source_path = Path(args.input)
    output_path = Path(args.output)
    recovered = recover(source_path.read_bytes())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(recovered)
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
