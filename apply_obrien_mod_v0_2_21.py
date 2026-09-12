#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.21 to a clean Brogue CE 1.15.1 tree.

v0.2.21 fixes the 20/20 primary combat staffs so their Starfleet storage
capacity is no longer mistaken for Brogue enchantment level.

Fire, Lightning and Poison keep a fixed 20-charge mission battery, but use a
native +3 staff enchantment for effect magnitude and natural recharge timing.
This removes the accidental +20 damage/duration scaling and the ~11-turn natural
recharge seen with a Wisdom ring. Blinking 10/10 and Tunneling 3/3 are unchanged.
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


# A primary combat staff has two independent values in this variant:
# - native Brogue enchantment (+3): effect magnitude and natural recharge curve;
# - Starfleet battery capacity (20): how many shots can be stored.
# Keep the marker separate from the Power Cell marker.
replace_once(
    "src/brogue/Rogue.h",
    """#define OBRIEN_POWER_CELL_CAPACITY 20\n#define OBRIEN_POWER_CELL_TRICKLE_TURNS 100\n#define OBRIEN_POWER_CELL_MARKER (-220)""",
    """#define OBRIEN_POWER_CELL_CAPACITY 20\n#define OBRIEN_POWER_CELL_TRICKLE_TURNS 100\n#define OBRIEN_POWER_CELL_MARKER (-220)\n#define OBRIEN_PRIMARY_STAFF_CAPACITY 20\n#define OBRIEN_PRIMARY_STAFF_ENCHANTMENT 3\n#define OBRIEN_PRIMARY_STAFF_MARKER (-221)""",
    "OBRIEN_PRIMARY_STAFF_CAPACITY",
)

# Expose the capacity helper because inventory display, recharge items and the
# Power Cell transfer path all need to ask the same question.
replace_once(
    "src/brogue/Rogue.h",
    """    short staffChargeDuration(const item *theItem);\n    void rechargeItemsIncrementally(short multiplier);""",
    """    short staffChargeCapacity(const item *theItem);\n    short staffChargeDuration(const item *theItem);\n    void rechargeItemsIncrementally(short multiplier);""",
    "short staffChargeCapacity(const item *theItem);",
)

# Capacity is 20 only for the three explicitly marked mission combat staffs.
# Every ordinary Brogue staff, Blink and Tunneling continue to use enchant1 as
# their native maximum charge count. staffChargeDuration deliberately remains
# based on enchant1, so +3 means native +3 recharge timing.
replace_once(
    "src/brogue/Time.c",
    """short staffChargeDuration(const item *theItem) {\n    // staffs of blinking and obstruction recharge half as fast so they're less powerful\n    return (theItem->kind == STAFF_BLINKING || theItem->kind == STAFF_OBSTRUCTION ? 10000 : 5000) / theItem->enchant1;\n}""",
    """short staffChargeCapacity(const item *theItem) {\n    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n        && theItem != NULL\n        && (theItem->category & STAFF)\n        && theItem->originDepth == OBRIEN_PRIMARY_STAFF_MARKER\n        && (theItem->kind == STAFF_FIRE\n            || theItem->kind == STAFF_LIGHTNING\n            || theItem->kind == STAFF_POISON)) {\n\n        return OBRIEN_PRIMARY_STAFF_CAPACITY;\n    }\n    return theItem ? theItem->enchant1 : 0;\n}\n\nshort staffChargeDuration(const item *theItem) {\n    // staffs of blinking and obstruction recharge half as fast so they're less powerful\n    return (theItem->kind == STAFF_BLINKING || theItem->kind == STAFF_OBSTRUCTION ? 10000 : 5000) / theItem->enchant1;\n}""",
    "short staffChargeCapacity(const item *theItem)",
)

# Natural staff charging must stop at the independent storage capacity. This is
# the key separation: recharge speed still comes from +3, maximum stored shots
# come from staffChargeCapacity().
replace_exact_count(
    "src/brogue/Time.c",
    "theItem->charges < theItem->enchant1",
    "theItem->charges < staffChargeCapacity(theItem)",
    2,
    "theItem->charges < staffChargeCapacity(theItem)",
)

