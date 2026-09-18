#!/usr/bin/env python3
from pathlib import Path
p=Path("src/brogue/Recordings.c")
s=p.read_text(encoding="utf-8")
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
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                    // O'Brien v0.2.24-v0.2.28 Call Security consumed a turn but
                    // failed to record its C keystroke. Leave the checkpoint
                    // untouched so executing the reconstructed C action consumes
                    // and validates it through the normal OOSCheck path.
                    if (locationInRecordingBuffer == 0 || recordingLocation == 0) {
                        printf("OBRIEN C-REPLAY cannot rewind checkpoint at buffer boundary.\n");
                        playbackPanic();
                        return;
                    }
                    locationInRecordingBuffer--;
                    recordingLocation--;
                    event->eventType = KEYSTROKE;
                    event->param1 = CREATE_ITEM_MONSTER_KEY;
                    event->param2 = 0;
                    event->controlKey = false;
                    event->shiftKey = false;
                    printf("OBRIEN C-REPLAY synthetic C turn=%li depth=%i checkpointLoc=%li\n",
                           rogue.playerTurnNumber, rogue.depthLevel, recordingLocation);
                    fflush(stdout);
                    return;
                }
                // fall through for other variants
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;'''
if old not in s: raise SystemExit("recallEvent RNG anchor missing")
p.write_text(s.replace(old,new,1),encoding="utf-8")
print("missing Call Security replay shim applied")
