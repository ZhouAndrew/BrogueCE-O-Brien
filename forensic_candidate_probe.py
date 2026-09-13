#!/usr/bin/env python3
from pathlib import Path

p = Path('src/brogue/Recordings.c')
s = p.read_text(encoding='utf-8')

old = '''            case RNG_CHECK:
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;'''
new = r'''            case RNG_CHECK:
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
                    && rogue.playerTurnNumber == 3
                    && recordingLocation == 54) {
                    const char *action = getenv("OBRIEN_FORENSIC_ACTION");
                    if (!action) action = "turn";

                    // recallEvent has consumed only the RNG_CHECK event byte. Put
                    // it back so the candidate action's real OOSCheck sees the
                    // untouched 06 0b checkpoint at byte offset 53.
                    if (locationInRecordingBuffer > 0 && recordingLocation > 0) {
                        locationInRecordingBuffer--;
                        recordingLocation--;
                    }

                    printf("CANDIDATE begin action=%s turn=%li depth=%i loc=%li hp=%i/%i pos=%i,%i ticks=%i nutrition=%i justRested=%i justSearched=%i auto=%i cautious=%i disturbed=%i awareness=%i\n",
                           action, rogue.playerTurnNumber, rogue.depthLevel,
                           recordingLocation, player.currentHP, player.info.maxHP,
                           player.loc.x, player.loc.y, player.ticksUntilTurn,
                           player.status[STATUS_NUTRITION], rogue.justRested,
                           rogue.justSearched, rogue.automationActive,
                           rogue.cautiousMode, rogue.disturbed, rogue.awarenessBonus);
                    fflush(stdout);

                    if (!strcmp(action, "turn")) {
                        playerTurnEnded();
                    } else if (!strcmp(action, "rest")) {
                        rogue.justRested = true;
                        playerTurnEnded();
                    } else if (!strcmp(action, "rest2")) {
                        rogue.justRested = true;
                        playerTurnEnded();
                        if (!rogue.gameHasEnded && !rogue.playbackOOS) {
                            rogue.justRested = true;
                            playerTurnEnded();
                        }
                    } else if (!strcmp(action, "searched")) {
                        rogue.justSearched = true;
                        playerTurnEnded();
                    } else if (!strcmp(action, "automation")) {
                        rogue.automationActive = true;
                        playerTurnEnded();
                    } else if (!strcmp(action, "cautious")) {
                        rogue.cautiousMode = true;
                        playerTurnEnded();
                    } else if (!strcmp(action, "undisturbed")) {
                        rogue.disturbed = false;
                        playerTurnEnded();
                    } else if (!strcmp(action, "search30")) {
                        search(30);
                        rogue.justSearched = true;
                        playerTurnEnded();
                    } else if (!strcmp(action, "search60")) {
                        search(60);
                        rogue.justSearched = true;
                        playerTurnEnded();
                    } else if (!strcmp(action, "search160")) {
                        search(160);
                        rogue.justSearched = true;
                        playerTurnEnded();
                    } else if (!strncmp(action, "move", 4) && strlen(action) == 5
                               && action[4] >= '0' && action[4] <= '7') {
                        playerMoves(action[4] - '0');
                    } else if (!strncmp(action, "run", 3) && strlen(action) == 4
                               && action[3] >= '0' && action[3] <= '7') {
                        playerRuns(action[3] - '0');
                    } else {
                        printf("CANDIDATE unknown action=%s\n", action);
                    }

                    printf("CANDIDATE end action=%s turn=%li depth=%i loc=%li hp=%i/%i pos=%i,%i ended=%i oos=%i\n",
                           action, rogue.playerTurnNumber, rogue.depthLevel,
                           recordingLocation, player.currentHP, player.info.maxHP,
                           player.loc.x, player.loc.y, rogue.gameHasEnded,
                           rogue.playbackOOS);
                    fflush(stdout);
                    exit(0);
                }
                // fall through outside the exact first legacy gap
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;'''
if old not in s:
    raise SystemExit('candidate recallEvent anchor missing')
s = s.replace(old, new, 1)

old = '''    if (rogue.playbackMode) {
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);
        if (eventType != RNG_CHECK || recordedNumber != x) {'''
new = '''    if (rogue.playbackMode) {
        printf("CANDIDATE OOS before turn=%li loc=%li current=%lu\\n",
               rogue.playerTurnNumber, recordingLocation, x);
        fflush(stdout);
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);
        printf("CANDIDATE OOS read turn=%li event=%u recorded=%lu loc=%li\\n",
               rogue.playerTurnNumber, (unsigned) eventType, recordedNumber,
               recordingLocation);
        fflush(stdout);
        if (eventType != RNG_CHECK || recordedNumber != x) {'''
if old not in s:
    raise SystemExit('candidate OOS anchor missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('candidate action probe applied')
