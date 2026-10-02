#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.34.

v0.2.34 replaces the bare per-level magic-map call with an automatic,
transient Scroll of Magic Mapping effect. The scroll is created as a real item
object, auto-read by the game, and immediately destroyed without entering the
pack, consuming a player turn, consuming substantive RNG, or recording a fake
player input.

Replay behavior is boundary-aware:
- ruleset 33+ recordings reproduce automatic mapping during strict replay;
- pre-v0.2.33 historical replay remains unchanged until a SAVED_GAME_LOADED
  boundary is encountered;
- when an old O'Brien save returns to live play, the current level is mapped
  immediately, and the SAVED_GAME_LOADED boundary makes that state reproducible
  if the continued game is saved and loaded again.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_33.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_33.py next to this updater.")


def source_has_v033_or_later():
    main = ROOT / "src/brogue/RogueMain.c"
    rec = ROOT / "src/brogue/Recordings.c"
    if not main.exists() or not rec.exists():
        return False
    mt = main.read_text(encoding="utf-8")
    rt = rec.read_text(encoding="utf-8")
    return (
        "OBRIEN_RULESET_V033" in rt
        and (
            "O'Brien Must Survive v0.2.33" in mt
            or "O'Brien Must Survive v0.2.34" in mt
        )
    )


if source_has_v033_or_later():
    print("Detected O'Brien v0.2.33+ already applied; skipping historical patch replay.")
else:
    runpy.run_path(str(PREVIOUS_PATCH), run_name="__main__")


def replace_once(rel, old, new, marker=None):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker and marker in text:
        print(f"already patched {rel}")
        return
    if old not in text:
        raise SystemExit(f"Cannot patch {rel}: expected v0.2.33-compatible source was not found.")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel}")


def insert_once_before(rel, anchor, insertion, marker):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print(f"already patched {rel}")
        return
    if anchor not in text:
        raise SystemExit(f"Cannot patch {rel}: insertion anchor was not found.")
    path.write_text(text.replace(anchor, insertion + anchor, 1), encoding="utf-8")
    print(f"patched {rel}")


def insert_after_function_end(rel, signature, insertion, marker):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print(f"already patched {rel}")
        return

    start = text.find(signature)
    if start < 0:
        raise SystemExit(f"Cannot patch {rel}: function {signature!r} was not found.")
    brace = text.find("{", start)
    if brace < 0:
        raise SystemExit(f"Cannot patch {rel}: opening brace for {signature!r} was not found.")

    depth = 0
    i = brace
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                text = text[:i + 1] + insertion + text[i + 1:]
                path.write_text(text, encoding="utf-8")
                print(f"patched {rel}")
                return
        i += 1
    raise SystemExit(f"Cannot patch {rel}: closing brace for {signature!r} was not found.")


# ---------------------------------------------------------------------------
# Native scroll effect + transient automatic scroll.
# ---------------------------------------------------------------------------

