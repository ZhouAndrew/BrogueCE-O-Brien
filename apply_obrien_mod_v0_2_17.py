#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.17 to a clean Brogue CE 1.15.1 tree.

v0.2.17 keeps the initial emergency Scroll of Recharging and adds one more
Scroll of Recharging to every tenth-depth stairhead cache (10, 20, 30, ...).
The ordinary five-depth caches at 5, 15, 25, ... do not receive one. All scrolls
remain physical floor supplies and obey the v0.2.12 clear 3x3 stairhead lane.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_16.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_16.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.16 source was not found.")


# Periodic caches already arrive every five depths. Add the high-power external
# recharge only on every second periodic cache: depths 10, 20, 30, ... . This is
# deliberately separate from the ordinary gas/food resupply so depth 5/15/25
# cannot reset all three Power Cells.
replace_once(
    "src/brogue/RogueMain.c",
    """    obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);\n\n    // A life potion is rare medical support, not an every-cache permanent-stat fountain.""",
    """    obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);\n\n    // v0.2.17 deep logistics reset: one Recharge scroll every ten depths.\n    if (depth % (OBRIEN_SUPPLY_INTERVAL * 2) == 0) {\n        obrienPlaceSupplyItem(SCROLL, SCROLL_RECHARGING, 1, 0, anchor);\n    }\n\n    // A life potion is rare medical support, not an every-cache permanent-stat fountain.""",
    "v0.2.17 deep logistics reset",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.16\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.17\\n\");",
    "O'Brien Must Survive v0.2.17",
)

print("O'Brien Must Survive v0.2.17 applied.")
print("- Initial stairhead cache still includes one emergency Scroll of Recharging")
print("- Depths 10, 20, 30, ... each receive one additional Scroll of Recharging")
print("- Depths 5, 15, 25, ... keep the ordinary periodic cache without a Recharge scroll")
print("- Recharge scrolls remain floor-staged and obey the clear 3x3 stairhead lane")
print("- Using one still fills Starfleet Emergency Power Cells to 20/20")
print("Build normally with: make -B")
