#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.8 to a clean Brogue CE 1.15.1 tree.

v0.2.8 includes v0.2.7 and gives O'Brien an active Recharge spell for his
20-charge combat staffs. Recharge is a deliberate one-turn tactical reload,
not a passive staff-regeneration bonus. It fully refills fire, lightning and
poison staffs in the pack, while leaving blinking and all other staffs alone.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_7.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_7.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.7 source was not found.")


# Reserve a dedicated command key for O'Brien's field-recharge spell.
replace_once(
    "src/brogue/Rogue.h",
    "#define APPLY_KEY           'a'\n#define THROW_KEY           't'",
    "#define APPLY_KEY           'a'\n#define OBRIEN_RECHARGE_KEY 'p'\n#define THROW_KEY           't'",
    "#define OBRIEN_RECHARGE_KEY 'p'",
)

# Expose the spell helper to the input layer.
replace_once(
    "src/brogue/Rogue.h",
    "    void apply(item *theItem);\n    boolean eat(item *theItem, boolean recordCommands);",
    "    void apply(item *theItem);\n    boolean obrienRechargeCombatStaffs(void);\n    boolean eat(item *theItem, boolean recordCommands);",
    "boolean obrienRechargeCombatStaffs(void);",
)

# Active Recharge spell. O'Brien spends one action to refill the three combat
# staffs to their existing maximum. Blink is intentionally excluded: it remains
# a mobility tool with its own ordinary Brogue recharge behavior.
replace_once(
    "src/brogue/Items.c",
    "static boolean useCharm(item *theItem) {",
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
    "boolean obrienRechargeCombatStaffs(void) {",
)

# Put the spell in the normal action menu only for the O'Brien variant.
replace_once(
    "src/brogue/IO.c",
    """            if (KEYBOARD_LABELS) {
                sprintf(buttons[buttonCount].text, "  %sA: %sAutopilot  ",              yellowColorEscape, whiteColorEscape);
            } else {
                strcpy(buttons[buttonCount].text, "  Autopilot  ");
            }
            buttons[buttonCount].hotkey[0] = AUTOPLAY_KEY;
            buttonCount++;

            if (KEYBOARD_LABELS) {
                sprintf(buttons[buttonCount].text, "  %sT: %sRe-throw at last monster  ",              yellowColorEscape, whiteColorEscape);""",
    """            if (KEYBOARD_LABELS) {
                sprintf(buttons[buttonCount].text, "  %sA: %sAutopilot  ",              yellowColorEscape, whiteColorEscape);
            } else {
                strcpy(buttons[buttonCount].text, "  Autopilot  ");
            }
            buttons[buttonCount].hotkey[0] = AUTOPLAY_KEY;
            buttonCount++;

            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                if (KEYBOARD_LABELS) {
                    sprintf(buttons[buttonCount].text, "  %sp: %sRecharge combat staffs  ", yellowColorEscape, whiteColorEscape);
                } else {
                    strcpy(buttons[buttonCount].text, "  Recharge combat staffs  ");
                }
                buttons[buttonCount].hotkey[0] = OBRIEN_RECHARGE_KEY;
                buttonCount++;
            }

            if (KEYBOARD_LABELS) {
                sprintf(buttons[buttonCount].text, "  %sT: %sRe-throw at last monster  ",              yellowColorEscape, whiteColorEscape);""",
    "Recharge combat staffs",
)

# Casting Recharge consumes one player action when it actually transfers power.
# If all three combat staff types in the pack are already full, no turn is spent.
replace_once(
    "src/brogue/IO.c",
    """        case APPLY_KEY:
            apply(NULL);
            break;
        case THROW_KEY:""",
    """        case APPLY_KEY:
            apply(NULL);
            break;
        case OBRIEN_RECHARGE_KEY:
            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
                && obrienRechargeCombatStaffs()) {

                recordKeystroke(OBRIEN_RECHARGE_KEY, false, false);
                playerTurnEnded();
            }
            break;
        case THROW_KEY:""",
    "case OBRIEN_RECHARGE_KEY:",
)

print("O'Brien Must Survive v0.2.8 applied.")
print("- Press p in the O'Brien variant to cast Recharge")
print("- Recharge spends one turn and fully refills carried fire/lightning/poison staffs to their existing maxima")
print("- Blink and every other staff are excluded from the spell")
print("- If all eligible combat staffs are already full, no turn is consumed")
print("- Ordinary Brogue natural staff recharge is unchanged")
print("Build normally with: make -B")
