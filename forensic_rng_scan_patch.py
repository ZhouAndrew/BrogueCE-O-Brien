#!/usr/bin/env python3
from pathlib import Path

# 1) When recallEvent sees the first unexpected RNG_CHECK, scan the current
# substantive RNG stream forward without pretending this is a production repair.
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
                    printf("RNG_SCAN stray_at=%li turn=%li depth=%i recorded=%u rngCount=%lu\\n",
                           recordingLocation - 2, rogue.playerTurnNumber, rogue.depthLevel,
                           (unsigned) recordedCheck, randomNumbersGenerated);
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

# 2) Measure substantive RNG usage in the code that runs *after* the normal
# per-turn checkpoint. This distinguishes current post-processing from logic that
# existed only in the old/dirty save-producing tree.
p = Path('src/brogue/Time.c')
s = p.read_text(encoding='utf-8')
old = '''    removeDeadMonsters();
    rogue.playbackBetweenTurns = true;
    RNGCheck();
    handleHealthAlerts();

    if (rogue.flareCount > 0) {
        animateFlares(rogue.flares, rogue.flareCount);
        rogue.flareCount = 0;
    }
    
    if (player.status[STATUS_NUTRITION] <= 1) {
        forceEatFood();
    }
}'''
new = '''    removeDeadMonsters();
    rogue.playbackBetweenTurns = true;
    if (rogue.playerTurnNumber <= 5) {
        printf("POSTCHECK stage=before_rngcheck turn=%li depth=%i count=%lu flares=%i hp=%i nutrition=%i\\n",
               rogue.playerTurnNumber, rogue.depthLevel, randomNumbersGenerated,
               rogue.flareCount, player.currentHP, player.status[STATUS_NUTRITION]);
        fflush(stdout);
    }
    RNGCheck();
    if (rogue.playerTurnNumber <= 5) {
        printf("POSTCHECK stage=after_rngcheck turn=%li depth=%i count=%lu flares=%i\\n",
               rogue.playerTurnNumber, rogue.depthLevel, randomNumbersGenerated, rogue.flareCount);
        fflush(stdout);
    }
    handleHealthAlerts();
    if (rogue.playerTurnNumber <= 5) {
        printf("POSTCHECK stage=after_health turn=%li depth=%i count=%lu flares=%i\\n",
               rogue.playerTurnNumber, rogue.depthLevel, randomNumbersGenerated, rogue.flareCount);
        fflush(stdout);
    }

    if (rogue.flareCount > 0) {
        if (rogue.playerTurnNumber <= 5) {
            printf("POSTCHECK stage=before_flares turn=%li depth=%i count=%lu flares=%i\\n",
                   rogue.playerTurnNumber, rogue.depthLevel, randomNumbersGenerated, rogue.flareCount);
            fflush(stdout);
        }
        animateFlares(rogue.flares, rogue.flareCount);
        rogue.flareCount = 0;
        if (rogue.playerTurnNumber <= 5) {
            printf("POSTCHECK stage=after_flares turn=%li depth=%i count=%lu flares=%i\\n",
                   rogue.playerTurnNumber, rogue.depthLevel, randomNumbersGenerated, rogue.flareCount);
            fflush(stdout);
        }
    }
    
    if (player.status[STATUS_NUTRITION] <= 1) {
        if (rogue.playerTurnNumber <= 5) {
            printf("POSTCHECK stage=before_forceeat turn=%li depth=%i count=%lu\\n",
                   rogue.playerTurnNumber, rogue.depthLevel, randomNumbersGenerated);
            fflush(stdout);
        }
        forceEatFood();
    }
    if (rogue.playerTurnNumber <= 5) {
        printf("POSTCHECK stage=return turn=%li depth=%i count=%lu\\n",
               rogue.playerTurnNumber, rogue.depthLevel, randomNumbersGenerated);
        fflush(stdout);
    }
}'''
if old not in s:
    raise SystemExit('playerTurnEnded post-check anchor missing')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('forensic RNG scanner + post-check counter applied')
