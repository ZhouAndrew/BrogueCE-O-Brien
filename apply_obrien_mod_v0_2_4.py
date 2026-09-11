#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.4 to a clean Brogue CE 1.15.1 tree.

v0.2.4 includes v0.2.3 and changes deep-water inventory behavior only for the
O'Brien variant: Starfleet field-pack contents no longer randomly wash out of
the player's inventory while wading/swimming through deep water.

Other water effects remain intact, and Brogue / Rapid Brogue / Bullet Brogue
keep the original Brogue current mechanic unchanged.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_3.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_3.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.3 source was not found.")


# Brogue normally has deep water periodically knock a random unequipped item out
# of the player's pack and send it drifting away. O'Brien's Starfleet field pack
# is secured, so suppress only that inventory-loss sub-behavior in this Variant.
# Deep water still extinguishes fire, affects visibility/movement, etc.
replace_once(
    "src/brogue/Time.c",
    """        if (monst == &player) {\n            if (!(pmap[x][y].flags & HAS_ITEM) && rand_percent(ticks * 50 / 100)) {\n                itemCandidates = numberOfMatchingPackItems(ALL_ITEMS, 0, (ITEM_EQUIPPED), false);""",
    """        if (monst == &player) {\n            if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE\n                && !(pmap[x][y].flags & HAS_ITEM)\n                && rand_percent(ticks * 50 / 100)) {\n                itemCandidates = numberOfMatchingPackItems(ALL_ITEMS, 0, (ITEM_EQUIPPED), false);""",
    "gameVariant != VARIANT_OBRIEN_MUST_SURVIVE",
)

print("O'Brien Must Survive v0.2.4 applied.")
print("- Deep water no longer ejects carried items in the O'Brien variant")
print("- Other water behavior is unchanged")
print("- Other Brogue variants retain the original current mechanic")
print("Build normally with: make -B")
