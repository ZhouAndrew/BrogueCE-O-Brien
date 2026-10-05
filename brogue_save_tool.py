#!/usr/bin/env python3
"""
Brogue CE .broguesave structural validator / comparator / safe truncator.

Important:
- This validates the binary recording structure.
- It does NOT prove that Brogue's game simulation will remain RNG-synchronized.
  Only replaying with the exact Brogue executable can prove "no OUT OF SYNC".
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import argparse, hashlib, json

HEADER_LEN = 36
KEYSTROKE = 0
MOUSE_UP = 1
MOUSE_DOWN = 2
RIGHT_MOUSE_DOWN = 3
RIGHT_MOUSE_UP = 4
MOUSE_ENTERED_CELL = 5
RNG_CHECK = 6
SAVED_GAME_LOADED = 7
END_OF_RECORDING = 8
EVENT_ERROR = 9

EVENT_LEN = {
    KEYSTROKE: 3,
    MOUSE_UP: 4,
    MOUSE_DOWN: 4,
    RIGHT_MOUSE_DOWN: 4,
    RIGHT_MOUSE_UP: 4,
    MOUSE_ENTERED_CELL: 4,
    RNG_CHECK: 2,
    SAVED_GAME_LOADED: 1,
    END_OF_RECORDING: 1,
    EVENT_ERROR: 1,
}

@dataclass
class Event:
    index: int
    offset: int
    type: int
    raw: bytes
    turns_before: int

def read_u32be(b: bytes) -> int:
    return int.from_bytes(b, "big")

def header(data: bytes) -> dict:
    if len(data) < HEADER_LEN:
        raise ValueError("file shorter than 36-byte header")
    version = data[:15].split(b"\0", 1)[0].decode("ascii", "replace")
    return {
        "version": version,
        "mode": data[15],
        "seed": int.from_bytes(data[16:24], "big"),
        "turns": read_u32be(data[24:28]),
        "deepest_level_header": read_u32be(data[28:32]),
        "length_header": read_u32be(data[32:36]),
        "actual_length": len(data),
    }

def parse_events(data: bytes) -> list[Event]:
    i = HEADER_LEN
    events = []
    turns = 0
    idx = 0
    while i < len(data):
        t = data[i]
        if t not in EVENT_LEN:
            raise ValueError(f"unknown event type {t} at byte offset {i}")
        n = EVENT_LEN[t]
        if i + n > len(data):
            raise ValueError(f"truncated event type {t} at byte offset {i}")
        raw = data[i:i+n]
        events.append(Event(idx, i, t, raw, turns))
        if t == RNG_CHECK:
            turns += 1
        i += n
        idx += 1
    return events

def inspect_file(path: Path) -> dict:
    data = path.read_bytes()
    h = header(data)
    ev = parse_events(data)
    counts = Counter(e.type for e in ev)
    loads = [
        {"event_index": e.index, "offset": e.offset, "turns_before": e.turns_before}
        for e in ev if e.type == SAVED_GAME_LOADED
    ]
    rng_count = counts[RNG_CHECK]
    return {
        "path": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "header": h,
        "event_count": len(ev),
        "event_type_counts": dict(sorted(counts.items())),
        "rng_check_count": rng_count,
        "saved_game_loaded": loads,
        "checks": {
            "length_matches_header": h["length_header"] == len(data),
            "rng_count_matches_turn_header": rng_count == h["turns"],
            "event_stream_parses_to_eof": True,
        }
    }

def compare_files(a: Path, b: Path) -> dict:
    da, db = a.read_bytes(), b.read_bytes()
    ea, eb = parse_events(da), parse_events(db)

    body_a, body_b = da[HEADER_LEN:], db[HEADER_LEN:]
    m = min(len(body_a), len(body_b))
    diff_body = next((i for i in range(m) if body_a[i] != body_b[i]), None)

    common_events = 0
    for xa, xb in zip(ea, eb):
        if xa.type != xb.type or xa.raw != xb.raw:
            break
        common_events += 1

    turns = sum(1 for e in ea[:common_events] if e.type == RNG_CHECK)

    prev_load = None
    for e in ea[:common_events]:
        if e.type == SAVED_GAME_LOADED:
            prev_load = {
                "event_index": e.index,
                "offset": e.offset,
                "turns_before": e.turns_before,
            }

    def describe(e):
        if e is None:
            return None
        return {
            "index": e.index,
            "offset": e.offset,
            "type": e.type,
            "raw_hex": e.raw.hex(),
            "turns_before": e.turns_before,
        }

    next_a = ea[common_events] if common_events < len(ea) else None
    next_b = eb[common_events] if common_events < len(eb) else None

    return {
        "a": str(a),
        "b": str(b),
        "body_first_different_offset": None if diff_body is None else HEADER_LEN + diff_body,
        "common_events": common_events,
        "common_rng_checks": turns,
        "last_saved_game_loaded_in_common_prefix": prev_load,
        "next_event_a": describe(next_a),
        "next_event_b": describe(next_b),
    }

def truncate_at_rng_turn(src: Path, dst: Path, target_turns: int, deepest_level_header: int | None):
    data = src.read_bytes()
    ev = parse_events(data)
    rng_seen = 0
    cut = HEADER_LEN
    for e in ev:
        cut = e.offset + len(e.raw)
        if e.type == RNG_CHECK:
            rng_seen += 1
            if rng_seen == target_turns:
                break
    else:
        raise ValueError(f"source has only {rng_seen} RNG checks, target={target_turns}")

    out = bytearray(data[:cut])
    out[24:28] = target_turns.to_bytes(4, "big")
    if deepest_level_header is not None:
        out[28:32] = deepest_level_header.to_bytes(4, "big")
    out[32:36] = len(out).to_bytes(4, "big")
    dst.write_bytes(out)

    result = inspect_file(dst)
    result["note"] = "Structurally valid truncation only. This is NOT engine replay verification."
    return result

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect")
    p.add_argument("files", nargs="+")

    p = sub.add_parser("compare")
    p.add_argument("a")
    p.add_argument("b")

    p = sub.add_parser("truncate")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--turn", type=int, required=True)
    p.add_argument("--deepest-level-header", type=int)

    args = ap.parse_args()
    if args.cmd == "inspect":
        print(json.dumps([inspect_file(Path(x)) for x in args.files], indent=2))
    elif args.cmd == "compare":
        print(json.dumps(compare_files(Path(args.a), Path(args.b)), indent=2))
    else:
        print(json.dumps(
            truncate_at_rng_turn(Path(args.src), Path(args.dst), args.turn, args.deepest_level_header),
            indent=2,
        ))

if __name__ == "__main__":
    main()
