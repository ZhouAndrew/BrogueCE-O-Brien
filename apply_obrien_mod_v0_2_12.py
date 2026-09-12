#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.12 to a clean Brogue CE 1.15.1 tree.

v0.2.12 includes v0.2.11 and keeps stairhead logistics from forcing the player
through equipment tiles. DS9 caches still appear near designated stairwells,
but the 3x3 area centered on the stair anchor is reserved as an item-free exit
lane for O'Brien. If no suitable cache tile can be found outside that clear
zone, that supply item is omitted rather than blocking the route.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_11.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_11.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.11 source was not found.")


# Cache items should be choices beside the route, never a carpet the player must
# cross immediately after arriving. Keep the stair square and all eight adjacent
# squares free of O'Brien supply items. Retrying lets the normal Brogue placement
# helper find nearby alternatives; if the area is too cramped, omit the item rather
# than violating the clear-lane rule.
replace_once(
    "src/brogue/RogueMain.c",
    """    getQualifyingLocNear(&loc, anchor, true, 0,\n                         (T_OBSTRUCTS_ITEMS | T_OBSTRUCTS_PASSABILITY),\n                         (HAS_ITEM | HAS_MONSTER | HAS_PLAYER | HAS_STAIRS | IS_IN_MACHINE),\n                         false, false);\n\n    if (!coordinatesAreInMap(loc.x, loc.y)) {\n        deleteItem(supply);\n        return;\n    }\n\n    placeItemAt(supply, loc);""",
    """    // v0.2.12 clear stairhead lane: never place DS9 cache items on the stair\n    // or any of its eight neighboring squares. The player must always have an\n    // equipment-free first step out of the stairhead area.\n    for (short attempt = 0; attempt < 64; attempt++) {\n        getQualifyingLocNear(&loc, anchor, true, 0,\n                             (T_OBSTRUCTS_ITEMS | T_OBSTRUCTS_PASSABILITY),\n                             (HAS_ITEM | HAS_MONSTER | HAS_PLAYER | HAS_STAIRS | IS_IN_MACHINE),\n                             false, false);\n\n        if (coordinatesAreInMap(loc.x, loc.y)\n            && (abs(loc.x - anchor.x) > 1 || abs(loc.y - anchor.y) > 1)) {\n            break;\n        }\n        loc = INVALID_POS;\n    }\n\n    if (!coordinatesAreInMap(loc.x, loc.y)) {\n        deleteItem(supply);\n        return;\n    }\n\n    placeItemAt(supply, loc);""",
    "v0.2.12 clear stairhead lane",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.11\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.12\\n\");",
    "O'Brien Must Survive v0.2.12",
)

print("O'Brien Must Survive v0.2.12 applied.")
print("- Stairhead caches reserve the full 3x3 area around the stair anchor")
print("- O'Brien is never forced to step across DS9-supplied equipment to leave the stair")
print("- Cache items that cannot be placed outside the clear lane are omitted instead")
print("- Tunneling and all other auxiliary cache equipment remain available")
print("Build normally with: make -B")
