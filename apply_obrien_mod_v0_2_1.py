#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.1 to a clean Brogue CE 1.15.1 tree.

v0.2.1 includes v0.2, then changes Doctor Bashir from an eager combat ally into
a defensive field medic: he follows and supports O'Brien, heals/shields/hastes,
keeps his distance, retreats when badly hurt, and does not initiate attacks.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
BASE_PATCH = ROOT / "apply_obrien_mod.py"

if not BASE_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod.py next to this updater.")

# First apply the complete v0.2 variant/supply/pronoun patch. It is idempotent.
runpy.run_path(str(BASE_PATCH), run_name="__main__")


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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2 source was not found.")


# Bashir should behave like a doctor/support officer, not a second assault unit.
replace_once(
    "src/brogue/RogueMain.c",
    "bashir->info.flags |= (MONST_MALE | MONST_MAINTAINS_DISTANCE);",
    "bashir->info.flags |= (MONST_MALE | MONST_MAINTAINS_DISTANCE | MONST_FLEES_NEAR_DEATH);",
    "MONST_MALE | MONST_MAINTAINS_DISTANCE | MONST_FLEES_NEAR_DEATH",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    bashir->info.accuracy = 120;\n    bashir->info.damage.lowerBound = 2;\n    bashir->info.damage.upperBound = 4;""",
    """    // Bashir can defend himself if forced by an abnormal status, but he is not a fighter.\n    bashir->info.accuracy = 75;\n    bashir->info.damage.lowerBound = 1;\n    bashir->info.damage.upperBound = 2;""",
    "Bashir can defend himself if forced by an abnormal status",
)

# Keep ordinary Brogue allies unchanged. Only Bashir in the O'Brien variant refuses
# to initiate physical attacks. His healing/protection/haste bolts are support logic
# and continue to function normally.
replace_once(
    "src/brogue/Monsters.c",
    """boolean monsterWillAttackTarget(const creature *attacker, const creature *defender) {\n    if (attacker == defender || (defender->bookkeepingFlags & MB_IS_DYING)) {\n        return false;\n    }\n    if (attacker == &player""",
    """boolean monsterWillAttackTarget(const creature *attacker, const creature *defender) {\n    if (attacker == defender || (defender->bookkeepingFlags & MB_IS_DYING)) {\n        return false;\n    }\n\n    // Doctor Bashir is a field medic. In this variant he supports O'Brien rather\n    // than seeking enemies to fight. Discord can still override this, preserving\n    // the normal Brogue status-effect semantics.\n    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n        && attacker != &player\n        && attacker->creatureState == MONSTER_ALLY\n        && !strcmp(attacker->info.monsterName, \"Bashir\")\n        && !attacker->status[STATUS_DISCORDANT]) {\n        return false;\n    }\n\n    if (attacker == &player""",
    "Doctor Bashir is a field medic",
)

print("O'Brien Must Survive v0.2.1 applied: Bashir is now a defensive support medic.")
print("Build normally with: make -B")
