#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.2 to a clean Brogue CE 1.15.1 tree.

v0.2.2 includes v0.2.1 and corrects Doctor Bashir's role again:
- finite health;
- follows O'Brien instead of charging distant enemies;
- may defend himself only when an enemy is already adjacent;
- medical support is healing only;
- no haste ability;
- no personal shield ability;
- no Starfleet-issued protection charm in the initial cache.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_1.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_1.py next to this updater.")

# Apply the complete v0.2.1 patch first. It is designed to be idempotent.
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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.1 source was not found.")


# Bashir is a doctor, not a Borg drone or a fantasy buffer. Healing is the only
# special support ability attached to him. He has no haste and no personal shield.
replace_once(
    "src/brogue/RogueMain.c",
    """    bashir->info.bolts[0] = BOLT_HEALING;\n    bashir->info.bolts[1] = BOLT_SHIELDING;\n    bashir->info.bolts[2] = BOLT_HASTE;\n    bashir->info.bolts[3] = 0;""",
    """    // Bashir has no personal shield or haste ability; medical support is healing only.\n    bashir->info.bolts[0] = BOLT_HEALING;\n    bashir->info.bolts[1] = 0;\n    bashir->info.bolts[2] = 0;\n    bashir->info.bolts[3] = 0;""",
    "Bashir has no personal shield or haste ability",
)

# Likewise, do not frame a magical protection charm as standard Starfleet field kit.
# Dungeon-generated Brogue items remain part of the dungeon; this only changes the
# mission cache supplied by DS9.
replace_once(
    "src/brogue/RogueMain.c",
    "    obrienPlaceSupplyItem(CHARM, CHARM_PROTECTION, 1, 2, anchor);\n",
    "",
    "Bashir has no personal shield or haste ability",
)

print("O'Brien Must Survive v0.2.2 applied: Bashir heals, stays close, and has no shield or haste.")
print("Build normally with: make -B")
