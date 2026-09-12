#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.24 to a clean Brogue CE 1.15.1 tree.

v0.2.24 adds the away-team emergency-security layer discussed after v0.2.23:
- `C` is a real O'Brien-variant command/spell: Call Security;
- it materializes one Holographic Security Officer (HSO) at a time;
- the HSO is a flying, high-integrity, rapidly self-repairing permanent ally;
- it carries simulated enchanted Lightning and Poison staff systems, each 20/20,
  with fast Wisdom-equivalent recharge while deployed;
- it has a strong sword profile for close protection, anti-magic bolt reflection,
  fire/web/water/environmental resilience, and inanimate physiology;
- because it is an ally, normal ally AI makes it fight/rear-guard when enemies are
  present and regroup with O'Brien after combat instead of remaining behind;
- Bashir now emergency-beams out when critically wounded or lethally hit and is
  rematerialized after a recovery interval instead of being permanently lost.

The HSO's two 20-shot staff magazines are runtime tactical systems rather than
pack items: the hologram does not consume O'Brien's inventory slots and cannot
be looted for duplicated staffs. A loaded save rebinds the single HSO runtime
and initializes its virtual magazines safely.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_23.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_23.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.23 source was not found.")


# Bashir's existing constructor is the canonical source of his current v0.2.x
# stats/equipment. Export it so crew-maintenance code can rematerialize him after
# an emergency medical beam-out without duplicating a second stat definition.
replace_once(
    "src/brogue/RogueMain.c",
    "static void obrienSpawnBashir(pos anchor) {",
    "void obrienSpawnBashir(pos anchor) {",
    "void obrienSpawnBashir(pos anchor)",
)