# Inventory labels still show the Starfleet battery as 20/20 even though its
# internal native enchantment is +3.
replace_once(
    "src/brogue/Items.c",
    """            if (includeDetails) {\n                if ((theItem->flags & ITEM_IDENTIFIED) || rogue.playbackOmniscience) {\n                    sprintf(buf, \"%s%s [%i/%i]\", root, grayEscapeSequence, theItem->charges, theItem->enchant1);\n                    strcpy(root, buf);\n                } else if (theItem->flags & ITEM_MAX_CHARGES_KNOWN) {\n                    sprintf(buf, \"%s%s [?/%i]\", root, grayEscapeSequence, theItem->enchant1);\n                    strcpy(root, buf);\n                }\n            }\n            break;""",
    """            if (includeDetails) {\n                if ((theItem->flags & ITEM_IDENTIFIED) || rogue.playbackOmniscience) {\n                    sprintf(buf, \"%s%s [%i/%i]\", root, grayEscapeSequence,\n                            theItem->charges, staffChargeCapacity(theItem));\n                    strcpy(root, buf);\n                } else if (theItem->flags & ITEM_MAX_CHARGES_KNOWN) {\n                    sprintf(buf, \"%s%s [?/%i]\", root, grayEscapeSequence, staffChargeCapacity(theItem));\n                    strcpy(root, buf);\n                }\n            }\n            break;""",
    "staffChargeCapacity(theItem));",
)

# Likewise, the detail pane reports the independent capacity while calculating
# recharge time from native Brogue staffChargeDuration(+3). That means Wisdom
# continues to work normally, but no longer sees an accidental +20 staff.
replace_once(
    "src/brogue/Items.c",
    """            // charges\n            new = apparentRingBonus(RING_WISDOM);\n            if ((theItem->flags & ITEM_IDENTIFIED)  || rogue.playbackOmniscience) {\n                sprintf(buf2, \"\\\n\\\nThe %s has %i charges remaining out of a maximum of %i charges, and%s recovers a charge in approximately %lli turns. \",\n                        theName,\n                        theItem->charges,\n                        theItem->enchant1,\n                        new == 0 ? \"\" : \", with your current rings,\",\n                        FP_DIV(staffChargeDuration(theItem), 10 * ringWisdomMultiplier(new * FP_FACTOR)));\n                strcat(buf, buf2);\n            } else if (theItem->flags & ITEM_MAX_CHARGES_KNOWN) {\n                sprintf(buf2, \"\\\n\\\nThe %s has a maximum of %i charges, and%s recovers a charge in approximately %lli turns. \",\n                        theName,\n                        theItem->enchant1,\n                        new == 0 ? \"\" : \", with your current rings,\",\n                        FP_DIV(staffChargeDuration(theItem), 10 * ringWisdomMultiplier(new * FP_FACTOR)));\n                strcat(buf, buf2);\n            }""",
    """            // charges\n            new = apparentRingBonus(RING_WISDOM);\n            if ((theItem->flags & ITEM_IDENTIFIED)  || rogue.playbackOmniscience) {\n                sprintf(buf2, \"\\\n\\\nThe %s has %i charges remaining out of a maximum of %i charges, and%s recovers a charge in approximately %lli turns. \",\n                        theName,\n                        theItem->charges,\n                        staffChargeCapacity(theItem),\n                        new == 0 ? \"\" : \", with your current rings,\",\n                        FP_DIV(staffChargeDuration(theItem), 10 * ringWisdomMultiplier(new * FP_FACTOR)));\n                strcat(buf, buf2);\n            } else if (theItem->flags & ITEM_MAX_CHARGES_KNOWN) {\n                sprintf(buf2, \"\\\n\\\nThe %s has a maximum of %i charges, and%s recovers a charge in approximately %lli turns. \",\n                        theName,\n                        staffChargeCapacity(theItem),\n                        new == 0 ? \"\" : \", with your current rings,\",\n                        FP_DIV(staffChargeDuration(theItem), 10 * ringWisdomMultiplier(new * FP_FACTOR)));\n                strcat(buf, buf2);\n            }""",
    "staffChargeCapacity(theItem),",
)

# Native Recharging charm / Scroll of Recharging fills the independent battery
# to 20, but recharge progress remains on the +3 native curve.
replace_once(
    "src/brogue/Items.c",
    """        if (tempItem->category & categories & STAFF) {\n            x++;\n            tempItem->charges = tempItem->enchant1;\n            tempItem->enchant2 = (tempItem->kind == STAFF_BLINKING || tempItem->kind == STAFF_OBSTRUCTION ? 10000 : 5000) / tempItem->enchant1;\n        }""",
    """        if (tempItem->category & categories & STAFF) {\n            x++;\n            tempItem->charges = staffChargeCapacity(tempItem);\n            tempItem->enchant2 = staffChargeDuration(tempItem);\n        }""",
    "tempItem->charges = staffChargeCapacity(tempItem);",
)

