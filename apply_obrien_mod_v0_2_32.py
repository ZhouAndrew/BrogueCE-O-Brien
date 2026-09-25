#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.32 to a Brogue CE 1.15.1 tree.

v0.2.32 adds a compatibility flag for a forensic replay edge case in Bashir's
medical-return timer. The flag lives in byte 13 of the existing 36-byte
recording header, which was previously unused after the NUL-terminated CE
version string. It does not change event offsets, the variant tag, or the
ruleset-generation byte at index 14.

Normal recordings keep the historical >= recovery boundary. Recordings
explicitly tagged with OBRIEN_COMPAT_DELAY_BASHIR_RETURN use a strict >
boundary, delaying Bashir's automatic rematerialization by one input boundary.
This lets affected recordings replay without changing any recorded input or
RNG_CHECK bytes.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_31.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_31.py next to this updater.")


def source_has_v031_or_later():
    main = ROOT / "src/brogue/RogueMain.c"
    rec = ROOT / "src/brogue/Recordings.c"
    if not main.exists() or not rec.exists():
        return False
    mt = main.read_text(encoding="utf-8")
    rt = rec.read_text(encoding="utf-8")
    return (
        "OBRIEN_RULESET_V031" in rt
        and (
            "O'Brien Must Survive v0.2.31" in mt
            or "O'Brien Must Survive v0.2.32" in mt
        )
    )


if source_has_v031_or_later():
    print("Detected O'Brien v0.2.31+ already applied; skipping historical patch replay.")
else:
    runpy.run_path(str(PREVIOUS_PATCH), run_name="__main__")


def replace_once(rel, old, new, marker=None):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker and marker in text:
        print(f"already patched {rel}")
        return
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"patched {rel}")
        return
    raise SystemExit(f"Cannot patch {rel}: expected compatible v0.2.31 source was not found.")


replace_once(
    "src/brogue/Recordings.c",
    """#define OBRIEN_RULESET_HEADER_INDEX    14
#define OBRIEN_RULESET_V030            30
#define OBRIEN_RULESET_V031            31
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V031;

boolean obrienRulesetAtLeast(short version) {""",
    """#define OBRIEN_COMPAT_HEADER_INDEX     13
#define OBRIEN_COMPAT_DELAY_BASHIR_RETURN 0x01
#define OBRIEN_RULESET_HEADER_INDEX    14
#define OBRIEN_RULESET_V030            30
#define OBRIEN_RULESET_V031            31
static unsigned char obrienCompatibilityFlags = 0;
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V031;

boolean obrienBashirRecoveryUsesDelayedBoundary(void) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && (obrienCompatibilityFlags & OBRIEN_COMPAT_DELAY_BASHIR_RETURN) != 0;
}

boolean obrienRulesetAtLeast(short version) {""",
    "OBRIEN_COMPAT_DELAY_BASHIR_RETURN",
)

replace_once(
    "src/brogue/Rogue.h",
    """    boolean obrienRulesetAtLeast(short version);
    void flushBufferToFile(void);""",
    """    boolean obrienRulesetAtLeast(short version);
    boolean obrienBashirRecoveryUsesDelayedBoundary(void);
    void flushBufferToFile(void);""",
    "boolean obrienBashirRecoveryUsesDelayedBoundary(void);",
)

replace_once(
    "src/brogue/Recordings.c",
    """    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
        c[OBRIEN_RULESET_HEADER_INDEX] = obrienRulesetVersion;
    }
    c[15] = RECORDING_VARIANT_TAG""",
    """    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
        c[OBRIEN_COMPAT_HEADER_INDEX] = obrienCompatibilityFlags;
        c[OBRIEN_RULESET_HEADER_INDEX] = obrienRulesetVersion;
    }
    c[15] = RECORDING_VARIANT_TAG""",
    "c[OBRIEN_COMPAT_HEADER_INDEX] = obrienCompatibilityFlags;",
)

replace_once(
    "src/brogue/Recordings.c",
    """        for (i=0; i<15; i++) {
            versionString[i] = recallChar();
        }
        obrienRulesetVersion = (unsigned char) versionString[OBRIEN_RULESET_HEADER_INDEX];
        modeVariantByte = recallChar();""",
    """        for (i=0; i<15; i++) {
            versionString[i] = recallChar();
        }
        obrienCompatibilityFlags = (unsigned char) versionString[OBRIEN_COMPAT_HEADER_INDEX];
        obrienRulesetVersion = (unsigned char) versionString[OBRIEN_RULESET_HEADER_INDEX];
        modeVariantByte = recallChar();""",
    "obrienCompatibilityFlags = (unsigned char) versionString[OBRIEN_COMPAT_HEADER_INDEX];",
)

replace_once(
    "src/brogue/Recordings.c",
    """        obrienRulesetVersion = OBRIEN_RULESET_V031;

        // If present, set the patch version for playing the game.""",
    """        obrienCompatibilityFlags = 0;
        obrienRulesetVersion = OBRIEN_RULESET_V031;

        // If present, set the patch version for playing the game.""",
    "obrienCompatibilityFlags = 0;",
)

replace_once(
    "src/brogue/Monsters.c",
    """    if (obrienBashirReturnTurn
        && rogue.absoluteTurnNumber >= obrienBashirReturnTurn
        && obrienFindLivingCrew("Bashir") == NULL) {""",
    """    if (obrienBashirReturnTurn
        && (obrienBashirRecoveryUsesDelayedBoundary()
            ? rogue.absoluteTurnNumber > obrienBashirReturnTurn
            : rogue.absoluteTurnNumber >= obrienBashirReturnTurn)
        && obrienFindLivingCrew("Bashir") == NULL) {""",
    "obrienBashirRecoveryUsesDelayedBoundary()",
)

replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.31",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.32",
    "O'Brien Must Survive v0.2.32",
)

print("O'Brien Must Survive v0.2.32 applied.")
print("- header byte 13 now carries opt-in O'Brien replay compatibility flags")
print("- affected recordings can delay Bashir rematerialization by one input boundary")
print("- untagged recordings retain the historical >= Bashir recovery boundary")
print("- ruleset generation remains 31; event stream and existing header offsets are unchanged")
print("Build with: make -B -j3 bin/brogue")
