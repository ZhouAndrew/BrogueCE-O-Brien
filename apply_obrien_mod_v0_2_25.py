#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.25 to a clean Brogue CE 1.15.1 tree.

v0.2.25 fixes the too-fast passive recharge of O'Brien's three 20-shot primary
combat staffs without removing or nerfing the +3 Ring of Wisdom.

Fire, Lightning and Poison keep:
- 20-shot Starfleet battery capacity;
- native +3 effect strength;
- full compatibility with the native Wisdom ring, Recharging charm/scrolls,
  Emergency Power Cells and enchanting.

Only their passive base recharge interval is changed. A marked primary combat
staff now uses a 5000-tick base charge interval (the ordinary +1-staff pacing)
instead of dividing that interval by its +3 effect enchantment. Wisdom still
accelerates that interval through Brogue's normal ringWisdomMultiplier() path.
This keeps Wisdom useful while preventing +3 effect strength + +3 Wisdom from
turning the 20-shot battery into near-continuous fire.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_24.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_24.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.24 source was not found.")


# Separate effect enchantment from passive recharge pacing. The Ring of Wisdom
# remains +3 and continues to accelerate staff charging in rechargeItemsIncrementally().
replace_once(
    "src/brogue/Rogue.h",
    """#define OBRIEN_PRIMARY_STAFF_CAPACITY 20
#define OBRIEN_PRIMARY_STAFF_ENCHANTMENT 3
#define OBRIEN_PRIMARY_STAFF_MARKER (-221)""",
    """#define OBRIEN_PRIMARY_STAFF_CAPACITY 20
#define OBRIEN_PRIMARY_STAFF_ENCHANTMENT 3
#define OBRIEN_PRIMARY_STAFF_MARKER (-221)
#define OBRIEN_PRIMARY_STAFF_RECHARGE_DURATION 5000""",
    "OBRIEN_PRIMARY_STAFF_RECHARGE_DURATION",
)

replace_once(
    "src/brogue/Time.c",
    """short staffChargeDuration(const item *theItem) {
    // staffs of blinking and obstruction recharge half as fast so they're less powerful
    return (theItem->kind == STAFF_BLINKING || theItem->kind == STAFF_OBSTRUCTION ? 10000 : 5000) / theItem->enchant1;
}""",
    """short staffChargeDuration(const item *theItem) {
    // v0.2.25: O'Brien's marked Fire/Lightning/Poison staffs keep +3 effect
    // strength but no longer get +3's passive recharge-speed bonus on top of
    // the +3 Wisdom ring. Wisdom still accelerates this duration normally in
    // rechargeItemsIncrementally().
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && theItem != NULL
        && (theItem->category & STAFF)
        && theItem->originDepth == OBRIEN_PRIMARY_STAFF_MARKER
        && (theItem->kind == STAFF_FIRE
            || theItem->kind == STAFF_LIGHTNING
            || theItem->kind == STAFF_POISON)) {

        return OBRIEN_PRIMARY_STAFF_RECHARGE_DURATION;
    }

    // staffs of blinking and obstruction recharge half as fast so they're less powerful
    return (theItem->kind == STAFF_BLINKING || theItem->kind == STAFF_OBSTRUCTION ? 10000 : 5000) / theItem->enchant1;
}""",
    "v0.2.25: O'Brien's marked Fire/Lightning/Poison staffs keep +3 effect",
)

# Version banner.
replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.24\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.25\\n\");",
    "O'Brien Must Survive v0.2.25",
)

print("O'Brien Must Survive v0.2.25 applied.")
print("- Ring of Wisdom +3 is retained and still accelerates staff recharge normally")
print("- Fire / Lightning / Poison remain 20/20 capacity with +3 effect strength")
print("- Their passive base recharge interval is now 5000 ticks instead of 5000/3")
print("- Emergency Power Cells remain 20-unit finite reserves at 1 unit / 100 turns")
print("- Native +3 Recharging charm remains the slow strategic full-system reset")
print("- Blinking 10/10, Tunneling 3/3 and all ordinary dungeon staffs are unchanged")
print("Build normally with: make -B")
