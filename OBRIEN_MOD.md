# O'Brien Must Survive v0.2.24

This repository includes a chained updater for **Brogue CE 1.15.1**. Apply the newest updater to a clean source tree; it runs all earlier O'Brien patches in order.

## v0.2.24 design

- **O'Brien Must Survive is a fourth Variant**, alongside Brogue, Rapid Brogue and Bullet Brogue.
- **Normal / Easy / Wizard remain Modes** and are independent of the selected Variant.
- O'Brien keeps normal Brogue fragility: the mod improves equipment, information, mobility, logistics and away-team support rather than turning him into a tank.
- Full tricorder analysis identifies item type, enchantment, runic state and curse state in the O'Brien variant.
- **v0.2.23** fixed cramped stairhead resupply loss while preserving the protected 3x3 stairhead lane.
- **v0.2.24** adds a real O'Brien-variant command/spell, `Call Security`, plus emergency medical transport for Bashir.

## Call Security spell

Press **`C`** in O'Brien Must Survive, or choose **Call Security spell** from the action menu.

`Call Security` is an intrinsic away-team ability, not an inventory charm or staff, so it consumes no backpack slot. It consumes one player turn when a new security hologram is successfully deployed. Only **one** Holographic Security Officer can be active at a time; attempting to call another while one is already active does not consume a turn.

The deployed **Holographic Security Officer (HSO)** is designed as a mobile rear-guard/bodyguard rather than a replacement player character:

- permanent **Flying** / levitation behavior;
- **180 Integrity (HP)** and defense 80;
- very fast autonomous self-repair: roughly **1 Integrity per 2 turns** while able to regenerate;
- strong close-protection sword profile: **8-14 melee damage**, high accuracy;
- **Lightning emitter: 20/20** finite tactical charges;
- **Poison emitter: 20/20** finite tactical charges;
- both emitter magazines recharge at **1 charge per 35 turns**, a Wisdom-equivalent fast recharge layer;
- the two emitter systems are treated as enchanted/+3-equivalent tactical staffs, but they are internal holographic systems rather than lootable pack items;
- **100% bolt reflection** (`MA_REFLECT_100`) provides the anti-magic protection layer without making the HSO physically invulnerable;
- fire, webs and deep-water penalties are ignored, and the inanimate hologram does not depend on biological breathing/food/medical support;
- the HSO is permanent Starfleet crew: friendly fire cannot trigger `unAlly()` defection.

The HSO uses normal Brogue ally AI after deployment. That is intentional: while enemies are present it can intercept, fight and absorb damage; when the fight ends it resumes following O'Brien instead of remaining behind as a disposable stationary summon. In practice this gives the intended **rear guard -> win/escape -> regroup** behavior.

If the hologram is destroyed, it is simply a lost projection, not a dead Starfleet officer; a later `Call Security` can deploy a fresh HSO.

## Bashir: emergency medical beam-out and return

Bashir remains a finite-HP medic and can still be hurt by Lightning, fire and other friendly-fire effects. Friendly fire never makes him defect.

Beginning in v0.2.24, Bashir also has an emergency medical transport rule:

- at **25% HP or below**, his next monster-state update triggers emergency beam-out;
- if a single hit would kill him before that threshold logic runs, the lethal death is intercepted and converted into the same medical beam-out;
- the beam-out is an administrative disappearance, so it does not leave a corpse or normal death/drop effects;
- after **120 turns** of recovery, Bashir rematerializes beside the away team using the same canonical Bashir constructor as the initial mission spawn.

This means an accidental O'Brien Lightning hit can still be tactically disastrous -- the team may lose its medic for 120 turns -- but it no longer permanently deletes Bashir from the mission.

## Mission-ready starting pack

O'Brien begins with the fixed Starfleet mission kit **already in his backpack**:

- Fire staff: `20/20` storage, native Brogue `+3` effect/recharge level
- Lightning staff: `20/20` storage, native Brogue `+3` effect/recharge level
- Poison staff: `20/20` storage, native Brogue `+3` effect/recharge level
- Blinking staff: `10/10`, capped at 20 spaces in this variant
- Tunneling staff: `3/3`
- Three separate **Starfleet Emergency Power Cells**, each `20/20`
- One native **Recharging charm +3**, initially ready
- Ring of Regeneration: `+3`, automatically equipped
- Ring of Wisdom: `+3`, automatically equipped

The two mission rings occupy Brogue's normal two ring slots from turn zero. They are not permanently locked: the player can later replace them using normal Brogue equipment rules.

## 20-shot capacity is not +20 enchantment

The three primary combat staffs use two independent values:

- **Starfleet battery capacity: 20 shots**
- **Native Brogue staff enchantment: +3**

Fire, Lightning and Poison therefore retain `20/20` mission storage without accidentally behaving like +20 staffs. Damage/effect magnitude and natural recharge timing use Brogue's ordinary +3 formulas.

