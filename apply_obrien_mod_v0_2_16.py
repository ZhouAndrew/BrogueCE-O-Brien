#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.16 to a clean Brogue CE 1.15.1 tree.

v0.2.16 adds one emergency Scroll of Recharging to the initial stairhead cache.
It is deliberately staged on the floor instead of carried from turn zero. The
scroll remains a scarce external high-power recharge source: in O'Brien mode it
retains Brogue's normal recharge effect and also fills all Starfleet Emergency
Power Cells to 20/20. The v0.2.12 stairhead-clearance rule still applies.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_15.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_15.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.15 source was not found.")


# One emergency external recharge source is staged with the initial stairhead
# supplies. It is not part of the starting backpack and does not repeat in the
# five-depth periodic caches. Placement goes through obrienPlaceSupplyItem(), so
# the v0.2.12 clear 3x3 stairhead lane remains guaranteed.
replace_once(
    "src/brogue/RogueMain.c",
    "    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 2, 0, anchor);\n",
    """    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 2, 0, anchor);\n\n    // v0.2.16 emergency external power: one high-power recharge source at deployment.\n    obrienPlaceSupplyItem(SCROLL, SCROLL_RECHARGING, 1, 0, anchor);\n""",
    "v0.2.16 emergency external power",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.15\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.16\\n\");",
    "O'Brien Must Survive v0.2.16",
)

print("O'Brien Must Survive v0.2.16 applied.")
print("- Initial stairhead cache: one emergency Scroll of Recharging")
print("- The scroll is floor-staged, not preloaded in O'Brien's backpack")
print("- It retains native Brogue recharge behavior and fills Emergency Power Cells to 20/20")
print("- It does not repeat in periodic five-depth resupply caches")
print("- The clear 3x3 stairhead lane remains enforced")
print("Build normally with: make -B")
