#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.5 to a clean Brogue CE 1.15.1 tree.

v0.2.5 includes v0.2.4 and finishes the field-kit behavior discussed for the
O'Brien variant:
- permanent Starfleet/tricorder recognition of item *types* (not full magical stats);
- stairhead caches reliably deploy on first visit to designated supply depths;
- firebolt and lightning staffs start at 20/20;
- blinking staff starts at 10/10 and is capped to a 20-space blink range;
- Bashir has permanent flight/levitation so terrain does not make the medic fall behind.

The changes remain scoped to O'Brien Must Survive unless noted otherwise.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_4.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_4.py next to this updater.")

runpy.run_path(str(PREVIOUS_PATCH), run_name="__main__")


def replace_once(rel, old, new, marker=None):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"patched {rel}")
        return
    if marker and marker in text:
        print(f"already patched {rel}")
        return
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.4 source was not found.")


# Permanent field analysis means O'Brien can tell WHAT an object is. It does not
# grant omniscient knowledge of hidden enchantments, runics or curses on ordinary
# dungeon equipment. Randomized potion/scroll/staff/wand/ring kinds are therefore
# known from the beginning, while Brogue's deeper per-object identification rules
# remain relevant.
replace_once(
    "src/brogue/RogueMain.c",
    """    shuffleFlavors();\n\n    for (i = 0; i < gameConst->numberFeats; i++) {""",
    """    shuffleFlavors();\n\n    if (obrienVariantActive()) {\n        // Permanent Starfleet field analysis: recognize item types, not hidden magic.\n        for (i = 0; i < gameConst->numberPotionKinds; i++) {\n            potionTable[i].identified = true;\n        }\n        for (i = 0; i < gameConst->numberScrollKinds; i++) {\n            scrollTable[i].identified = true;\n        }\n        for (i = 0; i < NUMBER_STAFF_KINDS; i++) {\n            staffTable[i].identified = true;\n        }\n        for (i = 0; i < gameConst->numberWandKinds; i++) {\n            wandTable[i].identified = true;\n        }\n        for (i = 0; i < NUMBER_RING_KINDS; i++) {\n            ringTable[i].identified = true;\n        }\n    }\n\n    for (i = 0; i < gameConst->numberFeats; i++) {""",
    "recognize item types, not hidden magic",
)

# v0.2.3 used identify(), which fully identified the individual object but did not
# reliably reveal randomized potion/scroll names. Replace that with kind recognition.
# This fixes the nonsense labels without automatically exposing enchant/runic/curse
# details on ordinary dungeon gear.
replace_once(
    "src/brogue/Items.c",
    """        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identify(theItem);\n        }\n\n        theItem = addItemToPack(theItem);\n\n        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identify(theItem);\n        }""",
    """        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identifyItemKind(theItem);\n        }\n\n        theItem = addItemToPack(theItem);\n\n        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identifyItemKind(theItem);\n        }""",
    "identifyItemKind(theItem);",
)

# Do not make stairhead logistics depend on the precise way the first visit was
# entered. Descending stairs, falling in, or another unusual first-entry path all
# still stage that depth's one-time cache beside its up stair. The visited flag
# prevents farming the same supply depth by repeatedly changing levels.
replace_once(
    "src/brogue/RogueMain.c",
    """    if (!levels[rogue.depthLevel-1].visited) {\n        if (obrienVariantActive() && stairDirection == 1) {\n            obrienFirstVisitToDepth(rogue.depthLevel, rogue.upLoc);\n        }\n        levels[rogue.depthLevel-1].visited = true;""",
    """    if (!levels[rogue.depthLevel-1].visited) {\n        if (obrienVariantActive()) {\n            obrienFirstVisitToDepth(rogue.depthLevel, rogue.upLoc);\n        }\n        levels[rogue.depthLevel-1].visited = true;""",
    "if (obrienVariantActive()) {\n            obrienFirstVisitToDepth(rogue.depthLevel, rogue.upLoc);",
)

# Requested Starfleet staff capacities. In Brogue, a staff's enchant1 is also its
# maximum charge count, so these are deliberately high-capacity mission tools.
replace_once(
    "src/brogue/RogueMain.c",
    """    obrienPlaceSupplyItem(STAFF, STAFF_BLINKING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_TUNNELING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_LIGHTNING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_FIRE, 1, 3, anchor);""",
    """    obrienPlaceSupplyItem(STAFF, STAFF_BLINKING, 1, 10, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_TUNNELING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_LIGHTNING, 1, 20, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_FIRE, 1, 20, anchor);""",
    "obrienPlaceSupplyItem(STAFF, STAFF_FIRE, 1, 20, anchor);",
)

# A 10-charge blinking staff would normally have a 22-space range because Brogue
# derives blink range from staff enchantment. The requested field unit is 10/10
# with a maximum 20-space blink, so cap only the O'Brien variant's blink formula.
replace_once(
    "src/brogue/PowerTables.c",
    "short staffBlinkDistance(fixpt enchant)        {return ((int) (2 + enchant * 2 / FP_FACTOR));}",
    """short staffBlinkDistance(fixpt enchant) {\n    short distance = (short) (2 + enchant * 2 / FP_FACTOR);\n    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n        return min(20, distance);\n    }\n    return distance;\n}""",
    "return min(20, distance);",
)

# Bashir needs to remain with O'Brien across water, chasms and awkward terrain.
# MONST_FLIES is permanent levitation; set the live status too because Bashir is
# converted from MK_YOU after generateMonster() has already initialized statuses.
replace_once(
    "src/brogue/RogueMain.c",
    """    bashir->info.flags &= ~MONST_FEMALE;\n    bashir->info.flags |= (MONST_MALE | MONST_MAINTAINS_DISTANCE);\n    bashir->info.maxHP = 36;""",
    """    bashir->info.flags &= ~MONST_FEMALE;\n    bashir->info.flags |= (MONST_MALE | MONST_MAINTAINS_DISTANCE | MONST_FLIES);\n    bashir->status[STATUS_LEVITATING] = 1000;\n    bashir->maxStatus[STATUS_LEVITATING] = 1000;\n    bashir->info.maxHP = 36;""",
    "MONST_MALE | MONST_MAINTAINS_DISTANCE | MONST_FLIES",
)

print("O'Brien Must Survive v0.2.5 applied.")
print("- Permanent field analysis recognizes item types without revealing hidden magic")
print("- Stairhead cache deploys on first visit to supply depths regardless of entry method")
print("- Firebolt: 20/20")
print("- Lightning: 20/20")
print("- Blinking: 10/10, max range 20 spaces")
print("- Bashir: permanent flight/levitation, finite HP, defensive medic behavior retained")
print("Build normally with: make -B")
