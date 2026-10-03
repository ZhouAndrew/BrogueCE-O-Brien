#!/usr/bin/env python3
from pathlib import Path

p = Path("src/brogue/Monsters.c")
s = p.read_text(encoding="utf-8")

old = """void obrienSavedGameLoadedBoundary(void) {
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && obrienRulesetAtLeast(35)) {
        obrienBashirLastStrengthPotionTurn = rogue.absoluteTurnNumber;
    }
}"""

new = """void obrienSavedGameLoadedBoundary(void) {
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && obrienRulesetAtLeast(35)) {
        if (getenv("OBRIEN_USER_SAVE_PROBE")) {
            printf("OBRIEN_BOUNDARY before player=%li absolute=%lu bashirReturn=%lu strengthClock=%lu "
                   "securityPtr=%p L=%d P=%d recharge=%lu suspended=%d storedHP=%d storedL=%d storedP=%d\\n",
                   rogue.playerTurnNumber, rogue.absoluteTurnNumber,
                   obrienBashirReturnTurn, obrienBashirLastStrengthPotionTurn,
                   (void *) obrienSecurityRuntimeMonst,
                   obrienSecurityLightningCharges, obrienSecurityPoisonCharges,
                   obrienSecurityLastRechargeTurn, obrienSecuritySuspended,
                   obrienSecurityStoredIntegrity,
                   obrienSecurityStoredLightningCharges,
                   obrienSecurityStoredPoisonCharges);
            fflush(stdout);
        }

        // A historical SAVED_GAME_LOADED marks a process restart. Reconstruct
        // every O'Brien gameplay-relevant process-local static from its fresh
        // process value before the resumed run continues.
        obrienBashirReturnTurn = 0;
        obrienBashirLastStrengthPotionTurn = rogue.absoluteTurnNumber;

        obrienSecurityRuntimeMonst = NULL;
        obrienSecurityLightningCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityPoisonCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityLastRechargeTurn = 0;
        obrienSecuritySuspended = false;
        obrienSecurityStoredIntegrity = 0;
        obrienSecurityStoredLightningCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityStoredPoisonCharges = OBRIEN_SECURITY_MAX_CHARGES;

        if (getenv("OBRIEN_USER_SAVE_PROBE")) {
            printf("OBRIEN_BOUNDARY after player=%li absolute=%lu bashirReturn=%lu strengthClock=%lu "
                   "securityPtr=%p L=%d P=%d recharge=%lu suspended=%d storedHP=%d storedL=%d storedP=%d\\n",
                   rogue.playerTurnNumber, rogue.absoluteTurnNumber,
                   obrienBashirReturnTurn, obrienBashirLastStrengthPotionTurn,
                   (void *) obrienSecurityRuntimeMonst,
                   obrienSecurityLightningCharges, obrienSecurityPoisonCharges,
                   obrienSecurityLastRechargeTurn, obrienSecuritySuspended,
                   obrienSecurityStoredIntegrity,
                   obrienSecurityStoredLightningCharges,
                   obrienSecurityStoredPoisonCharges);
            fflush(stdout);
        }
    }
}"""

if old not in s:
    raise SystemExit("v0.2.36 saved-game boundary anchor missing")
p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("temporary full O'Brien gameplay-static boundary fix applied")
