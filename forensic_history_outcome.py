#!/usr/bin/env python3
from pathlib import Path

p = Path('src/brogue/Recordings.c')
s = p.read_text(encoding='utf-8')

old = '''static void playbackPanic() {\n\n    if (!rogue.playbackOOS) {'''
new = '''static void playbackPanic() {\n\n    printf("FORENSIC_OOS turn=%li depth=%i hp=%i/%i ended=%i oos=%i loc=%li len=%lu\\n",\n           rogue.playerTurnNumber, rogue.depthLevel, player.currentHP, player.info.maxHP,\n           rogue.gameHasEnded, rogue.playbackOOS, recordingLocation, lengthOfPlaybackFile);\n    fflush(stdout);\n    exit(92);\n\n    if (!rogue.playbackOOS) {'''
if old not in s:
    raise SystemExit('history diagnostic anchor missing: playbackPanic')
s = s.replace(old, new, 1)

old = '''    if (!rogue.gameHasEnded && !rogue.playbackOOS) {\n        switchToPlaying();\n        recordChar(SAVED_GAME_LOADED);\n    }\n    return true;\n}'''
new = '''    printf("FORENSIC_END turn=%li target=%li depth=%i deepest=%i hp=%i/%i ended=%i oos=%i loc=%li len=%lu\\n",\n           rogue.playerTurnNumber, rogue.howManyTurns, rogue.depthLevel, rogue.deepestLevel,\n           player.currentHP, player.info.maxHP, rogue.gameHasEnded, rogue.playbackOOS,\n           recordingLocation, lengthOfPlaybackFile);\n    fflush(stdout);\n    if (rogue.playerTurnNumber == rogue.howManyTurns\n        && player.currentHP > 0\n        && !rogue.gameHasEnded\n        && !rogue.playbackOOS) {\n        exit(0);\n    }\n    exit(93);\n\n    if (!rogue.gameHasEnded && !rogue.playbackOOS) {\n        switchToPlaying();\n        recordChar(SAVED_GAME_LOADED);\n    }\n    return true;\n}'''
if old not in s:
    raise SystemExit('history diagnostic anchor missing: loadSavedGame end')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('historical replay outcome diagnostics applied')
