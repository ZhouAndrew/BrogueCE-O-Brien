#!/usr/bin/env python3
"""Apply O'Brien Must Survive v0.2.29 to a Brogue CE 1.15.1 tree.

v0.2.29 fixes two recording-integrity bugs found while reconstructing the
historical 3727-turn O'Brien save:

1. Call Security / Toggle Security Hologram consumed a turn but did not record
   its C command. The turn's RNG_CHECK was therefore left in the recording with
   no preceding input event.
2. Emergency Power Cell use recorded "a" plus the cell letter, but omitted the
   selected target staff letter. Playback could select the cell but could not
   reproduce the transfer.

The fixes record the missing inputs at the point where the actions are committed,
before playerTurnEnded() writes the normal RNG checkpoint. Playback remains
Brogue-strict: there is no RNG scanning, checkpoint skipping, or synthetic input
inside the production engine.

The companion repair_legacy_obrien_save.py utility contains a hash-locked,
deterministic migration for the one known 3727-turn historical fixture. It only
inserts the inputs proven missing by forensic replay and updates the header file
length.
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
    monsters = ROOT / "src/brogue/Monsters.c"
    items = ROOT / "src/brogue/Items.c"
    if not all(p.exists() for p in (rec, main, monsters, items)):
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
    raise SystemExit(f"Cannot patch {rel}: expected compatible v0.2.28 source was not found.")


# Call Security is a real turn-taking action. Record C immediately before the
# turn ends, so the event stream is KEY(C), RNG_CHECK rather than a bare check.
replace_once(
    "src/brogue/Monsters.c",
    """        messageWithColor("Security Hologram offline. C will redeploy it with retained tactical state.",
                         &itemMessageColor, 0);
        playerTurnEnded();
        return true;""",
    """        messageWithColor("Security Hologram offline. C will redeploy it with retained tactical state.",
                         &itemMessageColor, 0);
        recordKeystroke(CREATE_ITEM_MONSTER_KEY, false, false); // v0.2.29 recording integrity
        playerTurnEnded();
        return true;""",
    "v0.2.29 recording integrity",
)

replace_once(
    "src/brogue/Monsters.c",
    """    messageWithColor(buf, &itemMessageColor, 0);
    playerTurnEnded();
    return true;
}""",
    """    messageWithColor(buf, &itemMessageColor, 0);
    recordKeystroke(CREATE_ITEM_MONSTER_KEY, false, false); // v0.2.29 Call Security record
    playerTurnEnded();
    return true;
}""",
    "v0.2.29 Call Security record",
)

# A Power Cell transfer has a nested inventory choice. recordApplyItemCommand()
# writes "a" + cell letter; append the chosen staff letter so playback can make
# the same nested choice before the turn's RNG checkpoint.
replace_once(
    "src/brogue/Items.c",
    """    rogue.featRecord[FEAT_PURE_WARRIOR] = false;
    recordApplyItemCommand(cell);
    return true;
}""",
    """    rogue.featRecord[FEAT_PURE_WARRIOR] = false;
    recordApplyItemCommand(cell);
    recordKeystroke(target->inventoryLetter, false, false); // v0.2.29 Power Cell target
    return true;
}""",
    "v0.2.29 Power Cell target",
)

replace_once(
    "src/brogue/RogueMain.c",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.28",
    "Supports variant (obrien_must_survive): O'Brien Must Survive v0.2.29",
    "O'Brien Must Survive v0.2.29",
)

print("O'Brien Must Survive v0.2.29 applied.")
print("- Call Security now records C before its normal turn RNG checkpoint")
print("- Emergency Power Cell transfers now record the selected target staff")
print("- production playback remains strict; no RNG relock or checkpoint skipping")
print("- exact historical 3727-turn repair is handled by repair_legacy_obrien_save.py")
print("Build with: make -B -j3 bin/brogue")
