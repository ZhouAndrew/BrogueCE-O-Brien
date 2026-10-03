#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.36.

v0.2.36 adds a strict replay-compatibility boundary for historical ruleset 35
recordings without weakening RNG verification.

The ruleset-35 issue is a replay-only process-boundary mismatch: old recordings
can contain SAVED_GAME_LOADED events, while Bashir's 2000-turn Strength-potion
fabrication clock lives in process-local static state.  When an old save is
replayed from turn zero, that clock can otherwise continue across a historical
load boundary and fabricate a potion earlier than the recorded run did,
consuming substantive RNG and causing the next RNG_CHECK to fail.

Compatibility policy:
- ruleset 35 playback recognizes SAVED_GAME_LOADED as a strict state boundary;
- at that boundary Bashir's fabrication clock is rebased to the current
  absolute turn;
- live resume of ruleset 35+ performs the same rebase before recording the
  normal SAVED_GAME_LOADED marker, so future replay sees the same state change;
- no RNG_CHECK is skipped, changed, fabricated, re-locked or ignored;
- pre-v0.2.35 rulesets retain their existing replay behavior unchanged.

New missions use ruleset generation 36.  Gameplay is otherwise unchanged from
v0.2.35.
"""

from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_35.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_35.py next to this updater.")


def source_has_v035_or_later() -> bool:
    main = ROOT / "src/brogue/RogueMain.c"
    rec = ROOT / "src/brogue/Recordings.c"
    if not main.exists() or not rec.exists():
        return False
    mt = main.read_text(encoding="utf-8")
    rt = rec.read_text(encoding="utf-8")
    return (
        "OBRIEN_RULESET_V035" in rt
        and (
            "O'Brien Must Survive v0.2.35" in mt
            or "O'Brien Must Survive v0.2.36" in mt
        )
    )


if source_has_v035_or_later():
    print("Detected O'Brien v0.2.35+ already applied; skipping historical patch replay.")
else:
    runpy.run_path(str(PREVIOUS_PATCH), run_name="__main__")


def replace_once(rel: str, old: str, new: str, marker: str | None = None) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker and marker in text:
        print(f"already patched {rel}: {marker}")
        return
    if old not in text:
        raise SystemExit(f"Cannot patch {rel}: expected v0.2.35-compatible source was not found.")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel}")


def regex_replace_once(rel: str, pattern: str, repl: str, marker: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print(f"already patched {rel}: {marker}")
        return
    new_text, count = re.subn(pattern, repl, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"Cannot patch {rel}: pattern for {marker!r} matched {count} times.")
    path.write_text(new_text, encoding="utf-8")
    print(f"patched {rel}")


# ---------------------------------------------------------------------------
# Ruleset generation 36 and strict ruleset-35 replay predicate.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Recordings.c",
    """#define OBRIEN_RULESET_V033            33
#define OBRIEN_RULESET_V035            35
static unsigned char obrienCompatibilityFlags = 0;
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V035;""",
    """#define OBRIEN_RULESET_V033            33
#define OBRIEN_RULESET_V035            35
#define OBRIEN_RULESET_V036            36
static unsigned char obrienCompatibilityFlags = 0;
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V036;""",
    "OBRIEN_RULESET_V036",
)

replace_once(
    "src/brogue/Recordings.c",
    """boolean obrienRulesetAtLeast(short version) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && obrienRulesetVersion >= version;
}
""",
    """boolean obrienRulesetAtLeast(short version) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && obrienRulesetVersion >= version;
}

boolean obrienStrictReplayRuleset35(void) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && rogue.playbackMode
        && obrienRulesetVersion == OBRIEN_RULESET_V035;
}
""",
    "boolean obrienStrictReplayRuleset35(void)",
)

replace_once(
    "src/brogue/Rogue.h",
    "    boolean obrienRulesetAtLeast(short version);\n",
    """    boolean obrienRulesetAtLeast(short version);
    boolean obrienStrictReplayRuleset35(void);
    void obrienSavedGameLoadedBoundary(void);
