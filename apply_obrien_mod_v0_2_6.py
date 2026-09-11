#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.6 to a clean Brogue CE 1.15.1 tree.

v0.2.6 includes v0.2.5 and tightens the Starfleet field-kit rules:
- O'Brien gets full, explicit identification of inspected or picked-up objects,
  including enchantment, runic and curse information;
- the initial stairhead cache includes a 20/20 staff of poison for O'Brien;
- Bashir carries his own 20/20 staff of poison, but his AI remains the defensive
  medic behavior from v0.2.1/v0.2.2: no distant target acquisition or charging.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_5.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_5.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.5 source was not found.")


# Full tricorder identification on pickup. Type recognition alone is not enough:
# O'Brien must also know enchantment, runic and curse details clearly.
replace_once(
    "src/brogue/Items.c",
    """        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identifyItemKind(theItem);\n        }\n\n        theItem = addItemToPack(theItem);\n\n        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identifyItemKind(theItem);\n        }""",
    """        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identifyItemKind(theItem);\n            identify(theItem);\n        }\n\n        theItem = addItemToPack(theItem);\n\n        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n            identifyItemKind(theItem);\n            identify(theItem);\n        }""",
    "Full tricorder identification on pickup",
)

# Looking at an item is itself a tricorder scan, so the detail pane must never
# conceal enchantments, runics or curses in the O'Brien variant.
replace_once(
    "src/brogue/Items.c",
    """    singular = (theItem->quantity == 1 ? true : false);\n    carried = itemIsCarried(theItem);\n\n    // Name\n    itemName(theItem, theName, true, true, NULL);""",
    """    singular = (theItem->quantity == 1 ? true : false);\n    carried = itemIsCarried(theItem);\n\n    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {\n        // Full tricorder identification: type, enchantment, runic and curse state.\n        identifyItemKind(theItem);\n        identify(theItem);\n    }\n\n    // Name\n    itemName(theItem, theName, true, true, NULL);""",
    "Full tricorder identification: type, enchantment, runic and curse state",
)

# Restore the poison staff as part of O'Brien's selectable field cache. Offensive
# staffs use the same requested 20-charge mission capacity as firebolt/lightning.
replace_once(
    "src/brogue/RogueMain.c",
    """    obrienPlaceSupplyItem(STAFF, STAFF_TUNNELING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_LIGHTNING, 1, 20, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_FIRE, 1, 20, anchor);""",
    """    obrienPlaceSupplyItem(STAFF, STAFF_TUNNELING, 1, 3, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_LIGHTNING, 1, 20, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_FIRE, 1, 20, anchor);\n    obrienPlaceSupplyItem(STAFF, STAFF_POISON, 1, 20, anchor);""",
    "obrienPlaceSupplyItem(STAFF, STAFF_POISON, 1, 20, anchor);",
)

# Bashir also carries a finite 20/20 poison staff as field equipment. This does
# not add BOLT_POISON to his innate spell list, so he does not gain unlimited
# ranged poison fire and his defensive medic AI remains intact.
replace_once(
    "src/brogue/RogueMain.c",
    """    bashir->info.bolts[0] = BOLT_HEALING;\n    bashir->info.bolts[1] = 0;\n    bashir->info.bolts[2] = 0;\n    bashir->info.bolts[3] = 0;\n\n    becomeAllyWith(bashir);""",
    """    bashir->info.bolts[0] = BOLT_HEALING;\n    bashir->info.bolts[1] = 0;\n    bashir->info.bolts[2] = 0;\n    bashir->info.bolts[3] = 0;\n\n    // Bashir carries a finite poison staff; it is equipment, not an innate spell.\n    bashir->carriedItem = generateItem(STAFF, STAFF_POISON);\n    if (bashir->carriedItem) {\n        bashir->carriedItem->enchant1 = 20;\n        bashir->carriedItem->charges = 20;\n        identifyItemKind(bashir->carriedItem);\n        identify(bashir->carriedItem);\n    }\n\n    becomeAllyWith(bashir);""",
    "Bashir carries a finite poison staff",
)

print("O'Brien Must Survive v0.2.6 applied.")
print("- Full tricorder identification: type + enchantment + runic + curse state")
print("- O'Brien selectable poison staff: 20/20")
print("- Bashir carried poison staff: 20/20, finite equipment")
print("- Bashir remains a non-charging defensive medic; no innate poison bolt was added")
print("Build normally with: make -B")
