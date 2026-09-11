#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2 to a clean Brogue CE 1.15.1 source tree.

The mod is a real fourth game Variant. Normal/Easy/Wizard remain independent Modes.
Mission and periodic supplies are materialized on the floor by the stairwell so the
player chooses what to carry; they are never force-added to the pack.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent


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
    raise SystemExit(f"Cannot patch {rel}: expected Brogue CE 1.15.1 source was not found.")


if not (ROOT / "src/brogue/Rogue.h").exists():
    raise SystemExit("Run this script from the root of a Brogue CE source tree.")

# Do not try to layer v0.2 on top of the old compile-time v0.1.x patch.
all_probe = (ROOT / "src/brogue/RogueMain.c").read_text(encoding="utf-8")
if "OBRIEN_BROGUE" in all_probe and "VARIANT_OBRIEN_MUST_SURVIVE" not in all_probe:
    raise SystemExit("This tree contains the old OBRIEN_BROGUE compile-time patch. Apply v0.2 to a clean source tree.")

replace_once(
    "src/brogue/Rogue.h",
    """enum gameVariant {\n    VARIANT_BROGUE,\n    VARIANT_RAPID_BROGUE,\n    VARIANT_BULLET_BROGUE,\n    NUMBER_VARIANTS\n};""",
    """enum gameVariant {\n    VARIANT_BROGUE,\n    VARIANT_RAPID_BROGUE,\n    VARIANT_BULLET_BROGUE,\n    VARIANT_OBRIEN_MUST_SURVIVE,\n    NUMBER_VARIANTS\n};""",
    "VARIANT_OBRIEN_MUST_SURVIVE",
)

# Main menu: add O'Brien as a fourth Variant; Modes stay untouched.
replace_once(
    "src/brogue/MainMenu.c",
    """    snprintf(tmpBuf, TEXT_MAX_LENGTH, \"%sBullet Brogue%s\\n\", goldColorEscape, whiteColorEscape);\n    append(textBuf, tmpBuf, TEXT_MAX_LENGTH);\n    append(textBuf, \"No time? Death wish? Bullet Brogue is for you. Not best for new players!\\n\\n\", TEXT_MAX_LENGTH);\n\n    brogueButton buttons[3];\n    initializeMainMenuButton(&(buttons[0]), \"  %sR%sapid Brogue     \", 'r', 'R', NG_NOTHING);\n    initializeMainMenuButton(&(buttons[1]), \"     %sB%srogue        \", 'b', 'B', NG_NOTHING);\n    initializeMainMenuButton(&(buttons[2]), \"   Bu%sl%slet Brogue   \", 'l', 'L', NG_NOTHING);\n\n    const SavedDisplayBuffer rbuf = saveDisplayBuffer();\n    gameVariantChoice = printTextBox(textBuf, 20, 7, 45, &white, &black, buttons, 3);""",
    """    snprintf(tmpBuf, TEXT_MAX_LENGTH, \"%sBullet Brogue%s\\n\", goldColorEscape, whiteColorEscape);\n    append(textBuf, tmpBuf, TEXT_MAX_LENGTH);\n    append(textBuf, \"No time? Death wish? Bullet Brogue is for you. Not best for new players!\\n\\n\", TEXT_MAX_LENGTH);\n\n    snprintf(tmpBuf, TEXT_MAX_LENGTH, \"%sO'Brien Must Survive%s\\n\", goldColorEscape, whiteColorEscape);\n    append(textBuf, tmpBuf, TEXT_MAX_LENGTH);\n    append(textBuf, \"A Starfleet field-survival variant. Mission supplies arrive by the stairwell; choose what you can carry and keep O'Brien alive.\\n\\n\", TEXT_MAX_LENGTH);\n\n    brogueButton buttons[4];\n    initializeMainMenuButton(&(buttons[0]), \"  %sR%sapid Brogue     \", 'r', 'R', NG_NOTHING);\n    initializeMainMenuButton(&(buttons[1]), \"     %sB%srogue        \", 'b', 'B', NG_NOTHING);\n    initializeMainMenuButton(&(buttons[2]), \"   Bu%sl%slet Brogue   \", 'l', 'L', NG_NOTHING);\n    initializeMainMenuButton(&(buttons[3]), \" %sO%s'Brien Survives  \", 'o', 'O', NG_NOTHING);\n\n    const SavedDisplayBuffer rbuf = saveDisplayBuffer();\n    gameVariantChoice = printTextBox(textBuf, 14, 4, 58, &white, &black, buttons, 4);""",
    "O'Brien Must Survive",
)