AUTOMAP_SCROLL_HELPER = r'''
static void applyMagicMappingScrollEffect(item *theScroll, boolean automatic, boolean showEffect) {
#ifdef BROGUE_AUTOMAP_TEST
    unsigned long automapTurnBefore = rogue.playerTurnNumber;
    unsigned long automapAbsoluteTurnBefore = rogue.absoluteTurnNumber;
    long automapVisibleBefore = 0;
    long automapItemsBefore = 0;
    long automapDetectedItemsBefore = 0;
    long automapMonstersBefore = 0;
    short testX, testY;

    for (testX = 0; testX < DCOLS; testX++) {
        for (testY = 0; testY < DROWS; testY++) {
            if (pmap[testX][testY].flags & ANY_KIND_OF_VISIBLE) automapVisibleBefore++;
            if (pmap[testX][testY].flags & HAS_ITEM) automapItemsBefore++;
            if (pmap[testX][testY].flags & ITEM_DETECTED) automapDetectedItemsBefore++;
            if (pmap[testX][testY].flags & (HAS_MONSTER | HAS_DORMANT_MONSTER)) automapMonstersBefore++;
        }
    }
#endif

    if (!theScroll
        || theScroll->category != SCROLL
        || theScroll->kind != SCROLL_MAGIC_MAPPING) {

        return;
    }

    if (showEffect) {
        confirmMessages();
        messageWithColor(automatic
                             ? "Starfleet automatically applies a scroll of magic mapping."
                             : "this scroll has a map on it!",
                         &itemMessageColor, 0);
    }

    magicMapCurrentLevel();

    if (showEffect) {
        colorFlash(&magicMapFlashColor, 0, MAGIC_MAPPED, 15,
                   DCOLS + DROWS, player.loc.x, player.loc.y);
    }

#ifdef BROGUE_AUTOMAP_TEST
    {
        long automapVisibleAfter = 0;
        long automapItemsAfter = 0;
        long automapDetectedItemsAfter = 0;
        long automapMonstersAfter = 0;

        for (testX = 0; testX < DCOLS; testX++) {
            for (testY = 0; testY < DROWS; testY++) {
                if (pmap[testX][testY].flags & ANY_KIND_OF_VISIBLE) automapVisibleAfter++;
                if (pmap[testX][testY].flags & HAS_ITEM) automapItemsAfter++;
                if (pmap[testX][testY].flags & ITEM_DETECTED) automapDetectedItemsAfter++;
                if (pmap[testX][testY].flags & (HAS_MONSTER | HAS_DORMANT_MONSTER)) automapMonstersAfter++;

                if (pmap[testX][testY].layers[DUNGEON] != GRANITE
                    && !(pmap[testX][testY].flags & (DISCOVERED | MAGIC_MAPPED))) {

                    fprintf(stderr,
                            "AUTOMAP TEST FAILURE: depth %d cell %d,%d not mapped\n",
                            rogue.depthLevel, testX, testY);
                    exit(86);
                }
            }
        }

        if (automapVisibleBefore != automapVisibleAfter
            || automapItemsBefore != automapItemsAfter
            || automapDetectedItemsBefore != automapDetectedItemsAfter
            || automapMonstersBefore != automapMonstersAfter) {

            fprintf(stderr,
                    "AUTOMAP TEST FAILURE: visibility/entity state changed on depth %d\n",
                    rogue.depthLevel);
            exit(87);
        }

        if (automapTurnBefore != rogue.playerTurnNumber
            || automapAbsoluteTurnBefore != rogue.absoluteTurnNumber) {

            fprintf(stderr,
                    "AUTOMAP TEST FAILURE: automatic mapping consumed a turn\n");
            exit(88);
        }
    }
#endif
}

void obrienAutoApplyMagicMappingScroll(boolean showEffect) {
#ifdef BROGUE_AUTOMAP_TEST
    unsigned long constructionRngBefore = randomNumbersGenerated;
#endif
    item *mappingScroll = initializeItem();

    // Construct a real Mapping scroll without makeItemInto()/generateItem().
    // Those helpers make a category-selection RNG call even when the category
    // is fixed. The transient object itself must be RNG-neutral; the native
    // Magic Mapping effect may legitimately consume substantive RNG while
    // discovering secret terrain, exactly as a manually read scroll does.
#ifdef BROGUE_AUTOMAP_TEST
    if (constructionRngBefore != randomNumbersGenerated) {
        fprintf(stderr, "AUTOMAP TEST FAILURE: transient scroll construction consumed RNG\\n");
        exit(89);
    }
#endif
    mappingScroll->category = SCROLL;
    mappingScroll->kind = SCROLL_MAGIC_MAPPING;
    mappingScroll->displayChar = G_SCROLL;
    mappingScroll->flags |= (ITEM_FLAMMABLE | ITEM_IDENTIFIED);

    applyMagicMappingScrollEffect(mappingScroll, true, showEffect);
    deleteItem(mappingScroll);
}

'''

insert_once_before(
    "src/brogue/Items.c",
    "boolean readScroll(item *theItem) {",
    AUTOMAP_SCROLL_HELPER,
    "void obrienAutoApplyMagicMappingScroll(boolean showEffect)",
)

replace_once(
    "src/brogue/Items.c",
    """        case SCROLL_MAGIC_MAPPING:
            confirmMessages();
            messageWithColor("this scroll has a map on it!", &itemMessageColor, 0);
            magicMapCurrentLevel();
            colorFlash(&magicMapFlashColor, 0, MAGIC_MAPPED, 15, DCOLS + DROWS, player.loc.x, player.loc.y);
            break;""",
    """        case SCROLL_MAGIC_MAPPING:
            applyMagicMappingScrollEffect(theScroll, false, true);
            break;""",
    "applyMagicMappingScrollEffect(theScroll, false, true);",
)

replace_once(
    "src/brogue/Rogue.h",
    """    void magicMapCurrentLevel(void);
    boolean readScroll(item *theItem);""",
    """    void magicMapCurrentLevel(void);
    void obrienAutoApplyMagicMappingScroll(boolean showEffect);
    boolean readScroll(item *theItem);""",
    "void obrienAutoApplyMagicMappingScroll(boolean showEffect);",
)


# ---------------------------------------------------------------------------
# Replay/live boundary state.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Recordings.c",
    """static unsigned char obrienCompatibilityFlags = 0;
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V033;""",
    """static unsigned char obrienCompatibilityFlags = 0;
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V033;
static boolean obrienAutoMapContinuation = false;""",
    "static boolean obrienAutoMapContinuation = false;",
)

