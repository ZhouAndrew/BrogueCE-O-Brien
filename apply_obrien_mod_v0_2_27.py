#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.27 to a clean Brogue CE 1.15.1 tree.

v0.2.27 turns the intrinsic C command into a true Security Hologram toggle:
- C while no HSO is active deploys one Security Hologram;
- C while the HSO is active deactivates it immediately;
- a manual shutdown preserves integrity and emitter charge state for redeployment;
- only one HSO can exist at a time;
- the HSO uses Brogue's native TELEPATHIC_VISIBLE path as a long-distance visual
  link, rather than a custom map-reveal implementation.

Lightning friendly-fire remains native Brogue behavior. This update gives O'Brien
an immediate way to take the hologram offline without making its bolts magically
ignore friendly targets.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_26.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_26.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.26 source was not found.")


# Preserve the state of a manually deactivated projection. This prevents C-off / C-on
# from becoming a free heal or free 20/20 emitter refill.
replace_once(
    "src/brogue/Monsters.c",
    """static unsigned long obrienSecurityLastRechargeTurn = 0;
static unsigned long obrienBashirReturnTurn = 0;""",
    """static unsigned long obrienSecurityLastRechargeTurn = 0;
// v0.2.27: manual HSO shutdown is suspension, not destruction.
static boolean obrienSecuritySuspended = false;
static short obrienSecurityStoredIntegrity = 0;
static short obrienSecurityStoredLightningCharges = OBRIEN_SECURITY_MAX_CHARGES;
static short obrienSecurityStoredPoisonCharges = OBRIEN_SECURITY_MAX_CHARGES;
static unsigned long obrienBashirReturnTurn = 0;""",
    "v0.2.27: manual HSO shutdown is suspension",
)

replace_once(
    "src/brogue/Monsters.c",
    """static void obrienBindSecurityRuntime(creature *monst) {
    if (!obrienIsSecurityHologram(monst)) {
        return;
    }
    if (obrienSecurityRuntimeMonst != monst) {
        obrienSecurityRuntimeMonst = monst;
        obrienSecurityLightningCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityPoisonCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityLastRechargeTurn = rogue.absoluteTurnNumber;
    }
}""",
    """static void obrienBindSecurityRuntime(creature *monst) {
    if (!obrienIsSecurityHologram(monst)) {
        return;
    }
    if (obrienSecurityRuntimeMonst != monst) {
        obrienSecurityRuntimeMonst = monst;
        if (obrienSecuritySuspended) {
            // A manual C-toggle shutdown preserves tactical state. The hologram
            // was offline, so passive repair/recharge does not advance while absent.
            monst->currentHP = max(1, min(monst->info.maxHP, obrienSecurityStoredIntegrity));
            obrienSecurityLightningCharges = max(0, min(OBRIEN_SECURITY_MAX_CHARGES,
                                                         obrienSecurityStoredLightningCharges));
            obrienSecurityPoisonCharges = max(0, min(OBRIEN_SECURITY_MAX_CHARGES,
                                                      obrienSecurityStoredPoisonCharges));
            obrienSecurityLastRechargeTurn = rogue.absoluteTurnNumber;
            obrienSecuritySuspended = false;
        } else {
            // A genuinely destroyed projection is recreated fresh.
            obrienSecurityLightningCharges = OBRIEN_SECURITY_MAX_CHARGES;
            obrienSecurityPoisonCharges = OBRIEN_SECURITY_MAX_CHARGES;
            obrienSecurityLastRechargeTurn = rogue.absoluteTurnNumber;
        }
    }
}""",
    "A manual C-toggle shutdown preserves tactical state",
)

# Keep the native remote-vision link asserted for old saves as well as newly
# deployed HSO instances. Brogue's own updateTelepathy() turns a
# MB_TELEPATHICALLY_REVEALED creature into TELEPATHIC_VISIBLE cells around it,
# and the normal renderer describes this as seeing through another creature's eyes.
replace_once(
    "src/brogue/Monsters.c",
    """        obrienBindSecurityRuntime(monst);
        obrienRechargeSecurityWeapons(monst);
        if (monst->creatureState != MONSTER_ALLY) {""",
    """        obrienBindSecurityRuntime(monst);
        obrienRechargeSecurityWeapons(monst);
        monst->bookkeepingFlags |= MB_TELEPATHICALLY_REVEALED;
        if (monst->creatureState != MONSTER_ALLY) {""",
    "monst->bookkeepingFlags |= MB_TELEPATHICALLY_REVEALED;",
)

