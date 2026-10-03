#!/usr/bin/env python3
from pathlib import Path

p = Path("src/brogue/Math.c")
s = p.read_text(encoding="utf-8")
old = """long rand_range(long lowerBound, long upperBound) {
    if (upperBound <= lowerBound) {
        return lowerBound;
    }
    if (rogue.RNG == RNG_SUBSTANTIVE) {
        randomNumbersGenerated++;
    }
    long interval = upperBound - lowerBound + 1;
    brogueAssert(interval > 1); // to verify that we didn't wrap around
    return lowerBound + range(interval, rogue.RNG);
}"""
new = """long rand_range(long lowerBound, long upperBound) {
    if (upperBound <= lowerBound) {
        return lowerBound;
    }
    if (rogue.RNG == RNG_SUBSTANTIVE) {
        randomNumbersGenerated++;
    }
    long interval = upperBound - lowerBound + 1;
    long retval;
    brogueAssert(interval > 1); // to verify that we didn't wrap around
    retval = lowerBound + range(interval, rogue.RNG);
    if (getenv("OBRIEN_RNG_DIAG")
        && rogue.RNG == RNG_SUBSTANTIVE
        && rogue.playerTurnNumber >= 2053
        && rogue.playerTurnNumber <= 2054) {
        printf("RNG_CALL player=%li absolute=%lu count=%lu bounds=%ld..%ld value=%ld\\n",
               rogue.playerTurnNumber, rogue.absoluteTurnNumber,
               randomNumbersGenerated, lowerBound, upperBound, retval);
        fflush(stdout);
    }
    return retval;
}

void obrienDebugPeekSubstantiveBytes(short count) {
    ranctx copy = RNGState[RNG_SUBSTANTIVE];
    unsigned long div = RAND_MAX_COMBO / 256;
    short i;
    for (i = 1; i <= count; i++) {
        long r;
        do {
            r = ranval(&copy) / div;
        } while (r >= 256);
        printf("RNG_PEEK offset=%d byte=%ld\\n", i, r);
    }
    fflush(stdout);
}"""
if old not in s:
    raise SystemExit("normal rand_range anchor missing")
p.write_text(s.replace(old, new, 1), encoding="utf-8")

p = Path("src/brogue/Recordings.c")
s = p.read_text(encoding="utf-8")
anchor = """// compare a random number once per player turn so we instantly know if we are out of sync during playback
void RNGCheck() {"""
replacement = """// CI-only diagnostic helper implemented in Math.c.
void obrienDebugPeekSubstantiveBytes(short count);

// compare a random number once per player turn so we instantly know if we are out of sync during playback
void RNGCheck() {"""
if anchor not in s:
    raise SystemExit("RNGCheck declaration anchor missing")
s = s.replace(anchor, replacement, 1)

old = """    randomNumber = (unsigned long) rand_range(0, 255);
    OOSCheck(randomNumber, 1);

    rogue.RNG = oldRNG;
}"""
new2 = """    randomNumber = (unsigned long) rand_range(0, 255);
    OOSCheck(randomNumber, 1);

    if (getenv("OBRIEN_RNG_DIAG") && rogue.playerTurnNumber == 2053) {
        printf("RNG_AFTER_2053 player=%li absolute=%lu count=%lu check=%lu\\n",
               rogue.playerTurnNumber, rogue.absoluteTurnNumber,
               randomNumbersGenerated, randomNumber);
        obrienDebugPeekSubstantiveBytes(96);
    }

    rogue.RNG = oldRNG;
}"""
if old not in s:
    raise SystemExit("RNGCheck body anchor missing")
p.write_text(s.replace(old, new2, 1), encoding="utf-8")
print("turn-2054 RNG diagnostic instrumentation applied")
