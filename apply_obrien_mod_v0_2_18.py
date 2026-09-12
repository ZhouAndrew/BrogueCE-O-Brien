#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.18 to a clean Brogue CE 1.15.1 tree.

v0.2.18 replaces the floor/cadence Recharging-scroll scheme with one ordinary
Brogue Scroll of Recharging carried in O'Brien's starting backpack. It remains
a normal one-use scroll. In O'Brien mode, the v0.2.15 integration still means
using it also fills all Starfleet Emergency Power Cells to 20/20.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_17.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_17.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.17 source was not found.")


# Add one ordinary Brogue scroll to the starting pack without changing how the
# scroll itself works. It uses the normal Apply/consume path.
replace_once(
    "src/brogue/RogueMain.c",
    "static void obrienLoadStartingPack(void) {",
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

static void obrienLoadStartingPack(void) {''',
    "obrienAddMissionScrollToPack",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    obrienAddEmergencyPowerCellToPack();
    obrienAddEmergencyPowerCellToPack();
    obrienAddEmergencyPowerCellToPack(); // v0.2.15 emergency power cells""",
    """    obrienAddEmergencyPowerCellToPack();
    obrienAddEmergencyPowerCellToPack();
    obrienAddEmergencyPowerCellToPack(); // v0.2.15 emergency power cells

    // v0.2.18 ordinary Recharging spell/scroll carried from deployment.
    obrienAddMissionScrollToPack(SCROLL_RECHARGING);""",
    "v0.2.18 ordinary Recharging spell/scroll carried from deployment",
)

# Remove the depth-1 floor-staged scroll introduced in v0.2.16.
replace_once(
    "src/brogue/RogueMain.c",
    """    // v0.2.16 emergency external power: one high-power recharge source at deployment.
    obrienPlaceSupplyItem(SCROLL, SCROLL_RECHARGING, 1, 0, anchor);
""",
    "",
    "v0.2.18 ordinary Recharging spell/scroll carried from deployment",
)

# Remove the every-ten-depth extra scroll introduced in v0.2.17. Recharging
# scrolls after deployment should once again come only from normal dungeon loot.
replace_once(
    "src/brogue/RogueMain.c",
    """    // v0.2.17 deep logistics reset: one Recharge scroll every ten depths.
    if (depth % (OBRIEN_SUPPLY_INTERVAL * 2) == 0) {
        obrienPlaceSupplyItem(SCROLL, SCROLL_RECHARGING, 1, 0, anchor);
    }

""",
    "",
    "v0.2.18 ordinary Recharging spell/scroll carried from deployment",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.17\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.18\\n\");",
    "O'Brien Must Survive v0.2.18",
)

print("O'Brien Must Survive v0.2.18 applied.")
print("- One ordinary Scroll of Recharging starts in O'Brien's backpack")
print("- The stairhead Recharging scroll is removed")
print("- The every-ten-depth Recharging-scroll resupply is removed")
print("- The scroll remains a normal one-use Brogue consumable")
print("- In O'Brien mode it also fills Starfleet Emergency Power Cells to 20/20")
print("Build normally with: make -B")
