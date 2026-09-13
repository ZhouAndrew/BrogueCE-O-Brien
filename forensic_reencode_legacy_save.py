#!/usr/bin/env python3
"""Forensic one-shot legacy save re-encoder.

Applied after O'Brien v0.2.28.  When OBRIEN_MIGRATE_OUTPUT is set during
playback, the old file supplies only user input and turn-boundary structure.
The current engine writes a second, self-consistent recording stream containing
its own inputs and RNG_CHECK values.  Consecutive legacy RNG_CHECK records are
translated into explicit REST turns beyond the first checkpoint in each run.
The original file is never modified.
"""
from pathlib import Path

p = Path('src/brogue/Recordings.c')
s = p.read_text(encoding='utf-8')


def repl(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'migration patch anchor missing: {label}')
    s = s.replace(old, new, 1)

# State and raw output buffer.  Keeping this separate from Brogue's normal
# recording buffer prevents playback reads and migration writes from colliding.
anchor = '''enum recordingSeekModes {
    RECORDING_SEEK_MODE_TURN,
    RECORDING_SEEK_MODE_DEPTH
};
'''
insert = anchor + r'''

#define OBRIEN_MIGRATION_MAX_BYTES (1024 * 1024)
static boolean obrienMigrationActive = false;
static unsigned char obrienMigrationStream[OBRIEN_MIGRATION_MAX_BYTES];
static unsigned long obrienMigrationLength = 0;
static const char *obrienMigrationOutputPath = NULL;
static unsigned long obrienMigrationPendingRests = 0;
static unsigned long obrienMigrationLegacyRuns = 0;
static unsigned long obrienMigrationInsertedRests = 0;

static void obrienMigrationRecordChar(unsigned char c) {
    if (obrienMigrationLength >= OBRIEN_MIGRATION_MAX_BYTES) {
        fprintf(stderr, "MIGRATION output buffer exceeded %u bytes\n", OBRIEN_MIGRATION_MAX_BYTES);
        exit(93);
    }
    obrienMigrationStream[obrienMigrationLength++] = c;
}

static void obrienMigrationRecordNumber(unsigned long number, short numberOfBytes) {
    for (short i = numberOfBytes - 1; i >= 0; i--) {
        unsigned long divisor = 1;
        for (short j = 0; j < i; j++) divisor *= 256;
        obrienMigrationRecordChar((unsigned char) ((number / divisor) % 256));
    }
}
'''
repl(anchor, insert, 'migration state')

# Emit the final header + migrated stream.  This intentionally writes the
# v0.2.28 tagged variant byte instead of copying the legacy header.
anchor = '''static void recordNumber(unsigned long number, short numberOfBytes) {
    short i;
    unsigned char c[10];

    numberToString(number, numberOfBytes, c);
    for (i=0; i<numberOfBytes; i++) {
        recordChar(c[i]);
    }
}
'''
insert = anchor + r'''

static void obrienMigrationFinalize(void) {
    if (!obrienMigrationActive || !obrienMigrationOutputPath || !obrienMigrationOutputPath[0]) {
        return;
    }

    unsigned char header[RECORDING_HEADER_LENGTH] = {0};
    for (short i = 0; i < 15 && rogue.versionString[i]; i++) {
        header[i] = (unsigned char) rogue.versionString[i];
    }
    header[15] = 0x80 | ((gameVariant & 0x07) << 4) | (rogue.mode & 0x0F);
    numberToString(rogue.seed, 8, &header[16]);
    numberToString(rogue.playerTurnNumber, 4, &header[24]);
    numberToString(rogue.deepestLevel, 4, &header[28]);
    numberToString(RECORDING_HEADER_LENGTH + obrienMigrationLength, 4, &header[32]);

    FILE *out = fopen(obrienMigrationOutputPath, "wb");
    if (!out) {
        perror("MIGRATION fopen");
        exit(94);
    }
    fwrite(header, 1, RECORDING_HEADER_LENGTH, out);
    fwrite(obrienMigrationStream, 1, obrienMigrationLength, out);
    fclose(out);

    printf("MIGRATION_FINAL output=%s turn=%li depth=%i deepest=%i hp=%i/%i ended=%i oos=%i bytes=%lu legacyRuns=%lu insertedRests=%lu sourceLoc=%li sourceLen=%lu\n",
           obrienMigrationOutputPath, rogue.playerTurnNumber, rogue.depthLevel,
           rogue.deepestLevel, player.currentHP, player.info.maxHP,
           rogue.gameHasEnded, rogue.playbackOOS,
           RECORDING_HEADER_LENGTH + obrienMigrationLength,
           obrienMigrationLegacyRuns, obrienMigrationInsertedRests,
           recordingLocation, lengthOfPlaybackFile);
    fflush(stdout);
}
'''
repl(anchor, insert, 'migration finalize')

# During migration, actions executed by the playback engine are mirrored into
# the new stream instead of being discarded merely because playbackMode is set.
old = '''void recordEvent(rogueEvent *event) {
    unsigned char c;

    if (rogue.playbackMode) {
        return;
    }

    recordChar((unsigned char) event->eventType);'''
new = '''void recordEvent(rogueEvent *event) {
    unsigned char c;

    if (rogue.playbackMode) {
        if (obrienMigrationActive) {
            obrienMigrationRecordChar((unsigned char) event->eventType);
            if (event->eventType == KEYSTROKE) {
                c = compressKeystroke(event->param1);
                if (c == UNKNOWN_KEY) return;
                obrienMigrationRecordChar(c);
            } else {
                obrienMigrationRecordChar((unsigned char) event->param1);
                obrienMigrationRecordChar((unsigned char) event->param2);
            }
            c = 0;
            if (event->controlKey) c += Fl(1);
            if (event->shiftKey) c += Fl(2);
            obrienMigrationRecordChar(c);
        }
        return;
    }

    recordChar((unsigned char) event->eventType);'''
