#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.30 to a Brogue CE 1.15.1 tree.

v0.2.30 is a compatibility-preserving UI/logistics/ally-information update:

- O'Brien Must Survive moves from Change Variant to Change Mode in the title UI,
  while keeping the existing VARIANT_OBRIEN_MUST_SURVIVE enum value and tagged
  recording/save header representation. Old saves therefore keep the same wire
  format and legacy CLI variant names remain valid.
- Bashir and the Security Hologram get dedicated ally examine text instead of
  inheriting MK_YOU/MK_GOLEM hostile combat previews.
- The Security Hologram still reflects hostile reflectable bolts, but beneficial
  ally-targeted support bolts pass through normally.
- Starfleet resupply no longer issues caustic/poison gas. The former poison-gas
  allocation is converted to paralysis-gas canisters, carried as one magazine
  stack that consumes one canister per throw.
- O'Brien Recharging effects include wands and other native charge/cooldown
  equipment (staffs, wands and charms) while leaving non-rechargeable weapon and
  armor bookkeeping untouched.
- Old "Holographic Security Officer" save instances are recognized and normalized
  to "Security Hologram" at runtime.
- New v0.2.30 games start with one Scroll of Magic Mapping and one directional
  Wand of Negation. A ruleset-generation byte in the previously zero tail of the
  recording version field keeps pre-v0.2.30 O'Brien saves on their historical
  starting kit and historical v0.2.29 gameplay rules during replay.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_29.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_29.py next to this updater.")


def source_has_v029_or_later():
    main = ROOT / "src/brogue/RogueMain.c"
    recordings = ROOT / "src/brogue/Recordings.c"
    if not main.exists() or not recordings.exists():
        return False
    main_text = main.read_text(encoding="utf-8")
    rec_text = recordings.read_text(encoding="utf-8")
    return (
        "RECORDING_VARIANT_TAG" in rec_text
        and (
            "O'Brien Must Survive v0.2.29" in main_text
            or "O'Brien Must Survive v0.2.30" in main_text
        )
    )


if source_has_v029_or_later():
    print("Detected O'Brien v0.2.29+ already applied; skipping historical patch replay.")
else:
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
    raise SystemExit(f"Cannot patch {rel}: expected compatible v0.2.29 source was not found.")

def insert_once_before(rel, anchor, insertion, marker):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print(f"already patched {rel}")
        return
    if anchor in text:
        path.write_text(text.replace(anchor, insertion + anchor, 1), encoding="utf-8")
        print(f"patched {rel}")
        return
    raise SystemExit(f"Cannot patch {rel}: insertion anchor was not found.")


# ---------------------------------------------------------------------------
# Save/recording ruleset generation.
#
# Header bytes 0..14 are the historical version-string field. CE 1.15.1 ends
# well before byte 14, so byte 14 is zero in old recordings and remains after
# the C-string terminator. v0.2.30 stores its O'Brien ruleset generation there
# without changing the 36-byte header layout, seed offsets or variant id.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Recordings.c",
    "#define RECORDING_MODE_MASK            0x0F",
    """#define RECORDING_MODE_MASK            0x0F

#define OBRIEN_RULESET_HEADER_INDEX    14
#define OBRIEN_RULESET_V030            30
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V030;

boolean obrienRulesetAtLeast(short version) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && obrienRulesetVersion >= version;
}""",
    "OBRIEN_RULESET_V030",
)

replace_once(
    "src/brogue/Rogue.h",
    "    void initRecording(void);",
    """    void initRecording(void);
    boolean obrienRulesetAtLeast(short version);""",
    "boolean obrienRulesetAtLeast(short version);",
)