# C is now a true toggle. Manual shutdown is administrative disappearance, not
# death; the stored state above is restored on the next deployment. A naturally
# destroyed HSO does not set obrienSecuritySuspended, so the replacement is fresh.
replace_once(
    "src/brogue/Monsters.c",
    """boolean obrienCallSecuritySpell(void) {
    creature *security;""",
    """boolean obrienCallSecuritySpell(void) {
    creature *security;
    char buf[COLS];""",
    "char buf[COLS];",
)

replace_once(
    "src/brogue/Monsters.c",
    """    security = obrienFindLivingCrew("Security Hologram");
    if (security != NULL) {
        message("Security hologram already deployed; it will regroup after combat.", 0);
        return false;
    }

    security = generateMonster(MK_GOLEM, false, false);""",
    """    security = obrienFindLivingCrew("Security Hologram");
    if (security != NULL) {
        obrienRechargeSecurityWeapons(security);
        obrienSecurityStoredIntegrity = security->currentHP;
        obrienSecurityStoredLightningCharges = obrienSecurityLightningCharges;
        obrienSecurityStoredPoisonCharges = obrienSecurityPoisonCharges;
        obrienSecuritySuspended = true;
        obrienSecurityRuntimeMonst = NULL;
        security->bookkeepingFlags &= ~MB_TELEPATHICALLY_REVEALED;
        killCreature(security, true);
        messageWithColor("Security Hologram offline. C will redeploy it with retained tactical state.",
                         &itemMessageColor, 0);
        playerTurnEnded();
        return true;
    }

    // If the previous projection was actually destroyed, ensure a newly allocated
    // HSO cannot accidentally inherit the stale runtime pointer/charge state.
    if (!obrienSecuritySuspended) {
        obrienSecurityRuntimeMonst = NULL;
    }

    security = generateMonster(MK_GOLEM, false, false);""",
    "C will redeploy it with retained tactical state",
)

replace_once(
    "src/brogue/Monsters.c",
    """    becomeAllyWith(security);
    security->loc = getQualifyingPathLocNear(player.loc, true,""",
    """    becomeAllyWith(security);
    // Native Brogue long-distance visual link: updateTelepathy() uses this flag
    // to expose the HSO's local field through TELEPATHIC_VISIBLE.
    security->bookkeepingFlags |= MB_TELEPATHICALLY_REVEALED;
    security->loc = getQualifyingPathLocNear(player.loc, true,""",
    "Native Brogue long-distance visual link",
)

replace_once(
    "src/brogue/Monsters.c",
    """    messageWithColor("Call Security: Security Hologram online. Lightning 20/20; Poison 20/20.", &itemMessageColor, 0);
    playerTurnEnded();""",
    """    sprintf(buf, "Security Hologram online. Lightning %d/%d; Poison %d/%d.",
            obrienSecurityLightningCharges, OBRIEN_SECURITY_MAX_CHARGES,
            obrienSecurityPoisonCharges, OBRIEN_SECURITY_MAX_CHARGES);
    messageWithColor(buf, &itemMessageColor, 0);
    playerTurnEnded();""",
    "Security Hologram online. Lightning %d/%d; Poison %d/%d.",
)

# The action menu should describe what C now does instead of implying a summon-only
# spell. The key binding and non-O'Brien Wizard create-item behavior are unchanged.
io_path = ROOT / "src/brogue/IO.c"
io_text = io_path.read_text(encoding="utf-8")
if "Call Security spell" in io_text:
    io_path.write_text(io_text.replace("Call Security spell", "Toggle Security Hologram"), encoding="utf-8")
    print("patched src/brogue/IO.c")
elif "Toggle Security Hologram" in io_text:
    print("already patched src/brogue/IO.c")
else:
    raise SystemExit("Cannot patch src/brogue/IO.c: Call Security menu label not found.")


# Version banner.
replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.26",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.27",
    "O'Brien Must Survive v0.2.27",
)

print("O'Brien Must Survive v0.2.27 applied.")
print("- C is now a true Security Hologram toggle: deploy when OFF, deactivate when ON")
print("- Manual shutdown preserves HSO integrity plus Lightning/Poison charge state")
print("- Only one Security Hologram can be active at a time")
print("- HSO uses Brogue's native MB_TELEPATHICALLY_REVEALED -> TELEPATHIC_VISIBLE remote vision path")
print("- HSO Lightning friendly-fire remains native Brogue behavior")
print("- HSO combat stats, flight, repair and emitter recharge pacing are otherwise unchanged")
print("Build normally with: make -B")
