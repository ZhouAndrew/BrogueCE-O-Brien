#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.22 to a clean Brogue CE 1.15.1 tree.

v0.2.22 makes Doctor Bashir permanent Starfleet crew and upgrades DS9
stairhead logistics:
- friendly fire can still injure Bashir, but it can never make him defect;
- old saves where friendly fire already stripped Bashir's ally state are repaired;
- periodic resupply moves from every 5 depths to every 3 depths;
- each periodic cache carries three +2 Health charms as field first-aid units;
- each cache carries one +3 ally-support staff, alternating Protection/Haste;
- each cache carries one Life potion for O'Brien plus ration and fruit;
- the existing finite levitation and battlefield-control gas resupply remains.

The v0.2.12 clear 3x3 stairhead lane and first-visit-only cache behavior remain
unchanged, so returning to an old supply floor cannot duplicate a cache.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_21.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_21.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.21 source was not found.")


# Bashir is permanent crew. Vanilla Brogue intentionally makes an ally defect
# when the player directly damages it; that behavior remains for ordinary allies,
# but is wrong for a Starfleet teammate who has merely been caught in friendly
# fire. Damage is NOT cancelled here -- only the unAlly transition is blocked.
replace_once(
    "src/brogue/Monsters.c",
    """void unAlly(creature *monst) {
    if (monst->creatureState == MONSTER_ALLY) {""",
    """void unAlly(creature *monst) {
    // v0.2.22 permanent crew: friendly fire can hurt Bashir, but never make him defect.
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && monst != NULL
        && !strcmp(monst->info.monsterName, "Bashir")) {

        return;
    }

    if (monst->creatureState == MONSTER_ALLY) {""",
    "v0.2.22 permanent crew",
)

# Repair saves made before v0.2.22 where the vanilla unAlly() path has already
# turned Bashir into a tracking/fleeing non-ally. This restores only team identity;
# status effects (poison, discord, fear, etc.) are left untouched.
replace_once(
    "src/brogue/Monsters.c",
    """void updateMonsterState(creature *monst) {
    short x, y, closestFearedEnemy;
    boolean awareOfPlayer;

    x = monst->loc.x;""",
    """void updateMonsterState(creature *monst) {
    short x, y, closestFearedEnemy;
    boolean awareOfPlayer;

    // v0.2.22 old-save repair: Bashir is Starfleet crew, not a tame dungeon pet.
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && monst != NULL
        && monst->currentHP > 0
        && !(monst->bookkeepingFlags & MB_IS_DYING)
        && !strcmp(monst->info.monsterName, "Bashir")
        && monst->creatureState != MONSTER_ALLY) {

        monst->creatureState = MONSTER_ALLY;
        monst->bookkeepingFlags |= MB_FOLLOWER;
        monst->leader = &player;
    }

    x = monst->loc.x;""",
    "v0.2.22 old-save repair",
)

# Starfleet logistics now check in every three depths instead of every five.
replace_once(
    "src/brogue/RogueMain.c",
    "#define OBRIEN_SUPPLY_INTERVAL 5",
    "#define OBRIEN_SUPPLY_INTERVAL 3",
    "#define OBRIEN_SUPPLY_INTERVAL 3",
)

# Replace the old five-depth cache. Keep the finite gas/levitation support from
# v0.2.9, but add a real medical/logistics layer every three depths.
replace_once(
    "src/brogue/RogueMain.c",
    """static void obrienDeployPeriodicSupplies(short depth, pos anchor) {
    // Resupply keeps the mission viable; it is intentionally biased toward survival,
    // movement and ammunition rather than throw-and-win offensive consumables.
    obrienPlaceSupplyItem(FOOD, RATION, 2, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 1, 0, anchor);

    // v0.2.9 AoE gas resupply: finite battlefield-control payloads.
    // Fire staff supplies the ignition follow-up, so no dedicated incineration flask is required.
    obrienPlaceSupplyItem(POTION, POTION_POISON, 2, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 2, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);

    // A life potion is rare medical support, not an every-cache permanent-stat fountain.
    if (depth % (OBRIEN_SUPPLY_INTERVAL * 2) == 0) {
        obrienPlaceSupplyItem(POTION, POTION_LIFE, 1, 0, anchor);
    }
}""",
    """static void obrienDeployPeriodicSupplies(short depth, pos anchor) {
    // v0.2.22 three-depth Starfleet resupply: routine medicine, food and
    // away-team support, while keeping the finite tactical gas allocation.
    obrienPlaceSupplyItem(FOOD, RATION, 1, 0, anchor);
    obrienPlaceSupplyItem(FOOD, FRUIT, 1, 0, anchor);

    // Three independent +2 Health charms serve as field first-aid units.
    // They are floor-staged choices and still consume normal pack slots.
    obrienPlaceSupplyItem(CHARM, CHARM_HEALTH, 1, 2, anchor);
    obrienPlaceSupplyItem(CHARM, CHARM_HEALTH, 1, 2, anchor);
    obrienPlaceSupplyItem(CHARM, CHARM_HEALTH, 1, 2, anchor);

    // One support staff per cache for strengthening the away team.
    // Alternate the role so repeated resupplies do not produce only one tool.
    if (((depth / OBRIEN_SUPPLY_INTERVAL) & 1) != 0) {
        obrienPlaceSupplyItem(STAFF, STAFF_PROTECTION, 1, 3, anchor);
    } else {
        obrienPlaceSupplyItem(STAFF, STAFF_HASTE, 1, 3, anchor);
    }

    // O'Brien's emergency medical reserve is issued at every resupply.
    obrienPlaceSupplyItem(POTION, POTION_LIFE, 1, 0, anchor);

    // Existing finite movement / battlefield-control allocation remains.
    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 1, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_POISON, 2, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 2, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);
}""",
    "v0.2.22 three-depth Starfleet resupply",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    printf("Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.21\\n");""",
    """    printf("Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.22\\n");""",
    "O'Brien Must Survive v0.2.22",
)

print("O'Brien Must Survive v0.2.22 applied.")
print("- Bashir is permanent crew: friendly fire still damages him but never causes defection")
print("- Old saves with a friendly-fire-defected Bashir repair his ally/follower identity")
print("- Periodic Starfleet resupply: every 3 depths (3, 6, 9, 12, ...)")
print("- Every cache: 3 x Health charm +2 field first-aid units")
print("- Every cache: 1 x ally-support staff +3, alternating Protection / Haste")
print("- Every cache: 1 x Potion of Life, 1 x ration, 1 x fruit")
print("- Existing levitation + finite poison/paralysis/confusion gas support remains")
print("- v0.2.12 clear 3x3 stairhead lane and first-visit-only cache behavior remain")
print("Build normally with: make -B")
