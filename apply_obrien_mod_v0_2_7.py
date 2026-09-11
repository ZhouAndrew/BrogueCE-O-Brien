#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.7 to a clean Brogue CE 1.15.1 tree.

v0.2.7 includes v0.2.6 and restores limited offensive gas canisters to the
periodic DS9 stairhead resupply. They are finite tactical consumables, not
survival supplies and not unlimited firepower.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_6.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_6.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.6 source was not found.")


# Periodic logistics should include finite tactical gas options. These are placed
# on the stairhead floor cache like all other supplies; nothing is forced into the
# pack. One of each gas per 5-depth cache keeps them useful without turning the
# mission into unlimited consumable firepower.
replace_once(
    "src/brogue/RogueMain.c",
    """    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_FIRE_IMMUNITY, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_INVISIBILITY, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_HASTE_SELF, 1, 0, anchor);\n\n    // A life potion is rare medical support, not an every-cache permanent-stat fountain.""",
    """    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_FIRE_IMMUNITY, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_INVISIBILITY, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_HASTE_SELF, 1, 0, anchor);\n\n    // Finite tactical gas canisters: offensive tools, not survival consumables.\n    obrienPlaceSupplyItem(POTION, POTION_POISON, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 1, 0, anchor);\n    obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 1, 0, anchor);\n\n    // A life potion is rare medical support, not an every-cache permanent-stat fountain.""",
    "Finite tactical gas canisters: offensive tools, not survival consumables.",
)

print("O'Brien Must Survive v0.2.7 applied.")
print("- Every periodic stairhead cache includes 1 poison gas, 1 paralysis gas and 1 confusion gas potion")
print("- Offensive gas remains finite floor loot; it is never auto-inserted into the pack")
print("- Survival supplies and the rare life-potion cadence are unchanged")
print("Build normally with: make -B")
