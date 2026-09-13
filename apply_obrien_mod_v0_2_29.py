#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.29 to a Brogue CE 1.15.1 tree.

v0.2.29 adds compatibility for long O'Brien saves recorded by an older O'Brien
ruleset that emitted additional RNG_CHECK records between player input events.
Those checks are audit records, not input.  Treating event ID 6 as a keystroke
causes loading to abort even though the recording stream is intact.

For O'Brien recordings only, when recallEvent encounters an unexpected RNG_CHECK,
consume its one-byte payload and perform the same substantive rand_range(0,255)
step that RNGCheck() would have performed in the older build.  This both skips the
obsolete audit record and keeps the substantive RNG state aligned for the rest of
the replay.  Other variants retain Brogue CE's strict playback behavior.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_28.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_28.py next to this updater.")


def source_has_v028_or_later():
    rec = ROOT / "src/brogue/Recordings.c"
    main = ROOT / "src/brogue/RogueMain.c"
    if not rec.exists() or not main.exists():
        return False
    rec_text = rec.read_text(encoding="utf-8")
    main_text = main.read_text(encoding="utf-8")
    return (
        "RECORDING_VARIANT_TAG" in rec_text
        and (
            "O'Brien Must Survive v0.2.28" in main_text
            or "O'Brien Must Survive v0.2.29" in main_text
        )
    )


if source_has_v028_or_later():
    print("Detected O'Brien v0.2.28+ already applied; skipping historical patch replay.")
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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.28 source was not found.")


replace_once(
    "src/brogue/Recordings.c",
    """            case RNG_CHECK:
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message(\"Unrecognized event type in playback.\", REQUIRE_ACKNOWLEDGMENT);
                printf(\"Unrecognized event type in playback: event ID %i\", c);
                tryAgain = true;
                playbackPanic();
                break;""",
    """            case RNG_CHECK:
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                    /* v0.2.29 long-save compatibility: some older O'Brien builds
                     * emitted additional RNGCheck() audit records between input
                     * events.  Reproduce the old audit RNG step as well as
                     * consuming its recorded byte; otherwise later substantive
                     * RNG would be one call behind for every skipped checkpoint.
                     */
                    const unsigned char recordedCheck = recallChar();
                    const short oldRNG = rogue.RNG;
                    rogue.RNG = RNG_SUBSTANTIVE;
                    const unsigned char replayedCheck = (unsigned char) rand_range(0, 255);
                    rogue.RNG = oldRNG;
                    if (recordedCheck != replayedCheck) {
                        printf(\"O'Brien legacy RNG checkpoint mismatch at location %li: recorded %u, replayed %u.\\n\",
                               recordingLocation - 1, (unsigned) recordedCheck, (unsigned) replayedCheck);
                    }
                    tryAgain = true;
                    break;
                }
                /* Non-O'Brien variants keep the original strict behavior. */
                // fall through
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message(\"Unrecognized event type in playback.\", REQUIRE_ACKNOWLEDGMENT);
                printf(\"Unrecognized event type in playback: event ID %i\", c);
                tryAgain = true;
                playbackPanic();
                break;""",
    "v0.2.29 long-save compatibility",
)

replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.28",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.29",
    "O'Brien Must Survive v0.2.29",
)

print("O'Brien Must Survive v0.2.29 applied.")
print("- legacy O'Brien RNG_CHECK records encountered between input events are replayed, not treated as input")
print("- each salvaged checkpoint advances substantive RNG exactly once to preserve alignment")
print("- non-O'Brien playback remains strict and unchanged")
print("Build with: make -B -j3 bin/brogue")
