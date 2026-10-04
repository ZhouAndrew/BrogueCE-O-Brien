#!/usr/bin/env python3
from pathlib import Path
p=Path("forensic_reencode_legacy_save.py")
s=p.read_text()
old="""old = '''    rogue.patchVersion          = 0;

    if (rogue.playbackMode) {'''
new = '''    rogue.patchVersion          = 0;

    if (rogue.playbackMode) {
        const char *migrationPath = getenv(\"OBRIEN_MIGRATE_OUTPUT\");"""
new="""old = '''    rogue.patchVersion          = 0;
    // v0.2.34: reset replay/live mapping boundary for each recording session.
    obrienAutoMapContinuation = false;

    if (rogue.playbackMode) {'''
new = '''    rogue.patchVersion          = 0;
    // v0.2.34: reset replay/live mapping boundary for each recording session.
    obrienAutoMapContinuation = false;

    if (rogue.playbackMode) {
        const char *migrationPath = getenv(\"OBRIEN_MIGRATE_OUTPUT\");"""
if old not in s:
    raise SystemExit("forensic updater anchor text not found")
p.write_text(s.replace(old,new,1))
print("made forensic reencoder v0.2.36-init compatible")