replace_once(
    "src/brogue/MainMenu.c",
    """    } else if (gameVariantChoice == 2) {\n        gameVariant = VARIANT_BULLET_BROGUE;\n    } else {""",
    """    } else if (gameVariantChoice == 2) {\n        gameVariant = VARIANT_BULLET_BROGUE;\n    } else if (gameVariantChoice == 3) {\n        gameVariant = VARIANT_OBRIEN_MUST_SURVIVE;\n    } else {""",
    "gameVariantChoice == 3",
)

# CLI support.
replace_once(
    "src/platform/main.c",
    "\"--variant variant_name     run a variant game (options: rapid_brogue, bullet_brogue)\\n\"",
    "\"--variant variant_name     run a variant game (options: rapid_brogue, bullet_brogue, obrien_must_survive)\\n\"",
    "obrien_must_survive",
)

replace_once(
    "src/platform/main.c",
    """                if (!strcmp(\"bullet_brogue\", argv[i + 1])) {\n                    gameVariant = VARIANT_BULLET_BROGUE;\n                }\n                i++;""",
    """                if (!strcmp(\"bullet_brogue\", argv[i + 1])) {\n                    gameVariant = VARIANT_BULLET_BROGUE;\n                }\n                if (!strcmp(\"obrien_must_survive\", argv[i + 1]) || !strcmp(\"obrien\", argv[i + 1])) {\n                    gameVariant = VARIANT_OBRIEN_MUST_SURVIVE;\n                }\n                i++;""",
    "!strcmp(\"obrien\"",
)

# Never display a negative pack capacity. The actual O'Brien supply system also
# avoids forced inventory insertion, so this is a UI safety net rather than a hack.
replace_once(
    "src/brogue/Items.c",
    "itemSpaceRemaining = MAX_PACK_ITEMS - numberOfItemsInPack();",
    "itemSpaceRemaining = max(0, MAX_PACK_ITEMS - numberOfItemsInPack());",
    "max(0, MAX_PACK_ITEMS - numberOfItemsInPack())",
)

