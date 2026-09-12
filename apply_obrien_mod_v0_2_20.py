#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.20 to a clean Brogue CE 1.15.1 tree.

v0.2.20 removes the synthetic carried "Spell of Recharging" introduced in
v0.2.19 and restores Brogue's native Recharging charm as O'Brien's strategic
full-system recharge reserve.

The starting reserve is one native +3 Recharging charm. It starts ready and,
after use, recharges on Brogue's original cooldown curve (about 1664 turns at
+3). The three Starfleet Emergency Power Cells remain separate 20-unit batteries.
They are now distinguished by a dedicated marker instead of hijacking every
CHARM_RECHARGING in the O'Brien variant. Therefore ordinary/random Recharging
charms keep their native Brogue behavior.

Using a native Recharging charm still recharges staffs normally and, in the
O'Brien variant, also fills the three marked Emergency Power Cells to 20/20.
Naturally found Scrolls of Recharging continue to fill the marked Cells too.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_19.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_19.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.19 source was not found.")


# The fake spell marker is gone. A dedicated marker now identifies only the
# three emergency batteries, leaving native Recharging charms untouched.
replace_once(
    "src/brogue/Rogue.h",
    "#define OBRIEN_POWER_CELL_TRICKLE_TURNS 100\n#define OBRIEN_RECHARGE_SPELL_MARKER (-219)",
    "#define OBRIEN_POWER_CELL_TRICKLE_TURNS 100\n#define OBRIEN_POWER_CELL_MARKER (-220)",
    "OBRIEN_POWER_CELL_MARKER",
)

# Restore native charm generation. Power Cells are specialized explicitly by
# obrienAddEmergencyPowerCellToPack() after generation instead of globally
# redefining every CHARM_RECHARGING in the O'Brien variant.
replace_once(
    "src/brogue/Items.c",
    """        case CHARM:\n            if (itemKind < 0) {\n                itemKind = chooseKind(charmTable, gameConst->numberCharmKinds);\n            }\n            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && itemKind == CHARM_RECHARGING) {\n                // v0.2.15 Starfleet Emergency Power Cell: charges are stored energy,\n                // enchant2 is the passive trickle-charge progress counter.\n                theItem->charges = OBRIEN_POWER_CELL_CAPACITY;\n                theItem->enchant1 = 0;\n                theItem->enchant2 = 0;\n            } else {\n                theItem->charges = 0; // Charms are initially ready for use.\n                theItem->enchant1 = randClump(charmTable[itemKind].range);\n                while (rand_percent(7)) {\n                    theItem->enchant1++;\n                }\n            }\n            theItem->flags |= ITEM_IDENTIFIED;\n            break;""",
    """        case CHARM:\n            if (itemKind < 0) {\n                itemKind = chooseKind(charmTable, gameConst->numberCharmKinds);\n            }\n            theItem->charges = 0; // Charms are initially ready for use.\n            theItem->enchant1 = randClump(charmTable[itemKind].range);\n            while (rand_percent(7)) {\n                theItem->enchant1++;\n            }\n            theItem->flags |= ITEM_IDENTIFIED;\n            break;""",
    "v0.2.20 native Recharging charms",
)

# Inventory naming applies the battery label only to the three marked cells.
replace_once(
    "src/brogue/Items.c",
    """        case CHARM:\n            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && theItem->kind == CHARM_RECHARGING) {\n                sprintf(root, \"Starfleet Emergency Power Cell%s\", pluralization);""",
    """        case CHARM:\n            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n                && theItem->kind == CHARM_RECHARGING\n                && theItem->originDepth == OBRIEN_POWER_CELL_MARKER) {\n                sprintf(root, \"Starfleet Emergency Power Cell%s\", pluralization);""",
    "theItem->originDepth == OBRIEN_POWER_CELL_MARKER",
)