insert_after_function_end(
    "src/brogue/Recordings.c",
    "boolean obrienRulesetAtLeast(short version)",
    r'''

boolean obrienAutomaticMappingEnabled(void) {
    return gameVariant == VARIANT_OBRIEN_MUST_SURVIVE
        && (obrienRulesetAtLeast(33)
            || obrienAutoMapContinuation
            || !rogue.playbackMode);
}
''',
    "boolean obrienAutomaticMappingEnabled(void)",
)

replace_once(
    "src/brogue/Rogue.h",
    """    boolean obrienRulesetAtLeast(short version);
    boolean obrienBashirRecoveryUsesDelayedBoundary(void);""",
    """    boolean obrienRulesetAtLeast(short version);
    boolean obrienAutomaticMappingEnabled(void);
    boolean obrienBashirRecoveryUsesDelayedBoundary(void);""",
    "boolean obrienAutomaticMappingEnabled(void);",
)

replace_once(
    "src/brogue/Recordings.c",
    """    rogue.patchVersion          = 0;

    if (rogue.playbackMode) {""",
    """    rogue.patchVersion          = 0;
    // v0.2.34: reset replay/live mapping boundary for each recording session.
    obrienAutoMapContinuation = false;

    if (rogue.playbackMode) {""",
    "v0.2.34: reset replay/live mapping boundary for each recording session.",
)

replace_once(
    "src/brogue/Recordings.c",
    """            case SAVED_GAME_LOADED:
                tryAgain = true;
                flashTemporaryAlert(" Saved game loaded ", 1000);
                break;""",
    """            case SAVED_GAME_LOADED:
                tryAgain = true;
                if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
                    // This marks the historical point at which an old save was
                    // resumed under v0.2.34 live rules. Recreate the current-level
                    // map silently during replay, then map future level entries.
                    obrienAutoMapContinuation = true;
                    obrienAutoApplyMagicMappingScroll(false);
                }
                flashTemporaryAlert(" Saved game loaded ", 1000);
                break;""",
    "This marks the historical point at which an old save was",
)

replace_once(
    "src/brogue/Recordings.c",
    """    blackOutScreen();
    refreshSideBar(-1, -1, false);
    updateMessageDisplay();
    displayLevel();
}""",
    """    blackOutScreen();
    refreshSideBar(-1, -1, false);
    updateMessageDisplay();
    displayLevel();

    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE) {
        // Strict historical replay has finished. From this exact boundary onward
        // O'Brien receives the automatic Mapping scroll behavior, including old
        // saves whose original ruleset predates v0.2.33.
        obrienAutoMapContinuation = true;
        obrienAutoApplyMagicMappingScroll(hasGraphics);
        displayLevel();
    }
}""",
    "Strict historical replay has finished. From this exact boundary onward",
)


# ---------------------------------------------------------------------------
# Move automapping to the actual final display path.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/RogueMain.c",
    """    // v0.2.33: new O'Brien missions receive a complete terrain map on
    // every entered depth. This is ruleset-gated so historical recordings keep
    // their original map/discovery state and strict RNG checkpoints.
    if (gameVariant == VARIANT_OBRIEN_MUST_SURVIVE && obrienRulesetAtLeast(33)) {
        magicMapCurrentLevel();
    }

""",
    "",
    "v0.2.34 mapping occurs after the first level display",
)

replace_once(
    "src/brogue/RogueMain.c",
    """    rogue.playbackBetweenTurns = true;
    displayLevel();
    refreshSideBar(-1, -1, false);""",
    """    rogue.playbackBetweenTurns = true;
    displayLevel();

    // v0.2.34 mapping occurs after the first level display. In live SDL play
    // this produces the same visible flash as a real Mapping scroll and then
    // redraws the final mapped level. During strict replay the effect is silent.
    if (obrienAutomaticMappingEnabled()) {
        obrienAutoApplyMagicMappingScroll(hasGraphics && !rogue.playbackMode);
        displayLevel();
    }

    refreshSideBar(-1, -1, false);""",
    "v0.2.34 mapping occurs after the first level display",
)

replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.33",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.34",
    "O'Brien Must Survive v0.2.34",
)

print("O'Brien Must Survive v0.2.34 applied.")
print("- automatic mapping now uses a transient real Scroll of Magic Mapping object")
print("- the transient scroll object consumes no player turn, fake input event, pack slot, or extra RNG")
print("- native Magic Mapping RNG consumption is preserved and replayed at save/load boundaries")
print("- the scroll effect runs on the final level display path and redraws the mapped level")
print("- old O'Brien saves gain mapping when replay finishes and live play resumes")
print("- SAVED_GAME_LOADED boundaries reproduce that transition on later replay")
print("- ruleset 33+ recordings retain automatic mapping during strict replay")
print("Build with: make -B -j3 bin/brogue")
