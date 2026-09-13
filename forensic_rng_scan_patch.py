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
                    int hit11 = 0, hit24 = 0, hit208 = 0;
                    rogue.RNG = RNG_SUBSTANTIVE;
                    printf("RNG_SCAN stray_at=%li turn=%li depth=%i recorded=%u rngCount=%lu\\n",
                           recordingLocation - 2, rogue.playerTurnNumber, rogue.depthLevel,
                           (unsigned) recordedCheck, randomNumbersGenerated);
                    for (i = 1; i <= 4096; i++) {
                        unsigned char v = (unsigned char) rand_range(0, 255);
                        if (v == 11 && hit11 < 8) { printf("RNG_SCAN MATCH_11 draw=%li\\n", i); hit11++; }
                        if (v == 24 && hit24 < 8) { printf("RNG_SCAN MATCH_24 draw=%li\\n", i); hit24++; }
                        if (v == 208 && hit208 < 8) { printf("RNG_SCAN MATCH_208 draw=%li\\n", i); hit208++; }
                    }
                    rogue.RNG = savedRNG;
                    fflush(stdout);
                    exit(0);
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
if old not in s: raise SystemExit('RNG case anchor missing')
p.write_text(s.replace(old,new,1),encoding='utf-8')
print('RNG distance scanner applied')
