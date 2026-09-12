#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.13 to a clean Brogue CE 1.15.1 tree.

v0.2.13 includes v0.2.12 and moves the Tunneling staff into O'Brien's
mission-ready starting backpack. The depth-1 stairhead cache no longer carries
a duplicate Tunneling staff. All v0.2.12 clear-stairhead placement rules remain
unchanged.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_12.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_12.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.12 source was not found.")


# Tunneling is a core engineering tool, so O'Brien should deploy with it rather
# than having to recover it from the first stairhead cache.
replace_once(
    "src/brogue/RogueMain.c",
    """    obrienAddMissionItemToPack(STAFF, STAFF_POISON, 20);\n    obrienAddMissionItemToPack(STAFF, STAFF_BLINKING, 10);""",
    """    obrienAddMissionItemToPack(STAFF, STAFF_POISON, 20);\n    obrienAddMissionItemToPack(STAFF, STAFF_BLINKING, 10);\n    obrienAddMissionItemToPack(STAFF, STAFF_TUNNELING, 3);""",
    "obrienAddMissionItemToPack(STAFF, STAFF_TUNNELING, 3);",
)

# Remove the old floor-cache copy so the starting kit is not duplicated.
replace_once(
    "src/brogue/RogueMain.c",
    "    obrienPlaceSupplyItem(STAFF, STAFF_TUNNELING, 1, 3, anchor);\n",
    "",
    "v0.2.13 Tunneling in starting pack",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.12\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.13\\n\");",
    "O'Brien Must Survive v0.2.13",
)

# Add a stable marker for CI/idempotence without changing gameplay.
replace_once(
    "src/brogue/RogueMain.c",
    "    obrienAddMissionItemToPack(STAFF, STAFF_TUNNELING, 3);",
    "    obrienAddMissionItemToPack(STAFF, STAFF_TUNNELING, 3); // v0.2.13 Tunneling in starting pack",
    "v0.2.13 Tunneling in starting pack",
)

print("O'Brien Must Survive v0.2.13 applied.")
print("- Starting pack now includes Tunneling staff 3/3")
print("- Initial stairhead cache no longer contains a duplicate Tunneling staff")
print("- v0.2.12 clear 3x3 stairhead lane remains unchanged")
print("- Native Recharging charms can recharge Tunneling under Brogue's normal rules")
print("Build normally with: make -B")
