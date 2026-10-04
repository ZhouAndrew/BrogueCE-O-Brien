#!/usr/bin/env python3
from pathlib import Path

p = Path("src/brogue/Recordings.c")
s = p.read_text(encoding="utf-8")

def repl(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f"general migration anchor missing: {label}")
    s = s.replace(old, new, 1)

# Preserve O'Brien compatibility/ruleset bytes in the regenerated recording.
repl(
'''    for (short i = 0; i < 15 && rogue.versionString[i]; i++) {
        header[i] = (unsigned char) rogue.versionString[i];
    }
    header[15] = 0x80 | ((gameVariant & 0x07) << 4) | (rogue.mode & 0x0F);''',
'''    for (short i = 0; i < 15 && rogue.versionString[i]; i++) {
        header[i] = (unsigned char) rogue.versionString[i];
    }
    header[OBRIEN_COMPAT_HEADER_INDEX] = obrienCompatibilityFlags;
    header[OBRIEN_RULESET_HEADER_INDEX] = obrienRulesetVersion;
    header[15] = 0x80 | ((gameVariant & 0x07) << 4) | (rogue.mode & 0x0F);''',
"preserve O'Brien header state")

# Pair source RNG markers with current-engine turns. A source checkpoint with
# no unmatched current checkpoint means the historical action consumed a turn
# but the current interpretation did not; materialize a REST to keep turn/time
# structure exact and make the regenerated recording replayable.
repl(
'''static unsigned long obrienMigrationEventCount = 0;
static unsigned long obrienMigrationGeneratedChecks = 0;''',
'''static unsigned long obrienMigrationEventCount = 0;
static unsigned long obrienMigrationGeneratedChecks = 0;
static unsigned long obrienMigrationUnmatchedGeneratedChecks = 0;
static boolean obrienMigrationNextGeneratedCheckAlreadyPaired = false;
static unsigned long obrienMigrationSourceChecks = 0;''',
"migration pairing state")

repl(
'''        obrienMigrationEventCount = 0;
        obrienMigrationGeneratedChecks = 0;''',
'''        obrienMigrationEventCount = 0;
        obrienMigrationGeneratedChecks = 0;
        obrienMigrationUnmatchedGeneratedChecks = 0;
        obrienMigrationNextGeneratedCheckAlreadyPaired = false;
        obrienMigrationSourceChecks = 0;''',
"reset pairing state")

repl(
'''            obrienMigrationRecordChar(RNG_CHECK);
            obrienMigrationRecordNumber(x, numberOfBytes);
            obrienMigrationGeneratedChecks++;
            return;''',
'''            obrienMigrationRecordChar(RNG_CHECK);
            obrienMigrationRecordNumber(x, numberOfBytes);
            obrienMigrationGeneratedChecks++;
            if (obrienMigrationNextGeneratedCheckAlreadyPaired) {
                obrienMigrationNextGeneratedCheckAlreadyPaired = false;
            } else {
                obrienMigrationUnmatchedGeneratedChecks++;
            }

            // A diverged current-engine automatic action can continue for many
            // turns without asking recallEvent() for another source input.
            // The source save's declared target turn is authoritative for the
            // recovered continuation, so finalize exactly at that boundary.
            if (rogue.playerTurnNumber == rogue.howManyTurns) {
                obrienMigrationFinalize();
                exit(0);
            }
            if (rogue.playerTurnNumber > rogue.howManyTurns) {
                fprintf(stderr, "MIGRATION overshot target turn: %li > %li\\n",
                        rogue.playerTurnNumber, rogue.howManyTurns);
                exit(98);
            }
            return;''',
"pair generated checks")

old_case = '''            case RNG_CHECK:
                if (obrienMigrationActive) {
                    unsigned long runLength = 1;
                    (void) recallNumber(1); // legacy RNG payload
                    while (recordingLocation < lengthOfPlaybackFile) {
                        unsigned char nextType = recallChar();
                        if (nextType == RNG_CHECK) {
                            (void) recallNumber(1);
                            runLength++;
                        } else {
                            // One-byte pushback is safe here: recallChar just consumed it.
                            locationInRecordingBuffer--;
                            recordingLocation--;
                            break;
                        }
                    }
                    obrienMigrationLegacyRuns++;
                    if (runLength > 1) {
                        obrienMigrationPendingRests += runLength - 1;
                        obrienMigrationPendingRests--;
                        obrienMigrationInsertedRests++;
                        event->eventType = KEYSTROKE;
                        event->param1 = REST_KEY;
                        event->param2 = 0;
                        event->controlKey = false;
                        event->shiftKey = false;
                        obrienMigrationRecordEventData(event);
                        return;
                    }
                    tryAgain = true;
                    break;
                }
                // normal playback treats RNG_CHECK here as an error'''
