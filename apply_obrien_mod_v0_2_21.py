#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.21 to a clean Brogue CE 1.15.1 tree.

Fire, Lightning and Poison keep 20-shot Starfleet batteries, but their Brogue
staff enchantment is +3 for effect magnitude and natural recharge timing.
Capacity and enchantment are deliberately independent.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_20.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_20.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.20 source was not found.")


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


# Independent Starfleet battery capacity for the three primary combat staffs.
replace_once(
    "src/brogue/Rogue.h",
    """#define OBRIEN_POWER_CELL_CAPACITY 20
#define OBRIEN_POWER_CELL_TRICKLE_TURNS 100
#define OBRIEN_POWER_CELL_MARKER (-220)""",
    """#define OBRIEN_POWER_CELL_CAPACITY 20
#define OBRIEN_POWER_CELL_TRICKLE_TURNS 100
#define OBRIEN_POWER_CELL_MARKER (-220)
#define OBRIEN_PRIMARY_STAFF_CAPACITY 20
#define OBRIEN_PRIMARY_STAFF_ENCHANTMENT 3
#define OBRIEN_PRIMARY_STAFF_MARKER (-221)""",
    "OBRIEN_PRIMARY_STAFF_CAPACITY",
)

replace_once(
    "src/brogue/Rogue.h",
    """    short staffChargeDuration(const item *theItem);
    void rechargeItemsIncrementally(short multiplier);""",
    """    short staffChargeCapacity(const item *theItem);
    short staffChargeDuration(const item *theItem);
    void rechargeItemsIncrementally(short multiplier);""",
    "short staffChargeCapacity(const item *theItem);",
)

# Ordinary staffs still use enchant1 as capacity. Only marked O'Brien primary
# Fire/Lightning/Poison staffs get the separate 20-shot battery.
replace_once(
    "src/brogue/Time.c",
    """short staffChargeDuration(const item *theItem) {
    // staffs of blinking and obstruction recharge half as fast so they're less powerful
    return (theItem->kind == STAFF_BLINKING || theItem->kind == STAFF_OBSTRUCTION ? 10000 : 5000) / theItem->enchant1;
}""",
    """short staffChargeCapacity(const item *theItem) {
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && theItem != NULL
        && (theItem->category & STAFF)
        && theItem->originDepth == OBRIEN_PRIMARY_STAFF_MARKER
        && (theItem->kind == STAFF_FIRE
            || theItem->kind == STAFF_LIGHTNING
            || theItem->kind == STAFF_POISON)) {

        return OBRIEN_PRIMARY_STAFF_CAPACITY;
    }
    return theItem ? theItem->enchant1 : 0;
}

short staffChargeDuration(const item *theItem) {
    // staffs of blinking and obstruction recharge half as fast so they're less powerful
    return (theItem->kind == STAFF_BLINKING || theItem->kind == STAFF_OBSTRUCTION ? 10000 : 5000) / theItem->enchant1;
}""",
    "short staffChargeCapacity(const item *theItem)",
)

replace_exact_count(
    "src/brogue/Time.c",
    "theItem->charges < theItem->enchant1",
    "theItem->charges < staffChargeCapacity(theItem)",
    2,
    "theItem->charges < staffChargeCapacity(theItem)",
)

# Inventory name: retain 20/20 presentation even though the effect enchantment is +3.
replace_once(
    "src/brogue/Items.c",
    """            if (includeDetails) {
                if ((theItem->flags & ITEM_IDENTIFIED) || rogue.playbackOmniscience) {
                    sprintf(buf, "%s%s [%i/%i]", root, grayEscapeSequence, theItem->charges, theItem->enchant1);
                    strcpy(root, buf);
                } else if (theItem->flags & ITEM_MAX_CHARGES_KNOWN) {
                    sprintf(buf, "%s%s [?/%i]", root, grayEscapeSequence, theItem->enchant1);
                    strcpy(root, buf);
                }
            }
            break;""",
    """            if (includeDetails) {
                if ((theItem->flags & ITEM_IDENTIFIED) || rogue.playbackOmniscience) {
                    sprintf(buf, "%s%s [%i/%i]", root, grayEscapeSequence,
                            theItem->charges, staffChargeCapacity(theItem));
                    strcpy(root, buf);
                } else if (theItem->flags & ITEM_MAX_CHARGES_KNOWN) {
                    sprintf(buf, "%s%s [?/%i]", root, grayEscapeSequence, staffChargeCapacity(theItem));
                    strcpy(root, buf);
                }
            }
            break;""",
    "staffChargeCapacity(theItem));",
)

# Detail pane: only replace the maximum-capacity arguments. Recharge timing still
# comes from staffChargeDuration(), which deliberately uses the native +3 enchant.
replace_once(
    "src/brogue/Items.c",
    """                        theName,
                        theItem->charges,
                        theItem->enchant1,
                        new == 0 ? "" : ", with your current rings,",""",
    """                        theName,
                        theItem->charges,
                        staffChargeCapacity(theItem),
                        new == 0 ? "" : ", with your current rings,",""",
    "theItem->charges,\n                        staffChargeCapacity(theItem),",
)

replace_once(
    "src/brogue/Items.c",
    """                        theName,
                        theItem->enchant1,
                        new == 0 ? "" : ", with your current rings,",""",
    """                        theName,
                        staffChargeCapacity(theItem),
                        new == 0 ? "" : ", with your current rings,",""",
    "theName,\n                        staffChargeCapacity(theItem),",
)

