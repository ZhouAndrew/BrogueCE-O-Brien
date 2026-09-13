#!/usr/bin/env python3
from pathlib import Path

p = Path('src/brogue/RogueMain.c')
s = p.read_text(encoding='utf-8')
old = '''void executeEvent(rogueEvent *theEvent) {
    rogue.playbackBetweenTurns = false;
    if (theEvent->eventType == KEYSTROKE) {
        executeKeystroke(theEvent->param1, theEvent->controlKey, theEvent->shiftKey);'''
new = '''void executeEvent(rogueEvent *theEvent) {
    rogue.playbackBetweenTurns = false;
    if (theEvent->eventType == KEYSTROKE) {
        if (rogue.playbackMode
            && gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
            && rogue.playerTurnNumber == 2
            && theEvent->param1 == 'k') {
            printf("FORENSIC THIRD_K before stairs turn=%li depth=%i pos=%i,%i down=%i,%i\\n",
                   rogue.playerTurnNumber, rogue.depthLevel,
                   player.loc.x, player.loc.y, rogue.downLoc.x, rogue.downLoc.y);
            fflush(stdout);
            useStairs(1);
            printf("FORENSIC THIRD_K after stairs turn=%li depth=%i pos=%i,%i oos=%i ended=%i\\n",
                   rogue.playerTurnNumber, rogue.depthLevel,
                   player.loc.x, player.loc.y, rogue.playbackOOS, rogue.gameHasEnded);
            fflush(stdout);
            return;
        }
        executeKeystroke(theEvent->param1, theEvent->controlKey, theEvent->shiftKey);'''
if old not in s:
    raise SystemExit('executeEvent anchor missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

r = Path('src/brogue/Recordings.c')
t = r.read_text(encoding='utf-8')
old = '''    if (rogue.playbackMode) {
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);'''
new = '''    if (rogue.playbackMode) {
        printf("FORENSIC OOS expect turn=%li depth=%i loc=%li value=%lu\\n",
               rogue.playerTurnNumber, rogue.depthLevel, recordingLocation, x);
        fflush(stdout);
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);
        printf("FORENSIC OOS read event=%u recorded=%lu loc=%li\\n",
               (unsigned) eventType, recordedNumber, recordingLocation);
        fflush(stdout);'''
if old not in t:
    raise SystemExit('OOS anchor missing')
r.write_text(t.replace(old, new, 1), encoding='utf-8')
print('third-k stairs probe applied')
