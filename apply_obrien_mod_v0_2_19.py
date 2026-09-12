#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.19 to a clean Brogue CE 1.15.1 tree.

v0.2.19 corrects the carried recharge reserve introduced in v0.2.18: it is a
Spell of Recharging, not a Scroll of Recharging. The spell is carried in
O'Brien's starting backpack and uses the normal Apply command. Its recharge
effect remains integrated with v0.2.15, so casting it also fills all Starfleet
Emergency Power Cells to 20/20.

Implementation note: Brogue CE has no native SPELL item category, so the mission
spell reuses the existing recharging-effect inventory plumbing internally, but
it is explicitly marked and presented/handled as Spell of Recharging in the
O'Brien variant rather than as a scroll.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_18.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_18.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.18 source was not found.")


# A stable marker distinguishes the carried mission spell from ordinary dungeon
# Scrolls of Recharging. It is intentionally outside normal positive depth values.
replace_once(
    "src/brogue/Rogue.h",
    "#define OBRIEN_POWER_CELL_TRICKLE_TURNS 100",
    "#define OBRIEN_POWER_CELL_TRICKLE_TURNS 100\n#define OBRIEN_RECHARGE_SPELL_MARKER (-219)",
    "OBRIEN_RECHARGE_SPELL_MARKER",
)

# Replace the v0.2.18 scroll helper with a dedicated mission-spell helper. The
# marker is what makes this object semantically distinct from ordinary scrolls.
replace_once(
    "src/brogue/RogueMain.c",
    r'''static void obrienAddMissionScrollToPack(short kind) {
    item *scroll = generateItem(SCROLL, kind);

    if (!scroll) {
        return;
    }

    scroll->quantity = 1;
    scroll->flags &= ~ITEM_CURSED;
    identifyItemKind(scroll);
    identify(scroll);
    addItemToPack(scroll);
}
''',
    r'''static void obrienAddMissionRechargeSpellToPack(void) {
    item *spell = generateItem(SCROLL, SCROLL_RECHARGING);

    if (!spell) {
        return;
    }

    spell->quantity = 1;
    spell->flags &= ~ITEM_CURSED;
    spell->originDepth = OBRIEN_RECHARGE_SPELL_MARKER;
    identifyItemKind(spell);
    identify(spell);
    addItemToPack(spell);
}
''',
    "obrienAddMissionRechargeSpellToPack",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    // v0.2.18 ordinary Recharging spell/scroll carried from deployment.\n    obrienAddMissionScrollToPack(SCROLL_RECHARGING);""",
    """    // v0.2.19 genuine carried Spell of Recharging.\n    obrienAddMissionRechargeSpellToPack();""",
    "v0.2.19 genuine carried Spell of Recharging",
)

# Inventory naming: this explicitly-marked mission object is a Spell, never shown
# to the player as a scroll. Ordinary random Scrolls of Recharging are unchanged.
replace_once(
    "src/brogue/Items.c",
    r'''        case SCROLL:
            if (scrollTable[theItem->kind].identified || rogue.playbackOmniscience) {
                sprintf(root, "scroll%s of %s", pluralization, scrollTable[theItem->kind].name);''',
    r'''        case SCROLL:
            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
                && theItem->kind == SCROLL_RECHARGING
                && theItem->originDepth == OBRIEN_RECHARGE_SPELL_MARKER) {

                sprintf(root, "Spell%s of Recharging", pluralization);
            } else if (scrollTable[theItem->kind].identified || rogue.playbackOmniscience) {
                sprintf(root, "scroll%s of %s", pluralization, scrollTable[theItem->kind].name);''',
    "Spell%s of Recharging",
)

# Likewise, generic item-kind queries should identify it as a spell, not expose
# the internal recharging-scroll transport category.
replace_once(
    "src/brogue/Items.c",
    "void itemKindName(item *theItem, char *kindName) {\n\n    // use lookup table for randomly generated items with more than one kind per category",
    """void itemKindName(item *theItem, char *kindName) {\n\n    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE\n        && theItem->category == SCROLL\n        && theItem->kind == SCROLL_RECHARGING\n        && theItem->originDepth == OBRIEN_RECHARGE_SPELL_MARKER) {\n\n        strcpy(kindName, \"Spell of Recharging\");\n        return;\n    }\n\n    // use lookup table for randomly generated items with more than one kind per category""",
    "strcpy(kindName, \"Spell of Recharging\")",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.18\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.19\\n\");",
    "O'Brien Must Survive v0.2.19",
)

print("O'Brien Must Survive v0.2.19 applied.")
print("- Starting backpack contains one Spell of Recharging")
print("- It is shown and identified as a Spell, not a Scroll")
print("- Use the normal Apply command to cast it")
print("- Casting it performs the Recharging effect and fills Emergency Power Cells to 20/20")
print("- Ordinary dungeon Scrolls of Recharging remain ordinary scrolls")
print("Build normally with: make -B")
