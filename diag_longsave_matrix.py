#!/usr/bin/env python3
from pathlib import Path

p = Path("src/brogue/Recordings.c")
s = p.read_text(encoding="utf-8")

old = """static void playbackPanic() {

    if (!rogue.playbackOOS) {"""
new = """static void playbackPanic() {

    if (getenv("OBRIEN_MATRIX_DIAG")) {
        printf("MATRIX_OOS turn=%li depth=%i hp=%i/%i loc=%li len=%lu\\n",
               rogue.playerTurnNumber, rogue.depthLevel,
               player.currentHP, player.info.maxHP,
               recordingLocation, lengthOfPlaybackFile);
        fflush(stdout);
        exit(92);
    }

    if (!rogue.playbackOOS) {"""
if old not in s:
    raise SystemExit("playbackPanic anchor missing")
s = s.replace(old, new, 1)

old = """    if (!rogue.gameHasEnded && !rogue.playbackOOS) {
        switchToPlaying();
        recordChar(SAVED_GAME_LOADED);
    }
    return true;
}"""
new = """    if (getenv("OBRIEN_MATRIX_DIAG")) {
        printf("MATRIX_END turn=%li target=%li depth=%i deepest=%i hp=%i/%i ended=%i oos=%i loc=%li len=%lu\\n",
               rogue.playerTurnNumber, rogue.howManyTurns,
               rogue.depthLevel, rogue.deepestLevel,
               player.currentHP, player.info.maxHP,
               rogue.gameHasEnded, rogue.playbackOOS,
               recordingLocation, lengthOfPlaybackFile);
        fflush(stdout);
        exit((rogue.playerTurnNumber == rogue.howManyTurns
              && player.currentHP > 0
              && !rogue.gameHasEnded
              && !rogue.playbackOOS) ? 0 : 93);
    }

    if (!rogue.gameHasEnded && !rogue.playbackOOS) {
        switchToPlaying();
        recordChar(SAVED_GAME_LOADED);
    }
    return true;
}"""
if old not in s:
    raise SystemExit("loadSavedGame end anchor missing")
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("matrix diagnostic patch applied")
