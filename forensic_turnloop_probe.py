#!/usr/bin/env python3
from pathlib import Path

p = Path('src/brogue/Time.c')
s = p.read_text(encoding='utf-8')

old = '''void playerTurnEnded() {
    short soonestTurn, damage, turnsRequiredToShore, turnsToShore;
    char buf[COLS], buf2[COLS];
    boolean fastForward = false;
    short oldRNG;'''
new = '''void playerTurnEnded() {
    short soonestTurn, damage, turnsRequiredToShore, turnsToShore;
    char buf[COLS], buf2[COLS];
    boolean fastForward = false;
    short oldRNG;
    int forensicLoopIteration = 0;

    if (rogue.playbackMode && rogue.playerTurnNumber <= 3) {
        printf("TURNLOOP enter pturn=%li abs=%li par=%i ticks=%i loc=%li\\n",
               rogue.playerTurnNumber, rogue.absoluteTurnNumber,
               player.status[STATUS_PARALYZED], player.ticksUntilTurn,
               recordingLocation);
        fflush(stdout);
    }'''
if old not in s:
    raise SystemExit('playerTurnEnded header anchor missing')
s = s.replace(old, new, 1)

old = '''    do {
        if (rogue.gameHasEnded) {
            return;
        }

        if (!player.status[STATUS_PARALYZED]) {'''
new = '''    do {
        forensicLoopIteration++;
        if (rogue.playbackMode && rogue.playerTurnNumber <= 3) {
            printf("TURNLOOP iter-begin n=%i pturn=%li abs=%li par=%i ticks=%i rngCount=%lu loc=%li\\n",
                   forensicLoopIteration, rogue.playerTurnNumber,
                   rogue.absoluteTurnNumber, player.status[STATUS_PARALYZED],
                   player.ticksUntilTurn, randomNumbersGenerated,
                   recordingLocation);
            fflush(stdout);
        }
        if (rogue.gameHasEnded) {
            return;
        }

        if (!player.status[STATUS_PARALYZED]) {'''
if old not in s:
    raise SystemExit('do-loop begin anchor missing')
s = s.replace(old, new, 1)

old = '''        if (player.currentHP > player.info.maxHP) {
            player.currentHP = player.info.maxHP;
        }

        if (player.bookkeepingFlags & MB_IS_FALLING) {'''
new = '''        if (player.currentHP > player.info.maxHP) {
            player.currentHP = player.info.maxHP;
        }

        if (rogue.playbackMode && rogue.playerTurnNumber <= 3) {
            printf("TURNLOOP iter-end n=%i pturn=%li abs=%li par=%i ticks=%i rngCount=%lu falling=%i loc=%li\\n",
                   forensicLoopIteration, rogue.playerTurnNumber,
                   rogue.absoluteTurnNumber, player.status[STATUS_PARALYZED],
                   player.ticksUntilTurn, randomNumbersGenerated,
                   !!(player.bookkeepingFlags & MB_IS_FALLING),
                   recordingLocation);
            fflush(stdout);
        }

        if (player.bookkeepingFlags & MB_IS_FALLING) {'''
if old not in s:
    raise SystemExit('loop end anchor missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('turn-loop probe applied')
