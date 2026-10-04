#!/usr/bin/env python3
from pathlib import Path

p = Path("forensic_reencode_legacy_save.py")
s = p.read_text(encoding="utf-8")

old_anchor = """old = '''    rogue.patchVersion          = 0;

    if (rogue.playbackMode) {'''"""
new_anchor = """old = '''    rogue.patchVersion          = 0;
    // v0.2.34: reset replay/live mapping boundary for each recording session.
    obrienAutoMapContinuation = false;

    if (rogue.playbackMode) {'''"""

if old_anchor not in s:
    raise SystemExit("forensic updater old-anchor literal not found")

s = s.replace(old_anchor, new_anchor, 1)
p.write_text(s, encoding="utf-8")
print("made forensic reencoder v0.2.36-init compatible")
