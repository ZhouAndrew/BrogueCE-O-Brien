#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.35.

v0.2.35 changes the periodic Starfleet tactical resupply for new missions:
the allocation that historically began as caustic/poison gas is now restored as
its own slot and issued as Potion of Incineration instead of being folded into
the paralysis-gas magazine.

New ruleset 35 periodic tactical payload:
- 2 x Potion of Incineration
- 2-shot paralysis-gas magazine
- 2 x Potion of Confusion

Historical rulesets are preserved exactly:
- rulesets 30-34 keep the four-shot paralysis-gas magazine + 2 confusion;
- older rulesets retain their historical poison/paralysis/confusion layout.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
PREVIOUS_PATCH = ROOT / "apply_obrien_mod_v0_2_34.py"

if not PREVIOUS_PATCH.exists():
    raise SystemExit("Missing apply_obrien_mod_v0_2_34.py next to this updater.")


def source_has_v034_or_later():
    main = ROOT / "src/brogue/RogueMain.c"
    rec = ROOT / "src/brogue/Recordings.c"
    if not main.exists() or not rec.exists():
        return False

    mt = main.read_text(encoding="utf-8")
    rt = rec.read_text(encoding="utf-8")
    return (
        "OBRIEN_RULESET_V033" in rt
        and (
            "O'Brien Must Survive v0.2.34" in mt
            or "O'Brien Must Survive v0.2.35" in mt
        )
    )


if source_has_v034_or_later():
    print("Detected O'Brien v0.2.34+ already applied; skipping historical patch replay.")
else:
    runpy.run_path(str(PREVIOUS_PATCH), run_name="__main__")


def replace_once(rel, old, new, marker=None):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")

    if marker and marker in text:
        print(f"already patched {rel}")
        return

    if old not in text:
        raise SystemExit(
            f"Cannot patch {rel}: expected v0.2.34-compatible source was not found."
        )

    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel}")


# ---------------------------------------------------------------------------
# Ruleset generation 35.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/Recordings.c",
    """#define OBRIEN_RULESET_V030            30
#define OBRIEN_RULESET_V031            31
#define OBRIEN_RULESET_V033            33
static unsigned char obrienCompatibilityFlags = 0;
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V033;""",
    """#define OBRIEN_RULESET_V030            30
#define OBRIEN_RULESET_V031            31
#define OBRIEN_RULESET_V033            33
#define OBRIEN_RULESET_V035            35
static unsigned char obrienCompatibilityFlags = 0;
static unsigned char obrienRulesetVersion = OBRIEN_RULESET_V035;""",
    "OBRIEN_RULESET_V035",
)

replace_once(
    "src/brogue/Recordings.c",
    """        obrienCompatibilityFlags = 0;
        obrienRulesetVersion = OBRIEN_RULESET_V033;

        // If present, set the patch version for playing the game.""",
    """        obrienCompatibilityFlags = 0;
        // v0.2.35: brand-new missions start on ruleset 35.
        obrienRulesetVersion = OBRIEN_RULESET_V035;

        // If present, set the patch version for playing the game.""",
    "v0.2.35: brand-new missions start on ruleset 35.",
)


# ---------------------------------------------------------------------------
# Periodic tactical resupply.
# ---------------------------------------------------------------------------

replace_once(
    "src/brogue/RogueMain.c",
    """    if (obrienRulesetAtLeast(30)) {
        // v0.2.30: no Starfleet-issued caustic/poison gas. The former poison
        // allocation is folded into one four-shot paralysis-gas magazine.
        obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 4, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);
    } else {
        // Historical v0.2.29 layout for old save/recording replay.
        obrienPlaceSupplyItem(POTION, POTION_POISON, 2, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 2, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);
    }""",
    """    if (obrienRulesetAtLeast(35)) {
        // v0.2.35: restore the former caustic/poison allocation as its own
        // tactical payload, but issue Incineration instead of poison gas.
        // The paralysis allocation therefore returns to a two-shot magazine.
        obrienPlaceSupplyItem(POTION, POTION_INCINERATION, 2, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 2, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);
    } else if (obrienRulesetAtLeast(30)) {
        // Historical v0.2.30-v0.2.34 layout: no Starfleet-issued poison gas;
        // the former poison allocation is folded into a four-shot paralysis magazine.
        obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 4, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);
    } else {
        // Historical v0.2.29 layout for old save/recording replay.
        obrienPlaceSupplyItem(POTION, POTION_POISON, 2, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_PARALYSIS, 2, 0, anchor);
        obrienPlaceSupplyItem(POTION, POTION_CONFUSION, 2, 0, anchor);
    }""",
    "v0.2.35: restore the former caustic/poison allocation",
)


replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.34",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.35",
    "O'Brien Must Survive v0.2.35",
)

print("O'Brien Must Survive v0.2.35 applied.")
print("- new ruleset 35 periodic caches issue 2 Incineration potions")
print("- paralysis tactical resupply returns to a two-shot magazine")
print("- confusion resupply remains quantity 2")
print("- rulesets 30-34 keep their historical four-shot paralysis magazine")
print("- older recordings keep their historical poison/paralysis/confusion layout")
print("Build with: make -B -j3 bin/brogue")