replace_once(
    "src/brogue/Recordings.c",
    """    for (i = 0; rogue.versionString[i] != '\\0'; i++) {
        c[i] = rogue.versionString[i];
    }
    c[15] = RECORDING_VARIANT_TAG""",
    """    for (i = 0; rogue.versionString[i] != '\\0'; i++) {
        c[i] = rogue.versionString[i];
    }
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
        c[OBRIEN_RULESET_HEADER_INDEX] = obrienRulesetVersion;
    }
    c[15] = RECORDING_VARIANT_TAG""",
    "c[OBRIEN_RULESET_HEADER_INDEX] = obrienRulesetVersion;",
)

replace_once(
    "src/brogue/Recordings.c",
    """        for (i=0; i<15; i++) {
            versionString[i] = recallChar();
        }
        modeVariantByte = recallChar();""",
    """        for (i=0; i<15; i++) {
            versionString[i] = recallChar();
        }
        obrienRulesetVersion = (unsigned char) versionString[OBRIEN_RULESET_HEADER_INDEX];
        modeVariantByte = recallChar();""",
    "obrienRulesetVersion = (unsigned char) versionString[OBRIEN_RULESET_HEADER_INDEX];",
)

replace_once(
    "src/brogue/Recordings.c",
    """    } else {
        // If present, set the patch version for playing the game.
        rogue.patchVersion = BROGUE_PATCH;""",
    """    } else {
        // Brand-new games use the current ruleset. When a historical save is
        // loaded and then resumed, playback has already restored its old value
        // and switchToPlaying() leaves it intact.
        obrienRulesetVersion = OBRIEN_RULESET_V030;

        // If present, set the patch version for playing the game.
        rogue.patchVersion = BROGUE_PATCH;""",
    "Brand-new games use the current ruleset",
)

# ---------------------------------------------------------------------------
# UI: expose O'Brien under Change Mode, but retain the historical variant ID.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/MainMenu.c",
    """    snprintf(tmpBuf, TEXT_MAX_LENGTH, "%sO'Brien Must Survive%s\\n", goldColorEscape, whiteColorEscape);
    append(textBuf, tmpBuf, TEXT_MAX_LENGTH);
    append(textBuf, "A Starfleet field-survival variant. O'Brien starts mission-ready; auxiliary supplies arrive by the stairwell. Keep him alive.\\n\\n", TEXT_MAX_LENGTH);

    brogueButton buttons[4];
    initializeMainMenuButton(&(buttons[0]), "  %sR%sapid Brogue     ", 'r', 'R', NG_NOTHING);
    initializeMainMenuButton(&(buttons[1]), "     %sB%srogue        ", 'b', 'B', NG_NOTHING);
    initializeMainMenuButton(&(buttons[2]), "   Bu%sl%slet Brogue   ", 'l', 'L', NG_NOTHING);
    initializeMainMenuButton(&(buttons[3]), " %sO%s'Brien Survives  ", 'o', 'O', NG_NOTHING);

    const SavedDisplayBuffer rbuf = saveDisplayBuffer();
    gameVariantChoice = printTextBox(textBuf, 14, 4, 58, &white, &black, buttons, 4);""",
    """    brogueButton buttons[3];
    initializeMainMenuButton(&(buttons[0]), "  %sR%sapid Brogue     ", 'r', 'R', NG_NOTHING);
    initializeMainMenuButton(&(buttons[1]), "     %sB%srogue        ", 'b', 'B', NG_NOTHING);
    initializeMainMenuButton(&(buttons[2]), "   Bu%sl%slet Brogue   ", 'l', 'L', NG_NOTHING);

    const SavedDisplayBuffer rbuf = saveDisplayBuffer();
    gameVariantChoice = printTextBox(textBuf, 20, 7, 45, &white, &black, buttons, 3);""",
    "compatibility-preserving wire representation",
)

replace_once(
    "src/brogue/MainMenu.c",
    """    } else if (gameVariantChoice == 2) {
        gameVariant = VARIANT_BULLET_BROGUE;
    } else if (gameVariantChoice == 3) {
        gameVariant = VARIANT_OBRIEN_MUST_SURVIVE;
    } else {""",
    """    } else if (gameVariantChoice == 2) {
        gameVariant = VARIANT_BULLET_BROGUE;
    } else {""",
    "compatibility-preserving wire representation",
)

