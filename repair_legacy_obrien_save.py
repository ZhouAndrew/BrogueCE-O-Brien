#!/usr/bin/env python3
"""Tag a legacy O'Brien Brogue save/recording with v0.2.28 variant metadata.

Brogue CE 1.15.1 used byte 15 of its 36-byte recording header for game mode only.
O'Brien v0.2.28 keeps that byte but packs a marker + variant + mode into it.
This utility changes only byte 15; the seed, turn count, depth, length and event
stream are left byte-for-byte untouched.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

HEADER_LENGTH = 36
VARIANT_TAG = 0x80
VARIANT_SHIFT = 4
VARIANT_MASK = 0x07
MODE_MASK = 0x0F
VARIANT_OBRIEN_MUST_SURVIVE = 3


def tagged_byte(mode: int) -> int:
    return (
        VARIANT_TAG
        | ((VARIANT_OBRIEN_MUST_SURVIVE & VARIANT_MASK) << VARIANT_SHIFT)
        | (mode & MODE_MASK)
    )


def migrate_bytes(data: bytes) -> bytes:
    if len(data) < HEADER_LENGTH:
        raise ValueError("file is shorter than the 36-byte Brogue recording header")

    # CE 1.15.x recordingVersionString begins with this stable prefix. Keep the
    # check deliberately narrow enough to avoid modifying unrelated binary files.
    if not data[:2] == b"CE":
        raise ValueError("file does not look like a Brogue CE save/recording")

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
    args = parser.parse_args()

    src = args.path
    if not src.is_file():
        parser.error(f"not a file: {src}")
    if args.in_place and args.output is not None:
        parser.error("--in-place and --output cannot be used together")

    original = src.read_bytes()
    try:
        repaired = migrate_bytes(original)
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

    if repaired == original:
        print(f"already tagged as O'Brien v0.2.28 format: {destination}")
    else:
        print(f"tagged legacy O'Brien recording: {destination}")
        print("changed exactly header byte 15; event stream is unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
