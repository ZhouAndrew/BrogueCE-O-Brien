#!/usr/bin/env python3
from pathlib import Path

p = Path('src/brogue/Recordings.c')
s = p.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'forensic patch anchor missing: {label}')
    s = s.replace(old, new, 1)

replace_once(
'''enum recordingSeekModes {
    RECORDING_SEEK_MODE_TURN,
    RECORDING_SEEK_MODE_DEPTH
};

static void recordChar(unsigned char c) {''',
'''enum recordingSeekModes {
    RECORDING_SEEK_MODE_TURN,
    RECORDING_SEEK_MODE_DEPTH
};

/* FORENSIC_EXTRA_TURN: one-byte logical pushback so a stray RNG_CHECK can be
 * handed back to playerTurnEnded()->RNGCheck()->OOSCheck(). */
static int forensicPushedChar = -1;

static void recordChar(unsigned char c) {''',
'enum')

replace_once(
'''static unsigned char recallChar() {
    unsigned char c;
    if (recordingLocation > lengthOfPlaybackFile) {
        return END_OF_RECORDING;
    }
    c = inputRecordBuffer[locationInRecordingBuffer++];
    recordingLocation++;
    if (locationInRecordingBuffer >= INPUT_RECORD_BUFFER) {
        fillBufferFromFile();
    }
    return c;
}
''',
'''static unsigned char recallChar() {
    unsigned char c;
    if (forensicPushedChar >= 0) {
        c = (unsigned char) forensicPushedChar;
        forensicPushedChar = -1;
        recordingLocation++;
        return c;
    }
    if (recordingLocation > lengthOfPlaybackFile) {
        return END_OF_RECORDING;
    }
    c = inputRecordBuffer[locationInRecordingBuffer++];
    recordingLocation++;
    if (locationInRecordingBuffer >= INPUT_RECORD_BUFFER) {
        fillBufferFromFile();
    }
    return c;
}

static void forensicPushBackChar(unsigned char c) {
    if (forensicPushedChar >= 0) {
        printf("FORENSIC ERROR double pushback at loc=%li\\n", recordingLocation);
        playbackPanic();
        return;
    }
    forensicPushedChar = c;
    if (recordingLocation > 0) recordingLocation--;
}
''',
'recallChar')

replace_once(
'''            case RNG_CHECK:
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;''',
'''            case RNG_CHECK:
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                    short savedRNG = rogue.RNG;
                    printf("FORENSIC stray RNG_CHECK -> full playerTurnEnded before: turn=%li depth=%i hp=%i loc=%li\\n",
                           rogue.playerTurnNumber, rogue.depthLevel, player.currentHP, recordingLocation - 1);
                    fflush(stdout);
                    forensicPushBackChar(c);
                    rogue.RNG = RNG_SUBSTANTIVE;
                    playerTurnEnded();
                    rogue.RNG = savedRNG;
                    printf("FORENSIC after extra playerTurnEnded: turn=%li depth=%i hp=%i ended=%i oos=%i loc=%li\\n",
                           rogue.playerTurnNumber, rogue.depthLevel, player.currentHP,
                           rogue.gameHasEnded, rogue.playbackOOS, recordingLocation);
                    fflush(stdout);
                    tryAgain = true;
                    break;
                }
                // fall through for non-O'Brien variants
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;''',
'recallEvent RNG')

replace_once(
'''    locationInRecordingBuffer   = 0;
    positionInPlaybackFile      = 0;
    recordingLocation           = 0;
    maxLevelChanges             = 0;''',
'''    locationInRecordingBuffer   = 0;
    positionInPlaybackFile      = 0;
    recordingLocation           = 0;
    forensicPushedChar          = -1;
    maxLevelChanges             = 0;''',
'init reset')

replace_once(
'''    if (rogue.playbackMode) {
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);''',
'''    if (rogue.playbackMode) {
        printf("FORENSIC OOS expect turn=%li depth=%i loc=%li value=%lu\\n",
               rogue.playerTurnNumber, rogue.depthLevel, recordingLocation, x);
        fflush(stdout);
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);
        printf("FORENSIC OOS read event=%u recorded=%lu loc=%li\\n",
               (unsigned) eventType, recordedNumber, recordingLocation);
        fflush(stdout);''',
'OOS')

p.write_text(s, encoding='utf-8')
print('forensic extra-turn patch applied')