replace_once(
    "src/brogue/MainMenu.c",
    """    snprintf(tmpBuf, TEXT_MAX_LENGTH, "%sWizard Mode%s\\n", goldColorEscape, whiteColorEscape);
    append(textBuf, tmpBuf, TEXT_MAX_LENGTH);
    append(textBuf, "Play as an invincible wizard that starts with legendary items and is magically reborn after every "
                    "death. Summon monsters and make them friend or foe. Conjure any item out of thin air. "
                    "(Your score is not saved.)", TEXT_MAX_LENGTH);

    brogueButton buttons[3];
    initializeMainMenuButton(&(buttons[0]), "      %sW%sizard       ", 'w', 'W', NG_NOTHING);
    initializeMainMenuButton(&(buttons[1]), "       %sE%sasy        ", 'e', 'E', NG_NOTHING);
    initializeMainMenuButton(&(buttons[2]), "      %sN%sormal       ", 'n', 'N', NG_NOTHING);
    const SavedDisplayBuffer rbuf = saveDisplayBuffer();
    gameMode = printTextBox(textBuf, 10, 5, 66, &white, &black, buttons, 3);
    restoreDisplayBuffer(&rbuf);
    if (gameMode == 0) {
        rogue.mode = GAME_MODE_WIZARD;
    } else if (gameMode == 1) {
        rogue.mode = GAME_MODE_EASY;
    } else if (gameMode == 2) {
        rogue.mode = GAME_MODE_NORMAL;
    }

    rogue.nextGame = NG_NOTHING;""",
    """    snprintf(tmpBuf, TEXT_MAX_LENGTH, "%sWizard Mode%s\\n", goldColorEscape, whiteColorEscape);
    append(textBuf, tmpBuf, TEXT_MAX_LENGTH);
    append(textBuf, "Play as an invincible wizard that starts with legendary items and is magically reborn after every "
                    "death. Summon monsters and make them friend or foe. Conjure any item out of thin air. "
                    "(Your score is not saved.)\\n\\n", TEXT_MAX_LENGTH);

    snprintf(tmpBuf, TEXT_MAX_LENGTH, "%sO'Brien Must Survive%s\\n", goldColorEscape, whiteColorEscape);
    append(textBuf, tmpBuf, TEXT_MAX_LENGTH);
    append(textBuf, "Starfleet field-survival mode: mission equipment, Bashir medical support, Security Hologram, "
                    "tricorder identification and stairhead logistics. Keep O'Brien alive.", TEXT_MAX_LENGTH);

    brogueButton buttons[4];
    initializeMainMenuButton(&(buttons[0]), "      %sW%sizard       ", 'w', 'W', NG_NOTHING);
    initializeMainMenuButton(&(buttons[1]), "       %sE%sasy        ", 'e', 'E', NG_NOTHING);
    initializeMainMenuButton(&(buttons[2]), "      %sN%sormal       ", 'n', 'N', NG_NOTHING);
    initializeMainMenuButton(&(buttons[3]), " %sO%s'Brien Survives  ", 'o', 'O', NG_NOTHING);
    const SavedDisplayBuffer rbuf = saveDisplayBuffer();
    gameMode = printTextBox(textBuf, 7, 3, 72, &white, &black, buttons, 4);
    restoreDisplayBuffer(&rbuf);
    if (gameMode == 0) {
        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
            gameVariant = VARIANT_BROGUE;
        }
        rogue.mode = GAME_MODE_WIZARD;
    } else if (gameMode == 1) {
        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
            gameVariant = VARIANT_BROGUE;
        }
        rogue.mode = GAME_MODE_EASY;
    } else if (gameMode == 2) {
        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
            gameVariant = VARIANT_BROGUE;
        }
        rogue.mode = GAME_MODE_NORMAL;
    } else if (gameMode == 3) {
        // UI mode, compatibility-preserving wire representation: keep the
        // historical variant enum value so old O'Brien saves/recordings load.
        rogue.mode = GAME_MODE_NORMAL;
        gameVariant = VARIANT_OBRIEN_MUST_SURVIVE;
    }

    rogue.nextGame = NG_NOTHING;""",
    "compatibility-preserving wire representation",
)