# Only marked cells get the Power Cell description. Ordinary Recharging charms
# use Brogue's native help text and native cooldown formula.
replace_once(
    "src/brogue/Items.c",
    """                case CHARM_RECHARGING:\n                    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n                        sprintf(buf2, \"\\n\\nThis Starfleet Emergency Power Cell stores up to %i charge-units. Applying it transfers up to %i units immediately to one selected staff, consuming only the energy actually transferred. It trickle-charges at one unit per %i turns; Wisdom and Reaping do not accelerate it. A Spell of Recharging or Scroll of Recharging fills it completely.\",\n                                OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_TRICKLE_TURNS);\n                    } else {""",
    """                case CHARM_RECHARGING:\n                    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n                        && theItem->originDepth == OBRIEN_POWER_CELL_MARKER) {\n                        sprintf(buf2, \"\\n\\nThis Starfleet Emergency Power Cell stores up to %i charge-units. Applying it transfers up to %i units immediately to one selected staff, consuming only the energy actually transferred. It trickle-charges at one unit per %i turns; Wisdom and Reaping do not accelerate it. A Recharging charm or Scroll of Recharging fills it completely.\",\n                                OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_TRICKLE_TURNS);\n                    } else {""",
    "A Recharging charm or Scroll of Recharging fills it completely.",
)

# Shared helper for native Recharging charms: they recharge staffs exactly as
# Brogue normally does, and additionally refill only the marked O'Brien cells.
replace_once(
    "src/brogue/Items.c",
    "static boolean useObrienEmergencyPowerCell(item *cell) {",
    r'''static void obrienFillEmergencyPowerCells(void) {
    item *tempItem;

    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE) {
        return;
    }

    for (tempItem = packItems->nextItem; tempItem != NULL; tempItem = tempItem->nextItem) {
        if ((tempItem->category & CHARM)
            && tempItem->kind == CHARM_RECHARGING
            && tempItem->originDepth == OBRIEN_POWER_CELL_MARKER) {

            tempItem->charges = OBRIEN_POWER_CELL_CAPACITY;
            tempItem->enchant2 = 0;
        }
    }
}

static boolean useObrienEmergencyPowerCell(item *cell) {''',
    "obrienFillEmergencyPowerCells",
)

# Only marked Recharging-charm instances are Power Cells. Unmarked ones proceed
# through native useCharm() behavior.
replace_once(
    "src/brogue/Items.c",
    """    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && theItem->kind == CHARM_RECHARGING) {\n        return useObrienEmergencyPowerCell(theItem);\n    }""",
    """    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n        && theItem->kind == CHARM_RECHARGING\n        && theItem->originDepth == OBRIEN_POWER_CELL_MARKER) {\n        return useObrienEmergencyPowerCell(theItem);\n    }""",
    "theItem->originDepth == OBRIEN_POWER_CELL_MARKER",
)

# Native Recharging charm remains Brogue-native for staffs, with one O'Brien-only
# extension: it also restores marked emergency batteries to full reserve.
replace_once(
    "src/brogue/Items.c",
    """        case CHARM_RECHARGING:\n            rechargeItems(STAFF);\n            break;""",
    """        case CHARM_RECHARGING:\n            rechargeItems(STAFF);\n            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n                obrienFillEmergencyPowerCells();\n            }\n            break;""",
    "obrienFillEmergencyPowerCells();",
)

# Scrolls of Recharging still refill Power Cells, but only marked cells are
# interpreted as batteries. Native Recharging charms remain normal charms.
replace_once(
    "src/brogue/Items.c",
    """            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && tempItem->kind == CHARM_RECHARGING) {\n                tempItem->charges = OBRIEN_POWER_CELL_CAPACITY;\n                tempItem->enchant2 = 0;\n            } else {""",
    """            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n                && tempItem->kind == CHARM_RECHARGING\n                && tempItem->originDepth == OBRIEN_POWER_CELL_MARKER) {\n                tempItem->charges = OBRIEN_POWER_CELL_CAPACITY;\n                tempItem->enchant2 = 0;\n            } else {""",
    "tempItem->originDepth == OBRIEN_POWER_CELL_MARKER",
)

# Native charm cooldown machinery skips only marked Power Cells.
replace_once(
    "src/brogue/Time.c",
    """                   && !(gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && theItem->kind == CHARM_RECHARGING)) {""",
    """                   && !(gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n                        && theItem->kind == CHARM_RECHARGING\n                        && theItem->originDepth == OBRIEN_POWER_CELL_MARKER)) {""",
    "theItem->originDepth == OBRIEN_POWER_CELL_MARKER",
)

# Likewise, passive 1/100-turn trickle applies only to the three marked cells.
replace_once(
    "src/brogue/Time.c",
    """        if ((theItem->category & CHARM) && theItem->kind == CHARM_RECHARGING) {\n            if (theItem->charges >= OBRIEN_POWER_CELL_CAPACITY) {""",
    """        if ((theItem->category & CHARM)\n            && theItem->kind == CHARM_RECHARGING\n            && theItem->originDepth == OBRIEN_POWER_CELL_MARKER) {\n            if (theItem->charges >= OBRIEN_POWER_CELL_CAPACITY) {""",
    "theItem->originDepth == OBRIEN_POWER_CELL_MARKER",
)

