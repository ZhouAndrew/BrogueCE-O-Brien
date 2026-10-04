#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.37.

v0.2.37 adds an explicit compatibility flag for one historical ruleset-35
Bashir Strength-potion fabrication phase that was process-local and therefore
not represented in the recording stream.

Compatibility policy:
- header byte 13 bit 0x02 means the recording needs the historical Strength
  fabrication phase at replayed SAVED_GAME_LOADED boundaries;
- that phase is applied only while replaying the old recording;
- once replay finishes and the save resumes live play, the normal v0.2.36+
  save/load boundary rebase is used;
- RNG_CHECK remains strict: no recorded checkpoint is skipped, rewritten,
  scanned, guessed or re-locked.

New missions use ruleset generation 37. Gameplay is otherwise unchanged from
v0.2.36.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_36.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_36.py next to this updater.")


def source_has_v036_or_later() -> bool:
    main = ROOT / "src/brogue/RogueMain.c"
    rec = ROOT / "src/brogue/Recordings.c"
    if not main.exists() or not rec.exists():
        return False
    mt = main.read_text(encoding="utf-8")
    rt = rec.read_text(encoding="utf-8")
    return (
        "OBRIEN_RULESET_V036" in rt
        and (
            "O'Brien Must Survive v0.2.36" in mt
            or "O'Brien Must Survive v0.2.37" in mt
        )
    )


if source_has_v036_or_later():
    print("Detected O'Brien v0.2.36+ already applied; skipping historical patch replay.")
else:
    runpy.run_path(str(PREVIOUS_PATCH), run_name="__main__")


def replace_once(rel: str, old: str, new: str, marker: str | None = None) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker and marker in text:
        print(f"already patched {rel}: {marker}")
        return
    if old not in text:
        raise SystemExit(f"Cannot patch {rel}: expected v0.2.36-compatible source was not found.")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel}")


# ---------------------------------------------------------------------------
# Ruleset generation 37 and compatibility bit 0x02.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Recordings.c",
    """#define OBRIEN_RULESET_V035            35
#define OBRIEN_RULESET_V036            36
static unsigned char obrienCompatibilityFlags = 0;
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V036;""",
    """#define OBRIEN_RULESET_V035            35
#define OBRIEN_RULESET_V036            36
#define OBRIEN_RULESET_V037            37
#define OBRIEN_COMPAT_LEGACY_STRENGTH_CLOCK 0x02
static unsigned char obrienCompatibilityFlags = 0;
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V037;""",
    "OBRIEN_RULESET_V037",
)

replace_once(
    "src/brogue/Recordings.c",
    """boolean obrienStrictReplayRuleset35(void) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && rogue.playbackMode
        && obrienRulesetVersion == OBRIEN_RULESET_V035;
}
""",
    """boolean obrienStrictReplayRuleset35(void) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && rogue.playbackMode
        && obrienRulesetVersion == OBRIEN_RULESET_V035;
}

boolean obrienLegacyStrengthClockPhase(void) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && rogue.playbackMode
        && (obrienCompatibilityFlags & OBRIEN_COMPAT_LEGACY_STRENGTH_CLOCK) != 0;
}
""",
    "boolean obrienLegacyStrengthClockPhase(void)",
)

replace_once(
    "src/brogue/Rogue.h",
    """    boolean obrienStrictReplayRuleset35(void);
    void obrienSavedGameLoadedBoundary(void);""",
    """    boolean obrienStrictReplayRuleset35(void);
    boolean obrienLegacyStrengthClockPhase(void);
    void obrienSavedGameLoadedBoundary(void);""",
    "boolean obrienLegacyStrengthClockPhase(void);",
)

replace_once(
    "src/brogue/Recordings.c",
    """        // v0.2.36: brand-new missions start on ruleset 36.
        obrienRulesetVersion = OBRIEN_RULESET_V036;""",
    """        // v0.2.37: brand-new missions start on ruleset 37.
        obrienRulesetVersion = OBRIEN_RULESET_V037;""",
    "v0.2.37: brand-new missions start on ruleset 37.",
)


# ---------------------------------------------------------------------------
# Replay-only historical Bashir fabrication phase.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Monsters.c",
    """        obrienBashirLastStrengthPotionTurn = rogue.absoluteTurnNumber;""",
    """        // v0.2.37: a small set of historical ruleset-35 recordings
        // crossed this process boundary with the old process-local fabrication
        // phase. Header compat bit 0x02 restores that replay-only phase.
        // Live resume deliberately falls back to the normal current-turn rebase.
        obrienBashirLastStrengthPotionTurn =
            obrienLegacyStrengthClockPhase() ? 40 : rogue.absoluteTurnNumber;""",
    "v0.2.37: a small set of historical ruleset-35 recordings",
)


# ---------------------------------------------------------------------------
# Public version text.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.36",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.37",
    "O'Brien Must Survive v0.2.37",
)

print("O'Brien Must Survive v0.2.37 applied.")
print("- new missions use ruleset generation 37")
print("- header compatibility bit 0x02 restores the verified historical Bashir Strength-clock phase during replay")
print("- live resume uses the normal current-turn fabrication-clock rebase")
print("- RNG_CHECK remains strict; no checkpoint is skipped, rewritten, scanned or re-locked")
print("- gameplay otherwise remains v0.2.36")
print("Build with: make -B -j3 bin/brogue")
