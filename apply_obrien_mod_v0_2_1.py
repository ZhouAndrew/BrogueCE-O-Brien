#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.1 to a clean Brogue CE 1.15.1 tree.

v0.2.1 includes v0.2, then changes Doctor Bashir from an eager combat ally into
a defensive field medic. He still has finite health and can fight at close range,
but he does not run across the level hunting enemies. His priority remains support.
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


# Bashir is a doctor/support officer, not a second assault unit. Keep the original
# finite 36 HP. He keeps distance when possible but can still defend himself in melee.
replace_once(
    "src/brogue/RogueMain.c",
    """    bashir->info.accuracy = 120;\n    bashir->info.damage.lowerBound = 2;\n    bashir->info.damage.upperBound = 4;""",
    """    // Bashir has finite health and is capable in close combat, but should not charge enemies.\n    bashir->info.accuracy = 100;\n    bashir->info.damage.lowerBound = 2;\n    bashir->info.damage.upperBound = 4;""",
    "Bashir has finite health and is capable in close combat",
)

# Keep ordinary Brogue allies unchanged. Only Bashir in the O'Brien variant is
# restricted to defensive close-range fighting. Distant enemies are not attack
# targets, so he will not chase them. Adjacent enemies may still be attacked.
# When badly hurt he stops initiating even adjacent melee unless discordant.
replace_once(
    "src/brogue/Monsters.c",
    """boolean monsterWillAttackTarget(const creature *attacker, const creature *defender) {\n    if (attacker == defender || (defender->bookkeepingFlags & MB_IS_DYING)) {\n        return false;\n    }\n    if (attacker == &player""",
    """boolean monsterWillAttackTarget(const creature *attacker, const creature *defender) {\n    if (attacker == defender || (defender->bookkeepingFlags & MB_IS_DYING)) {\n        return false;\n    }\n\n    // Doctor Bashir is a field medic with finite health, not an assault unit.\n    // He may fight an enemy already in melee range, but he will not acquire a\n    // distant enemy as an attack target and charge toward it. Below one-third\n    // health he stops initiating melee as well. Discord preserves normal Brogue\n    // status-effect behavior and can override this restraint.\n    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n        && attacker != &player\n        && attacker->creatureState == MONSTER_ALLY\n        && !strcmp(attacker->info.monsterName, \"Bashir\")\n        && !attacker->status[STATUS_DISCORDANT]\n        && (distanceBetween(attacker->loc, defender->loc) > 1\n            || attacker->currentHP <= attacker->info.maxHP / 3)) {\n        return false;\n    }\n\n    if (attacker == &player""",
    "Doctor Bashir is a field medic with finite health",
)

print("O'Brien Must Survive v0.2.1 applied: Bashir now fights defensively at close range only.")
print("Build normally with: make -B")
