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
                    const unsigned char recordedCheck = recallChar();
                    printf("FORENSIC STATE stray_at=%li turn=%li depth=%i recorded=%u hp=%i/%i pos=%i,%i\\n",
                           recordingLocation - 2, rogue.playerTurnNumber, rogue.depthLevel,
                           (unsigned) recordedCheck, player.currentHP, player.info.maxHP,
                           player.loc.x, player.loc.y);
                    printf("FORENSIC STATUS paralyzed=%i confused=%i entranced=%i stuck=%i levitating=%i poisoned=%i burning=%i\\n",
                           player.status[STATUS_PARALYZED], player.status[STATUS_CONFUSED],
                           player.status[STATUS_ENTRANCED], player.status[STATUS_STUCK],
                           player.status[STATUS_LEVITATING], player.status[STATUS_POISONED],
                           player.status[STATUS_BURNING]);
                    printf("FORENSIC CELL dungeon=%i liquid=%i gas=%i surface=%i flags=%lu nutrition=%i ticks=%i\\n",
                           pmapAt(player.loc)->layers[DUNGEON],
                           pmapAt(player.loc)->layers[LIQUID],
                           pmapAt(player.loc)->layers[GAS],
                           pmapAt(player.loc)->layers[SURFACE],
                           (unsigned long) pmapAt(player.loc)->flags,
                           player.status[STATUS_NUTRITION], player.ticksUntilTurn);
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
                break;''',
'recallEvent RNG')

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
print('forensic state-dump patch applied')
