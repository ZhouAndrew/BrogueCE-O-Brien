#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.15 to a clean Brogue CE 1.15.1 tree.

v0.2.15 replaces O'Brien's three +12 native Recharging charms with Starfleet
Emergency Power Cells:
- three separate cells, each storing 20 charge-units;
- applying a cell transfers up to 20 units instantly to one selected staff;
- only the amount actually needed is consumed;
- cells recover only 1 unit per 100 turns by slow trickle charging;
- Wisdom and Reaping do not accelerate cell trickle charging;
- Scroll of Recharging is an external high-power source and fills cells to 20/20;
- ordinary Brogue variants keep the original Recharging charm behavior.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_14.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_14.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.14 source was not found.")


def replace_exact_count(rel, old, new, expected_count, marker=None):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count == expected_count:
        path.write_text(text.replace(old, new), encoding="utf-8")
        print(f"patched {rel} ({expected_count} occurrences)")
        return
    if count == 0 and marker and marker in text:
        print(f"already patched {rel}")
        return
    raise SystemExit(
        f"Cannot patch {rel}: expected {expected_count} occurrences, found {count}."
    )


# Shared constants. These are deliberately fixed technical limits, not enchantment
# levels: the cell is a 20-unit battery and its passive trickle charger restores
# one unit every 100 player-time turns.
replace_once(
    "src/brogue/Rogue.h",
    """enum gameVariant {\n    VARIANT_BROGUE,\n    VARIANT_RAPID_BROGUE,\n    VARIANT_BULLET_BROGUE,\n    VARIANT_OBRIEN_MUST_SURVIVE,\n    NUMBER_VARIANTS\n};""",
    """enum gameVariant {\n    VARIANT_BROGUE,\n    VARIANT_RAPID_BROGUE,\n    VARIANT_BULLET_BROGUE,\n    VARIANT_OBRIEN_MUST_SURVIVE,\n    NUMBER_VARIANTS\n};\n\n#define OBRIEN_POWER_CELL_CAPACITY 20\n#define OBRIEN_POWER_CELL_TRICKLE_TURNS 100""",
    "OBRIEN_POWER_CELL_CAPACITY",
)

# In the O'Brien variant, a Recharging charm is represented as a Starfleet
# Emergency Power Cell. Normal variants retain ordinary Brogue charm generation.
replace_once(
    "src/brogue/Items.c",
    """        case CHARM:\n            if (itemKind < 0) {\n                itemKind = chooseKind(charmTable, gameConst->numberCharmKinds);\n            }\n            theItem->charges = 0; // Charms are initially ready for use.\n            theItem->enchant1 = randClump(charmTable[itemKind].range);\n            while (rand_percent(7)) {\n                theItem->enchant1++;\n            }\n            theItem->flags |= ITEM_IDENTIFIED;\n            break;""",
    """        case CHARM:\n            if (itemKind < 0) {\n                itemKind = chooseKind(charmTable, gameConst->numberCharmKinds);\n            }\n            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && itemKind == CHARM_RECHARGING) {\n                // v0.2.15 Starfleet Emergency Power Cell: charges are stored energy,\n                // enchant2 is the passive trickle-charge progress counter.\n                theItem->charges = OBRIEN_POWER_CELL_CAPACITY;\n                theItem->enchant1 = 0;\n                theItem->enchant2 = 0;\n            } else {\n                theItem->charges = 0; // Charms are initially ready for use.\n                theItem->enchant1 = randClump(charmTable[itemKind].range);\n                while (rand_percent(7)) {\n                    theItem->enchant1++;\n                }\n            }\n            theItem->flags |= ITEM_IDENTIFIED;\n            break;""",
    "v0.2.15 Starfleet Emergency Power Cell",
)