# Emergency Power Cells also transfer against the independent battery capacity.
replace_once(
    "src/brogue/Items.c",
    """    if (target->charges >= target->enchant1) {\n        itemName(target, targetName, false, false, NULL);\n        sprintf(buf, \"Your %s is already fully charged.\", targetName);\n        messageWithColor(buf, &itemMessageColor, 0);\n        return false;\n    }\n\n    transferred = min(cell->charges, target->enchant1 - target->charges);""",
    """    if (target->charges >= staffChargeCapacity(target)) {\n        itemName(target, targetName, false, false, NULL);\n        sprintf(buf, \"Your %s is already fully charged.\", targetName);\n        messageWithColor(buf, &itemMessageColor, 0);\n        return false;\n    }\n\n    transferred = min(cell->charges, staffChargeCapacity(target) - target->charges);""",
    "target->charges >= staffChargeCapacity(target)",
)

# Enchanting a marked 20-capacity staff should improve its native effect/recharge
# enchantment, not collapse a partially charged 20-shot battery down to the new
# enchantment number. Ordinary staffs retain the original clamp behavior.
replace_once(
    "src/brogue/Items.c",
    """        if ((theItem->category & STAFF)\n            && theItem->charges > newEnchant) {\n\n            theItem->charges = newEnchant;\n        }""",
    """        if ((theItem->category & STAFF)\n            && theItem->charges > (theItem->originDepth == OBRIEN_PRIMARY_STAFF_MARKER\n                                   ? OBRIEN_PRIMARY_STAFF_CAPACITY\n                                   : newEnchant)) {\n\n            theItem->charges = (theItem->originDepth == OBRIEN_PRIMARY_STAFF_MARKER\n                                ? OBRIEN_PRIMARY_STAFF_CAPACITY\n                                : newEnchant);\n        }""",
    "theItem->originDepth == OBRIEN_PRIMARY_STAFF_MARKER",
)

# Build the three primary staffs explicitly as +3 Brogue staffs carrying a
# separate 20-unit Starfleet battery. The generic helper remains for Blink,
# Tunneling and other native-capacity mission items.
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
    """    obrienAddMissionItemToPack(STAFF, STAFF_FIRE, 20);\n    obrienAddMissionItemToPack(STAFF, STAFF_LIGHTNING, 20);\n    obrienAddMissionItemToPack(STAFF, STAFF_POISON, 20);\n    obrienAddMissionItemToPack(STAFF, STAFF_BLINKING, 10);""",
    """    obrienAddPrimaryCombatStaffToPack(STAFF_FIRE);\n    obrienAddPrimaryCombatStaffToPack(STAFF_LIGHTNING);\n    obrienAddPrimaryCombatStaffToPack(STAFF_POISON);\n    obrienAddMissionItemToPack(STAFF, STAFF_BLINKING, 10);""",
    "obrienAddPrimaryCombatStaffToPack(STAFF_FIRE);",
)

# Bashir's finite poison staff follows the same split model if it is ever
# inspected, dropped or transferred: 20 stored shots, native +3 poison power.
replace_once(
    "src/brogue/RogueMain.c",
    """    if (bashir->carriedItem) {\n        bashir->carriedItem->enchant1 = 20;\n        bashir->carriedItem->charges = 20;\n        identifyItemKind(bashir->carriedItem);\n        identify(bashir->carriedItem);\n    }""",
    """    if (bashir->carriedItem) {\n        bashir->carriedItem->enchant1 = OBRIEN_PRIMARY_STAFF_ENCHANTMENT;\n        bashir->carriedItem->charges = OBRIEN_PRIMARY_STAFF_CAPACITY;\n        bashir->carriedItem->originDepth = OBRIEN_PRIMARY_STAFF_MARKER;\n        identifyItemKind(bashir->carriedItem);\n        identify(bashir->carriedItem);\n    }""",
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
print("- Natural recharge, Wisdom and staff effects now follow ordinary Brogue +3 rules")
print("- Recharging charm/scroll and Emergency Power Cells still fill the full 20-shot battery")
print("- Bashir's finite poison staff uses the same 20-capacity / +3 split")
print("- Blinking 10/10 and Tunneling 3/3 are unchanged")
print("Build normally with: make -B")