replace_once(
    "src/brogue/MainMenu.c",
    """    if (WIZARD_MODE) {
        strcpy(gameModeString, "Wizard Mode");
    } else if (rogue.mode == GAME_MODE_EASY) {
        strcpy(gameModeString, "Easy Mode");
    }""",
    """    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
        strcpy(gameModeString, "O'Brien Must Survive");
    } else if (WIZARD_MODE) {
        strcpy(gameModeString, "Wizard Mode");
    } else if (rogue.mode == GAME_MODE_EASY) {
        strcpy(gameModeString, "Easy Mode");
    }""",
    "strcpy(gameModeString, \"O'Brien Must Survive\")",
)

# ---------------------------------------------------------------------------
# New v0.2.30 standard issue. These additions are ruleset-gated because adding
# generated items at turn zero changes RNG consumption and inventory letters.
# Old recordings therefore reconstruct the exact pre-v0.2.30 starting pack.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/RogueMain.c",
    "    obrienAddMissionItemToPack(STAFF, STAFF_TUNNELING, 3); // v0.2.13 Tunneling in starting pack\n",
    """    obrienAddMissionItemToPack(STAFF, STAFF_TUNNELING, 3); // v0.2.13 Tunneling in starting pack

    if (obrienRulesetAtLeast(30)) {
        // One-use map plus a native directional anti-magic weapon.
        obrienAddMissionItemToPack(SCROLL, SCROLL_MAGIC_MAPPING, 0);
        obrienAddMissionItemToPack(WAND, WAND_NEGATION, 0);
    }
""",
    "SCROLL_MAGIC_MAPPING, 0",
)

# ---------------------------------------------------------------------------
# Paralysis-gas magazine logistics.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Rogue.h",
    """#define OBRIEN_PRIMARY_STAFF_CAPACITY 20
#define OBRIEN_PRIMARY_STAFF_ENCHANTMENT 3
#define OBRIEN_PRIMARY_STAFF_MARKER (-221)""",
    """#define OBRIEN_PRIMARY_STAFF_CAPACITY 20
#define OBRIEN_PRIMARY_STAFF_ENCHANTMENT 3
#define OBRIEN_PRIMARY_STAFF_MARKER (-221)
#define OBRIEN_PARALYSIS_GAS_MAGAZINE_QUIVER 61001""",
    "OBRIEN_PARALYSIS_GAS_MAGAZINE_QUIVER",
)

insert_once_before(
    "src/brogue/Items.c",
    """/// @brief Checks if an item is a throwing weapon
/// @param theItem the item
/// @return true if the item is a throwing weapon
static boolean itemIsThrowingWeapon(const item *theItem) {""",
    """// v0.2.30 Starfleet paralysis-gas canisters use a quiver-style marker so
// the whole issued magazine occupies one pack slot while each throw consumes
// exactly one canister. Ordinary/random paralysis potions remain ordinary.
static boolean obrienIsParalysisGasMagazine(const item *theItem) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && obrienRulesetAtLeast(30)
        && theItem != NULL
        && (theItem->category & POTION)
        && theItem->kind == POTION_PARALYSIS
        && theItem->quiverNumber == OBRIEN_PARALYSIS_GAS_MAGAZINE_QUIVER;
}

""",
    "static boolean obrienIsParalysisGasMagazine",
)

