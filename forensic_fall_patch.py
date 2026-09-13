#!/usr/bin/env python3
from pathlib import Path

rec = Path('src/brogue/Recordings.c')
time = Path('src/brogue/Time.c')
rs = rec.read_text(encoding='utf-8')
ts = time.read_text(encoding='utf-8')

# Keep the real static playerFalls() untouched. Export only a thin forensic wrapper.
anchor = '''    rogue.flareCount = 0;
}



void activateMachine(short machineNumber) {'''
repl = '''    rogue.flareCount = 0;
}

void forensicPlayerFalls(void) {
    playerFalls();
}

void activateMachine(short machineNumber) {'''
if anchor not in ts:
    raise SystemExit('playerFalls wrapper anchor missing')
ts = ts.replace(anchor, repl, 1)
time.write_text(ts, encoding='utf-8')

anchor = '''            case RNG_CHECK:
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;'''
repl = '''            case RNG_CHECK:
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                    extern void forensicPlayerFalls(void);
                    printf("FORENSIC FALL begin stray_at=%li turn=%li depth=%i hp=%i pos=%i,%i\\n",
                           recordingLocation - 1, rogue.playerTurnNumber, rogue.depthLevel,
                           player.currentHP, player.loc.x, player.loc.y);
                    fflush(stdout);
                    // Return the RNG event byte to the stream. This probe runs at offset 53,
                    // well inside the current 1000-byte buffer, so physical one-byte rewind is safe.
                    locationInRecordingBuffer--;
                    recordingLocation--;
                    forensicPlayerFalls();
                    printf("FORENSIC FALL end turn=%li depth=%i hp=%i loc=%li oos=%i ended=%i\\n",
                           rogue.playerTurnNumber, rogue.depthLevel, player.currentHP,
                           recordingLocation, rogue.playbackOOS, rogue.gameHasEnded);
                    fflush(stdout);
                    exit(0);
                }
                // fall through for non-O'Brien variants
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;'''
if anchor not in rs:
    raise SystemExit('recallEvent RNG anchor missing')
rs = rs.replace(anchor, repl, 1)

anchor = '''    if (rogue.playbackMode) {
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);'''
repl = '''    if (rogue.playbackMode) {
        printf("FORENSIC OOS expect turn=%li depth=%i loc=%li value=%lu\\n",
               rogue.playerTurnNumber, rogue.depthLevel, recordingLocation, x);
        fflush(stdout);
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);
        printf("FORENSIC OOS read event=%u recorded=%lu loc=%li\\n",
               (unsigned) eventType, recordedNumber, recordingLocation);
        fflush(stdout);'''
if anchor not in rs:
    raise SystemExit('OOS anchor missing')
rs = rs.replace(anchor, repl, 1)
rec.write_text(rs, encoding='utf-8')
print('forensic fall patch applied')