# Inventory naming shows energy directly instead of a meaningless +enchantment
# and native charm cooldown percentage.
replace_once(
    "src/brogue/Items.c",
    """        case CHARM:\n            sprintf(root, \"%s charm%s\", charmTable[theItem->kind].name, pluralization);\n\n            if (includeDetails) {\n                sprintf(buf, \"%s%i %s\", (theItem->enchant1 < 0 ? \"\" : \"+\"), theItem->enchant1, root);\n                strcpy(root, buf);\n\n                if (theItem->charges) {\n                    sprintf(buf, \"%s %s(%i%%)\",\n                            root,\n                            grayEscapeSequence,\n                            (charmRechargeDelay(theItem->kind, theItem->enchant1) - theItem->charges) * 100 / charmRechargeDelay(theItem->kind, theItem->enchant1));\n                    strcpy(root, buf);\n                } else {\n                    strcat(root, grayEscapeSequence);\n                    strcat(root, \" (ready)\");\n                }\n            }\n            break;""",
    """        case CHARM:\n            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && theItem->kind == CHARM_RECHARGING) {\n                sprintf(root, \"Starfleet Emergency Power Cell%s\", pluralization);\n                if (includeDetails) {\n                    sprintf(buf, \"%s%s [%i/%i]\", root, grayEscapeSequence,\n                            theItem->charges, OBRIEN_POWER_CELL_CAPACITY);\n                    strcpy(root, buf);\n                }\n            } else {\n                sprintf(root, \"%s charm%s\", charmTable[theItem->kind].name, pluralization);\n\n                if (includeDetails) {\n                    sprintf(buf, \"%s%i %s\", (theItem->enchant1 < 0 ? \"\" : \"+\"), theItem->enchant1, root);\n                    strcpy(root, buf);\n\n                    if (theItem->charges) {\n                        sprintf(buf, \"%s %s(%i%%)\",\n                                root,\n                                grayEscapeSequence,\n                                (charmRechargeDelay(theItem->kind, theItem->enchant1) - theItem->charges) * 100 / charmRechargeDelay(theItem->kind, theItem->enchant1));\n                        strcpy(root, buf);\n                    } else {\n                        strcat(root, grayEscapeSequence);\n                        strcat(root, \" (ready)\");\n                    }\n                }\n            }\n            break;""",
    "Starfleet Emergency Power Cell",
)

# Explain the O'Brien-specific energy model in the item details while leaving the
# native description untouched in every other variant.
replace_once(
    "src/brogue/Items.c",
    """                case CHARM_RECHARGING:\n                    sprintf(buf2, \"\\n\\nWhen used, the charm will recharge your staffs (though not your wands or charms), after which it will recharge in %i turns. (If the charm is enchanted, it will recharge in %i turns.)\",\n                            charmRechargeDelay(theItem->kind, theItem->enchant1),\n                            charmRechargeDelay(theItem->kind, theItem->enchant1 + enchantMagnitude()));\n                    break;""",
    """                case CHARM_RECHARGING:\n                    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n                        sprintf(buf2, \"\\n\\nThis Starfleet Emergency Power Cell stores up to %i charge-units. Applying it transfers up to %i units immediately to one selected staff, consuming only the energy actually transferred. It trickle-charges at one unit per %i turns; Wisdom and Reaping do not accelerate it. A Scroll of Recharging fills it completely.\",\n                                OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_TRICKLE_TURNS);\n                    } else {\n                        sprintf(buf2, \"\\n\\nWhen used, the charm will recharge your staffs (though not your wands or charms), after which it will recharge in %i turns. (If the charm is enchanted, it will recharge in %i turns.)\",\n                                charmRechargeDelay(theItem->kind, theItem->enchant1),\n                                charmRechargeDelay(theItem->kind, theItem->enchant1 + enchantMagnitude()));\n                    }\n                    break;""",
    "A Scroll of Recharging fills it completely",
)