OBRIEN_SECURITY_RUNTIME = r'''
// v0.2.24 Call Security / away-team emergency runtime.
// The HSO's two staff magazines are deliberately runtime systems rather than
// inventory objects: the hologram cannot donate or duplicate Starfleet weapons.
#define OBRIEN_SECURITY_MAX_CHARGES 20
#define OBRIEN_SECURITY_RECHARGE_TURNS 35
#define OBRIEN_BASHIR_RECOVERY_TURNS 120

extern void obrienSpawnBashir(pos anchor);

static creature *obrienSecurityRuntimeMonst = NULL;
static short obrienSecurityLightningCharges = OBRIEN_SECURITY_MAX_CHARGES;
static short obrienSecurityPoisonCharges = OBRIEN_SECURITY_MAX_CHARGES;
static unsigned long obrienSecurityLastRechargeTurn = 0;
static unsigned long obrienBashirReturnTurn = 0;

static boolean obrienIsBashir(const creature *monst) {
    return monst != NULL && !strcmp(monst->info.monsterName, "Bashir");
}

static boolean obrienIsSecurityHologram(const creature *monst) {
    return monst != NULL && !strcmp(monst->info.monsterName, "Holographic Security Officer");
}

static creature *obrienFindLivingCrew(const char *name) {
    for (creatureIterator it = iterateCreatures(monsters); hasNextCreature(it);) {
        creature *monst = nextCreature(&it);
        if (monst != NULL
            && monst->currentHP > 0
            && !(monst->bookkeepingFlags & (MB_IS_DYING | MB_HAS_DIED))
            && !strcmp(monst->info.monsterName, name)) {

            return monst;
        }
    }
    return NULL;
}

static void obrienBindSecurityRuntime(creature *monst) {
    if (!obrienIsSecurityHologram(monst)) {
        return;
    }
    if (obrienSecurityRuntimeMonst != monst) {
        obrienSecurityRuntimeMonst = monst;
        obrienSecurityLightningCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityPoisonCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityLastRechargeTurn = rogue.absoluteTurnNumber;
    }
}

static void obrienRechargeSecurityWeapons(creature *monst) {
    if (!obrienIsSecurityHologram(monst)) {
        return;
    }
    obrienBindSecurityRuntime(monst);

    if (obrienSecurityLightningCharges >= OBRIEN_SECURITY_MAX_CHARGES
        && obrienSecurityPoisonCharges >= OBRIEN_SECURITY_MAX_CHARGES) {

        // Do not bank an unlimited amount of recharge time while both emitters
        // are full; this mirrors a capped staff battery rather than a reservoir.
        obrienSecurityLastRechargeTurn = rogue.absoluteTurnNumber;
        return;
    }

    while (rogue.absoluteTurnNumber >= obrienSecurityLastRechargeTurn + OBRIEN_SECURITY_RECHARGE_TURNS) {
        if (obrienSecurityLightningCharges < OBRIEN_SECURITY_MAX_CHARGES) {
            obrienSecurityLightningCharges++;
        }
        if (obrienSecurityPoisonCharges < OBRIEN_SECURITY_MAX_CHARGES) {
            obrienSecurityPoisonCharges++;
        }
        obrienSecurityLastRechargeTurn += OBRIEN_SECURITY_RECHARGE_TURNS;
    }
}

static boolean obrienSecurityBoltAvailable(creature *monst, enum boltType boltIndex) {
    if (!obrienIsSecurityHologram(monst)) {
        return true;
    }
    obrienRechargeSecurityWeapons(monst);
    if (boltIndex == BOLT_LIGHTNING) {
        return obrienSecurityLightningCharges > 0;
    }
    if (boltIndex == BOLT_POISON) {
        return obrienSecurityPoisonCharges > 0;
    }
    return true;
}

static void obrienSecurityConsumeBolt(creature *monst, enum boltType boltIndex) {
    if (!obrienIsSecurityHologram(monst)) {
        return;
    }
    obrienBindSecurityRuntime(monst);
    if (boltIndex == BOLT_LIGHTNING && obrienSecurityLightningCharges > 0) {
        obrienSecurityLightningCharges--;
    } else if (boltIndex == BOLT_POISON && obrienSecurityPoisonCharges > 0) {
        obrienSecurityPoisonCharges--;
    }
}

static void obrienBeginBashirRecovery(creature *bashir) {
    if (!obrienIsBashir(bashir)
        || (bashir->bookkeepingFlags & (MB_IS_DYING | MB_HAS_DIED))) {
        return;
    }

    obrienBashirReturnTurn = rogue.absoluteTurnNumber + OBRIEN_BASHIR_RECOVERY_TURNS;
    messageWithColor("Bashir is critically wounded. Emergency medical transport engaged.", &itemMessageColor, 0);
    killCreature(bashir, true);
}

// Called by Combat.c before a non-administrative death is finalized. Returning
// true converts a lethal hit on Bashir into a clean emergency beam-out.
boolean obrienInterceptCrewDeath(creature *decedent) {
    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE || !obrienIsBashir(decedent)) {
        return false;
    }

    obrienBashirReturnTurn = rogue.absoluteTurnNumber + OBRIEN_BASHIR_RECOVERY_TURNS;
    messageWithColor("Bashir's life signs are critical. Starfleet beams him out for emergency treatment.", &itemMessageColor, 0);
    return true;
}

// Called from the input loop so Bashir can return even while no Bashir creature
// exists on the current monster list.
void obrienCrewMaintenance(void) {
    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE) {
        return;
    }

    if (obrienBashirReturnTurn
        && rogue.absoluteTurnNumber >= obrienBashirReturnTurn
        && obrienFindLivingCrew("Bashir") == NULL) {

        obrienBashirReturnTurn = 0;
        obrienSpawnBashir(player.loc);
        messageWithColor("Bashir rematerializes beside the away team, recovered and ready for duty.", &itemMessageColor, 0);
    }
}

// `C` command in the O'Brien variant. This is a spell/ability, not a carried
// charm: it consumes a turn, deploys one hologram at a time, and therefore does
// not occupy a backpack slot. Standard ally AI handles interception, rear guard
// fighting and regrouping after the threat is gone.
boolean obrienCallSecuritySpell(void) {
    creature *security;

    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE) {
        return false;
    }

    security = obrienFindLivingCrew("Holographic Security Officer");
    if (security != NULL) {
        message("Security hologram already deployed; it will regroup after combat.", 0);
        return false;
    }

    security = generateMonster(MK_GOLEM, false, false);
    if (security == NULL) {
        message("Call Security failed: holographic emitter unavailable.", 0);
        return false;
    }

    strcpy(security->info.monsterName, "Holographic Security Officer");
    security->info.displayChar = G_WINGED_GUARDIAN;
    security->info.foreColor = &white;

    // High-integrity flying security platform. Physical attacks still matter;
    // anti-magic protection is represented by 100% bolt reflection rather than
    // total MONST_INVULNERABLE, so melee pressure can still wear the hologram down.
    security->info.flags = (MONST_INANIMATE
                            | MONST_FLIES
                            | MONST_IMMUNE_TO_FIRE
                            | MONST_IMMUNE_TO_WEBS
                            | MONST_IMMUNE_TO_WATER
                            | MONST_NEVER_SLEEPS
                            | MONST_NO_POLYMORPH);
    security->info.abilityFlags = MA_REFLECT_100;

    security->info.maxHP = 180;
    security->currentHP = security->info.maxHP;
    security->info.defense = 80;
    security->info.accuracy = 155;
    security->info.damage.lowerBound = 8;
    security->info.damage.upperBound = 14;
    security->info.damage.clumpFactor = 2;
    security->info.turnsBetweenRegen = 2; // fast autonomous integrity repair
    security->turnsUntilRegen = security->info.turnsBetweenRegen * 1000;

    security->info.movementSpeed = 80;
    security->info.attackSpeed = 85;
    security->movementSpeed = security->info.movementSpeed;
    security->attackSpeed = security->info.attackSpeed;
    security->ticksUntilTurn = security->movementSpeed;

    // Two +3-equivalent tactical emitters. Charge capacity/recharge is enforced
    // by the custom runtime around monstUseBolt(): Lightning 20/20, Poison 20/20.
    security->info.bolts[0] = BOLT_LIGHTNING;
    security->info.bolts[1] = BOLT_POISON;
    security->info.bolts[2] = BOLT_NONE;

    security->status[STATUS_LEVITATING] = 1000;
    security->maxStatus[STATUS_LEVITATING] = 1000;

    becomeAllyWith(security);
    security->loc = getQualifyingPathLocNear(player.loc, true,
                                              T_DIVIDES_LEVEL, 0,
                                              T_PATHING_BLOCKER,
                                              (HAS_PLAYER | HAS_MONSTER | HAS_STAIRS | IS_IN_MACHINE),
                                              false);

    if (!coordinatesAreInMap(security->loc.x, security->loc.y)) {
        killCreature(security, true);
        message("Call Security failed: no safe holographic projection point nearby.", 0);
        return false;
    }

    pmapAt(security->loc)->flags |= HAS_MONSTER;
    refreshDungeonCell(security->loc);
    obrienBindSecurityRuntime(security);

    messageWithColor("Call Security: Holographic Security Officer online. Lightning 20/20; Poison 20/20.", &itemMessageColor, 0);
    playerTurnEnded();
    return true;
}
'''

