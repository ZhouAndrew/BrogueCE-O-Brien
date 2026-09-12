#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.11 to a clean Brogue CE 1.15.1 tree.

v0.2.11 includes v0.2.10 and changes the opening logistics model:
- O'Brien begins with his standard mission kit already in the backpack;
- Fire, Lightning and Poison staffs remain 20/20;
- Blinking remains 10/10 with the existing 20-space O'Brien cap;
- three separate +12 native Recharging charms begin in the backpack;
- those standard items are removed from the depth-1 stairhead cache;
- Fire Immunity, Invisibility and Haste are no longer fixed DS9 cache supplies;
  they remain ordinary Brogue loot when the dungeon generates them;
- auxiliary stairhead caches and normal Brogue weapon/item pickup remain intact.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_10.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_10.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.10 source was not found.")


def replace_exact_count(rel, old, new, expected_count, marker=None):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count == expected_count:
        path.write_text(text.replace(old, new), encoding="utf-8")
        print(f"patched {rel} ({expected_count} occurrences)")
        return
    if count == 0 and marker and marker in text:
        print(f"already patched {rel}")
        return
    raise SystemExit(
        f"Cannot patch {rel}: expected {expected_count} occurrences, found {count}."
    )


# Standard Starfleet mission equipment belongs in O'Brien's pack at deployment,
# not scattered on the floor around the first stairwell. Keep this helper narrow:
# it creates only the fixed mission kit and does not alter normal dungeon loot.
replace_once(
    "src/brogue/RogueMain.c",
    "static void obrienDeployInitialSupplies(pos anchor) {",
    r'''// v0.2.11 mission-ready start: fixed Starfleet equipment is already packed.
static void obrienAddMissionItemToPack(unsigned long category, short kind, short enchant) {
    item *supply = generateItem(category, kind);

    if (!supply) {
        return;
    }

    supply->quantity = 1;
    supply->flags &= ~ITEM_CURSED;

    if (category & CHARM) {
        supply->enchant1 = enchant;
        supply->charges = 0;
    } else if (category & STAFF) {
        supply->enchant1 = max(1, enchant);
        supply->charges = supply->enchant1;
    }

    identifyItemKind(supply);
    identify(supply);
    addItemToPack(supply);
}

static void obrienLoadStartingPack(void) {
    // Primary ranged mission kit. These are powerful tools, not extra hit points.
    obrienAddMissionItemToPack(STAFF, STAFF_FIRE, 20);
    obrienAddMissionItemToPack(STAFF, STAFF_LIGHTNING, 20);
    obrienAddMissionItemToPack(STAFF, STAFF_POISON, 20);
    obrienAddMissionItemToPack(STAFF, STAFF_BLINKING, 10);

    // Three independent native Brogue reserve-power units.
    obrienAddMissionItemToPack(CHARM, CHARM_RECHARGING, 12);
    obrienAddMissionItemToPack(CHARM, CHARM_RECHARGING, 12);
    obrienAddMissionItemToPack(CHARM, CHARM_RECHARGING, 12);
}

static void obrienDeployInitialSupplies(pos anchor) {''',
    "v0.2.11 mission-ready start",
)

# Remove the standard mission kit from the depth-1 floor cache now that it is
# carried from turn zero. Optional engineering/survival equipment remains floor
# loot, preserving Brogue's choice-driven inventory management.
for line in (
    "    obrienPlaceSupplyItem(STAFF, STAFF_BLINKING, 1, 10, anchor);\n",
    "    obrienPlaceSupplyItem(STAFF, STAFF_LIGHTNING, 1, 20, anchor);\n",
    "    obrienPlaceSupplyItem(STAFF, STAFF_FIRE, 1, 20, anchor);\n",
    "    obrienPlaceSupplyItem(STAFF, STAFF_POISON, 1, 20, anchor);\n",
):
    replace_exact_count(
        "src/brogue/RogueMain.c",
        line,
        "",
        1,
        "v0.2.11 mission-ready start",
    )

replace_exact_count(
    "src/brogue/RogueMain.c",
    "    obrienPlaceSupplyItem(CHARM, CHARM_RECHARGING, 1, 12, anchor);\n",
    "",
    3,
    "v0.2.11 mission-ready start",
)

# Fire immunity and invisibility are too situational to be fixed Starfleet issue,
# and haste already belongs naturally in Brogue's loot ecosystem. Remove all fixed
# DS9-cache copies (initial and periodic) without touching ordinary generation.
for line in (
    "    obrienPlaceSupplyItem(POTION, POTION_FIRE_IMMUNITY, 1, 0, anchor);\n",
    "    obrienPlaceSupplyItem(POTION, POTION_INVISIBILITY, 1, 0, anchor);\n",
    "    obrienPlaceSupplyItem(POTION, POTION_HASTE_SELF, 1, 0, anchor);\n",
):
    replace_exact_count(
        "src/brogue/RogueMain.c",
        line,
        "",
        2,
        "v0.2.11 mission-ready start",
    )

# Load the mission kit after Brogue's ordinary ration/dagger/darts/armor are set up.
# This keeps the original starting gear and leaves plenty of normal pack capacity.
replace_once(
    "src/brogue/RogueMain.c",
    """    theItem = generateItem(ARMOR, LEATHER_ARMOR);\n    theItem->enchant1 = 0;\n    theItem->flags &= ~(ITEM_CURSED | ITEM_RUNIC);\n    identify(theItem);\n    theItem = addItemToPack(theItem);\n    equipItem(theItem, false, NULL);""",
    """    theItem = generateItem(ARMOR, LEATHER_ARMOR);\n    theItem->enchant1 = 0;\n    theItem->flags &= ~(ITEM_CURSED | ITEM_RUNIC);\n    identify(theItem);\n    theItem = addItemToPack(theItem);\n    equipItem(theItem, false, NULL);\n\n    if (obrienVariantActive()) {\n        obrienLoadStartingPack();\n    }""",
    "obrienLoadStartingPack();",
)

# Update player-facing wording: standard gear is already on O'Brien; stairheads now
# represent auxiliary logistics rather than character-creation equipment pickup.
replace_once(
    "src/brogue/RogueMain.c",
    "        message(\"Starfleet supplies are staged near designated stairwells; choose what your pack can actually hold.\", 0);",
    "        message(\"Standard mission equipment is already loaded in your pack; auxiliary supplies are staged near designated stairwells.\", 0);",
    "Standard mission equipment is already loaded in your pack",
)

replace_once(
    "src/brogue/MainMenu.c",
    "    append(textBuf, \"A Starfleet field-survival variant. Mission supplies arrive by the stairwell; choose what you can carry and keep O'Brien alive.\\n\\n\", TEXT_MAX_LENGTH);",
    "    append(textBuf, \"A Starfleet field-survival variant. O'Brien starts mission-ready; auxiliary supplies arrive by the stairwell. Keep him alive.\\n\\n\", TEXT_MAX_LENGTH);",
    "O'Brien starts mission-ready",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.11\\n\");",
    "O'Brien Must Survive v0.2.11",
)

print("O'Brien Must Survive v0.2.11 applied.")
print("- Starting pack: Fire 20/20, Lightning 20/20, Poison 20/20, Blink 10/10")
print("- Starting pack: three separate +12 native Recharging charms")
print("- Standard mission kit is no longer scattered in the initial stairhead cache")
print("- Fixed Fire Immunity, Invisibility and Haste cache supplies removed")
print("- Those items remain available through normal Brogue random loot")
print("- Auxiliary stairhead supplies, random weapons and normal pickups remain intact")
print("Build normally with: make -B")