new_case = '''            case RNG_CHECK:
                if (obrienMigrationActive) {
                    (void) recallNumber(1); // source RNG payload is structural only
                    obrienMigrationLegacyRuns++;
                    obrienMigrationSourceChecks++;

                    if (obrienMigrationUnmatchedGeneratedChecks > 0) {
                        // The preceding current-engine action consumed a turn;
                        // this source checkpoint is its historical counterpart.
                        obrienMigrationUnmatchedGeneratedChecks--;
                        tryAgain = true;
                        break;
                    }

                    // Historical turn existed, but the same input is now a no-op
                    // (or an old custom action was absent from the stream).
                    // Preserve the one-turn passage explicitly with a REST.
                    obrienMigrationInsertedRests++;
                    obrienMigrationNextGeneratedCheckAlreadyPaired = true;
                    event->eventType = KEYSTROKE;
                    event->param1 = REST_KEY;
                    event->param2 = 0;
                    event->controlKey = false;
                    event->shiftKey = false;
                    obrienMigrationRecordEventData(event);
                    return;
                }
                // normal playback treats RNG_CHECK here as an error'''
repl(old_case, new_case, "general source checkpoint pairing")

# Preserve historical save/load markers in the new stream because ruleset-35
# replay semantics deliberately use them as deterministic state boundaries.
repl(
'''            case SAVED_GAME_LOADED:
                tryAgain = true;
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {''',
'''            case SAVED_GAME_LOADED:
                tryAgain = true;
                if (obrienMigrationActive) {
                    obrienMigrationRecordChar(SAVED_GAME_LOADED);
                }
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {''',
"preserve saved-game boundary")

# Enrich final diagnostics.
repl(
r'''bytes=%lu events=%lu generatedChecks=%lu legacyRuns=%lu insertedRests=%lu sourceLoc=%li sourceLen=%lu\n''',
r'''bytes=%lu events=%lu generatedChecks=%lu sourceChecks=%lu unmatched=%lu legacyRuns=%lu insertedRests=%lu sourceLoc=%li sourceLen=%lu\n''',
"final diagnostic format")
repl(
'''           RECORDING_HEADER_LENGTH + obrienMigrationLength,
           obrienMigrationEventCount, obrienMigrationGeneratedChecks,
           obrienMigrationLegacyRuns, obrienMigrationInsertedRests,
           recordingLocation, lengthOfPlaybackFile);''',
'''           RECORDING_HEADER_LENGTH + obrienMigrationLength,
           obrienMigrationEventCount, obrienMigrationGeneratedChecks,
           obrienMigrationSourceChecks, obrienMigrationUnmatchedGeneratedChecks,
           obrienMigrationLegacyRuns, obrienMigrationInsertedRests,
           recordingLocation, lengthOfPlaybackFile);''',
"final diagnostic args")

# General acceptance for this user's 3714-turn source: preserve turn count,
# finish alive, consume all source checkpoints, and leave no unpaired generated
# turn. The final current state may differ from the historical simulation where
# old semantics were not reproducible, but the output itself must be strict.
repl(
'''        if (rogue.playerTurnNumber == rogue.howManyTurns
            && rogue.playerTurnNumber == 3727
            && player.currentHP > 0
            && !rogue.gameHasEnded
            && !rogue.playbackOOS
            && obrienMigrationLegacyRuns == 3691
            && obrienMigrationInsertedRests == 37) {''',
'''        if (rogue.playerTurnNumber == rogue.howManyTurns
            && rogue.playerTurnNumber == 3714
            && player.currentHP > 0
            && !rogue.gameHasEnded
            && !rogue.playbackOOS
            && obrienMigrationSourceChecks == 3714
            && obrienMigrationGeneratedChecks == 3714
            && obrienMigrationUnmatchedGeneratedChecks == 0) {''',
"general 3714 acceptance")

p.write_text(s, encoding="utf-8")
print("general 3714 migration pairing patch applied")
