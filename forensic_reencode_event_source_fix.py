#!/usr/bin/env python3
"""Fix the one-shot save re-encoder so recallEvent is the sole event source.

The legacy recording is authoritative for user input. During playback those
inputs are returned by recallEvent(); they are not guaranteed to pass through
recordEvent() again. Synthetic migration REST events also return directly from
recallEvent(). Therefore migrated input must be emitted exactly there, while
OOSCheck remains responsible only for current-engine RNG_CHECK records.

Apply after forensic_reencode_legacy_save.py.
"""
from pathlib import Path

p = Path('src/brogue/Recordings.c')
s = p.read_text(encoding='utf-8')


def repl(old: str, new: str, label: str) -> None:
    global s
    if old not in s:
        raise SystemExit(f'event-source fix anchor missing: {label}')
    s = s.replace(old, new, 1)


# Add explicit diagnostics. These counts make the final forensic acceptance
# self-describing rather than relying on a green build badge.
repl(
    '''static unsigned long obrienMigrationLegacyRuns = 0;\nstatic unsigned long obrienMigrationInsertedRests = 0;\n''',
    '''static unsigned long obrienMigrationLegacyRuns = 0;\nstatic unsigned long obrienMigrationInsertedRests = 0;\nstatic unsigned long obrienMigrationEventCount = 0;\nstatic unsigned long obrienMigrationGeneratedChecks = 0;\n''',
    'diagnostic counters',
)

# recordEvent must retain normal playback semantics. If a replayed command
# happens to call one of the recording helpers internally, mirroring here would
# duplicate the authoritative event already emitted by recallEvent().
old = '''    if (rogue.playbackMode) {\n        if (obrienMigrationActive) {\n            obrienMigrationRecordChar((unsigned char) event->eventType);\n            if (event->eventType == KEYSTROKE) {\n                c = compressKeystroke(event->param1);\n                if (c == UNKNOWN_KEY) return;\n                obrienMigrationRecordChar(c);\n            } else {\n                obrienMigrationRecordChar((unsigned char) event->param1);\n                obrienMigrationRecordChar((unsigned char) event->param2);\n            }\n            c = 0;\n            if (event->controlKey) c += Fl(1);\n            if (event->shiftKey) c += Fl(2);\n            obrienMigrationRecordChar(c);\n        }\n        return;\n    }\n'''
new = '''    if (rogue.playbackMode) {\n        return;\n    }\n'''
repl(old, new, 'disable recordEvent mirroring')

repl(
    '''    if (rogue.playbackMode && !obrienMigrationActive) {\n        return;\n    }\n\n    theEvent.eventType = KEYSTROKE;''',
    '''    if (rogue.playbackMode) {\n        return;\n    }\n\n    theEvent.eventType = KEYSTROKE;''',
    'restore recordKeystroke playback guard',
)

repl(
    '''void recordMouseClick(short x, short y, boolean controlKey, boolean shiftKey) {\n    rogueEvent theEvent;\n\n    if (rogue.playbackMode && !obrienMigrationActive) {\n        return;\n    }\n''',
    '''void recordMouseClick(short x, short y, boolean controlKey, boolean shiftKey) {\n    rogueEvent theEvent;\n\n    if (rogue.playbackMode) {\n        return;\n    }\n''',
    'restore recordMouseClick playback guard',
)

repl(
    '''void cancelKeystroke() {\n    if (rogue.playbackMode && obrienMigrationActive) {\n        brogueAssert(obrienMigrationLength >= 3);\n        obrienMigrationLength -= 3;\n        return;\n    }\n    brogueAssert(locationInRecordingBuffer >= 3);\n    locationInRecordingBuffer -= 3; // a keystroke is encoded into 3 bytes\n    recordingLocation -= 3;\n}''',
    '''void cancelKeystroke() {\n    brogueAssert(locationInRecordingBuffer >= 3);\n    locationInRecordingBuffer -= 3; // a keystroke is encoded into 3 bytes\n    recordingLocation -= 3;\n}''',
    'restore cancelKeystroke',
)

# The helper is deliberately placed after compressKeystroke/recordNumber are
# available. It serializes exactly the event recallEvent hands to the engine.
anchor = '''static void obrienMigrationFinalize(void) {\n'''
helper = r'''static void obrienMigrationRecordEventData(const rogueEvent *event) {
    unsigned char c;

    if (!obrienMigrationActive) {
        return;
    }

    obrienMigrationRecordChar((unsigned char) event->eventType);
    if (event->eventType == KEYSTROKE) {
        c = compressKeystroke(event->param1);
        if (c == UNKNOWN_KEY) {
            fprintf(stderr, "MIGRATION cannot encode keystroke %li\n", event->param1);
            exit(96);
        }
        obrienMigrationRecordChar(c);
    } else {
        obrienMigrationRecordChar((unsigned char) event->param1);
        obrienMigrationRecordChar((unsigned char) event->param2);
    }

    c = 0;
    if (event->controlKey) c += Fl(1);
    if (event->shiftKey) c += Fl(2);
    obrienMigrationRecordChar(c);
    obrienMigrationEventCount++;
}

'''
repl(anchor, helper + anchor, 'event serialization helper')