The Ring of Wisdom still accelerates natural staff recharge through Brogue's normal `ringWisdomMultiplier()` path. Capacity does not amplify Wisdom. Enchanting a marked mission staff can improve its native effect/recharge enchantment without reducing its separate 20-shot battery.

Bashir's poison staff uses the same 20-capacity / +3 model.

## Native Recharging charm

O'Brien carries a real Brogue **Recharging charm +3**. It uses Brogue's native Recharging-charm mechanics: applying it instantly recharges staffs, then the charm itself enters its normal slow cooldown. At +3 the native curve is about 1664 turns, subject to the game's integer timing.

In O'Brien Must Survive, activating the native Recharging charm also refills the three marked Starfleet Emergency Power Cells to `20/20`. Naturally found Recharging charms work normally and gain the same O'Brien-only full-system extension. Naturally found Scrolls of Recharging remain ordinary one-use scrolls and also refill marked Power Cells.

For the three marked primary combat staffs, Recharging fills the independent battery to `20/20`; it does not reinterpret capacity as enchantment.

## Starfleet Emergency Power Cells

The three Power Cells are finite high-discharge emergency batteries. Each stores **20 charge-units**. Applying a Cell lets O'Brien choose one staff and immediately transfer only the energy required, up to the Cell's remaining reserve and the target staff's capacity.

Power Cells passively recover only **1 charge-unit per 100 turns**, so a completely empty Cell needs about 2000 turns to recover to `20/20`. This trickle charge is based only on elapsed player time: **Wisdom does not accelerate it, and Reaping does not feed it**.

The energy model is therefore layered:

- O'Brien Fire / Lightning / Poison: native +3 staffs with separate 20-shot batteries.
- Bashir Poison: same finite mission-staff model.
- HSO Lightning / Poison: internal 20-shot tactical emitter magazines with fast 35-turn recharge.
- Other staffs: ordinary Brogue capacity/enchantment behavior unless explicitly defined otherwise.
- Power Cells: immediate finite 20-unit reserves with very slow trickle recovery.
- Recharging charm: slow-cycling full-system emergency reset.
- Scrolls of Recharging: rare one-use external resets from normal dungeon generation.

## Stairhead logistics

Auxiliary supplies materialize near designated stairwells as physical floor items, so normal Brogue inventory choices still matter. The full 3x3 area centered on the stair anchor remains an item-free exit zone.

In v0.2.12, the mod asked Brogue for a nearby item square and only afterward rejected squares inside the protected 3x3 lane. On cramped layouts the helper could repeatedly return those same nearest forbidden squares until the retry budget expired, causing individual supplies to be silently deleted. **v0.2.23 fixes this by temporarily marking the 3x3 lane as occupied during the location query and restoring every map flag immediately afterward.** Brogue therefore searches outward naturally for the cache instead of repeatedly returning a forbidden square.

**Periodic resupply occurs every 3 depths:** 3, 6, 9, 12, and so on. A cache is generated only on the first visit to that depth, so returning to a previously visited supply floor cannot duplicate it.

Each periodic cache contains:

- 3 x **Health charm +2**, serving as field first-aid units
- 1 x **ally-support staff +3**, alternating Protection and Haste between caches
- 1 x **Potion of Life** for O'Brien's emergency reserve
- 1 x ration
- 1 x fruit
- 1 x Potion of Levitation
- 2 x poison-gas potions
- 2 x paralysis-gas potions
- 2 x confusion-gas potions

The gas allocation remains finite battlefield-control support; no incineration potion is supplied because the Fire staff remains the ignition source. Fire Immunity and Invisibility are not fixed DS9-cache supplies, and Haste is no longer supplied as a fixed self-buff potion. Those items can still appear through normal Brogue generation.

The initial stairhead cache keeps optional survival supplies but does not duplicate Tunneling, the primary mission staffs, Power Cells, or the two mission rings. Full packs refuse additional pickups normally; carried items are never auto-dropped. Remaining capacity display is clamped at zero rather than becoming negative. Deep water does not eject O'Brien's carried items; other variants retain normal Brogue current behavior.

Normal dungeon weapons, armor, staffs, wands, charms, rings and other loot remain usable. O'Brien is an engineer, not a weapon-restricted class.

## Apply

Start from a clean checkout and run:

```bash
cd ~/Desktop/BrogueCE-O-Brien-src
git fetch origin
git reset --hard origin/master
python3 apply_obrien_mod_v0_2_24.py
make -B
./brogue
```

Use the repository's `./brogue` launcher rather than running `./bin/brogue` from the repository root. The launcher changes into `bin/` first so the game can find `bin/assets/tiles.png` correctly.

No special `CPPFLAGS` are required.

Then select:

`Play -> Change Variant -> O'Brien Must Survive`

Normal, Easy or Wizard mode can still be selected independently.

## Command line

For command-line variant selection, run from the repository root through the launcher:

```bash
./brogue --variant obrien_must_survive
```

or:

```bash
./brogue --variant obrien
```
