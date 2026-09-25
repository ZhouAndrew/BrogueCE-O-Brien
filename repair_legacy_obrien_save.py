#!/usr/bin/env python3
"""Repair legacy O'Brien Brogue recordings without altering reconstructed game state.

There are two supported migrations:

1. Generic legacy header tagging (v0.2.28): for an untagged Brogue CE recording,
   pack the O'Brien variant into header byte 15. The event stream is unchanged.
2. Exact 3727-turn historical fixture repair (v0.2.29): only when the input
   SHA-256 is the known forensic save, insert the 37 missing Call Security C
   keystrokes and four missing Emergency Power Cell target keystrokes proven by
   exhaustive replay. Existing RNG_CHECK bytes and all existing input bytes are
   preserved in order; only the header file-length field is updated.
3. Bashir recovery-boundary compatibility tagging (v0.2.32): with
   --bashir-recovery-delay-compat, set one spare header flag telling v0.2.32+
   playback to rematerialize Bashir on the following input boundary. The event
   stream, RNG_CHECK bytes, seed, turn count and file length are untouched.

The exact 3727-turn event insertion remains hash-locked. The v0.2.32 header
compatibility flag is opt-in and validates that the recording is O'Brien.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import sys

HEADER_LENGTH = 36
OBRIEN_COMPAT_HEADER_INDEX = 13
OBRIEN_COMPAT_DELAY_BASHIR_RETURN = 0x01
VARIANT_TAG = 0x80
VARIANT_SHIFT = 4
VARIANT_MASK = 0x07
MODE_MASK = 0x0F
VARIANT_OBRIEN_MUST_SURVIVE = 3

KEYSTROKE_EVENT = 0
RNG_CHECK_EVENT = 6
NO_MODIFIERS = 0

KNOWN_LONGSAVE_SHA256 = "dadc44db70a6b029e7be9dee422acc96d9a6b9063837c897305c335ee444b76d"
KNOWN_LONGSAVE_SIZE = 20507
KNOWN_LONGSAVE_TURNS = 3727
KNOWN_LONGSAVE_LEVEL_CHANGES = 14

# Absolute byte offsets in the original 20,507-byte file. Each location points
# at the RNG_CHECK that historical execution wrote after a successful C action,
# even though the C input itself was omitted.
KNOWN_MISSING_CALL_SECURITY_OFFSETS = (
    53, 55, 287, 3072, 3233, 3235, 3237, 3239, 3241, 3657, 3738,
    7927, 7976, 11911, 12446, 13733, 13785, 13936, 14566, 14636,
    14717, 15017, 15019, 15309, 15353, 15888, 15890, 16568, 16582,
    16584, 16628, 16845, 16989, 18368, 18442, 18812, 18883,
)

# Power Cell target selection was also omitted from recording. Forensic replay
# uniquely recovers the original target sequence as Fire, Lightning, Poison,
# Fire, whose inventory letters at those historical turns were e, f, g, e.
KNOWN_MISSING_POWER_CELL_TARGETS = (
    (10297, "e"),
    (15027, "f"),
    (18224, "g"),
    (18546, "e"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tagged_byte(mode: int) -> int:
    return (
        VARIANT_TAG
        | ((VARIANT_OBRIEN_MUST_SURVIVE & VARIANT_MASK) << VARIANT_SHIFT)
        | (mode & MODE_MASK)
    )


def encoded_key(letter: str) -> bytes:
    if len(letter) != 1 or ord(letter) >= 128:
        raise ValueError(f"unsupported historical key {letter!r}")
    return bytes((KEYSTROKE_EVENT, ord(letter), NO_MODIFIERS))


def repair_known_3727_longsave(data: bytes) -> bytes:
    if len(data) != KNOWN_LONGSAVE_SIZE:
        raise ValueError("known 3727-turn fixture size changed")
    if data[:9] != b"CE 1.15.1":
        raise ValueError("known 3727-turn fixture version header changed")
    if data[15] != tagged_byte(0):
        raise ValueError(
            f"known 3727-turn fixture variant byte changed: 0x{data[15]:02x}"
        )
    if int.from_bytes(data[24:28], "big") != KNOWN_LONGSAVE_TURNS:
        raise ValueError("known 3727-turn fixture turn count changed")
    if int.from_bytes(data[28:32], "big") != KNOWN_LONGSAVE_LEVEL_CHANGES:
        raise ValueError("known 3727-turn fixture depth count changed")
    if int.from_bytes(data[32:36], "big") != len(data):
        raise ValueError("known 3727-turn fixture header length is inconsistent")

    inserts: dict[int, list[bytes]] = {}

    for offset in KNOWN_MISSING_CALL_SECURITY_OFFSETS:
        if data[offset] != RNG_CHECK_EVENT:
            raise ValueError(
                f"expected RNG_CHECK at historical Call Security offset {offset}, "
                f"found {data[offset]}"
            )
        inserts.setdefault(offset, []).append(encoded_key("C"))

    for offset, target in KNOWN_MISSING_POWER_CELL_TARGETS:
        if data[offset] != RNG_CHECK_EVENT:
            raise ValueError(
                f"expected RNG_CHECK at historical Power Cell offset {offset}, "
                f"found {data[offset]}"
            )
        inserts.setdefault(offset, []).append(encoded_key(target))

    out = bytearray()
    for offset, value in enumerate(data):
        for insertion in inserts.get(offset, ()):
            out.extend(insertion)
        out.append(value)

    expected_added = (
        len(KNOWN_MISSING_CALL_SECURITY_OFFSETS)
        + len(KNOWN_MISSING_POWER_CELL_TARGETS)
    ) * 3
    if len(out) != len(data) + expected_added:
        raise ValueError("historical repair inserted an unexpected byte count")

    # The historical header already counted the turns correctly because the
    # omitted actions did execute. Only the physical recording length changes.
    out[32:36] = len(out).to_bytes(4, "big")
    return bytes(out)


def add_bashir_recovery_delay_compat(data: bytes) -> bytes:
    if len(data) < HEADER_LENGTH:
        raise ValueError("file is shorter than the 36-byte Brogue recording header")
    header_byte = data[15]
    if not (header_byte & VARIANT_TAG):
        raise ValueError("Bashir compatibility tagging requires a variant-tagged O'Brien recording")
    variant = (header_byte >> VARIANT_SHIFT) & VARIANT_MASK
    if variant != VARIANT_OBRIEN_MUST_SURVIVE:
        raise ValueError(
            f"Bashir compatibility tagging requires O'Brien variant; found variant {variant}"
        )
    out = bytearray(data)
    out[OBRIEN_COMPAT_HEADER_INDEX] |= OBRIEN_COMPAT_DELAY_BASHIR_RETURN
    return bytes(out)


def migrate_bytes(data: bytes) -> bytes:
    if len(data) < HEADER_LENGTH:
        raise ValueError("file is shorter than the 36-byte Brogue recording header")
    if data[:2] != b"CE":
        raise ValueError("file does not look like a Brogue CE save/recording")

    digest = sha256(data)
    if digest == KNOWN_LONGSAVE_SHA256:
        return repair_known_3727_longsave(data)

    header_byte = data[15]
    if header_byte & VARIANT_TAG:
        variant = (header_byte >> VARIANT_SHIFT) & VARIANT_MASK
        if variant == VARIANT_OBRIEN_MUST_SURVIVE:
            return data
        raise ValueError(
            f"recording already has tagged variant {variant}; refusing to relabel it as O'Brien"
        )

    # Legacy header: the whole byte was rogue.mode. Current modes fit in 4 bits.
    if header_byte > MODE_MASK:
        raise ValueError(f"legacy mode byte {header_byte} is outside the supported range")

    out = bytearray(data)
    out[15] = tagged_byte(header_byte)
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="legacy .broguesave or .broguerec file")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="replace the input file after writing a .bak backup",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="output path (default: <name>.obrien-fixed<suffix>)",
    )
    parser.add_argument(
        "--bashir-recovery-delay-compat",
        action="store_true",
        help=(
            "set the v0.2.32+ compatibility flag that delays Bashir automatic "
            "rematerialization by one input boundary; event bytes are unchanged"
        ),
    )
    args = parser.parse_args()

    src = args.path
    if not src.is_file():
        parser.error(f"not a file: {src}")
    if args.in_place and args.output is not None:
        parser.error("--in-place and --output cannot be used together")

    original = src.read_bytes()
    original_digest = sha256(original)
    try:
        repaired = migrate_bytes(original)
        if args.bashir_recovery_delay_compat:
            repaired = add_bashir_recovery_delay_compat(repaired)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.in_place:
        backup = src.with_name(src.name + ".bak")
        shutil.copy2(src, backup)
        destination = src
    elif args.output is not None:
        destination = args.output
    else:
        destination = src.with_name(src.stem + ".obrien-fixed" + src.suffix)

    destination.write_bytes(repaired)
    repaired_digest = sha256(repaired)

    if repaired == original:
        print(f"already compatible; no byte changes required: {destination}")
    elif args.bashir_recovery_delay_compat:
        print(f"tagged O'Brien recording for delayed Bashir recovery compatibility: {destination}")
        print(
            f"set header byte {OBRIEN_COMPAT_HEADER_INDEX} flag "
            f"0x{OBRIEN_COMPAT_DELAY_BASHIR_RETURN:02x}; event stream is unchanged"
        )
        print(f"sha256 {original_digest} -> {repaired_digest}")
    elif original_digest == KNOWN_LONGSAVE_SHA256:
        print(f"repaired exact historical 3727-turn O'Brien save: {destination}")
        print(
            "inserted 37 Call Security C events and 4 Power Cell target events; "
            "existing event/RNG bytes preserved"
        )
        print(
            f"size {len(original)} -> {len(repaired)}; "
            f"sha256 {original_digest} -> {repaired_digest}"
        )
    else:
        print(f"tagged legacy O'Brien recording: {destination}")
        print("changed exactly header byte 15; event stream is unchanged")
        print(f"sha256 {original_digest} -> {repaired_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