""",
    "boolean obrienStrictReplayRuleset35(void);",
)

rec_path = ROOT / "src/brogue/Recordings.c"
rec_text = rec_path.read_text(encoding="utf-8")
new_game_marker = "v0.2.36: brand-new missions start on ruleset 36."
if new_game_marker not in rec_text:
    pat = re.compile(
        r"(?P<indent>^[ \t]*)// v0\.2\.35: brand-new missions start on ruleset 35\.\n"
        r"(?P=indent)obrienRulesetVersion = OBRIEN_RULESET_V035;",
        re.MULTILINE,
    )
    match = pat.search(rec_text)
    if not match:
        raise SystemExit("Cannot patch src/brogue/Recordings.c: v0.2.35 new-game ruleset initializer not found.")
    indent = match.group("indent")
    replacement = (
        f"{indent}// {new_game_marker}\n"
        f"{indent}obrienRulesetVersion = OBRIEN_RULESET_V036;"
    )
    rec_text = rec_text[:match.start()] + replacement + rec_text[match.end():]
    rec_path.write_text(rec_text, encoding="utf-8")
    print("patched src/brogue/Recordings.c: new-game ruleset 36")
else:
    print("already patched src/brogue/Recordings.c: new-game ruleset 36")


# ---------------------------------------------------------------------------
# Bashir fabrication clock: make save/load boundaries replayable.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Monsters.c",
    """static unsigned long obrienBashirReturnTurn = 0;
static unsigned long obrienBashirLastStrengthPotionTurn = 0;""",
    """static unsigned long obrienBashirReturnTurn = 0;
static unsigned long obrienBashirLastStrengthPotionTurn = 0;

// v0.2.36 replay contract: this is the only process-local O'Brien timer whose
// historical save/load boundary must be reproduced explicitly.  The boundary
// itself is already present in old recordings as SAVED_GAME_LOADED.
void obrienSavedGameLoadedBoundary(void) {
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && obrienRulesetAtLeast(35)) {
        obrienBashirLastStrengthPotionTurn = rogue.absoluteTurnNumber;
    }
}""",
    "void obrienSavedGameLoadedBoundary(void)",
)


# During strict ruleset-35 replay, replay the same fabrication-clock boundary
# that existed when the historical save was resumed.  Ruleset 36+ records the
# same boundary deliberately, so it uses the same hook.
replace_once(
    "src/brogue/Recordings.c",
    """            case SAVED_GAME_LOADED:
                tryAgain = true;
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                    // This marks the historical point at which an old save was
                    // resumed under v0.2.34 live rules. Recreate the current-level
                    // map silently during replay, then map future level entries.
                    obrienAutoMapContinuation = true;
                    obrienAutoApplyMagicMappingScroll(false);
                }
                flashTemporaryAlert(" Saved game loaded ", 1000);
                break;""",
    """            case SAVED_GAME_LOADED:
                tryAgain = true;
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                    // v0.2.36 strict replay bridge: ruleset 35 recordings may
                    // cross a historical process boundary here. Rebase Bashir's
                    // process-local fabrication clock exactly at that boundary.
                    // Ruleset 36+ uses the same explicit boundary contract.
                    if (obrienStrictReplayRuleset35() || obrienRulesetAtLeast(36)) {
                        obrienSavedGameLoadedBoundary();
                    }

                    // This marks the historical point at which an old save was
                    // resumed under v0.2.34 live rules. Recreate the current-level
                    // map silently during replay, then map future level entries.
                    obrienAutoMapContinuation = true;
                    obrienAutoApplyMagicMappingScroll(false);
                }
                flashTemporaryAlert(" Saved game loaded ", 1000);
                break;""",
    "v0.2.36 strict replay bridge",
)


# A newly resumed ruleset-35+ game must perform the same rebase before the
# existing loadSavedGame() code records SAVED_GAME_LOADED. That makes the
# continuation self-describing and replay-stable without touching RNG_CHECK.
replace_once(
    "src/brogue/Recordings.c",
    """    displayLevel();

    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
        // Strict historical replay has finished. From this exact boundary onward
        // O'Brien receives the automatic Mapping scroll behavior, including old
        // saves whose original ruleset predates v0.2.33.
        obrienAutoMapContinuation = true;""",
    """    displayLevel();

    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
        // v0.2.36: live resume uses the same deterministic fabrication-clock
        // boundary that strict ruleset-35 replay recognizes above.
        if (obrienRulesetAtLeast(35)) {
            obrienSavedGameLoadedBoundary();
        }

        // Strict historical replay has finished. From this exact boundary onward
        // O'Brien receives the automatic Mapping scroll behavior, including old
        // saves whose original ruleset predates v0.2.33.
        obrienAutoMapContinuation = true;""",
    "v0.2.36: live resume uses the same deterministic fabrication-clock",
)


# ---------------------------------------------------------------------------
# Public version text.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.35",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.36",
    "O'Brien Must Survive v0.2.36",
)

print("O'Brien Must Survive v0.2.36 applied.")
print("- new missions use ruleset generation 36")
print("- historical ruleset 35 SAVED_GAME_LOADED boundaries rebase Bashir's Strength-potion clock")
print("- live ruleset 35+ resume records the same deterministic boundary semantics")
print("- RNG_CHECK remains strict; no checkpoint is skipped, rewritten, scanned or re-locked")
print("- gameplay otherwise remains v0.2.35")
print("Build with: make -B -j3 bin/brogue")
