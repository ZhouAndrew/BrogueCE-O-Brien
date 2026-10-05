#!/usr/bin/env python3
"""Recover the verified O'Brien v0.2.37 3714-turn checkpoint from a longer save.

This repair is deliberately conservative:
- it requires the exact known recording body through byte 20541;
- it rewrites only the 36-byte recording header metadata for that checkpoint;
- it hash-locks the produced file to the known v0.2.37 repaired SHA-256;
- with --engine, it runs the supplied headless Brogue engine and requires a
  successful resume at turn 3714 plus one live turn without playback OOS.
"""
from __future__ import annotations
import argparse, hashlib, os, subprocess
from pathlib import Path

CUT = 20541
TURN = 3714
DEEPEST = 13
KNOWN_BODY_SHA = "164d1de82fdf70afbb0fb29d8be4b029e6221ec59e282f0207aa17c5863dd928"
KNOWN_OUTPUT_SHA = "1942b1142e8edacd5c70e80dfdf4b429ff836e90b8326326ae14c3e5809a3c63"

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def repair(src: Path, dst: Path) -> None:
    data = src.read_bytes()
    if len(data) < CUT:
        raise SystemExit(f"input too short: {len(data)} < {CUT}")
    prefix = bytearray(data[:CUT])
    if sha(prefix[36:]) != KNOWN_BODY_SHA:
        raise SystemExit("refusing: recording body through turn 3714 is not the verified lineage")
    if prefix[13] != 0x03 or prefix[14] != 35:
        raise SystemExit(f"refusing: expected compat=0x03 ruleset=35, got 0x{prefix[13]:02x}/{prefix[14]}")
    prefix[24:28] = TURN.to_bytes(4, "big")
    prefix[28:32] = DEEPEST.to_bytes(4, "big")
    prefix[32:36] = CUT.to_bytes(4, "big")
    out = bytes(prefix)
    if sha(out) != KNOWN_OUTPUT_SHA:
        raise SystemExit(f"internal verification failed: unexpected output SHA {sha(out)}")
    dst.write_bytes(out)
    print(f"REPAIRED path={dst} bytes={len(out)} turn={TURN} deepest={DEEPEST} sha256={sha(out)}")

def verify(engine: Path, save: Path, log: Path) -> None:
    env = os.environ.copy()
    env["OBRIEN_USER_SAVE_PROBE"] = "1"
    p = subprocess.run(
        [str(engine), "--variant", "obrien", "-o", str(save)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env,
    )
    log.write_text(p.stdout, encoding="utf-8")
    required = [
        "USER_SAVE_RESUMED turn=3714 target=3714",
        "USER_SAVE_CONTINUED turn=3715 expected=3715",
        "playback=0 recording=1 oos=0",
    ]
    bad = ["USER_SAVE_OOS", "Expected RNG output", "Playback panic"]
    ok = p.returncode == 0 and all(x in p.stdout for x in required) and not any(x in p.stdout for x in bad)
    print(p.stdout, end="")
    print(f"ENGINE_VERIFY rc={p.returncode} result={'PASS' if ok else 'FAIL'} log={log}")
    if not ok:
        raise SystemExit(2)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--engine", type=Path)
    ap.add_argument("--log", type=Path)
    args = ap.parse_args()
    repair(args.input, args.output)
    if args.engine:
        log = args.log or args.output.with_suffix(args.output.suffix + ".verify.log")
        verify(args.engine, args.output, log)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
