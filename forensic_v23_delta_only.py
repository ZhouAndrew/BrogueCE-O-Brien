#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
p = ROOT / 'src/brogue/RogueMain.c'
s = p.read_text(encoding='utf-8')

old = '''    // v0.2.12 clear stairhead lane: never place DS9 cache items on the stair
    // or any of its eight neighboring squares. The player must always have an
    // equipment-free first step out of the stairhead area.
    for (short attempt = 0; attempt < 64; attempt++) {
        getQualifyingLocNear(&loc, anchor, true, 0,
                             (T_OBSTRUCTS_ITEMS | T_OBSTRUCTS_PASSABILITY),
                             (HAS_ITEM | HAS_MONSTER | HAS_PLAYER | HAS_STAIRS | IS_IN_MACHINE),
                             false, false);

        if (coordinatesAreInMap(loc.x, loc.y)
            && (abs(loc.x - anchor.x) > 1 || abs(loc.y - anchor.y) > 1)) {
            break;
        }
        loc = INVALID_POS;
    }

    if (!coordinatesAreInMap(loc.x, loc.y)) {
        deleteItem(supply);
        return;
    }

    placeItemAt(supply, loc);'''
new = '''    // v0.2.23 reliable clear stairhead lane: temporarily reserve the stair
    // and all eight neighboring squares *before* asking Brogue for a location.
    unsigned long savedStairheadFlags[3][3] = {{0}};
    boolean savedStairheadValid[3][3] = {{false}};

    for (short dx = -1; dx <= 1; dx++) {
        for (short dy = -1; dy <= 1; dy++) {
            pos reserved = { anchor.x + dx, anchor.y + dy };
            if (coordinatesAreInMap(reserved.x, reserved.y)) {
                savedStairheadValid[dx + 1][dy + 1] = true;
                savedStairheadFlags[dx + 1][dy + 1] = pmapAt(reserved)->flags;
                pmapAt(reserved)->flags |= HAS_ITEM;
            }
        }
    }

    getQualifyingLocNear(&loc, anchor, true, 0,
                         (T_OBSTRUCTS_ITEMS | T_OBSTRUCTS_PASSABILITY),
                         (HAS_ITEM | HAS_MONSTER | HAS_PLAYER | HAS_STAIRS | IS_IN_MACHINE),
                         false, false);

    for (short dx = -1; dx <= 1; dx++) {
        for (short dy = -1; dy <= 1; dy++) {
            if (savedStairheadValid[dx + 1][dy + 1]) {
                pos reserved = { anchor.x + dx, anchor.y + dy };
                pmapAt(reserved)->flags = savedStairheadFlags[dx + 1][dy + 1];
            }
        }
    }

    if (!coordinatesAreInMap(loc.x, loc.y)) {
        deleteItem(supply);
        return;
    }

    placeItemAt(supply, loc);'''
if old not in s and 'v0.2.23 reliable clear stairhead lane' not in s:
    raise SystemExit('v0.23 placement delta anchor missing')
if old in s:
    s = s.replace(old, new, 1)

s = s.replace("Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.22",
              "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.23", 1)
p.write_text(s, encoding='utf-8')
print('v0.23 delta-only applied')
