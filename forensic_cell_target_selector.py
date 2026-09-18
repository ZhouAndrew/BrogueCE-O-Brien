#!/usr/bin/env python3
from pathlib import Path
p=Path("src/brogue/Items.c")
s=p.read_text(encoding="utf-8")
old='''    target = promptForItemOfType(STAFF, 0, 0,
                                 KEYBOARD_LABELS ? "Transfer emergency power to which staff? (a-z; or <esc> to cancel)" : "Transfer emergency power to which staff?",
                                 true);
    if (!target) {
        return false;
    }'''
new='''    if (rogue.playbackMode && getenv("OBRIEN_FORENSIC_CELL_TARGETS")) {
        static unsigned long obrienForensicCellUseIndex = 0;
        const char *targets = getenv("OBRIEN_FORENSIC_CELL_TARGETS");
        char targetLetter = targets[obrienForensicCellUseIndex];
        if (!targetLetter) {
            printf("CELL_TARGET missing choice at use=%lu turn=%li\\n",
                   obrienForensicCellUseIndex, rogue.playerTurnNumber);
            fflush(stdout);
            return false;
        }
        obrienForensicCellUseIndex++;
        target = itemOfPackLetter(targetLetter);
        printf("CELL_TARGET use=%lu turn=%li cell=%c target=%c found=%i",
               obrienForensicCellUseIndex, rogue.playerTurnNumber,
               cell->inventoryLetter, targetLetter, target != NULL);
        if (target) {
            printf(" category=%u kind=%i charges=%i cap=%i enchant=%i\\n",
                   (unsigned) target->category, target->kind, target->charges,
                   staffChargeCapacity(target), target->enchant1);
        } else {
            printf("\\n");
        }
        fflush(stdout);
    } else {
        target = promptForItemOfType(STAFF, 0, 0,
                                     KEYBOARD_LABELS ? "Transfer emergency power to which staff? (a-z; or <esc> to cancel)" : "Transfer emergency power to which staff?",
                                     true);
    }
    if (!target) {
        return false;
    }'''
if old not in s: raise SystemExit("power cell target anchor missing")
p.write_text(s.replace(old,new,1),encoding="utf-8")
print("forensic power-cell target selector applied")