replace_once(
    "src/brogue/Items.c",
    """static boolean itemWillStackWithPack(item *theItem) {
    item *tempItem;
    if (theItem->category & GEM) {""",
    """static boolean itemWillStackWithPack(item *theItem) {
    item *tempItem;

    // A marked paralysis-gas magazine behaves like a javelin quiver for pack
    // capacity. It may merge with an existing paralysis stack without needing
    // another slot; if either side is already a magazine, the merged stack is one.
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && theItem != NULL
        && (theItem->category & POTION)
        && theItem->kind == POTION_PARALYSIS) {

        for (tempItem = packItems->nextItem; tempItem != NULL; tempItem = tempItem->nextItem) {
            if ((tempItem->category & POTION)
                && tempItem->kind == POTION_PARALYSIS
                && (obrienIsParalysisGasMagazine(theItem)
                    || obrienIsParalysisGasMagazine(tempItem))) {
                return true;
            }
        }
    }

    if (theItem->category & GEM) {""",
    "A marked paralysis-gas magazine behaves like a javelin quiver",
)

replace_once(
    "src/brogue/Items.c",
    """                // We found a match!
                stackItems(tempItem, theItem);

                // Pass back the incremented (old) item. No need to add it to the pack since it's already there.
                return tempItem;""",
    """                // We found a match!
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
                    && (theItem->category & POTION)
                    && theItem->kind == POTION_PARALYSIS
                    && (obrienIsParalysisGasMagazine(theItem)
                        || obrienIsParalysisGasMagazine(tempItem))) {
                    tempItem->quiverNumber = OBRIEN_PARALYSIS_GAS_MAGAZINE_QUIVER;
                }
                stackItems(tempItem, theItem);

                // Pass back the incremented (old) item. No need to add it to the pack since it's already there.
                return tempItem;""",
    "tempItem->quiverNumber = OBRIEN_PARALYSIS_GAS_MAGAZINE_QUIVER",
)

replace_once(
    "src/brogue/Items.c",
    """    for(theItem = packItems->nextItem; theItem != NULL; theItem = theItem->nextItem) {
        theCount += (theItem->category & (WEAPON | GEM) ? 1 : theItem->quantity);
    }""",
    """    for(theItem = packItems->nextItem; theItem != NULL; theItem = theItem->nextItem) {
        if (obrienIsParalysisGasMagazine(theItem)) {
            theCount += 1;
        } else {
            theCount += (theItem->category & (WEAPON | GEM) ? 1 : theItem->quantity);
        }
    }""",
    "if (obrienIsParalysisGasMagazine(theItem))",
)

replace_once(
    "src/brogue/Items.c",
    """        case POTION:
            if (potionTable[theItem->kind].identified || rogue.playbackOmniscience) {""",
    """        case POTION:
            if (obrienIsParalysisGasMagazine(theItem)) {
                sprintf(root, "paralysis-gas canister%s", pluralization);
            } else if (potionTable[theItem->kind].identified || rogue.playbackOmniscience) {""",
    "paralysis-gas canister%s",
)

replace_once(
    "src/brogue/Items.c",
    """    if (theItem->quantity > 1 && !(theItem->category & (WEAPON | GEM))) { // peel off the top item and drop it""",
    """    if (theItem->quantity > 1
        && !(theItem->category & (WEAPON | GEM))
        && !obrienIsParalysisGasMagazine(theItem)) { // ordinary stacks drop one; magazines drop as a unit""",
    "magazines drop as a unit",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    if (quantity > 0) {
        supply->quantity = quantity;
    }
    supply->flags &= ~ITEM_CURSED;""",
    """    if (quantity > 0) {
        supply->quantity = quantity;
    }
    if (obrienRulesetAtLeast(30)
        && (category & POTION) && kind == POTION_PARALYSIS) {
        // v0.2.30: issued paralysis gas is a single quiver-style canister magazine.
        supply->quiverNumber = OBRIEN_PARALYSIS_GAS_MAGAZINE_QUIVER;
    }
    supply->flags &= ~ITEM_CURSED;""",
    "issued paralysis gas is a single quiver-style canister magazine",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    obrienPlaceSupplyItem(POTION, POTION_POISON, 2, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 2, 0, anchor);
    obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);""",
    """    if (obrienRulesetAtLeast(30)) {
        // v0.2.30: no Starfleet-issued caustic/poison gas. The former poison
        // allocation is folded into one four-shot paralysis-gas magazine.
        obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 4, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);
    } else {
        // Historical v0.2.29 layout for old save/recording replay.
        obrienPlaceSupplyItem(POTION, POTION_POISON, 2, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 2, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);
    }""",
    "one four-shot paralysis-gas magazine",
)