replace_once(
    "src/brogue/Monsters.c",
    "#include \"Globals.h\"\n\nvoid mutateMonster(creature *monst, short mutationIndex) {",
    "#include \"Globals.h\"\n\n" + OBRIEN_SECURITY_RUNTIME + "\nvoid mutateMonster(creature *monst, short mutationIndex) {",
    "v0.2.24 Call Security / away-team emergency runtime",
)

# The HSO's two virtual staff magazines are finite 20-shot systems. Standard
# monster bolts are otherwise unlimited, so gate and consume only these two HSO
# bolt types at the exact point where a valid cast is committed.
replace_once(
    "src/brogue/Monsters.c",
    """                if (specificallyValidBoltTarget(monst, target, monst->info.bolts[i])) {
                    if ((monst->info.flags & MONST_ALWAYS_USE_ABILITY)
                        || rand_percent(30)) {

                        monsterCastSpell(monst, target, monst->info.bolts[i]);
                        return true;
                    }
                }""",
    """                if (specificallyValidBoltTarget(monst, target, monst->info.bolts[i])) {
                    if (!obrienSecurityBoltAvailable(monst, monst->info.bolts[i])) {
                        continue;
                    }
                    if ((monst->info.flags & MONST_ALWAYS_USE_ABILITY)
                        || rand_percent(30)) {

                        monsterCastSpell(monst, target, monst->info.bolts[i]);
                        obrienSecurityConsumeBolt(monst, monst->info.bolts[i]);
                        return true;
                    }
                }""",
    "obrienSecurityConsumeBolt(monst, monst->info.bolts[i])",
)

