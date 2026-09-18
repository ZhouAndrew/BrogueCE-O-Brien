#!/usr/bin/env python3
from pathlib import Path
p=Path("src/brogue/Recordings.c")
s=p.read_text()

old='''            case RNG_CHECK:
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;'''
new=r'''            case RNG_CHECK:
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
                    && rogue.playerTurnNumber == 3
                    && recordingLocation == 54) {
                    unsigned long skipped = 0;
                    unsigned char nextType;
                    do {
                        unsigned char payload = recallChar();
                        skipped++;
                        printf("SKIP53 checkpoint=%u afterTurn=%li loc=%li\n",
                               (unsigned) payload, rogue.playerTurnNumber, recordingLocation);
                        nextType = recallChar();
                    } while (nextType == RNG_CHECK);
                    locationInRecordingBuffer--;
                    recordingLocation--;
                    printf("SKIP53 done count=%lu next=%u loc=%li\n",
                           skipped, (unsigned) nextType, recordingLocation);
                    fflush(stdout);
                    tryAgain = true;
                    break;
                }
                // fall through
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;'''
if old not in s: raise SystemExit("recall anchor missing")
s=s.replace(old,new,1)

old='''    if (rogue.playbackMode) {
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);'''
new='''    if (rogue.playbackMode) {
        printf("SKIP53 OOS expect turn=%li loc=%li current=%lu\\n",
               rogue.playerTurnNumber, recordingLocation, x);
        fflush(stdout);
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);
        printf("SKIP53 OOS read event=%u recorded=%lu loc=%li\\n",
               (unsigned) eventType, recordedNumber, recordingLocation);
        fflush(stdout);'''
if old not in s: raise SystemExit("oos anchor missing")
s=s.replace(old,new,1)

old='''static void playbackPanic() {

    if (!rogue.playbackOOS) {'''
new='''static void playbackPanic() {
    if (getenv("OBRIEN_SKIP53_DIAG")) {
        printf("SKIP53 PANIC turn=%li depth=%i hp=%i/%i loc=%li\\n",
               rogue.playerTurnNumber, rogue.depthLevel,
               player.currentHP, player.info.maxHP, recordingLocation);
        fflush(stdout);
        exit(92);
    }

    if (!rogue.playbackOOS) {'''
if old not in s: raise SystemExit("panic anchor missing")
s=s.replace(old,new,1)
p.write_text(s)