# Native Recharging charm/scroll fills the independent battery, while reset of
# recharge progress continues to follow native staff timing.
replace_once(
    "src/brogue/Items.c",
    """        if (tempItem->category & categories & STAFF) {
            x++;
            tempItem->charges = tempItem->enchant1;
            tempItem->enchant2 = (tempItem->kind == STAFF_BLINKING || tempItem->kind == STAFF_OBSTRUCTION ? 10000 : 5000) / tempItem->enchant1;
        }""",
    """        if (tempItem->category & categories & STAFF) {
            x++;
            tempItem->charges = staffChargeCapacity(tempItem);
            tempItem->enchant2 = staffChargeDuration(tempItem);
        }""",
    "tempItem->charges = staffChargeCapacity(tempItem);",
)

# Emergency Power Cells transfer against storage capacity, not enchantment.
replace_once(
    "src/brogue/Items.c",
    """    if (target->charges >= target->enchant1) {
        itemName(target, targetName, false, false, NULL);
        sprintf(buf, "Your %s is already fully charged.", targetName);
        messageWithColor(buf, &itemMessageColor, 0);
        return false;
    }

    transferred = min(cell->charges, target->enchant1 - target->charges);""",
    """    if (target->charges >= staffChargeCapacity(target)) {
        itemName(target, targetName, false, false, NULL);
        sprintf(buf, "Your %s is already fully charged.", targetName);
        messageWithColor(buf, &itemMessageColor, 0);
        return false;
    }

    transferred = min(cell->charges, staffChargeCapacity(target) - target->charges);""",
    "target->charges >= staffChargeCapacity(target)",
)

# Enchanting a marked staff may improve native power/recharge without shrinking
# its separate 20-shot battery to the new enchantment number.
replace_once(
    "src/brogue/Items.c",
    """        if ((theItem->category & STAFF)
            && theItem->charges > newEnchant) {

            theItem->charges = newEnchant;
        }""",
    """        if ((theItem->category & STAFF)
            && theItem->charges > (theItem->originDepth == OBRIEN_PRIMARY_STAFF_MARKER
                                   ? OBRIEN_PRIMARY_STAFF_CAPACITY
                                   : newEnchant)) {

            theItem->charges = (theItem->originDepth == OBRIEN_PRIMARY_STAFF_MARKER
                                ? OBRIEN_PRIMARY_STAFF_CAPACITY
                                : newEnchant);
        }""",
    "theItem->originDepth == OBRIEN_PRIMARY_STAFF_MARKER",
)

# Create the three primary mission staffs as native +3 staffs with 20-shot cells.
replace_once(
    "src/brogue/RogueMain.c",
    "static void obrienLoadStartingPack(void) {",
    r'''static void obrienAddPrimaryCombatStaffToPack(short kind) {
    item *staff = generateItem(STAFF, kind);

    if (!staff) {
        return;
    }

    staff->quantity = 1;
    staff->flags &= ~ITEM_CURSED;
    staff->enchant1 = OBRIEN_PRIMARY_STAFF_ENCHANTMENT;
    staff->charges = OBRIEN_PRIMARY_STAFF_CAPACITY;
    staff->originDepth = OBRIEN_PRIMARY_STAFF_MARKER;
    identifyItemKind(staff);
    identify(staff);
    addItemToPack(staff);
}

static void obrienLoadStartingPack(void) {''',
    "static void obrienAddPrimaryCombatStaffToPack(short kind)",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    obrienAddMissionItemToPack(STAFF, STAFF_FIRE, 20);
    obrienAddMissionItemToPack(STAFF, STAFF_LIGHTNING, 20);
    obrienAddMissionItemToPack(STAFF, STAFF_POISON, 20);
    obrienAddMissionItemToPack(STAFF, STAFF_BLINKING, 10);""",
    """    obrienAddPrimaryCombatStaffToPack(STAFF_FIRE);
    obrienAddPrimaryCombatStaffToPack(STAFF_LIGHTNING);
    obrienAddPrimaryCombatStaffToPack(STAFF_POISON);
    obrienAddMissionItemToPack(STAFF, STAFF_BLINKING, 10);""",
    "obrienAddPrimaryCombatStaffToPack(STAFF_FIRE);",
)

# Bashir's finite poison staff gets the same split model.
replace_once(
    "src/brogue/RogueMain.c",
    """    if (bashir->carriedItem) {
        bashir->carriedItem->enchant1 = 20;
        bashir->carriedItem->charges = 20;
        identifyItemKind(bashir->carriedItem);
        identify(bashir->carriedItem);
    }""",
    """    if (bashir->carriedItem) {
        bashir->carriedItem->enchant1 = OBRIEN_PRIMARY_STAFF_ENCHANTMENT;
        bashir->carriedItem->charges = OBRIEN_PRIMARY_STAFF_CAPACITY;
        bashir->carriedItem->originDepth = OBRIEN_PRIMARY_STAFF_MARKER;
        identifyItemKind(bashir->carriedItem);
        identify(bashir->carriedItem);
    }""",
    "bashir->carriedItem->originDepth = OBRIEN_PRIMARY_STAFF_MARKER",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.20\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.21\\n\");",
    "O'Brien Must Survive v0.2.21",
)

print("O'Brien Must Survive v0.2.21 applied.")
print("- Fire / Lightning / Poison: 20/20 storage, native +3 effect and recharge curve")
print("- 20-shot capacity no longer acts as +20 enchantment")
print("- Natural recharge and Wisdom now follow ordinary Brogue +3 staff rules")
print("- Recharging charm/scroll and Emergency Power Cells still fill to 20/20")
print("- Bashir's poison staff uses the same 20-capacity / +3 split")
print("- Blinking 10/10 and Tunneling 3/3 are unchanged")
print("Build normally with: make -B")
