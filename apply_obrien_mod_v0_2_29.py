#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.29 to a Brogue CE 1.15.1 tree.

v0.2.29 repairs long O'Brien save playback across older O'Brien rulesets.
Some old saves contain additional one-byte RNG_CHECK audit records between input
events, omit checks now expected by the current ruleset, or consumed substantive
RNG at different points.  A save is an input recording, so losing either byte
alignment or RNG phase eventually makes reconstruction fail.

For O'Brien recordings only, this compatibility layer:
- treats a stray RNG_CHECK as an audit record rather than player input;
- re-locks substantive RNG to recorded one-byte audit values with a bounded scan;
- if current code expects a checkpoint that the old save does not contain, puts
  the real input event byte back into the logical playback stream instead of
  consuming it as RNG data.
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


# One-byte logical pushback.  We cannot simply decrement the physical buffer
# index because recallChar() may just have crossed a 1000-byte input-buffer
# boundary.  Logical pushback works correctly on either side of that boundary.
replace_once(
    "src/brogue/Recordings.c",
    """enum recordingSeekModes {
    RECORDING_SEEK_MODE_TURN,
    RECORDING_SEEK_MODE_DEPTH
};

static void recordChar(unsigned char c) {""",
    """enum recordingSeekModes {
    RECORDING_SEEK_MODE_TURN,
    RECORDING_SEEK_MODE_DEPTH
};

/* OBRIEN_V029_PLAYBACK_PUSHBACK */
static int obrienPlaybackPushedChar = -1;

static void recordChar(unsigned char c) {""",
    "OBRIEN_V029_PLAYBACK_PUSHBACK",
)

replace_once(
    "src/brogue/Recordings.c",
    """static unsigned char recallChar() {
    unsigned char c;
    if (recordingLocation > lengthOfPlaybackFile) {
        return END_OF_RECORDING;
    }
    c = inputRecordBuffer[locationInRecordingBuffer++];
    recordingLocation++;
    if (locationInRecordingBuffer >= INPUT_RECORD_BUFFER) {
        fillBufferFromFile();
    }
    return c;
}
""",
    """static unsigned char recallChar() {
    unsigned char c;

    if (obrienPlaybackPushedChar >= 0) {
        c = (unsigned char) obrienPlaybackPushedChar;
        obrienPlaybackPushedChar = -1;
        recordingLocation++;
        return c;
    }

    if (recordingLocation > lengthOfPlaybackFile) {
        return END_OF_RECORDING;
    }
    c = inputRecordBuffer[locationInRecordingBuffer++];
    recordingLocation++;
    if (locationInRecordingBuffer >= INPUT_RECORD_BUFFER) {
        fillBufferFromFile();
    }
    return c;
}

static void obrienPushBackPlaybackChar(unsigned char c) {
    if (obrienPlaybackPushedChar >= 0) {
        return;
    }
    obrienPlaybackPushedChar = c;
    if (recordingLocation > 0) {
        recordingLocation--;
    }
}
""",
    "static void obrienPushBackPlaybackChar",
)

replace_once(
    "src/brogue/Recordings.c",
    """    locationInRecordingBuffer   = 0;
    positionInPlaybackFile      = 0;
    recordingLocation           = 0;
    maxLevelChanges             = 0;""",
    """    locationInRecordingBuffer   = 0;
    positionInPlaybackFile      = 0;
    recordingLocation           = 0;
    obrienPlaybackPushedChar    = -1;
    maxLevelChanges             = 0;""",
    "obrienPlaybackPushedChar    = -1;",
)

# Helper used by both kinds of legacy RNG mismatch. RNGCheck() records one byte
# in this Brogue CE branch. The bounded scan avoids an infinite loop on a
# genuinely corrupt file while allowing old rulesets to have consumed many
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

# A checkpoint appearing where current code requests input is not input. Consume
# its payload, re-lock substantive RNG to that audit byte, then ask for input
# again. This directly fixes event-ID-6 being mistaken for player input.
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

# In the opposite mismatch, current code asks for RNG_CHECK but an older save
# already has the next real input event. Check the event type before consuming
# an RNG payload and logically push the input type byte back for recallEvent().
replace_once(
    "src/brogue/Recordings.c",
    """        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);
        if (eventType != RNG_CHECK || recordedNumber != x) {
            if (eventType != RNG_CHECK) {
                printf(\"Event type mismatch in RNG check.\\n\");
                playbackPanic();
            } else if (recordedNumber != x) {""",
    """        eventType = recallChar();
        if (eventType != RNG_CHECK && gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
            obrienPushBackPlaybackChar(eventType);
            return;
        }
        recordedNumber = recallNumber(numberOfBytes);
        if (eventType != RNG_CHECK || recordedNumber != x) {
            if (eventType != RNG_CHECK) {
                printf(\"Event type mismatch in RNG check.\\n\");
                playbackPanic();
            } else if (recordedNumber != x) {""",
    "obrienPushBackPlaybackChar(eventType);",
)

# If current code calls RNGCheck at the right structural point but its byte
# differs, scan forward to the old audit value instead of aborting the load.
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
print("- missing legacy checkpoints preserve the next input byte with logical pushback")
print("- non-O'Brien playback remains strict and unchanged")
print("Build with: make -B -j3 bin/brogue")
