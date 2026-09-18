#!/usr/bin/env python3
from pathlib import Path
p=Path("src/brogue/Items.c")
s=p.read_text(encoding="utf-8")

old='''    if (theItem == NULL) {
        return;
    }

    confirmMessages();
    switch (theItem->category) {'''
new='''    if (theItem == NULL) {
        return;
    }

    if (rogue.playbackMode && rogue.playerTurnNumber >= 1915 && rogue.playerTurnNumber <= 1930) {
        printf("T1922 APPLY turn=%li depth=%i letter=%c category=%u kind=%i charges=%i enchant1=%i enchant2=%i origin=%i flags=%lu qty=%i\\n",
               rogue.playerTurnNumber, rogue.depthLevel, theItem->inventoryLetter,
               (unsigned) theItem->category, theItem->kind, theItem->charges,
               theItem->enchant1, theItem->enchant2, theItem->originDepth,
               theItem->flags, theItem->quantity);
        fflush(stdout);
    }

    confirmMessages();
    switch (theItem->category) {'''
if old not in s: raise SystemExit("apply selection anchor missing")
s=s.replace(old,new,1)

old='''        case CHARM:
            if (useCharm(theItem)) {
                break;
            }
            return;'''
new='''        case CHARM: {
            boolean obrienCharmUsed = useCharm(theItem);
            if (rogue.playbackMode && rogue.playerTurnNumber >= 1915 && rogue.playerTurnNumber <= 1930) {
                printf("T1922 CHARM_RESULT turn=%li letter=%c kind=%i used=%i charges_after=%i enchant2=%i\\n",
                       rogue.playerTurnNumber, theItem->inventoryLetter, theItem->kind,
                       obrienCharmUsed, theItem->charges, theItem->enchant2);
                fflush(stdout);
            }
            if (obrienCharmUsed) {
                break;
            }
            return;
        }'''
if old not in s: raise SystemExit("charm case anchor missing")
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
print("turn1922 item diagnostics applied")
