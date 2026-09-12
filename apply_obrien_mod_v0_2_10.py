#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.10 to a clean Brogue CE 1.15.1 tree.

v0.2.10 includes v0.2.9, removes the custom p-key Recharge ability, and
returns rapid staff refilling to Brogue's native CHARM_RECHARGING mechanic.
O'Brien starts with three separate +12 Recharging charms in the stairhead
field cache. Natural staff recharge is not accelerated.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_9.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_9.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.9 source was not found.")


# Remove the bespoke command key. Fast refilling now uses the game's native
# Recharging charm through the ordinary Apply ('a') command.
replace_once(
    "src/brogue/Rogue.h",
    "#define APPLY_KEY           'a'\n#define OBRIEN_RECHARGE_KEY 'p'\n#define THROW_KEY           't'",
    "#define APPLY_KEY           'a'\n#define THROW_KEY           't'",
    "v0.2.10 native Recharging charms",
)

replace_once(
    "src/brogue/Rogue.h",
    "    void apply(item *theItem);\n    boolean obrienRechargeCombatStaffs(void);\n    boolean eat(item *theItem, boolean recordCommands);",
    "    void apply(item *theItem);\n    boolean eat(item *theItem, boolean recordCommands);",
    "v0.2.10 native Recharging charms",
)

# Remove the custom refill implementation. Brogue already implements
# CHARM_RECHARGING by calling rechargeItems(STAFF), so keep that native path.
replace_once(
    "src/brogue/Items.c",
    """boolean obrienRechargeCombatStaffs(void) {
    item *tempItem;
    short recharged = 0;

    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE) {
        return false;
    }

    for (tempItem = packItems->nextItem; tempItem != NULL; tempItem = tempItem->nextItem) {
        if ((tempItem->category & STAFF)
            && (tempItem->kind == STAFF_FIRE
                || tempItem->kind == STAFF_LIGHTNING
                || tempItem->kind == STAFF_POISON)
            && tempItem->charges < tempItem->enchant1) {

            tempItem->charges = tempItem->enchant1;
            tempItem->enchant2 = staffChargeDuration(tempItem);
            tempItem->flags |= ITEM_MAX_CHARGES_KNOWN;
            recharged++;
        }
    }

    if (!recharged) {
        message("Your fire, lightning and poison staffs are already fully charged.", 0);
        return false;
    }

    rogue.featRecord[FEAT_PURE_WARRIOR] = false;
    message("You cast Recharge, routing reserve power into your combat staffs.", 0);
    return true;
}

static boolean useCharm(item *theItem) {""",
    "static boolean useCharm(item *theItem) {",
    "v0.2.10 native Recharging charms",
)

# Remove the custom action-menu entry.
replace_once(
    "src/brogue/IO.c",
    """            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                if (KEYBOARD_LABELS) {
                    sprintf(buttons[buttonCount].text, "  %sp: %sRecharge combat staffs  ", yellowColorEscape, whiteColorEscape);
                } else {
                    strcpy(buttons[buttonCount].text, "  Recharge combat staffs  ");
                }
                buttons[buttonCount].hotkey[0] = OBRIEN_RECHARGE_KEY;
                buttonCount++;
            }

""",
    "",
    "v0.2.10 native Recharging charms",
)

replace_once(
    "src/brogue/IO.c",
    """        case OBRIEN_RECHARGE_KEY:
            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
                && obrienRechargeCombatStaffs()) {

                recordKeystroke(OBRIEN_RECHARGE_KEY, false, false);
                playerTurnEnded();
            }
            break;
""",
    "",
    "v0.2.10 native Recharging charms",
)

# Three separate +12 charms model multiple reserve power packs. Each charm uses
# Brogue's own cooldown/reuse rules. They are placed as three distinct floor
# items, not combined into one quantity stack and not inserted into the backpack.
replace_once(
    "src/brogue/RogueMain.c",
    "    obrienPlaceSupplyItem(CHARM, CHARM_HEALTH, 1, 2, anchor);\n    obrienPlaceSupplyItem(RING, RING_REGENERATION, 1, 3, anchor);",
    """    obrienPlaceSupplyItem(CHARM, CHARM_HEALTH, 1, 2, anchor);

    // v0.2.10 native Recharging charms: three independent +12 reserve power packs.
    obrienPlaceSupplyItem(CHARM, CHARM_RECHARGING, 1, 12, anchor);
    obrienPlaceSupplyItem(CHARM, CHARM_RECHARGING, 1, 12, anchor);
    obrienPlaceSupplyItem(CHARM, CHARM_RECHARGING, 1, 12, anchor);

    obrienPlaceSupplyItem(RING, RING_REGENERATION, 1, 3, anchor);""",
    "v0.2.10 native Recharging charms",
)

print("O'Brien Must Survive v0.2.10 applied.")
print("- Removed the custom p-key Recharge command and custom refill function")
print("- Initial stairhead cache now contains three separate +12 Recharging charms")
print("- Use Brogue's native Apply command (a) to activate a Recharging charm")
print("- Native Recharging refills staffs according to Brogue's existing rules, including Blink/Tunneling")
print("- Fire/Lightning/Poison remain 20/20 and natural staff recharge speed is unchanged")
print("Build normally with: make -B")
