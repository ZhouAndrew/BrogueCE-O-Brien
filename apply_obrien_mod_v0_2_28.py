#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.28 to a clean Brogue CE 1.15.1 tree.

v0.2.28 makes O'Brien recordings self-describing. Brogue CE's 36-byte recording
header historically stored only the game mode, not the selected variant. That is
fatal for O'Brien playback because replaying the same seed as ordinary Brogue
changes substantive RNG use before the recorded input stream is consumed.

The fix keeps the header length unchanged. Byte 15 now contains a tagged packed
value: bit 7 marks the new format, bits 4..6 store gameVariant, and bits 0..3
store rogue.mode. Legacy untagged recordings remain readable with the currently
selected variant. A companion migration utility can tag old O'Brien saves.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_27.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_27.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.27 source was not found.")


# Keep the on-disk header at 36 bytes. We only use spare bits in the existing
# mode byte so offsets for seed/turn/depth/length and the event stream do not move.
replace_once(
    "src/brogue/Recordings.c",
    "#define RECORDING_HEADER_LENGTH     36  // bytes at the start of the recording file to store global data",
    """#define RECORDING_HEADER_LENGTH     36  // bytes at the start of the recording file to store global data

// v0.2.28 recording header byte 15 layout:
//   bit 7      = tagged variant-aware header
//   bits 4..6  = gameVariant (0..7)
//   bits 0..3  = gameMode (0..15)
// The header remains exactly 36 bytes, so all existing offsets remain stable.
#define RECORDING_VARIANT_TAG          0x80
#define RECORDING_VARIANT_SHIFT        4
#define RECORDING_VARIANT_MASK         0x07
#define RECORDING_MODE_MASK            0x0F""",
    "RECORDING_VARIANT_TAG",
)

replace_once(
    "src/brogue/Recordings.c",
    "    c[15] = rogue.mode;",
    """    c[15] = RECORDING_VARIANT_TAG
          | ((gameVariant & RECORDING_VARIANT_MASK) << RECORDING_VARIANT_SHIFT)
          | (rogue.mode & RECORDING_MODE_MASK);""",
    "((gameVariant & RECORDING_VARIANT_MASK) << RECORDING_VARIANT_SHIFT)",
)

replace_once(
    "src/brogue/Recordings.c",
    """    unsigned short recPatch;
    char buf[1000], *versionString = rogue.versionString;""",
    """    unsigned short recPatch;
    unsigned char modeVariantByte, encodedVariant;
    char buf[1000], *versionString = rogue.versionString;""",
    "unsigned char modeVariantByte, encodedVariant;",
)

replace_once(
    "src/brogue/Recordings.c",
    """        rogue.mode = recallChar();

        if (getPatchVersion(versionString, &recPatch) && recPatch <= gameConst->patchVersion) {""",
    """        modeVariantByte = recallChar();
        if (modeVariantByte & RECORDING_VARIANT_TAG) {
            rogue.mode = (enum gameMode) (modeVariantByte & RECORDING_MODE_MASK);
            encodedVariant = (modeVariantByte >> RECORDING_VARIANT_SHIFT) & RECORDING_VARIANT_MASK;
            if (encodedVariant < NUMBER_VARIANTS) {
                gameVariant = encodedVariant;
            } else {
                // Corrupt/future header: stay on ordinary Brogue rather than indexing
                // outside the variant table. Version validation below still applies.
                gameVariant = VARIANT_BROGUE;
            }
        } else {
            // Legacy Brogue header. It contains no variant field, so preserve the
            // variant selected by the caller. This keeps old vanilla recordings
            // unchanged and lets migrated/explicitly selected O'Brien games replay.
            rogue.mode = (enum gameMode) modeVariantByte;
        }

        if (getPatchVersion(versionString, &recPatch) && recPatch <= gameConst->patchVersion) {""",
    "modeVariantByte & RECORDING_VARIANT_TAG",
)

# Version banner only; gameplay rules are unchanged.
replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.27",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.28",
    "O'Brien Must Survive v0.2.28",
)

print("O'Brien Must Survive v0.2.28 applied.")
print("- recordings/saves now persist the selected variant in header byte 15")
print("- header stays 36 bytes; seed/turn/depth/event offsets are unchanged")
print("- legacy untagged recordings remain readable using the selected variant")
print("- use repair_legacy_obrien_save.py once for old O'Brien .broguesave/.broguerec files")
print("Build normally with: make -B")