# Emergency discharge: one Apply action can dump the cell's available energy into
# one staff, up to that staff's maximum. This is high-power discharge, not slow
# charging during combat.
replace_once(
    "src/brogue/Items.c",
    "static boolean useCharm(item *theItem) {\n\n    if (theItem->charges > 0) {",
    r'''static boolean useObrienEmergencyPowerCell(item *cell) {
    item *target;
    short transferred;
    char buf[COLS * 3], targetName[COLS * 3];

    if (cell->charges <= 0) {
        messageWithColor("The Starfleet Emergency Power Cell is depleted; its trickle charger needs time.", &itemMessageColor, 0);
        return false;
    }

    target = promptForItemOfType(STAFF, 0, 0,
                                 KEYBOARD_LABELS ? "Transfer emergency power to which staff? (a-z; or <esc> to cancel)" : "Transfer emergency power to which staff?",
                                 true);
    if (!target) {
        return false;
    }
    if (!(target->category & STAFF)) {
        message("Emergency power can only be transferred to a staff.", 0);
        return false;
    }
    if (target->charges >= target->enchant1) {
        itemName(target, targetName, false, false, NULL);
        sprintf(buf, "Your %s is already fully charged.", targetName);
        messageWithColor(buf, &itemMessageColor, 0);
        return false;
    }

    transferred = min(cell->charges, target->enchant1 - target->charges);
    target->charges += transferred;
    cell->charges -= transferred;
    cell->enchant2 = 0; // restart the slow trickle timer after a discharge

    itemName(target, targetName, false, false, NULL);
    sprintf(buf, "Emergency power transfer: %i charge-unit%s routed to your %s. Cell reserve: %i/%i.",
            transferred, transferred == 1 ? "" : "s", targetName,
            cell->charges, OBRIEN_POWER_CELL_CAPACITY);
    messageWithColor(buf, &itemMessageColor, 0);

    rogue.featRecord[FEAT_PURE_WARRIOR] = false;
    recordApplyItemCommand(cell);
    return true;
}

static boolean useCharm(item *theItem) {

    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && theItem->kind == CHARM_RECHARGING) {
        return useObrienEmergencyPowerCell(theItem);
    }

    if (theItem->charges > 0) {''',
    "useObrienEmergencyPowerCell",
)

# Scroll of Recharging is an external high-power source. Native Brogue charms
# become ready (charges=0); O'Brien power cells instead become physically full.
replace_once(
    "src/brogue/Items.c",
    """        if (tempItem->category & categories & CHARM) {\n            z++;\n            tempItem->charges = 0;\n        }""",
    """        if (tempItem->category & categories & CHARM) {\n            z++;\n            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && tempItem->kind == CHARM_RECHARGING) {\n                tempItem->charges = OBRIEN_POWER_CELL_CAPACITY;\n                tempItem->enchant2 = 0;\n            } else {\n                tempItem->charges = 0;\n            }\n        }""",
    "tempItem->charges = OBRIEN_POWER_CELL_CAPACITY",
)

# Never let the ordinary charm-cooldown machinery reinterpret stored cell energy
# as cooldown turns. This also keeps Wisdom/Reaping from changing cell charge.
replace_once(
    "src/brogue/Time.c",
    """        } else if ((theItem->category & CHARM) && (theItem->charges > 0)) {\n            theItem->charges = clamp(theItem->charges - multiplier, 0, charmRechargeDelay(theItem->kind, theItem->enchant1));""",
    """        } else if ((theItem->category & CHARM) && (theItem->charges > 0)\n                   && !(gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && theItem->kind == CHARM_RECHARGING)) {\n            theItem->charges = clamp(theItem->charges - multiplier, 0, charmRechargeDelay(theItem->kind, theItem->enchant1));""",
    "&& !(gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && theItem->kind == CHARM_RECHARGING)",
)