OBRIEN_HELPERS = r'''
#define OBRIEN_SUPPLY_INTERVAL 5

static boolean obrienVariantActive(void) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE;
}

static void obrienPlaceSupplyItem(unsigned long category, short kind, short quantity, short enchant, pos anchor) {
    item *supply = generateItem(category, kind);
    pos loc = INVALID_POS;

    if (!supply) {
        return;
    }

    if (quantity > 0) {
        supply->quantity = quantity;
    }
    supply->flags &= ~ITEM_CURSED;

    if (category & RING) {
        supply->enchant1 = enchant;
    } else if (category & CHARM) {
        supply->enchant1 = enchant;
        supply->charges = 0;
    } else if (category & STAFF) {
        supply->enchant1 = max(1, enchant);
        supply->charges = supply->enchant1;
    }

    identify(supply);

    getQualifyingLocNear(&loc, anchor, true, 0,
                         (T_OBSTRUCTS_ITEMS | T_OBSTRUCTS_PASSABILITY),
                         (HAS_ITEM | HAS_MONSTER | HAS_PLAYER | HAS_STAIRS | IS_IN_MACHINE),
                         false, false);

    if (!coordinatesAreInMap(loc.x, loc.y)) {
        deleteItem(supply);
        return;
    }

    placeItemAt(supply, loc);
}

static void obrienDeployInitialSupplies(pos anchor) {
    // A field cache, not a magically enlarged backpack. The player decides what to carry.
    obrienPlaceSupplyItem(FOOD, RATION, 2, 0, anchor);
    obrienPlaceSupplyItem(WEAPON, DART, 30, 0, anchor);
    obrienPlaceSupplyItem(WEAPON, INCENDIARY_DART, 6, 0, anchor);
    obrienPlaceSupplyItem(WEAPON, JAVELIN, 6, 0, anchor);

    // Survival and escape supplies. Deliberately no stockpile of offensive gas/fire potions.
    obrienPlaceSupplyItem(POTION, POTION_LIFE, 1, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 2, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_FIRE_IMMUNITY, 1, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_INVISIBILITY, 1, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_HASTE_SELF, 1, 0, anchor);

    // Reusable engineering / survival kit. Useful, but not infinite firepower.
    obrienPlaceSupplyItem(STAFF, STAFF_BLINKING, 1, 3, anchor);
    obrienPlaceSupplyItem(STAFF, STAFF_TUNNELING, 1, 3, anchor);
    obrienPlaceSupplyItem(STAFF, STAFF_LIGHTNING, 1, 3, anchor);
    obrienPlaceSupplyItem(CHARM, CHARM_HEALTH, 1, 2, anchor);
    obrienPlaceSupplyItem(CHARM, CHARM_PROTECTION, 1, 2, anchor);
    obrienPlaceSupplyItem(RING, RING_REGENERATION, 1, 3, anchor);
    obrienPlaceSupplyItem(RING, RING_WISDOM, 1, 3, anchor);
}

static void obrienDeployPeriodicSupplies(short depth, pos anchor) {
    // Resupply keeps the mission viable; it is intentionally biased toward survival,
    // movement and ammunition rather than throw-and-win offensive consumables.
    obrienPlaceSupplyItem(FOOD, RATION, 2, 0, anchor);
    obrienPlaceSupplyItem(WEAPON, DART, 15, 0, anchor);
    obrienPlaceSupplyItem(WEAPON, JAVELIN, 4, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_LEVITATION, 1, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_FIRE_IMMUNITY, 1, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_INVISIBILITY, 1, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_HASTE_SELF, 1, 0, anchor);

    // A life potion is rare medical support, not an every-cache permanent-stat fountain.
    if (depth % (OBRIEN_SUPPLY_INTERVAL * 2) == 0) {
        obrienPlaceSupplyItem(POTION, POTION_LIFE, 1, 0, anchor);
    }
}

static void obrienSpawnBashir(pos anchor) {
    creature *bashir = generateMonster(MK_YOU, false, false);
    if (!bashir) {
        return;
    }

    strcpy(bashir->info.monsterName, "Bashir");
    bashir->info.flags &= ~MONST_FEMALE;
    bashir->info.flags |= (MONST_MALE | MONST_MAINTAINS_DISTANCE);
    bashir->info.maxHP = 36;
    bashir->currentHP = bashir->info.maxHP;
    bashir->info.defense = 45;
    bashir->info.accuracy = 120;
    bashir->info.damage.lowerBound = 2;
    bashir->info.damage.upperBound = 4;
    bashir->info.damage.clumpFactor = 1;
    bashir->info.turnsBetweenRegen = 8;
    bashir->turnsUntilRegen = bashir->info.turnsBetweenRegen * 1000;
    bashir->info.bolts[0] = BOLT_HEALING;
    bashir->info.bolts[1] = BOLT_SHIELDING;
    bashir->info.bolts[2] = BOLT_HASTE;
    bashir->info.bolts[3] = 0;

    becomeAllyWith(bashir);
    bashir->loc = getQualifyingPathLocNear(anchor, true,
                                            T_DIVIDES_LEVEL, 0,
                                            T_PATHING_BLOCKER,
                                            (HAS_PLAYER | HAS_MONSTER | HAS_STAIRS | IS_IN_MACHINE),
                                            false);

    if (!coordinatesAreInMap(bashir->loc.x, bashir->loc.y)) {
        return;
    }

    pmapAt(bashir->loc)->flags |= HAS_MONSTER;
    refreshDungeonCell(bashir->loc);
}

static void obrienFirstVisitToDepth(short depth, pos entryStairs) {
    if (depth == 1) {
        obrienDeployInitialSupplies(entryStairs);
        obrienSpawnBashir(entryStairs);
        messageWithColor("Starfleet field supplies have materialized by the stairwell. Take only what you can carry.", &itemMessageColor, 0);
    } else if (depth % OBRIEN_SUPPLY_INTERVAL == 0) {
        obrienDeployPeriodicSupplies(depth, entryStairs);
        messageWithColor("A DS9 emergency resupply has materialized near the stairwell.", &itemMessageColor, 0);
    }
}
'''

