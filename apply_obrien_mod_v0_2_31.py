#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.31 to a Brogue CE 1.15.1 tree.

v0.2.31 extends deep-level logistics and Bashir's medical support:

- new v0.2.31 games use ruleset generation 31;
- on the first visit to every depth from 21 onward, Starfleet stages one
  Scroll of Magic Mapping near the entry stairwell;
- Bashir prepares one Potion of Strength every 2000 turns while available;
  if the pack is full, the completed dose waits until a slot is available;
- pre-v0.2.31 saves keep their historical ruleset generation, so old
  recordings do not gain either behavior retroactively.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_30.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_30.py next to this updater.")


def source_has_v030_or_later():
    main = ROOT / "src/brogue/RogueMain.c"
    recordings = ROOT / "src/brogue/Recordings.c"
    if not main.exists() or not recordings.exists():
        return False
    main_text = main.read_text(encoding="utf-8")
    rec_text = recordings.read_text(encoding="utf-8")
    return (
        "OBRIEN_RULESET_V030" in rec_text
        and (
            "O'Brien Must Survive v0.2.30" in main_text
            or "O'Brien Must Survive v0.2.31" in main_text
        )
    )


if source_has_v030_or_later():
    print("Detected O'Brien v0.2.30+ already applied; skipping historical patch replay.")
else:
    runpy.run_path(str(PREVIOUS_PATCH), run_name="__main__")


def replace_once(rel, old, new, marker=None):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker and marker in text:
        print(f"already patched {rel}")
        return
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"patched {rel}")
        return
    raise SystemExit(f"Cannot patch {rel}: expected compatible v0.2.30 source was not found.")


def insert_before_function_end(rel, signature, insertion, marker):
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
                text = text[:i] + insertion + text[i:]
                path.write_text(text, encoding="utf-8")
                print(f"patched {rel}")
                return
        i += 1

    raise SystemExit(f"Cannot patch {rel}: closing brace for {signature!r} was not found.")


# ---------------------------------------------------------------------------
# Ruleset generation 31.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Recordings.c",
    """#define OBRIEN_RULESET_V030            30
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V030;""",
    """#define OBRIEN_RULESET_V030            30
#define OBRIEN_RULESET_V031            31
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V031;""",
    "OBRIEN_RULESET_V031",
)

replace_once(
    "src/brogue/Recordings.c",
    "        obrienRulesetVersion = OBRIEN_RULESET_V030;",
    "        obrienRulesetVersion = OBRIEN_RULESET_V031;",
    "obrienRulesetVersion = OBRIEN_RULESET_V031;",
)


# ---------------------------------------------------------------------------
# Depth 21+: one Mapping scroll on every first visit.
# ---------------------------------------------------------------------------

insert_before_function_end(
    "src/brogue/RogueMain.c",
    "static void obrienFirstVisitToDepth(short depth, pos entryStairs)",
    """
    if (obrienRulesetAtLeast(31) && depth >= 21) {
        // Deep Delta-quadrant logistics: each newly reached depth gets one map
        // packet. First-visit gating is provided by the caller's level.visited flag.
        obrienPlaceSupplyItem(SCROLL, SCROLL_MAGIC_MAPPING, 1, 0, entryStairs);
        messageWithColor("Starfleet mapping data has materialized near the stairwell.",
                         &itemMessageColor, 0);
    }
""",
    "Deep Delta-quadrant logistics: each newly reached depth gets one map",
)


# ---------------------------------------------------------------------------
# Bashir fabricates a Strength potion every N turns.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Monsters.c",
    "#define OBRIEN_BASHIR_RECOVERY_TURNS 120",
    """#define OBRIEN_BASHIR_RECOVERY_TURNS 120
#define OBRIEN_BASHIR_STRENGTH_POTION_INTERVAL 2000""",
    "OBRIEN_BASHIR_STRENGTH_POTION_INTERVAL",
)

replace_once(
    "src/brogue/Monsters.c",
    "static unsigned long obrienBashirReturnTurn = 0;",
    """static unsigned long obrienBashirReturnTurn = 0;
static unsigned long obrienBashirLastStrengthPotionTurn = 0;""",
    "obrienBashirLastStrengthPotionTurn",
)

insert_before_function_end(
    "src/brogue/Monsters.c",
    "void obrienCrewMaintenance(void)",
    """
    if (obrienRulesetAtLeast(31)) {
        creature *bashir = obrienFindLivingCrew("Bashir");

        // Start the fabrication clock when Bashir first becomes available.
        if (obrienBashirLastStrengthPotionTurn == 0) {
            obrienBashirLastStrengthPotionTurn = rogue.absoluteTurnNumber;
        } else if (rogue.absoluteTurnNumber < obrienBashirLastStrengthPotionTurn) {
            // Playback rewind / restart safety.
            obrienBashirLastStrengthPotionTurn = rogue.absoluteTurnNumber;
        } else if (bashir != NULL
                   && rogue.absoluteTurnNumber
                          >= obrienBashirLastStrengthPotionTurn
                             + OBRIEN_BASHIR_STRENGTH_POTION_INTERVAL
                   && numberOfItemsInPack() < MAX_PACK_ITEMS) {

            item *prepared = generateItem(POTION, POTION_STRENGTH);
            if (prepared != NULL) {
                prepared->quantity = 1;
                prepared->flags &= ~ITEM_CURSED;
                identifyItemKind(prepared);
                identify(prepared);
                addItemToPack(prepared);
                obrienBashirLastStrengthPotionTurn = rogue.absoluteTurnNumber;
                messageWithColor("Bashir has prepared a Potion of Strength and added it to your pack.",
                                 &itemMessageColor, 0);
            }
        }
    }
""",
    "Bashir has prepared a Potion of Strength",
)

# Dedicated crew examine text should advertise the fabrication role.
replace_once(
    "src/brogue/Monsters.c",
    """                "Friendly fire can injure him but cannot make him defect. If critically wounded, "
                "emergency transport beams him out for treatment; he returns after %d turns.",""",
    """                "Friendly fire can injure him but cannot make him defect. In v0.2.31 missions he "
                "prepares one Potion of Strength every %d turns while available. If critically wounded, "
                "emergency transport beams him out for treatment; he returns after %d turns.",""",
    "prepares one Potion of Strength every %d turns",
)

replace_once(
    "src/brogue/Monsters.c",
    """                theItemName,
                OBRIEN_BASHIR_RECOVERY_TURNS);""",
    """                theItemName,
                OBRIEN_BASHIR_STRENGTH_POTION_INTERVAL,
                OBRIEN_BASHIR_RECOVERY_TURNS);""",
    "OBRIEN_BASHIR_STRENGTH_POTION_INTERVAL,",
)


# Version banner.
replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.30",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.31",
    "O'Brien Must Survive v0.2.31",
)

print("O'Brien Must Survive v0.2.31 applied.")
print("- every newly reached depth from 21 onward receives one Mapping scroll")
print("- Bashir prepares one identified Potion of Strength every 2000 turns while available")
print("- a full pack delays delivery instead of deleting or overfilling the potion")
print("- pre-v0.2.31 saves retain their historical ruleset and replay behavior")
print("Build with: make -B -j3 bin/brogue")
