#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.30 to a Brogue CE 1.15.1 tree.

v0.2.30 adds a deliberately narrow character-dialogue layer.

Only three characters are allowed to speak:
- Miles O'Brien (the player)
- Bashir
- Security Hologram / HSO

Everything else remains silent as a character. Ordinary Brogue narration and
combat/system messages remain narration; Golems, other allies, monsters and
summons do not receive personality dialogue.

The dialogue layer is cosmetic. It does not consume substantive RNG, change
turn order, alter AI, or add recorded input events.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_29.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_29.py next to this updater.")


def source_has_v029_or_later():
    main = ROOT / "src/brogue/RogueMain.c"
    monsters = ROOT / "src/brogue/Monsters.c"
    if not main.exists() or not monsters.exists():
        return False
    main_text = main.read_text(encoding="utf-8")
    monsters_text = monsters.read_text(encoding="utf-8")
    return (
        ("O'Brien Must Survive v0.2.29" in main_text
         or "O'Brien Must Survive v0.2.30" in main_text)
        and "v0.2.29 Call Security record" in monsters_text
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


DIALOGUE_RUNTIME = r'''// v0.2.30 three-person dialogue layer.
//
// Character speech is intentionally closed over exactly three wrappers:
// Miles O'Brien, Bashir and the Security Hologram (HSO). Do not route ordinary
// monsters, generic allies, summons or Golems through this system. Native Brogue
// messages remain narration and are not character speech.
static unsigned long obrienDialogueLastSeenTurn = 0;
static unsigned long obrienDialogueLastAmbientTurn = 0;
static short obrienDialogueLastDepth = 0;
static short obrienDialogueLastPlayerHP = -1;

static void obrienSay(const char *speaker, const char *line, const color *messageColor) {
    char buf[COLS * 3];

    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE || !speaker || !line) {
        return;
    }

    snprintf(buf, sizeof(buf), "%s: %s", speaker, line);
    messageWithColor(buf, messageColor ? messageColor : &white, 0);
}

static void obrienMilesSays(const char *line, const color *messageColor) {
    obrienSay("Miles", line, messageColor);
}

static void obrienBashirSays(const char *line, const color *messageColor) {
    obrienSay("Bashir", line, messageColor);
}

static void obrienHSOSays(const char *line, const color *messageColor) {
    obrienSay("HSO", line, messageColor);
}

static void obrienDialogueResetIfRewound(void) {
    if (rogue.absoluteTurnNumber < obrienDialogueLastSeenTurn
        || (rogue.playerTurnNumber <= 1 && obrienDialogueLastSeenTurn > 1)) {

        obrienDialogueLastAmbientTurn = rogue.absoluteTurnNumber;
        obrienDialogueLastDepth = 0;
        obrienDialogueLastPlayerHP = -1;
    }
    obrienDialogueLastSeenTurn = rogue.absoluteTurnNumber;
}

static boolean obrienDepthGetsDialogue(short depth) {
    return depth == 10 || depth == 15 || depth >= 20;
}

static void obrienDepthDialogue(void) {
    creature *bashir = obrienFindLivingCrew("Bashir");
    creature *security = obrienFindLivingCrew("Security Hologram");
    char line[COLS * 2];

    if (obrienDialogueLastDepth == 0) {
        obrienDialogueLastDepth = rogue.depthLevel;
        return;
    }
    if (rogue.depthLevel == obrienDialogueLastDepth) {
        return;
    }

    if (rogue.depthLevel > obrienDialogueLastDepth
        && obrienDepthGetsDialogue(rogue.depthLevel)) {

        if (security != NULL) {
            snprintf(line, sizeof(line),
                     "Depth %d. Threat level elevated. Integrity %d/%d; L %d/%d; P %d/%d.",
                     rogue.depthLevel,
                     security->currentHP, security->info.maxHP,
                     obrienSecurityLightningCharges, OBRIEN_SECURITY_MAX_CHARGES,
                     obrienSecurityPoisonCharges, OBRIEN_SECURITY_MAX_CHARGES);
            obrienHSOSays(line, &itemMessageColor);
        } else if (bashir != NULL) {
            snprintf(line, sizeof(line),
                     "Depth %d, Miles. The casualty risk is getting worse.",
                     rogue.depthLevel);
            obrienBashirSays(line, &itemMessageColor);
        } else {
            snprintf(line, sizeof(line), "Depth %d. Right. Keep moving.", rogue.depthLevel);
            obrienMilesSays(line, &itemMessageColor);
        }
    }

    obrienDialogueLastDepth = rogue.depthLevel;
}

static void obrienPlayerInjuryDialogue(void) {
    creature *bashir = obrienFindLivingCrew("Bashir");
    creature *security = obrienFindLivingCrew("Security Hologram");
    short oldHP = obrienDialogueLastPlayerHP;
    short newHP = player.currentHP;
    short maxHP = max(1, player.info.maxHP);

    if (oldHP < 0) {
        obrienDialogueLastPlayerHP = newHP;
        return;
    }

    if (newHP > 0 && newHP < oldHP) {
        if (newHP * 4 <= maxHP && oldHP * 4 > maxHP) {
            if (bashir != NULL) {
                obrienBashirSays("Miles, that's not a scratch. You're in critical condition.",
                                 &badMessageColor);
            } else if (security != NULL) {
                obrienHSOSays("O'Brien condition critical. Immediate withdrawal recommended.",
                              &badMessageColor);
            } else {
                obrienMilesSays("That's bad. Need some distance.", &badMessageColor);
            }
        } else if (newHP * 2 <= maxHP && oldHP * 2 > maxHP) {
            if (bashir != NULL) {
                obrienBashirSays("Miles, you're hurt. Try not to make it worse.",
                                 &itemMessageColor);
            } else if (security != NULL) {
                obrienHSOSays("O'Brien injury detected. Defensive posture recommended.",
                              &itemMessageColor);
            } else {
                obrienMilesSays("I've had worse. Keep moving.", &itemMessageColor);
            }
        }
    }

    obrienDialogueLastPlayerHP = newHP;
}

// Low-frequency corridor chatter. This is deliberately deterministic and
// state-gated: no RNG calls, no turn cost, and no dialogue flood during critical
// injury. At most one short exchange fires every 240 turns.
static void obrienAmbientDialogue(void) {
    creature *bashir = obrienFindLivingCrew("Bashir");
    creature *security = obrienFindLivingCrew("Security Hologram");
    unsigned long now = rogue.absoluteTurnNumber;
    unsigned long slot;

    if (player.currentHP <= 0 || player.currentHP * 2 <= max(1, player.info.maxHP)) {
        return;
    }

    if (obrienDialogueLastAmbientTurn == 0) {
        obrienDialogueLastAmbientTurn = now;
        return;
    }

    if (now < obrienDialogueLastAmbientTurn) {
        obrienDialogueLastAmbientTurn = now;
        return;
    }

    if (now - obrienDialogueLastAmbientTurn < 240) {
        return;
    }

    obrienDialogueLastAmbientTurn = now;
    slot = (rogue.playerTurnNumber / 240) % 6;

    if (bashir != NULL && security != NULL) {
        switch (slot) {
            case 0:
                obrienMilesSays("Tell me we finally found a quiet corridor.", &backgroundMessageColor);
                obrienHSOSays("No immediate hostile contact detected.", &backgroundMessageColor);
                break;
            case 1:
                obrienBashirSays("Miles, walking toward danger is not preventive medicine.", &backgroundMessageColor);
                obrienMilesSays("Noted, Doctor.", &backgroundMessageColor);
                break;
            case 2:
                obrienHSOSays("Tactical systems nominal.", &backgroundMessageColor);
                obrienMilesSays("Best news I've heard all day.", &backgroundMessageColor);
                break;
            case 3:
                obrienMilesSays("Julian, if you say this is fascinating, I'm leaving.", &backgroundMessageColor);
                obrienBashirSays("I was going to say medically inadvisable.", &backgroundMessageColor);
                break;
            case 4:
                obrienBashirSays("How are you still standing?", &backgroundMessageColor);
                obrienMilesSays("Practice.", &backgroundMessageColor);
                break;
            default:
                obrienHSOSays("Away-team formation remains acceptable.", &backgroundMessageColor);
                obrienBashirSays("That is almost reassuring.", &backgroundMessageColor);
                break;
        }
    } else if (bashir != NULL) {
        if (slot & 1) {
            obrienBashirSays("Miles, you do realize retreat is a medical option.", &backgroundMessageColor);
            obrienMilesSays("I'll keep it on the list.", &backgroundMessageColor);
        } else {
            obrienMilesSays("Still with me, Julian?", &backgroundMessageColor);
            obrienBashirSays("Against my better judgment.", &backgroundMessageColor);
        }
    } else if (security != NULL) {
        if (slot & 1) {
            obrienHSOSays("Tactical systems nominal. Awaiting orders.", &backgroundMessageColor);
        } else {
            obrienMilesSays("Keep an eye on the corridor.", &backgroundMessageColor);
            obrienHSOSays("Already doing so.", &backgroundMessageColor);
        }
    } else {
        switch (slot % 3) {
            case 0:
                obrienMilesSays("Quiet. I don't trust quiet.", &backgroundMessageColor);
                break;
            case 1:
                obrienMilesSays("One corridor at a time.", &backgroundMessageColor);
                break;
            default:
                obrienMilesSays("Could be worse. Usually is.", &backgroundMessageColor);
                break;
        }
    }
}

// Called from gameOver() before Brogue's normal "You die..." / Killed by...
// sequence. No character dialogue is emitted after that point.
void obrienDeathDialogue(void) {
    creature *bashir;
    creature *security;

    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE) {
        return;
    }

    bashir = obrienFindLivingCrew("Bashir");
    security = obrienFindLivingCrew("Security Hologram");

    if (bashir != NULL) {
        obrienBashirSays("Miles! Stay with me!", &badMessageColor);
    } else if (security != NULL) {
        obrienHSOSays("Critical condition. Medical support unavailable.", &badMessageColor);
    } else {
        obrienMilesSays("Right. That's not good.", &badMessageColor);
    }
}
'''

replace_once(
    "src/brogue/Monsters.c",
    '''static creature *obrienFindLivingCrew(const char *name) {
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
''',
    '''static creature *obrienFindLivingCrew(const char *name) {
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
''' + DIALOGUE_RUNTIME,
    "v0.2.30 three-person dialogue layer",
)

replace_once(
    "src/brogue/Monsters.c",
    '    messageWithColor("Bashir is critically wounded. Emergency medical transport engaged.", &itemMessageColor, 0);',
    '    obrienBashirSays("Miles, I am hit. Emergency transport engaged.", &itemMessageColor);',
    'Miles, I am hit. Emergency transport engaged.',
)

replace_once(
    "src/brogue/Monsters.c",
    '    messageWithColor("Bashir\\'s life signs are critical. Starfleet beams him out for emergency treatment.", &itemMessageColor, 0);',
    '    obrienBashirSays("Miles, medical emergency. Beam me out!", &badMessageColor);',
    'Miles, medical emergency. Beam me out!',
)

replace_once(
    "src/brogue/Monsters.c",
    '        messageWithColor("Bashir rematerializes beside the away team, recovered and ready for duty.", &itemMessageColor, 0);',
    '        obrienBashirSays("I am back, Miles. Let us try not to make that a habit.", &itemMessageColor);',
    'I am back, Miles. Let us try not to make that a habit.',
)

replace_once(
    "src/brogue/Monsters.c",
    '''        messageWithColor("Security Hologram offline. C will redeploy it with retained tactical state.",
                         &itemMessageColor, 0);
        recordKeystroke(CREATE_ITEM_MONSTER_KEY, false, false); // v0.2.29 recording integrity''',
    '''        obrienHSOSays("Deactivating. Tactical state retained.", &itemMessageColor);
        recordKeystroke(CREATE_ITEM_MONSTER_KEY, false, false); // v0.2.29 recording integrity''',
    'Deactivating. Tactical state retained.',
)

replace_once(
    "src/brogue/Monsters.c",
    '''    sprintf(buf, "Security Hologram online. Lightning %d/%d; Poison %d/%d.",
            obrienSecurityLightningCharges, OBRIEN_SECURITY_MAX_CHARGES,
            obrienSecurityPoisonCharges, OBRIEN_SECURITY_MAX_CHARGES);
    messageWithColor(buf, &itemMessageColor, 0);
    recordKeystroke(CREATE_ITEM_MONSTER_KEY, false, false); // v0.2.29 Call Security record''',
    '''    sprintf(buf, "Online. Integrity %d/%d; Lightning %d/%d; Poison %d/%d.",
            security->currentHP, security->info.maxHP,
            obrienSecurityLightningCharges, OBRIEN_SECURITY_MAX_CHARGES,
            obrienSecurityPoisonCharges, OBRIEN_SECURITY_MAX_CHARGES);
    obrienHSOSays(buf, &itemMessageColor);
    recordKeystroke(CREATE_ITEM_MONSTER_KEY, false, false); // v0.2.29 Call Security record''',
    "Online. Integrity %d/%d; Lightning %d/%d; Poison %d/%d.",
)

replace_once(
    "src/brogue/Monsters.c",
    '''void obrienCrewMaintenance(void) {
    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE) {
        return;
    }

    if (obrienBashirReturnTurn
        && rogue.absoluteTurnNumber >= obrienBashirReturnTurn
        && obrienFindLivingCrew("Bashir") == NULL) {

        obrienBashirReturnTurn = 0;
        obrienSpawnBashir(player.loc);
        obrienBashirSays("I am back, Miles. Let us try not to make that a habit.", &itemMessageColor);
    }
}''',
    '''void obrienCrewMaintenance(void) {
    if (gameVariant != VARIANT_OBRIEN_MUST_SURVIVE) {
        return;
    }

    obrienDialogueResetIfRewound();

    if (obrienBashirReturnTurn
        && rogue.absoluteTurnNumber >= obrienBashirReturnTurn
        && obrienFindLivingCrew("Bashir") == NULL) {

        obrienBashirReturnTurn = 0;
        obrienSpawnBashir(player.loc);
        obrienBashirSays("I am back, Miles. Let us try not to make that a habit.", &itemMessageColor);
    }

    obrienDepthDialogue();
    obrienPlayerInjuryDialogue();
    obrienAmbientDialogue();
}''',
    "obrienDepthDialogue();",
)

replace_once(
    "src/brogue/RogueMain.c",
    '''        if (!D_IMMORTAL && !nonInteractivePlayback) {
            rogue.playbackMode = false;
        }
        strcpy(buf, "You die...");''',
    '''        if (!D_IMMORTAL && !nonInteractivePlayback) {
            rogue.playbackMode = false;
        }
        if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
            extern void obrienDeathDialogue(void);
            obrienDeathDialogue();
        }
        strcpy(buf, "You die...");''',
    "obrienDeathDialogue();",
)

replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.29",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.30",
    "O'Brien Must Survive v0.2.30",
)

print("O'Brien Must Survive v0.2.30 applied.")
print("- dialogue speakers are hard-limited to Miles, Bashir and HSO")
print("- generic allies, Golems, monsters and summons receive no character dialogue")
print("- Bashir medical events and HSO deployment/status notices now speak in character")
print("- deterministic injury, deep-level and low-frequency ambient dialogue added without substantive RNG")
print("- one final living-crew line can fire before Brogue's normal death screen")
print("- no character dialogue is emitted after the You die / Killed by sequence begins")
print("Build with: make -B -j3 bin/brogue")