# Bashir now emergency-beams out at <=25% HP before ordinary AI can keep him in
# the kill zone. Also rebind a loaded HSO runtime, recharge its virtual staffs,
# and guarantee both named Starfleet crew members retain ally/follower identity.
replace_once(
    "src/brogue/Monsters.c",
    """    x = monst->loc.x;
    y = monst->loc.y;""",
    """    // v0.2.24 medical transport + holographic security maintenance.
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && obrienIsBashir(monst)
        && monst->currentHP > 0
        && !(monst->bookkeepingFlags & MB_IS_DYING)
        && monst->currentHP * 4 <= monst->info.maxHP) {

        obrienBeginBashirRecovery(monst);
        return;
    }

    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && obrienIsSecurityHologram(monst)
        && monst->currentHP > 0
        && !(monst->bookkeepingFlags & MB_IS_DYING)) {

        obrienBindSecurityRuntime(monst);
        obrienRechargeSecurityWeapons(monst);
        if (monst->creatureState != MONSTER_ALLY) {
            monst->creatureState = MONSTER_ALLY;
            monst->bookkeepingFlags |= MB_FOLLOWER;
            monst->leader = &player;
        }
    }

    x = monst->loc.x;
    y = monst->loc.y;""",
    "v0.2.24 medical transport + holographic security maintenance",
)

# Extend v0.2.22's permanent-crew friendly-fire rule to the holographic officer.
replace_once(
    "src/brogue/Monsters.c",
    """    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && monst != NULL
        && !strcmp(monst->info.monsterName, "Bashir")) {

        return;
    }""",
    """    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && monst != NULL
        && (!strcmp(monst->info.monsterName, "Bashir")
            || !strcmp(monst->info.monsterName, "Holographic Security Officer"))) {

        return;
    }""",
    "Holographic Security Officer\")))",
)

# Convert a lethal Bashir hit into administrative disappearance after scheduling
# his medical return. Damage is still real; the intervention occurs only at death.
replace_once(
    "src/brogue/Combat.c",
    "#include \"Globals.h\"\n\n\n/* Combat rules:",
    "#include \"Globals.h\"\n\nextern boolean obrienInterceptCrewDeath(creature *decedent);\n\n/* Combat rules:",
    "extern boolean obrienInterceptCrewDeath",
)

replace_once(
    "src/brogue/Combat.c",
    """void killCreature(creature *decedent, boolean administrativeDeath) {
    short x, y;
    char monstName[DCOLS], buf[DCOLS * 3];

    if (decedent->bookkeepingFlags & (MB_IS_DYING | MB_HAS_DIED)) {""",
    """void killCreature(creature *decedent, boolean administrativeDeath) {
    short x, y;
    char monstName[DCOLS], buf[DCOLS * 3];

    // v0.2.24 Bashir emergency medical transport: a lethal non-admin death
    // becomes a clean beam-out, with respawn scheduled by Monsters.c.
    if (!administrativeDeath && obrienInterceptCrewDeath(decedent)) {
        administrativeDeath = true;
    }

    if (decedent->bookkeepingFlags & (MB_IS_DYING | MB_HAS_DIED)) {""",
    "v0.2.24 Bashir emergency medical transport",
)

