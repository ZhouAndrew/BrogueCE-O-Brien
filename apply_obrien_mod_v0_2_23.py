#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.23 to a clean Brogue CE 1.15.1 tree.

v0.2.23 fixes the stairhead-placement failure exposed by cramped level layouts.
The v0.2.12 implementation rejected any candidate inside the protected 3x3
stairhead lane only *after* getQualifyingLocNear() returned it. Because those
rejected squares were still considered legal by the placement helper, repeated
calls could keep selecting the same near-stair squares until the 64-attempt
budget expired, silently deleting most of a resupply cache.

The fix temporarily marks the protected 3x3 lane as occupied while the normal
Brogue placement helper searches for a supply location, then restores the map
flags exactly. This makes the helper search outward naturally instead of being
asked to rediscover the same forbidden near-stair cells. The lane remains clear,
first-visit-only resupply remains unchanged, and supplies are omitted only if
Brogue genuinely cannot find any legal placement outside the protected lane.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_22.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_22.py next to this updater.")

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
    raise SystemExit(f"Cannot patch {rel}: expected v0.2.22 source was not found.")


# v0.2.12 tried to keep the 3x3 stairhead clear by rejecting returned locations
# inside that square. The problem is that getQualifyingLocNear() had no knowledge
# of that extra rule, so it could repeatedly return the same forbidden nearest
# cells and exhaust the retry limit. Reserve those cells *before* searching so
# the normal Brogue placement algorithm is forced to look outward immediately.
replace_once(
    "src/brogue/RogueMain.c",
    """    // v0.2.12 clear stairhead lane: never place DS9 cache items on the stair
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

    placeItemAt(supply, loc);""",
    """    // v0.2.23 reliable clear stairhead lane: temporarily reserve the stair
    // and all eight neighboring squares *before* asking Brogue for a location.
    // The placement helper therefore searches outward instead of repeatedly
    // proposing a square that this mod will reject after the fact.
    unsigned long savedStairheadFlags[3][3] = {{0}};
    boolean savedStairheadValid[3][3] = {{false}};

    for (short dx = -1; dx <= 1; dx++) {
        for (short dy = -1; dy <= 1; dy++) {
            pos reserved;
            reserved.x = anchor.x + dx;
            reserved.y = anchor.y + dy;

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

    // Restore every touched cell exactly, including any genuine pre-existing
    // HAS_ITEM bit. The reservation exists only during this one location query.
    for (short dx = -1; dx <= 1; dx++) {
        for (short dy = -1; dy <= 1; dy++) {
            if (savedStairheadValid[dx + 1][dy + 1]) {
                pos reserved;
                reserved.x = anchor.x + dx;
                reserved.y = anchor.y + dy;
                pmapAt(reserved)->flags = savedStairheadFlags[dx + 1][dy + 1];
            }
        }
    }

    if (!coordinatesAreInMap(loc.x, loc.y)) {
        deleteItem(supply);
        return;
    }

    placeItemAt(supply, loc);""",
    "v0.2.23 reliable clear stairhead lane",
)

replace_once(
    "src/brogue/RogueMain.c",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.22\\n\");",
    "    printf(\"Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.23\\n\");",
    "O'Brien Must Survive v0.2.23",
)

print("O'Brien Must Survive v0.2.23 applied.")
print("- Fixed cramped stairhead caches silently losing most supplies")
print("- The protected 3x3 stairhead lane is reserved before placement search")
print("- Brogue now searches outward naturally for each cache item")
print("- Original map flags are restored exactly after each location query")
print("- Every-3-depth resupply, Bashir loyalty and all v0.2.22 contents are unchanged")
print("Build normally with: make -B")
