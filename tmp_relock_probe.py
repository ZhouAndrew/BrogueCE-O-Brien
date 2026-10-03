#!/usr/bin/env python3
from pathlib import Path

p = Path("src/brogue/Recordings.c")
s = p.read_text(encoding="utf-8")

old = """        if (eventType != RNG_CHECK || recordedNumber != x) {
            if (eventType != RNG_CHECK) {
                printf("Event type mismatch in RNG check.\\n");
                playbackPanic();
            } else if (recordedNumber != x) {
                printf("Expected RNG output of %li; got %i.\\n", recordedNumber, (int) x);
                playbackPanic();
            }
        }"""

new = """        if (eventType != RNG_CHECK || recordedNumber != x) {
            if (eventType != RNG_CHECK) {
                printf("Event type mismatch in RNG check.\\n");
                playbackPanic();
            } else if (recordedNumber != x) {
                if (getenv("OBRIEN_RELOCK_PROBE")) {
                    printf("RELOCK offset=%li turn=%li expected=%lu actual=%lu bytes=%i\\n",
                           recordingLocation - numberOfBytes,
                           rogue.playerTurnNumber,
                           recordedNumber, x, numberOfBytes);
                    fflush(stdout);
                } else {
                    printf("Expected RNG output of %li; got %i.\\n", recordedNumber, (int) x);
                    playbackPanic();
                }
            }
        }"""

if old not in s:
    raise SystemExit("OOSCheck anchor missing")
p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("non-panicking RNG relock probe applied")
