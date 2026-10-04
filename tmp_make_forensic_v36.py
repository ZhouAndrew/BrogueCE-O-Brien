#!/usr/bin/env python3
from pathlib import Path
p=Path("forensic_reencode_legacy_save.py")
s=p.read_text()
old="""old = '''    rogue.patchVersion          = 0;

    if (rogue.playbackMode) {'''
new="""old = '''    rogue.patchVersion          = 0;
    // v0.2.34: reset replay/live mapping boundary for each recording session.
    obrienAutoMapContinuation = false;

    if (rogue.playbackMode) {'''
if new in s:
    print("forensic reencoder already v0.2.36-init compatible")
elif old in s:
    s=s.replace(old,new,1)
    p.write_text(s)
    print("made forensic reencoder v0.2.36-init compatible")
else:
    raise SystemExit("forensic updater anchor text not found")