# Count current-engine checks as they are written into the new stream.
repl(
    '''            obrienMigrationRecordChar(RNG_CHECK);\n            obrienMigrationRecordNumber(x, numberOfBytes);\n            return;''',
    '''            obrienMigrationRecordChar(RNG_CHECK);\n            obrienMigrationRecordNumber(x, numberOfBytes);\n            obrienMigrationGeneratedChecks++;\n            return;''',
    'generated RNG counter',
)

# Reset new diagnostics with the rest of the migration state.
repl(
    '''        obrienMigrationLegacyRuns = 0;\n        obrienMigrationInsertedRests = 0;\n''',
    '''        obrienMigrationLegacyRuns = 0;\n        obrienMigrationInsertedRests = 0;\n        obrienMigrationEventCount = 0;\n        obrienMigrationGeneratedChecks = 0;\n''',
    'reset diagnostics',
)

# A pending synthetic REST is itself part of the migrated recording.
repl(
    '''        event->controlKey = false;\n        event->shiftKey = false;\n        return;\n    }\n\n    do {\n''',
    '''        event->controlKey = false;\n        event->shiftKey = false;\n        obrienMigrationRecordEventData(event);\n        return;\n    }\n\n    do {\n''',
    'record pending synthetic rest',
)

# Same for the first REST materialized immediately from a multi-check run.
repl(
    '''                        event->controlKey = false;\n                        event->shiftKey = false;\n                        return;\n                    }\n                    tryAgain = true;\n''',
    '''                        event->controlKey = false;\n                        event->shiftKey = false;\n                        obrienMigrationRecordEventData(event);\n                        return;\n                    }\n                    tryAgain = true;\n''',
    'record first synthetic rest',
)

# Normal legacy events are emitted only after their modifier byte has been
# consumed, preserving the exact semantic input that the engine executes.
repl(
    '''    event->controlKey = (c & Fl(1)) ? true : false;\n    event->shiftKey =   (c & Fl(2)) ? true : false;\n}\n\nstatic void loadNextAnnotation()''',
    '''    event->controlKey = (c & Fl(1)) ? true : false;\n    event->shiftKey =   (c & Fl(2)) ? true : false;\n    if (obrienMigrationActive) {\n        obrienMigrationRecordEventData(event);\n    }\n}\n\nstatic void loadNextAnnotation()''',
    'record recalled legacy event',
)

# Enrich the final line so a CI run can prove what actually happened. Match
# only the stable tail of the C format string so Python escape depth cannot
# make this anchor brittle again.
repl(
    r'bytes=%lu legacyRuns=%lu insertedRests=%lu sourceLoc=%li sourceLen=%lu\n',
    r'bytes=%lu events=%lu generatedChecks=%lu legacyRuns=%lu insertedRests=%lu sourceLoc=%li sourceLen=%lu\n',
    'final diagnostic format',
)
repl(
    '''           RECORDING_HEADER_LENGTH + obrienMigrationLength,\n           obrienMigrationLegacyRuns, obrienMigrationInsertedRests,\n           recordingLocation, lengthOfPlaybackFile);''',
    '''           RECORDING_HEADER_LENGTH + obrienMigrationLength,\n           obrienMigrationEventCount, obrienMigrationGeneratedChecks,\n           obrienMigrationLegacyRuns, obrienMigrationInsertedRests,\n           recordingLocation, lengthOfPlaybackFile);''',
    'final diagnostic args',
)

# This is a forensic one-shot for the known 3727-turn file, so reject a merely
# survivable but structurally incomplete migration.
repl(
    '''        if (rogue.playerTurnNumber == rogue.howManyTurns\n            && player.currentHP > 0\n            && !rogue.gameHasEnded\n            && !rogue.playbackOOS) {''',
    '''        if (rogue.playerTurnNumber == rogue.howManyTurns\n            && rogue.playerTurnNumber == 3727\n            && player.currentHP > 0\n            && !rogue.gameHasEnded\n            && !rogue.playbackOOS\n            && obrienMigrationLegacyRuns == 3691\n            && obrienMigrationInsertedRests == 37) {''',
    'strict forensic acceptance',
)

p.write_text(s, encoding='utf-8')
print('migration event-source fix applied')
