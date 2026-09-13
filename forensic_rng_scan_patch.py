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
new = '''            case RNG_CHECK:
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                    const unsigned char recordedCheck = recallChar();
                    const short savedRNG = rogue.RNG;
                    long i;
                    int hitsRecorded = 0, hits24 = 0;
                    rogue.RNG = RNG_SUBSTANTIVE;
                    printf("RNG_SCAN stray_at=%li turn=%li depth=%i recorded=%u\\n",
                           recordingLocation - 2, rogue.playerTurnNumber, rogue.depthLevel,
                           (unsigned) recordedCheck);
                    for (i = 1; i <= 4096; i++) {
                        unsigned char v = (unsigned char) rand_range(0, 255);
                        if (i <= 32) {
                            printf("RNG_SCAN draw=%li value=%u\\n", i, (unsigned) v);
                        }
                        if (v == recordedCheck && hitsRecorded < 12) {
                            printf("RNG_SCAN MATCH_RECORDED draw=%li value=%u\\n", i, (unsigned) v);
                            hitsRecorded++;
                        }
                        if (v == 24 && hits24 < 12) {
                            printf("RNG_SCAN MATCH_24 draw=%li value=%u\\n", i, (unsigned) v);
                            hits24++;
                        }
                    }
                    rogue.RNG = savedRNG;
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
if old not in s:
    raise SystemExit('RNG case anchor missing')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('forensic RNG scanner applied')