# ---------------------------------------------------------------------------
# Recharge: all native rechargeable equipment in O'Brien mode, including wands.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Items.c",
    """        case CHARM_RECHARGING:
            rechargeItems(STAFF);
            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                obrienFillEmergencyPowerCells();
            }
            break;""",
    """        case CHARM_RECHARGING:
            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                if (obrienRulesetAtLeast(30)) {
                    // Recharge every native rechargeable equipment family. Do not
                    // touch WEAPON/ARMOR charges: those fields are auto-ID counters.
                    rechargeItems(STAFF | WAND | CHARM);
                } else {
                    rechargeItems(STAFF);
                }
                obrienFillEmergencyPowerCells();
            } else {
                rechargeItems(STAFF);
            }
            break;""",
    "Recharge every native rechargeable equipment family",
)

replace_once(
    "src/brogue/Items.c",
    """        case SCROLL_RECHARGING:
            rechargeItems(STAFF | CHARM);
            break;""",
    """        case SCROLL_RECHARGING:
            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && obrienRulesetAtLeast(30)) {
                rechargeItems(STAFF | WAND | CHARM);
            } else {
                rechargeItems(STAFF | CHARM);
            }
            break;""",
    "rechargeItems(STAFF | WAND | CHARM)",
)

replace_once(
    "src/brogue/Items.c",
    """                    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
                        && theItem->originDepth == OBRIEN_POWER_CELL_MARKER) {
                        sprintf(buf2, "\\n\\nThis Starfleet Emergency Power Cell stores up to %i charge-units. Applying it transfers up to %i units immediately to one selected staff, consuming only the energy actually transferred. It trickle-charges at one unit per %i turns; Wisdom and Reaping do not accelerate it. A Recharging charm or Scroll of Recharging fills it completely.",
                                OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_TRICKLE_TURNS);
                    } else {
                        sprintf(buf2, "\\n\\nWhen used, the charm will recharge your staffs (though not your wands or charms), after which it will recharge in %i turns. (If the charm is enchanted, it will recharge in %i turns.)",
                                charmRechargeDelay(theItem->kind, theItem->enchant1),
                                charmRechargeDelay(theItem->kind, theItem->enchant1 + enchantMagnitude()));
                    }""",
    """                    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
                        && theItem->originDepth == OBRIEN_POWER_CELL_MARKER) {
                        sprintf(buf2, "\\n\\nThis Starfleet Emergency Power Cell stores up to %i charge-units. Applying it transfers up to %i units immediately to one selected staff, consuming only the energy actually transferred. It trickle-charges at one unit per %i turns; Wisdom and Reaping do not accelerate it. A Recharging charm or Scroll of Recharging fills it completely.",
                                OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_CAPACITY, OBRIEN_POWER_CELL_TRICKLE_TURNS);
                    } else if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && obrienRulesetAtLeast(30)) {
                        sprintf(buf2, "\\n\\nWhen used, this Recharging charm restores rechargeable equipment throughout your pack: staffs, wands and charms. It then recharges in %i turns. (If the charm is enchanted, it will recharge in %i turns.)",
                                charmRechargeDelay(theItem->kind, theItem->enchant1),
                                charmRechargeDelay(theItem->kind, theItem->enchant1 + enchantMagnitude()));
                    } else {
                        sprintf(buf2, "\\n\\nWhen used, the charm will recharge your staffs (though not your wands or charms), after which it will recharge in %i turns. (If the charm is enchanted, it will recharge in %i turns.)",
                                charmRechargeDelay(theItem->kind, theItem->enchant1),
                                charmRechargeDelay(theItem->kind, theItem->enchant1 + enchantMagnitude()));
                    }""",
    "restores rechargeable equipment throughout your pack",
)

