#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/Desktop/BrogueCE-O-Brien-src}"
SRC="$ROOT/src/brogue/Recordings.c"

if [[ ! -f "$SRC" ]]; then
    echo "ERROR: cannot find $SRC" >&2
    echo "Usage: bash $0 /path/to/BrogueCE-O-Brien-src" >&2
    exit 2
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
cp -a "$SRC" "$SRC.pre-long-save-salvage-$STAMP.bak"

python3 - "$SRC" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

MARKER = "OBRIEN_LONG_SAVE_SALVAGE"
if MARKER in s:
    print("Recordings.c already contains the long-save salvage patch.")
    raise SystemExit(0)

needle = """enum recordingSeekModes {
    RECORDING_SEEK_MODE_TURN,
    RECORDING_SEEK_MODE_DEPTH
};

static void recordChar(unsigned char c) {"""
repl = """enum recordingSeekModes {
    RECORDING_SEEK_MODE_TURN,
    RECORDING_SEEK_MODE_DEPTH
};

/* OBRIEN_LONG_SAVE_SALVAGE
 * Old O'Brien long saves can contain an RNG_CHECK at a point where a newer
 * ruleset asks for the next input event (or vice versa).  The save stream is
 * still structurally valid; we need one byte of logical pushback so an
 * OOSCheck that is absent in the old stream does not consume a real input.
 */
static int obrienPlaybackPushedChar = -1;
static boolean obrienPlaybackSalvageWarned = false;

static void recordChar(unsigned char c) {"""
if needle not in s:
    raise SystemExit("Cannot patch: recordingSeekModes anchor not found.")
s = s.replace(needle, repl, 1)

needle = """static unsigned char recallChar() {
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
"""
repl = """static unsigned char recallChar() {
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

static void pushBackPlaybackChar(unsigned char c) {
    if (obrienPlaybackPushedChar >= 0) {
        return;
    }
    obrienPlaybackPushedChar = c;
    if (recordingLocation > 0) {
        recordingLocation--;
    }
}
"""
if needle not in s:
    raise SystemExit("Cannot patch: recallChar block not found.")
s = s.replace(needle, repl, 1)

needle = """            case RNG_CHECK:
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;
"""
repl = """            case RNG_CHECK:
                (void) recallChar();
                tryAgain = true;
                if (!obrienPlaybackSalvageWarned) {
                    printf("O'Brien long-save salvage: skipped a legacy RNG checkpoint at location %li.\\n",
                           recordingLocation - 2);
                    obrienPlaybackSalvageWarned = true;
                }
                break;
            case END_OF_RECORDING:
            case EVENT_ERROR:
            default:
                message("Unrecognized event type in playback.", REQUIRE_ACKNOWLEDGMENT);
                printf("Unrecognized event type in playback: event ID %i", c);
                tryAgain = true;
                playbackPanic();
                break;
"""
if needle not in s:
    raise SystemExit("Cannot patch: recallEvent RNG_CHECK block not found.")
s = s.replace(needle, repl, 1)

needle = """void OOSCheck(unsigned long x, short numberOfBytes) {
    unsigned char eventType;
    unsigned long recordedNumber;

    if (rogue.playbackMode) {
        eventType = recallChar();
        recordedNumber = recallNumber(numberOfBytes);
        if (eventType != RNG_CHECK || recordedNumber != x) {
            if (eventType != RNG_CHECK) {
                printf("Event type mismatch in RNG check.\\n");
                playbackPanic();
            } else if (recordedNumber != x) {
                printf("Expected RNG output of %li; got %i.\\n", recordedNumber, (int) x);
                playbackPanic();
            }
        }
    } else {
        recordChar(RNG_CHECK);
        recordNumber(x, numberOfBytes);
        considerFlushingBufferToFile();
    }
}
"""
repl = """void OOSCheck(unsigned long x, short numberOfBytes) {
    unsigned char eventType;
    unsigned long recordedNumber;

    if (rogue.playbackMode) {
        eventType = recallChar();

        if (eventType != RNG_CHECK) {
            pushBackPlaybackChar(eventType);
            if (!obrienPlaybackSalvageWarned) {
                printf("O'Brien long-save salvage: current build expected an RNG checkpoint that is absent in the old save.\\n");
                obrienPlaybackSalvageWarned = true;
            }
            return;
        }

        recordedNumber = recallNumber(numberOfBytes);
        if (recordedNumber != x) {
            if (!obrienPlaybackSalvageWarned) {
                printf("O'Brien long-save salvage: ignoring legacy RNG audit mismatch (recorded %li, current %i).\\n",
                       recordedNumber, (int) x);
                obrienPlaybackSalvageWarned = true;
            }
        }
    } else {
        recordChar(RNG_CHECK);
        recordNumber(x, numberOfBytes);
        considerFlushingBufferToFile();
    }
}
"""
if needle not in s:
    raise SystemExit("Cannot patch: OOSCheck block not found.")
s = s.replace(needle, repl, 1)

needle = """    locationInRecordingBuffer   = 0;
    positionInPlaybackFile      = 0;
    recordingLocation           = 0;
    maxLevelChanges             = 0;
"""
repl = """    locationInRecordingBuffer   = 0;
    positionInPlaybackFile      = 0;
    recordingLocation           = 0;
    obrienPlaybackPushedChar    = -1;
    obrienPlaybackSalvageWarned = false;
    maxLevelChanges             = 0;
"""
if needle not in s:
    raise SystemExit("Cannot patch: initRecording reset block not found.")
s = s.replace(needle, repl, 1)

path.write_text(s, encoding="utf-8")
print("Patched:", path)
PY

cd "$ROOT"
echo "Rebuilding Brogue..."
make -B -j3 bin/brogue

echo
echo "SUCCESS: salvage-compatible binary built."
echo "Run it from bin so assets resolve:"
echo "  cd \"$ROOT/bin\""
echo "  ./brogue"
echo
echo "Then load the long .broguesave."
