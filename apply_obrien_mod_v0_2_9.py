#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.9 to a clean Brogue CE 1.15.1 tree.

v0.2.9 includes v0.2.8 and rebalances the periodic DS9 stairhead cache around
area-effect gas canisters instead of short-range darts and javelins. Confusion,
paralysis and poison gas are the reusable tactical payload classes for O'Brien's
Fire staff follow-up; no incineration potion is added because Fire provides the
ignition source already.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_8.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_8.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.8 source was not found.")


# Darts and javelins are short-range single-target tools and no longer deserve
# fixed space in the 5-depth emergency cache. Replace them with a second canister
# of each AoE gas type. These remain finite floor supplies, not infinite attacks.
replace_once(
    "src/brogue/RogueMain.c",
    """    obrienPlaceSupplyItem(FOOD, RATION, 2, 0, anchor);\n    obrienPlaceSupplyItem(WEAPON, DART, 15, 0, anchor);\n    obrienPlaceSupplyItem(WEAPON, JAVELIN, 4, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 1, 0, anchor);""",
    """    obrienPlaceSupplyItem(FOOD, RATION, 2, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 1, 0, anchor);""",
    "v0.2.9 AoE gas resupply",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    // Finite tactical gas canisters: offensive tools, not survival consumables.\n    obrienPlaceSupplyItem(POTION, POTION_POISON, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 1, 0, anchor);""",
    """    // v0.2.9 AoE gas resupply: finite battlefield-control payloads.\n    // Fire staff supplies the ignition follow-up, so no dedicated incineration flask is required.\n    obrienPlaceSupplyItem(POTION, POTION_POISON, 2, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 2, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);""",
    "v0.2.9 AoE gas resupply",
)

print("O'Brien Must Survive v0.2.9 applied.")
print("- Periodic 5-depth caches no longer include 15 darts or 4 javelins")
print("- Every periodic cache now includes 2 poison gas, 2 paralysis gas and 2 confusion gas potions")
print("- Gas remains finite floor loot and is never forced into the backpack")
print("- No incineration potion was added; the Fire staff remains the ignition source")
print("- Initial cache, Recharge spell, Blink and medical cadence are unchanged")
print("Build normally with: make -B")