# Passive trickle charging is intentionally tied only to elapsed player-time. It
# bypasses ringWisdomMultiplier and rechargeItemsIncrementally(), so Wisdom and
# Reaping cannot turn the emergency battery into a miniature reactor.
replace_once(
    "src/brogue/Time.c",
    "void playerTurnEnded() {\n    short soonestTurn, damage, turnsRequiredToShore, turnsToShore;",
    r'''static void obrienTrickleChargeEmergencyPowerCells(void) {
    item *theItem;
    char itemNameBuf[DCOLS * 3], buf[DCOLS * 3];

    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE) {
        return;
    }

    for (theItem = packItems->nextItem; theItem != NULL; theItem = theItem->nextItem) {
        if ((theItem->category & CHARM) && theItem->kind == CHARM_RECHARGING) {
            if (theItem->charges >= OBRIEN_POWER_CELL_CAPACITY) {
                theItem->charges = OBRIEN_POWER_CELL_CAPACITY;
                theItem->enchant2 = 0;
                continue;
            }

            theItem->enchant2++;
            if (theItem->enchant2 >= OBRIEN_POWER_CELL_TRICKLE_TURNS) {
                theItem->enchant2 = 0;
                theItem->charges++;
                if (theItem->charges >= OBRIEN_POWER_CELL_CAPACITY) {
                    theItem->charges = OBRIEN_POWER_CELL_CAPACITY;
                    itemName(theItem, itemNameBuf, false, false, NULL);
                    sprintf(buf, "your %s is fully charged.", itemNameBuf);
                    message(buf, 0);
                }
            }
        }
    }
}

void playerTurnEnded() {
    short soonestTurn, damage, turnsRequiredToShore, turnsToShore;''',
    "obrienTrickleChargeEmergencyPowerCells",
)

replace_once(
    "src/brogue/Time.c",
    """        rogue.absoluteTurnNumber++;\n\n        if (player.status[STATUS_INVISIBLE]) {""",
    """        rogue.absoluteTurnNumber++;\n        obrienTrickleChargeEmergencyPowerCells();\n\n        if (player.status[STATUS_INVISIBLE]) {""",
    "obrienTrickleChargeEmergencyPowerCells();",
)

# O'Brien starts with three independent full 20-unit emergency batteries instead
# of three +12 cooldown-based Recharging charms.
replace_once(
    "src/brogue/RogueMain.c",
    "static void obrienLoadStartingPack(void) {",
    r'''static void obrienAddEmergencyPowerCellToPack(void) {
    item *cell = generateItem(CHARM, CHARM_RECHARGING);

    if (!cell) {
        return;
    }

    cell->quantity = 1;
    cell->flags &= ~ITEM_CURSED;
    cell->charges = OBRIEN_POWER_CELL_CAPACITY;
    cell->enchant1 = 0;
    cell->enchant2 = 0;
    identifyItemKind(cell);
    identify(cell);
    addItemToPack(cell);
}

static void obrienLoadStartingPack(void) {''',
    "obrienAddEmergencyPowerCellToPack",
)

replace_exact_count(
    "src/brogue/RogueMain.c",
    "    obrienAddMissionItemToPack(CHARM, CHARM_RECHARGING, 12);\n",
    "    obrienAddEmergencyPowerCellToPack();\n",
    3,
    "v0.2.15 emergency power cells",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.14\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.15\\n\");",
    "O'Brien Must Survive v0.2.15",
)

# Stable marker for CI/idempotence after the three replacements above.
replace_once(
    "src/brogue/RogueMain.c",
    "    obrienAddEmergencyPowerCellToPack();\n    obrienAddEmergencyPowerCellToPack();\n    obrienAddEmergencyPowerCellToPack();",
    "    obrienAddEmergencyPowerCellToPack();\n    obrienAddEmergencyPowerCellToPack();\n    obrienAddEmergencyPowerCellToPack(); // v0.2.15 emergency power cells",
    "v0.2.15 emergency power cells",
)

print("O'Brien Must Survive v0.2.15 applied.")
print("- Three Starfleet Emergency Power Cells start at 20/20 each")
print("- One Apply action transfers up to 20 units to one selected staff")
print("- Only energy actually transferred is consumed")
print("- Cells trickle-charge at 1 unit per 100 turns")
print("- Wisdom and Reaping do not accelerate Power Cell trickle charging")
print("- Scroll of Recharging fills Power Cells to 20/20")
print("- Normal variants retain native Recharging charm behavior")
print("Build normally with: make -B")
