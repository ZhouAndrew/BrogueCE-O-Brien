#!/usr/bin/env python3
from pathlib import Path

p = Path("src/brogue/Recordings.c")
s = p.read_text(encoding="utf-8")

old = """static void playbackPanic() {

    if (!rogue.playbackOOS) {"""
new = """static void playbackPanic() {

    if (getenv("OBRIEN_USER_SAVE_PROBE")) {
        printf("USER_SAVE_OOS turn=%li depth=%i hp=%i/%i loc=%li len=%lu\\n",
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

        if (getenv("OBRIEN_USER_SAVE_PROBE")) {
            const unsigned long savedTurnTarget = rogue.howManyTurns;
            printf("USER_SAVE_RESUMED turn=%li target=%lu depth=%i deepest=%i "
                   "hp=%i/%i playback=%i recording=%i oos=%i loc=%li len=%lu\\n",
                   rogue.playerTurnNumber, savedTurnTarget,
                   rogue.depthLevel, rogue.deepestLevel,
                   player.currentHP, player.info.maxHP,
                   rogue.playbackMode, rogue.recording, rogue.playbackOOS,
                   recordingLocation, lengthOfPlaybackFile);
            fflush(stdout);

            if (rogue.playerTurnNumber != savedTurnTarget
                || rogue.playbackMode
                || !rogue.recording
                || rogue.playbackOOS
                || player.currentHP <= 0) {
                exit(93);
            }

            rogue.justRested = true;
            recordKeystroke(REST_KEY, false, false);
            playerTurnEnded();
            flushBufferToFile();

            printf("USER_SAVE_CONTINUED turn=%li expected=%lu depth=%i hp=%i/%i "
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
print("generic user-save replay probe applied")
