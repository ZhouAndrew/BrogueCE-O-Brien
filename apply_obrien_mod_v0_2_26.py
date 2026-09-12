#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.26 to a clean Brogue CE 1.15.1 tree.

v0.2.26 shortens the in-game HSO unit name for Brogue's narrow sidebar.
The Call Security spell and all HSO behavior remain unchanged; only the runtime
unit name changes from "Holographic Security Officer" to "Security Hologram".

The rename is applied consistently to identity checks as well as display text,
so the one-HSO limit, permanent ally protection and regroup behavior continue
to recognize the deployed hologram correctly.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_25.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_25.py next to this updater.")

runpy.run_path(str(PREVIOUS_PATCH), run_name="__main__")


# v0.2.24 used the full title as both the visible monster name and the runtime
# identity key. Replace every occurrence together so display and identity cannot
# drift apart and accidentally permit duplicate holograms.
monsters_path = ROOT / "src/brogue/Monsters.c"
monsters_text = monsters_path.read_text(encoding="utf-8")
old_name = "Holographic Security Officer"
new_name = "Security Hologram"

if old_name in monsters_text:
    monsters_text = monsters_text.replace(old_name, new_name)
    monsters_path.write_text(monsters_text, encoding="utf-8")
    print("patched src/brogue/Monsters.c")
elif new_name in monsters_text:
    print("already patched src/brogue/Monsters.c")
else:
    raise SystemExit("Cannot patch src/brogue/Monsters.c: HSO runtime name not found.")


# Version banner.
rogue_main_path = ROOT / "src/brogue/RogueMain.c"
rogue_main_text = rogue_main_path.read_text(encoding="utf-8")
old_banner = "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.25"
new_banner = "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.26"

if old_banner in rogue_main_text:
    rogue_main_path.write_text(rogue_main_text.replace(old_banner, new_banner, 1), encoding="utf-8")
    print("patched src/brogue/RogueMain.c")
elif new_banner in rogue_main_text:
    print("already patched src/brogue/RogueMain.c")
else:
    raise SystemExit("Cannot patch src/brogue/RogueMain.c: v0.2.25 banner not found.")

print("O'Brien Must Survive v0.2.26 applied.")
print("- Call Security remains the intrinsic C spell and still consumes no backpack slot")
print("- HSO sidebar/runtime name shortened: Holographic Security Officer -> Security Hologram")
print("- One-HSO limit and permanent-ally identity checks use the new short name")
print("- HSO combat stats, Lightning/Poison emitters, flight and self-repair are unchanged")
print("- O'Brien staff recharge pacing and +3 Ring of Wisdom are unchanged from v0.2.25")
print("Build normally with: make -B")
