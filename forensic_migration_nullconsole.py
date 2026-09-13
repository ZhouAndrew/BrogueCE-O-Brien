#!/usr/bin/env python3
from pathlib import Path
p = Path('src/platform/main.c')
s = p.read_text(encoding='utf-8')
old = '''    rogue.nextGame = NG_NOTHING;
    rogue.nextGamePath[0] = '\\0';
    rogue.nextGameSeed = 0;
    rogue.mode = GAME_MODE_NORMAL;'''
new = '''    rogue.nextGame = NG_NOTHING;
    rogue.nextGamePath[0] = '\\0';
    rogue.nextGameSeed = 0;
    rogue.mode = GAME_MODE_NORMAL;

    // The forensic save re-encoder must run through the real NG_OPEN_GAME /
    // loadSavedGame path, but it needs no SDL renderer or user interaction.
    if (getenv("OBRIEN_MIGRATE_OUTPUT")) {
        currentConsole = nullConsole;
        nonInteractivePlayback = true;
    }'''
if old not in s:
    raise SystemExit('null-console migration anchor missing')
p.write_text(s.replace(old,new,1), encoding='utf-8')
print('migration null-console patch applied')