# ---------------------------------------------------------------------------
# Security Hologram: legacy-name compatibility + beneficial-bolt pass-through.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Monsters.c",
    """static boolean obrienIsSecurityHologram(const creature *monst) {
    return monst != NULL && !strcmp(monst->info.monsterName, "Security Hologram");
}""",
    """static boolean obrienIsSecurityHologram(const creature *monst) {
    return monst != NULL
        && (!strcmp(monst->info.monsterName, "Security Hologram")
            || !strcmp(monst->info.monsterName, "Holographic Security Officer"));
}""",
    'strcmp(monst->info.monsterName, "Holographic Security Officer")',
)

replace_once(
    "src/brogue/Monsters.c",
    """            && !(monst->bookkeepingFlags & (MB_IS_DYING | MB_HAS_DIED))
            && !strcmp(monst->info.monsterName, name)) {

            return monst;""",
    """            && !(monst->bookkeepingFlags & (MB_IS_DYING | MB_HAS_DIED))
            && (!strcmp(monst->info.monsterName, name)
                || (!strcmp(name, "Security Hologram") && obrienIsSecurityHologram(monst)))) {

            return monst;""",
    "(!strcmp(name, \"Security Hologram\") && obrienIsSecurityHologram(monst))",
)

replace_once(
    "src/brogue/Monsters.c",
    """static void obrienBindSecurityRuntime(creature *monst) {
    if (!obrienIsSecurityHologram(monst)) {
        return;
    }
    if (obrienSecurityRuntimeMonst != monst) {""",
    """static void obrienBindSecurityRuntime(creature *monst) {
    if (!obrienIsSecurityHologram(monst)) {
        return;
    }
    if (!strcmp(monst->info.monsterName, "Holographic Security Officer")) {
        // Normalize pre-v0.2.26 save instances without changing save layout.
        strcpy(monst->info.monsterName, "Security Hologram");
    }
    if (obrienSecurityRuntimeMonst != monst) {""",
    "Normalize pre-v0.2.26 save instances",
)

insert_once_before(
    "src/brogue/Items.c",
    """boolean projectileReflects(creature *attacker, creature *defender) {""",
    """static boolean obrienSecurityAcceptsBeneficialBolt(const creature *defender, const bolt *theBolt) {
    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE
        || !obrienRulesetAtLeast(30)
        || defender == NULL
        || theBolt == NULL
        || (strcmp(defender->info.monsterName, "Security Hologram")
            && strcmp(defender->info.monsterName, "Holographic Security Officer"))) {

        return false;
    }

    // Brogue marks healing, haste, shielding, invisibility, empowerment and
    // other ally-support effects with BF_TARGET_ALLIES. Those effects should
    // reach the friendly hologram instead of being reflected back at the caster.
    return (theBolt->flags & BF_TARGET_ALLIES) != 0;
}

""",
    "static boolean obrienSecurityAcceptsBeneficialBolt",
)

replace_once(
    "src/brogue/Items.c",
    """        if (monst
            && !(theBolt->flags & BF_NEVER_REFLECTS)
            && projectileReflects(shootingMonst, monst)
            && i < MAX_BOLT_LENGTH - max(DCOLS, DROWS)) {""",
    """        if (monst
            && !(theBolt->flags & BF_NEVER_REFLECTS)
            && !obrienSecurityAcceptsBeneficialBolt(monst, theBolt)
            && projectileReflects(shootingMonst, monst)
            && i < MAX_BOLT_LENGTH - max(DCOLS, DROWS)) {""",
    "!obrienSecurityAcceptsBeneficialBolt(monst, theBolt)",
)

