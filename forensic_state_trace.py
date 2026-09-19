#!/usr/bin/env python3
from pathlib import Path

def rep(path, old, new, label):
    p=Path(path); s=p.read_text()
    if old not in s:
        raise SystemExit(f"anchor missing: {label}")
    p.write_text(s.replace(old,new,1))
    print("patched",label)

rep("src/brogue/Monsters.c",
'''    security = obrienFindLivingCrew("Security Hologram");
    if (security != NULL) {''',
'''    security = obrienFindLivingCrew("Security Hologram");
    printf("TRACE_C enter turn=%li abs=%li depth=%i active=%i suspended=%i storedHP=%i L=%i P=%i\\n",
           rogue.playerTurnNumber, rogue.absoluteTurnNumber, rogue.depthLevel,
           security != NULL, obrienSecuritySuspended, obrienSecurityStoredIntegrity,
           obrienSecurityLightningCharges, obrienSecurityPoisonCharges);
    fflush(stdout);
    if (security != NULL) {
        printf("TRACE_C action=DEACTIVATE hp=%i\\n", security->currentHP);
        fflush(stdout);''',
"trace C enter")

rep("src/brogue/Monsters.c",
'''    security = generateMonster(MK_GOLEM, false, false);
    if (security == NULL) {
        message("Call Security failed: holographic emitter unavailable.", 0);
        return false;
    }''',
'''    security = generateMonster(MK_GOLEM, false, false);
    if (security == NULL) {
        printf("TRACE_C action=FAIL_GENERATE turn=%li\\n", rogue.playerTurnNumber);
        fflush(stdout);
        message("Call Security failed: holographic emitter unavailable.", 0);
        return false;
    }''',
"trace C generate fail")

rep("src/brogue/Monsters.c",
'''    if (!coordinatesAreInMap(security->loc.x, security->loc.y)) {
        killCreature(security, true);
        message("Call Security failed: no safe holographic projection point nearby.", 0);
        return false;
    }''',
'''    if (!coordinatesAreInMap(security->loc.x, security->loc.y)) {
        printf("TRACE_C action=FAIL_LOCATION turn=%li candidate=(%i,%i)\\n",
               rogue.playerTurnNumber, security->loc.x, security->loc.y);
        fflush(stdout);
        killCreature(security, true);
        message("Call Security failed: no safe holographic projection point nearby.", 0);
        return false;
    }''',
"trace C location fail")

rep("src/brogue/Monsters.c",
'''    pmapAt(security->loc)->flags |= HAS_MONSTER;
    refreshDungeonCell(security->loc);
    obrienBindSecurityRuntime(security);''',
'''    pmapAt(security->loc)->flags |= HAS_MONSTER;
    refreshDungeonCell(security->loc);
    obrienBindSecurityRuntime(security);
    printf("TRACE_C action=DEPLOY turn=%li loc=(%i,%i) hp=%i L=%i P=%i\\n",
           rogue.playerTurnNumber, security->loc.x, security->loc.y, security->currentHP,
           obrienSecurityLightningCharges, obrienSecurityPoisonCharges);
    fflush(stdout);''',
"trace C deploy")

rep("src/brogue/Items.c",
'''    target = promptForItemOfType(STAFF, 0, 0,
                                 KEYBOARD_LABELS ? "Transfer emergency power to which staff? (a-z; or <esc> to cancel)" : "Transfer emergency power to which staff?",
                                 true);''',
'''    if (rogue.playerTurnNumber >= 1880 && rogue.playerTurnNumber <= 1960) {
        printf("TRACE_CELL turn=%li cell=%c reserve=%i eligible-staffs:", rogue.playerTurnNumber,
               cell->inventoryLetter, cell->charges);
        for (item *ti = packItems->nextItem; ti != NULL; ti = ti->nextItem) {
            if (ti->category & STAFF) {
                printf(" %c[k=%i ch=%i cap=%i org=%i]", ti->inventoryLetter, ti->kind,
                       ti->charges, staffChargeCapacity(ti), ti->originDepth);
            }
        }
        printf("\\n");
        fflush(stdout);
    }
    target = promptForItemOfType(STAFF, 0, 0,
                                 KEYBOARD_LABELS ? "Transfer emergency power to which staff? (a-z; or <esc> to cancel)" : "Transfer emergency power to which staff?",
                                 true);''',
"trace power cell target list")

rep("src/brogue/Items.c",
'''    if (theItem == NULL) {
        return;
    }

    confirmMessages();
    switch (theItem->category) {''',
'''    if (theItem == NULL) {
        printf("TRACE_APPLY turn=%li result=NULL\\n", rogue.playerTurnNumber);
        fflush(stdout);
        return;
    }

    if (rogue.playerTurnNumber >= 1880 && rogue.playerTurnNumber <= 1960) {
        printf("TRACE_APPLY turn=%li letter=%c category=%u kind=%i charges=%i ench1=%i ench2=%i origin=%i flags=%lu\\n",
               rogue.playerTurnNumber, theItem->inventoryLetter, theItem->category, theItem->kind,
               theItem->charges, theItem->enchant1, theItem->enchant2, theItem->originDepth,
               theItem->flags);
        fflush(stdout);
    }

    confirmMessages();
    switch (theItem->category) {''',
"trace apply item")

print("forensic state trace patch applied")