# Wire the spell into the normal input system. `C` is already Brogue's Wizard
# create-item key, so O'Brien intercepts it as Call Security; non-O'Brien Wizard
# games keep the original debug behavior.
replace_once(
    "src/brogue/IO.c",
    "#include \"Globals.h\"\n\n#define D_DISABLE_BACKGROUND_COLORS",
    "#include \"Globals.h\"\n\nextern boolean obrienCallSecuritySpell(void);\nextern void obrienCrewMaintenance(void);\n\n#define D_DISABLE_BACKGROUND_COLORS",
    "extern boolean obrienCallSecuritySpell",
)

replace_once(
    "src/brogue/IO.c",
    """void executeKeystroke(signed long keystroke, boolean controlKey, boolean shiftKey) {
    short direction = -1;

    confirmMessages();""",
    """void executeKeystroke(signed long keystroke, boolean controlKey, boolean shiftKey) {
    short direction = -1;

    confirmMessages();
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
        obrienCrewMaintenance();
    }""",
    "obrienCrewMaintenance();",
)

replace_once(
    "src/brogue/IO.c",
    """        case CREATE_ITEM_MONSTER_KEY:
            DEBUG {
                dialogCreateItemOrMonster();
            }
            break;""",
    """        case CREATE_ITEM_MONSTER_KEY:
            if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                obrienCallSecuritySpell();
            } else {
                DEBUG {
                    dialogCreateItemOrMonster();
                }
            }
            break;""",
    "obrienCallSecuritySpell();",
)

# Add the spell to the action menu. In O'Brien Wizard mode this replaces the
# debug Create entry on C; other variants retain the original Wizard tool.
replace_once(
    "src/brogue/IO.c",
    """        DEBUG {
            buttonCount++;
            if (KEYBOARD_LABELS) {
                sprintf(buttons[buttonCount].text, "  %sC: %sCreate item or monster  ", yellowColorEscape, whiteColorEscape);
            } else {
                strcpy(buttons[buttonCount].text, "  Create item or monster  ");
            }
            buttons[buttonCount].hotkey[0] = CREATE_ITEM_MONSTER_KEY;
        }
        buttonCount++;""",
    """        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
            buttonCount++;
            if (KEYBOARD_LABELS) {
                sprintf(buttons[buttonCount].text, "  %sC: %sCall Security spell  ", yellowColorEscape, whiteColorEscape);
            } else {
                strcpy(buttons[buttonCount].text, "  Call Security spell  ");
            }
            buttons[buttonCount].hotkey[0] = CREATE_ITEM_MONSTER_KEY;
        } else {
            DEBUG {
                buttonCount++;
                if (KEYBOARD_LABELS) {
                    sprintf(buttons[buttonCount].text, "  %sC: %sCreate item or monster  ", yellowColorEscape, whiteColorEscape);
                } else {
                    strcpy(buttons[buttonCount].text, "  Create item or monster  ");
                }
                buttons[buttonCount].hotkey[0] = CREATE_ITEM_MONSTER_KEY;
            }
        }
        buttonCount++;""",
    "Call Security spell",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.23\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.24\\n\");",
    "O'Brien Must Survive v0.2.24",
)

print("O'Brien Must Survive v0.2.24 applied.")
print("- New C command/spell: Call Security")
print("- Deploys one flying Holographic Security Officer at a time")
print("- HSO: 180 integrity, defense 80, fast 1 HP / 2 turns self-repair")
print("- HSO: sword 8-14, Lightning 20/20, Poison 20/20")
print("- HSO staff magazines recharge one charge per 35 turns (Wisdom-equivalent)")
print("- HSO: 100% bolt reflection plus fire/web/water/environmental resilience")
print("- Standard ally AI makes the HSO fight/rear-guard and regroup after combat")
print("- Bashir emergency-beams out at <=25% HP or lethal damage and returns after 120 turns")
print("Build normally with: make -B")
