#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.14 to a clean Brogue CE 1.15.1 tree.

v0.2.14 includes v0.2.13 and moves both fixed +3 mission rings into
O'Brien's starting backpack. Ring of Regeneration +3 and Ring of Wisdom +3
are automatically equipped at deployment. They remain ordinary Brogue
equipment afterward and can be replaced normally by the player.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_13.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_13.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.13 source was not found.")


# The two +3 rings are standard mission equipment, not optional floor loot.
# Use Brogue's native equipItem() path so ring bonuses, flags and both ring slots
# are initialized exactly as normal equipment would be. force=true only prevents
# startup equipment friction; the rings are not locked and can be replaced later.
replace_once(
    "src/brogue/RogueMain.c",
    "static void obrienLoadStartingPack(void) {",
    r'''// v0.2.14 standard mission rings: carried and equipped from turn zero.
static void obrienAddAndEquipMissionRing(short kind, short enchant) {
    item *ring = generateItem(RING, kind);

    if (!ring) {
        return;
    }

    ring->quantity = 1;
    ring->flags &= ~ITEM_CURSED;
    ring->enchant1 = enchant;
    identifyItemKind(ring);
    identify(ring);
    ring = addItemToPack(ring);

    if (ring) {
        equipItem(ring, true, NULL);
    }
}

static void obrienLoadStartingPack(void) {''',
    "v0.2.14 standard mission rings",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    obrienAddMissionItemToPack(STAFF, STAFF_TUNNELING, 3); // v0.2.13 Tunneling in starting pack\n",
    """    obrienAddMissionItemToPack(STAFF, STAFF_TUNNELING, 3); // v0.2.13 Tunneling in starting pack\n\n    // Standard passive support: both native Brogue ring slots begin occupied.\n    obrienAddAndEquipMissionRing(RING_REGENERATION, 3);\n    obrienAddAndEquipMissionRing(RING_WISDOM, 3);\n""",
    "obrienAddAndEquipMissionRing(RING_REGENERATION, 3);",
)

# Remove the old depth-1 floor-cache copies so the rings are not duplicated.
replace_once(
    "src/brogue/RogueMain.c",
    "    obrienPlaceSupplyItem(RING, RING_REGENERATION, 1, 3, anchor);\n",
    "",
    "v0.2.14 standard mission rings",
)
replace_once(
    "src/brogue/RogueMain.c",
    "    obrienPlaceSupplyItem(RING, RING_WISDOM, 1, 3, anchor);\n",
    "",
    "v0.2.14 standard mission rings",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.13\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.14\\n\");",
    "O'Brien Must Survive v0.2.14",
)

print("O'Brien Must Survive v0.2.14 applied.")
print("- Starting pack now includes Ring of Regeneration +3")
print("- Starting pack now includes Ring of Wisdom +3")
print("- Both rings are automatically equipped at deployment")
print("- Rings are not locked; normal Brogue ring swapping remains available")
print("- Initial stairhead cache no longer contains duplicate mission rings")
print("Build normally with: make -B")