# ---------------------------------------------------------------------------
# Dedicated ally descriptions; skip hostile combat previews for named crew.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Monsters.c",
    """    monsterName(monstName, monst, true);
    strcpy(capMonstName, monstName);
    upperCase(capMonstName);

    if (!(monst->info.flags & MONST_RESTRICTED_TO_LIQUID)""",
    """    monsterName(monstName, monst, true);
    strcpy(capMonstName, monstName);
    upperCase(capMonstName);

    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && obrienIsBashir(monst)) {
        itemName(monst->carriedItem, theItemName, true, true, NULL);
        sprintf(buf,
                "     Bashir is your Starfleet medical officer and ally. He heals injured allies, "
                "keeps his distance, flies to keep pace with the away team, and carries %s. "
                "Friendly fire can injure him but cannot make him defect. If critically wounded, "
                "emergency transport beams him out for treatment; he returns after %d turns.",
                monst->carriedItem ? theItemName : "finite field equipment",
                OBRIEN_BASHIR_RECOVERY_TURNS);
        return;
    }

    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && obrienIsSecurityHologram(monst)) {
        obrienRechargeSecurityWeapons(monst);
        sprintf(buf,
                "     The Security Hologram is your Starfleet defensive ally. It flies, moves and "
                "attacks quickly, repairs its integrity rapidly, and carries finite tactical "
                "emitters: Lightning %d/%d and Poison %d/%d. Hostile reflectable bolts are returned "
                "by its defensive field; beneficial ally-support bolts pass through and affect it "
                "normally. It is immune to fire, webs and water hazards and maintains the away "
                "team's long-distance visual link.",
                obrienSecurityLightningCharges, OBRIEN_SECURITY_MAX_CHARGES,
                obrienSecurityPoisonCharges, OBRIEN_SECURITY_MAX_CHARGES);
        return;
    }

    if (!(monst->info.flags & MONST_RESTRICTED_TO_LIQUID)""",
    "beneficial ally-support bolts pass through",
)

# Avoid calling itemName(NULL, ...) in the dedicated Bashir branch.
replace_once(
    "src/brogue/Monsters.c",
    """    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && obrienIsBashir(monst)) {
        itemName(monst->carriedItem, theItemName, true, true, NULL);
        sprintf(buf,""",
    """    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && obrienIsBashir(monst)) {
        if (monst->carriedItem) {
            itemName(monst->carriedItem, theItemName, true, true, NULL);
        } else {
            strcpy(theItemName, "finite field equipment");
        }
        sprintf(buf,""",
    "strcpy(theItemName, \"finite field equipment\")",
)

replace_once(
    "src/brogue/Monsters.c",
    """                monst->carriedItem ? theItemName : "finite field equipment",
                OBRIEN_BASHIR_RECOVERY_TURNS);""",
    """                theItemName,
                OBRIEN_BASHIR_RECOVERY_TURNS);""",
    "                theItemName,\n                OBRIEN_BASHIR_RECOVERY_TURNS",
)

# Version banner. No enum renumbering and no recording header changes in v0.2.30.
replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.29",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.30",
    "O'Brien Must Survive v0.2.30",
)

print("O'Brien Must Survive v0.2.30 applied.")
print("- O'Brien moved from Change Variant to Change Mode without changing its saved variant ID")
print("- Bashir and Security Hologram now use dedicated ally examine descriptions")
print("- Security reflects hostile bolts but accepts beneficial BF_TARGET_ALLIES support bolts")
print("- Starfleet resupply issues no caustic gas; paralysis gas is a four-shot magazine stack")
print("- O'Brien Recharging charm/scroll effects include staffs, wands and charms")
print("- legacy Holographic Security Officer save instances are recognized and normalized")
print("- new games also start with Magic Mapping and a directional Wand of Negation")
print("- pre-v0.2.30 O'Brien recordings keep ruleset 0 for strict historical replay")
print("Build with: make -B -j3 bin/brogue")