repl(old, new, 'recordEvent mirror')

repl('''    if (rogue.playbackMode) {
        return;
    }

    theEvent.eventType = KEYSTROKE;''', '''    if (rogue.playbackMode && !obrienMigrationActive) {
        return;
    }

    theEvent.eventType = KEYSTROKE;''', 'recordKeystroke guard')

# second identical playback guard is recordMouseClick; replace after its unique declaration
old = '''void recordMouseClick(short x, short y, boolean controlKey, boolean shiftKey) {
    rogueEvent theEvent;

    if (rogue.playbackMode) {
        return;
    }
'''
new = '''void recordMouseClick(short x, short y, boolean controlKey, boolean shiftKey) {
    rogueEvent theEvent;

    if (rogue.playbackMode && !obrienMigrationActive) {
        return;
    }
'''
repl(old, new, 'recordMouseClick guard')

old = '''void cancelKeystroke() {
    brogueAssert(locationInRecordingBuffer >= 3);
    locationInRecordingBuffer -= 3; // a keystroke is encoded into 3 bytes
    recordingLocation -= 3;
}'''
new = '''void cancelKeystroke() {
    if (rogue.playbackMode && obrienMigrationActive) {
        brogueAssert(obrienMigrationLength >= 3);
        obrienMigrationLength -= 3;
        return;
    }
    brogueAssert(locationInRecordingBuffer >= 3);
    locationInRecordingBuffer -= 3; // a keystroke is encoded into 3 bytes
    recordingLocation -= 3;
}'''
repl(old, new, 'cancelKeystroke migration')

# Activate only on explicit environment request.
old = '''    rogue.patchVersion          = 0;

    if (rogue.playbackMode) {'''
new = '''    rogue.patchVersion          = 0;

    if (rogue.playbackMode) {
        const char *migrationPath = getenv("OBRIEN_MIGRATE_OUTPUT");
        obrienMigrationActive = (migrationPath && migrationPath[0]);
        obrienMigrationOutputPath = migrationPath;
        obrienMigrationLength = 0;
        obrienMigrationPendingRests = 0;
        obrienMigrationLegacyRuns = 0;
        obrienMigrationInsertedRests = 0;
    }

    if (rogue.playbackMode) {'''
repl(old, new, 'init migration activation')

# Current-engine RNG checks become the checks in the new stream.  They do not
# consume legacy checks; recallEvent handles those solely as structural markers.
old = '''    if (rogue.playbackMode) {
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);'''
new = '''    if (rogue.playbackMode) {
        if (obrienMigrationActive) {
            obrienMigrationRecordChar(RNG_CHECK);
            obrienMigrationRecordNumber(x, numberOfBytes);
            return;
        }
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);'''
repl(old, new, 'OOSCheck migration')

# At input boundaries, one legacy RNG record corresponds to the turn already
# generated by the preceding action.  Any additional consecutive RNG records
# are materialized as explicit REST turns in the migrated recording.
old = '''void recallEvent(rogueEvent *event) {
    unsigned char c;
    boolean tryAgain;

    do {
        tryAgain = false;
        c = recallChar();'''
new = '''void recallEvent(rogueEvent *event) {
    unsigned char c;
    boolean tryAgain;

    if (obrienMigrationActive && obrienMigrationPendingRests > 0) {
        obrienMigrationPendingRests--;
        obrienMigrationInsertedRests++;
        event->eventType = KEYSTROKE;
        event->param1 = REST_KEY;
        event->param2 = 0;
        event->controlKey = false;
        event->shiftKey = false;
        return;
    }

    do {
        tryAgain = false;
        c = recallChar();'''
repl(old, new, 'recallEvent pending rest')

old = '''            case RNG_CHECK:
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:'''
new = '''            case RNG_CHECK:
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
                        return;
                    }
                    tryAgain = true;
                    break;
                }
                // normal playback treats RNG_CHECK here as an error
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:'''
repl(old, new, 'recallEvent legacy RNG runs')

# In migration mode the synthetic event already has modifiers.  Normal events
# still consume their modifier byte from the legacy stream.
old = '''    // record the modifier keys
    c = recallChar();
    event->controlKey = (c & Fl(1)) ? true : false;
    event->shiftKey =   (c & Fl(2)) ? true : false;
}'''
new = '''    // record the modifier keys
    c = recallChar();
    event->controlKey = (c & Fl(1)) ? true : false;
    event->shiftKey =   (c & Fl(2)) ? true : false;
}'''
# no textual change needed; synthetic rest returns early above

# Finalize instead of switching to play.  The process exits after writing so it
# cannot accidentally append SAVED_GAME_LOADED or mutate the source save.
old = '''    if (!rogue.gameHasEnded && !rogue.playbackOOS) {
        switchToPlaying();
        recordChar(SAVED_GAME_LOADED);
    }
    return true;
}'''
new = '''    if (obrienMigrationActive) {
        obrienMigrationFinalize();
        if (rogue.playerTurnNumber == rogue.howManyTurns
            && player.currentHP > 0
            && !rogue.gameHasEnded
            && !rogue.playbackOOS) {
            exit(0);
        }
        exit(95);
    }

    if (!rogue.gameHasEnded && !rogue.playbackOOS) {
        switchToPlaying();
        recordChar(SAVED_GAME_LOADED);
    }
    return true;
}'''
repl(old, new, 'loadSavedGame finalize')

p.write_text(s, encoding='utf-8')
print('legacy save re-encoder patch applied')
