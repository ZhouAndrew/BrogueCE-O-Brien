#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.3 to a clean Brogue CE 1.15.1 tree.

v0.2.3 includes v0.2.2 and restores/refines O'Brien-specific behavior:
- Bashir uses '&' instead of inheriting the player's '@' glyph;
- items picked up in O'Brien Must Survive are immediately identified;
- O'Brien's initial stairhead cache again includes a firebolt staff;
- inventory capacity remains normal Brogue behavior: full packs refuse pickups;
  nothing already carried is automatically ejected.

Auto-identification is scoped to the O'Brien variant. Brogue, Rapid Brogue and
Bullet Brogue keep their normal identification rules.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_2.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_2.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.2 source was not found.")


# '@' is reserved visually for the player. Bashir is a companion NPC.
replace_once(
    "src/brogue/RogueMain.c",
    """    strcpy(bashir->info.monsterName, \"Bashir\");\n    bashir->info.flags &= ~MONST_FEMALE;""",
    """    strcpy(bashir->info.monsterName, \"Bashir\");\n    bashir->info.displayChar = '&';\n    bashir->info.flags &= ~MONST_FEMALE;""",
    "bashir->info.displayChar = '&';",
)

# Restore O'Brien's firebolt staff as selectable stairhead equipment. It is placed
# on the floor like all mission-cache gear; it is never force-added to the pack.
replace_once(
    "src/brogue/RogueMain.c",
    """    obrienPlaceSupplyItem(STAFF, STAFF_BLINKING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_TUNNELING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_LIGHTNING, 1, 3, anchor);""",
    """    obrienPlaceSupplyItem(STAFF, STAFF_BLINKING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_TUNNELING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_LIGHTNING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_FIRE, 1, 3, anchor);""",
    "obrienPlaceSupplyItem(STAFF, STAFF_FIRE, 1, 3, anchor);",
)

# Restore the original O'Brien field-analysis concept as a runtime Variant rule.
# Identify before packing so global potion/scroll kind knowledge is updated before
# the pickup message is composed. If the pickup merges into a carried stack, also
# identify the returned stack so its per-item details are known immediately.
replace_once(
    "src/brogue/Items.c",
    """        theItem = addItemToPack(theItem);\n\n        itemName(theItem, buf2, true, true, NULL); // include suffix, article""",
    """        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identify(theItem);\n        }\n\n        theItem = addItemToPack(theItem);\n\n        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identify(theItem);\n        }\n\n        itemName(theItem, buf2, true, true, NULL); // include suffix, article""",
    "gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identify(theItem);",
)

print("O'Brien Must Survive v0.2.3 applied.")
print("- Bashir glyph: &")
print("- O'Brien pickup analysis: immediate identification")
print("- Initial cache: firebolt staff restored")
print("- Full pack: pickups remain on the floor; carried items are never auto-dropped")
print("Build normally with: make -B")