# Explicitly mark only the three mission batteries after ordinary charm creation.
replace_once(
    "src/brogue/RogueMain.c",
    """    cell->charges = OBRIEN_POWER_CELL_CAPACITY;\n    cell->enchant1 = 0;\n    cell->enchant2 = 0;\n    identifyItemKind(cell);""",
    """    cell->charges = OBRIEN_POWER_CELL_CAPACITY;\n    cell->enchant1 = 0;\n    cell->enchant2 = 0;\n    cell->originDepth = OBRIEN_POWER_CELL_MARKER;\n    identifyItemKind(cell);""",
    "cell->originDepth = OBRIEN_POWER_CELL_MARKER",
)

# Remove the synthetic scroll-backed mission spell helper from v0.2.19.
replace_once(
    "src/brogue/RogueMain.c",
    r'''static void obrienAddMissionRechargeSpellToPack(void) {
    item *spell = generateItem(SCROLL, SCROLL_RECHARGING);

    if (!spell) {
        return;
    }

    spell->quantity = 1;
    spell->flags &= ~ITEM_CURSED;
    spell->originDepth = OBRIEN_RECHARGE_SPELL_MARKER;
    identifyItemKind(spell);
    identify(spell);
    addItemToPack(spell);
}
''',
    "",
    "v0.2.20 native slow Recharging charm",
)

# Replace the synthetic mission spell with one real +3 native Recharging charm.
replace_once(
    "src/brogue/RogueMain.c",
    """    // v0.2.19 genuine carried Spell of Recharging.\n    obrienAddMissionRechargeSpellToPack();""",
    """    // v0.2.20 native slow Recharging charm: strategic full-system reserve.\n    obrienAddMissionItemToPack(CHARM, CHARM_RECHARGING, 3);""",
    "v0.2.20 native slow Recharging charm",
)

# Remove v0.2.19's scroll-disguised-as-spell inventory naming.
replace_once(
    "src/brogue/Items.c",
    r'''        case SCROLL:
            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
                && theItem->kind == SCROLL_RECHARGING
                && theItem->originDepth == OBRIEN_RECHARGE_SPELL_MARKER) {

                sprintf(root, "Spell%s of Recharging", pluralization);
            } else if (scrollTable[theItem->kind].identified || rogue.playbackOmniscience) {
                sprintf(root, "scroll%s of %s", pluralization, scrollTable[theItem->kind].name);''',
    r'''        case SCROLL:
            if (scrollTable[theItem->kind].identified || rogue.playbackOmniscience) {
                sprintf(root, "scroll%s of %s", pluralization, scrollTable[theItem->kind].name);''',
    "v0.2.20 native Recharging charms",
)

replace_once(
    "src/brogue/Items.c",
    """void itemKindName(item *theItem, char *kindName) {\n\n    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n        && theItem->category == SCROLL\n        && theItem->kind == SCROLL_RECHARGING\n        && theItem->originDepth == OBRIEN_RECHARGE_SPELL_MARKER) {\n\n        strcpy(kindName, \"Spell of Recharging\");\n        return;\n    }\n\n    // use lookup table for randomly generated items with more than one kind per category""",
    """void itemKindName(item *theItem, char *kindName) {\n\n    // use lookup table for randomly generated items with more than one kind per category""",
    "v0.2.20 native Recharging charms",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.19\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.20\\n\");",
    "O'Brien Must Survive v0.2.20",
)

print("O'Brien Must Survive v0.2.20 applied.")
print("- Removed the synthetic scroll-backed Spell of Recharging")
print("- Starting backpack now carries one native +3 Recharging charm, initially ready")
print("- Native +3 cooldown remains Brogue's original slow curve (about 1664 turns)")
print("- Native Recharging charm recharges staffs and also fills marked Power Cells to 20/20")
print("- Three Starfleet Emergency Power Cells remain 20/20 high-discharge batteries")
print("- Only marked Power Cells use the 1 unit / 100 turns trickle-charge model")
print("- Random/native Recharging charms in O'Brien mode keep ordinary Brogue behavior")
print("- Scrolls of Recharging still refill marked Power Cells")
print("Build normally with: make -B")
