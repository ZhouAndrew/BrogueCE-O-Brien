#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.29 to a Brogue CE 1.15.1 tree.

v0.2.29 repairs long O'Brien save playback across older O'Brien rulesets.
Some old saves contain additional one-byte RNG_CHECK audit records between input
events and may also have consumed substantive RNG that the current ruleset no
longer consumes at the same point.  A save is an input recording, so losing RNG
alignment eventually makes the reconstruction diverge and event ID 6 can be
mistaken for ordinary input.

For O'Brien recordings only, this compatibility layer:
- treats a stray RNG_CHECK as an audit record rather than player input;
- advances the current substantive RNG until it re-locks to the recorded audit
  byte (bounded search), preserving the old stream's RNG phase as closely as
  possible;
- performs the same re-lock when a normally expected RNG_CHECK has a mismatched
  byte.
Other variants retain Brogue CE's original strict playback behavior.
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
    raise SystemExit(f"Cannot patch {rel}: expected compatible source was not found.")


# Helper used by both kinds of legacy mismatch.  RNGCheck() always records one
# byte in this Brogue CE branch.  The bounded scan avoids an infinite loop on a
# genuinely corrupt file while allowing older rule sets to have consumed many
# substantive random values between adjacent input records.
replace_once(
    "src/brogue/Recordings.c",
    """static uint64_t recallNumber(short numberOfBytes) {
    short i;
    uint64_t n;

    n = 0;

    for (i=0; i<numberOfBytes; i++) {
        n *= 256;
        n += (uint64_t) recallChar();
    }
    return n;
}
""",
    """static uint64_t recallNumber(short numberOfBytes) {
    short i;
    uint64_t n;

    n = 0;

    for (i=0; i<numberOfBytes; i++) {
        n *= 256;
        n += (uint64_t) recallChar();
    }
    return n;
}

/* OBRIEN_V029_RNG_RELOCK
 * Re-lock an old O'Brien recording to a recorded one-byte RNG audit value.
 * Return the number of additional substantive RNG draws used, or -1 if no
 * match was found inside the safety bound.
 */
static long obrienRelockRNGByte(unsigned char recordedCheck) {
    const long maxDraws = 4096;
    const short oldRNG = rogue.RNG;
    long draws;
    unsigned char replayedCheck = 0;

    rogue.RNG = RNG_SUBSTANTIVE;
    for (draws = 1; draws <= maxDraws; draws++) {
        replayedCheck = (unsigned char) rand_range(0, 255);
        if (replayedCheck == recordedCheck) {
            rogue.RNG = oldRNG;
            return draws;
        }
    }
    rogue.RNG = oldRNG;
    return -1;
}
""",
    "OBRIEN_V029_RNG_RELOCK",
)

# A checkpoint appearing where current code requests input is not input.  Consume
# its payload, re-lock substantive RNG to that audit byte, then ask for input
# again.  This directly fixes the user's event-ID-6 failure path.
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
                    const unsigned char recordedCheck = recallChar();
                    const long relockDraws = obrienRelockRNGByte(recordedCheck);
                    if (relockDraws < 0) {
                        printf(\"O'Brien long-save RNG relock failed at location %li for value %u; continuing salvage.\\n\",
                               recordingLocation - 1, (unsigned) recordedCheck);
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
    "const long relockDraws = obrienRelockRNGByte(recordedCheck);",
)

# If current code does call RNGCheck at the right structural point but its byte
# differs, current RNG is behind an old ruleset that consumed extra substantive
# randomness.  Scan forward to the recorded value instead of aborting the load.
replace_once(
    "src/brogue/Recordings.c",
    """            } else if (recordedNumber != x) {
                printf(\"Expected RNG output of %li; got %i.\\n\", recordedNumber, (int) x);
                playbackPanic();
            }
""",
    """            } else if (recordedNumber != x) {
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && numberOfBytes == 1) {
                    const long relockDraws = obrienRelockRNGByte((unsigned char) recordedNumber);
                    if (relockDraws < 0) {
                        printf(\"O'Brien long-save RNG relock failed for expected value %li after current value %i; continuing salvage.\\n\",
                               recordedNumber, (int) x);
                    }
                } else {
                    printf(\"Expected RNG output of %li; got %i.\\n\", recordedNumber, (int) x);
                    playbackPanic();
                }
            }
""",
    "O'Brien long-save RNG relock failed for expected value",
)

replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.28",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.29",
    "O'Brien Must Survive v0.2.29",
)

print("O'Brien Must Survive v0.2.29 applied.")
print("- stray legacy RNG_CHECK records are treated as audit records, not input")
print("- substantive RNG is re-locked to recorded one-byte checkpoints with a bounded scan")
print("- expected-check byte mismatches use the same O'Brien-only re-lock path")
print("- non-O'Brien playback remains strict and unchanged")
print("Build with: make -B -j3 bin/brogue")
