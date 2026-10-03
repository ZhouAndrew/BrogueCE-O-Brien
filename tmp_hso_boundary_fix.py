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
        obrienBashirLastStrengthPotionTurn = rogue.absoluteTurnNumber;

        // Historical ruleset-35 saves crossed a real process boundary here.
        // The Security Hologram's virtual emitter magazines and binding state
        // are process-local statics, so a fresh process reset them even though
        // the hologram creature itself was restored from the save. Reproduce
        // that boundary during full replay so tactical AI consumes RNG exactly
        // as the original resumed run did.
        obrienSecurityRuntimeMonst = NULL;
        obrienSecurityLightningCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityPoisonCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityLastRechargeTurn = rogue.absoluteTurnNumber;
        obrienSecuritySuspended = false;
        obrienSecurityStoredIntegrity = 0;
        obrienSecurityStoredLightningCharges = OBRIEN_SECURITY_MAX_CHARGES;
        obrienSecurityStoredPoisonCharges = OBRIEN_SECURITY_MAX_CHARGES;
    }
}"""

if old not in s:
    raise SystemExit("v0.2.36 saved-game boundary anchor missing")
p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("temporary HSO process-boundary compatibility fix applied")
