#!/usr/bin/env python3
"""CI-only acceptance probe for the repaired 3727-turn O'Brien save.

This instrumentation is never part of apply_obrien_mod_v0_2_29.py. It makes a
headless CI load fail fast on OOS, verifies loadSavedGame reaches the exact saved
state, verifies Brogue switches back into live recording mode, then executes one
ordinary REST turn to prove the repaired save can continue at turn 3728.
"""

from pathlib import Path

p = Path("src/brogue/Recordings.c")
s = p.read_text(encoding="utf-8")

old = """static void playbackPanic() {

    if (!rogue.playbackOOS) {"""
new = """static void playbackPanic() {

    if (getenv("OBRIEN_CI_LONGSAVE")) {
        printf("LONGSAVE_OOS turn=%li depth=%i hp=%i/%i loc=%li len=%lu\\n",
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
new = """    if (!rogue.gameHasEnded && !rogue.playbackOOS) {
        switchToPlaying();
        recordChar(SAVED_GAME_LOADED);

        if (getenv("OBRIEN_CI_LONGSAVE")) {
            const unsigned long savedTurnTarget = rogue.howManyTurns;

            printf("LONGSAVE_RESUMED turn=%li target=%lu depth=%i deepest=%i "
                   "hp=%i/%i playback=%i recording=%i oos=%i loc=%li len=%lu\\n",
                   rogue.playerTurnNumber, savedTurnTarget,
                   rogue.depthLevel, rogue.deepestLevel,
                   player.currentHP, player.info.maxHP,
                   rogue.playbackMode, rogue.recording, rogue.playbackOOS,
                   recordingLocation, lengthOfPlaybackFile);
            fflush(stdout);

            if (rogue.playerTurnNumber != savedTurnTarget
                || rogue.depthLevel != 14
                || rogue.deepestLevel != 14
                || player.currentHP != 40
                || player.info.maxHP != 40
                || rogue.playbackMode
                || !rogue.recording
                || rogue.playbackOOS) {
                exit(93);
            }

            rogue.justRested = true;
            recordKeystroke(REST_KEY, false, false);
            playerTurnEnded();
            flushBufferToFile();

            printf("LONGSAVE_CONTINUED turn=%li expected=%lu depth=%i hp=%i/%i "
                   "playback=%i recording=%i oos=%i\\n",
                   rogue.playerTurnNumber, savedTurnTarget + 1,
                   rogue.depthLevel, player.currentHP, player.info.maxHP,
                   rogue.playbackMode, rogue.recording, rogue.playbackOOS);
            fflush(stdout);

            exit((rogue.playerTurnNumber == savedTurnTarget + 1
                  && player.currentHP > 0
                  && !rogue.playbackMode
                  && rogue.recording
                  && !rogue.playbackOOS) ? 0 : 94);
        }
    }
    return true;
}"""
if old not in s:
    raise SystemExit("loadSavedGame terminal anchor missing")
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("CI long-save resume probe applied")