replace_once(
    "src/brogue/RogueMain.c",
    "#include <time.h>\n\nint rogueMain()",
    "#include <time.h>\n\n" + OBRIEN_HELPERS + "\nint rogueMain()",
    "static boolean obrienVariantActive(void)",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    printf(\"Supports variant (bullet_brogue): %s\\n\", bulletBrogueVersion);""",
    """    printf(\"Supports variant (bullet_brogue): %s\\n\", bulletBrogueVersion);\n    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2\\n\");""",
    "Supports variant (obrien_must_survive)",
)

replace_once(
    "src/brogue/RogueMain.c",
    """static void welcome() {\n    char buf[DCOLS*3], buf2[DCOLS*3];\n    message(\"Hello and welcome, adventurer, to the Dungeons of Doom!\", 0);""",
    """static void welcome() {\n    char buf[DCOLS*3], buf2[DCOLS*3];\n\n    if (obrienVariantActive()) {\n        message(\"Chief O'Brien: emergency field mission active. Survival takes priority.\", 0);\n        message(\"Starfleet supplies are staged near designated stairwells; choose what your pack can actually hold.\", 0);\n        messageWithColor(\"Bashir is assigned as your field medic and support officer.\", &backgroundMessageColor, 0);\n        flavorMessage(\"A transporter shimmer fades from the stone around you.\");\n        return;\n    }\n\n    message(\"Hello and welcome, adventurer, to the Dungeons of Doom!\", 0);""",
    "Chief O'Brien: emergency field mission active",
)

replace_once(
    "src/brogue/RogueMain.c",
    """        case VARIANT_BULLET_BROGUE:\n            initializeGameVariantBulletBrogue();\n            break;\n        default:""",
    """        case VARIANT_BULLET_BROGUE:\n            initializeGameVariantBulletBrogue();\n            break;\n        case VARIANT_OBRIEN_MUST_SURVIVE:\n            // O'Brien is a rules/mission variant built on the full Brogue dungeon tables.\n            initializeGameVariantBrogue();\n            break;\n        default:""",
    "case VARIANT_OBRIEN_MUST_SURVIVE:",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    player.info = monsterCatalog[0];\n    setPlayerDisplayChar();\n    initializeGender(&player);""",
    """    player.info = monsterCatalog[0];\n    setPlayerDisplayChar();\n    if (obrienVariantActive()) {\n        // Miles O'Brien is male; do not let Brogue randomly produce feminine pronouns.\n        player.info.flags &= ~MONST_FEMALE;\n        player.info.flags |= MONST_MALE;\n    }\n    initializeGender(&player);""",
    "Miles O'Brien is male",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    if (!levels[rogue.depthLevel-1].visited) {\n        levels[rogue.depthLevel-1].visited = true;""",
    """    if (!levels[rogue.depthLevel-1].visited) {\n        if (obrienVariantActive() && stairDirection == 1) {\n            obrienFirstVisitToDepth(rogue.depthLevel, rogue.upLoc);\n        }\n        levels[rogue.depthLevel-1].visited = true;""",
    "obrienFirstVisitToDepth(rogue.depthLevel, rogue.upLoc)",
)

print("O'Brien Must Survive v0.2 patch applied.")
print("Build normally; no -DOBRIEN_BROGUE flag is required.")
