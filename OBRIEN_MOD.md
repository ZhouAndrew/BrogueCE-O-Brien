# O'Brien Must Survive v0.2.23

This repository includes a chained updater for **Brogue CE 1.15.1**. Apply the newest updater to a clean source tree; it runs all earlier O'Brien patches in order.

## v0.2.23 design

- **O'Brien Must Survive is a fourth Variant**, alongside Brogue, Rapid Brogue and Bullet Brogue.
- **Normal / Easy / Wizard remain Modes** and are independent of the selected Variant.
- O'Brien keeps normal Brogue fragility: the mod improves equipment, information, mobility and logistics rather than turning him into a tank.
- Full tricorder analysis identifies item type, enchantment, runic state and curse state in the O'Brien variant.
- Bashir is a finite-HP defensive medic, follows O'Brien, has permanent flight/levitation, and carries a finite 20-shot poison staff. He has no innate poison bolt, shield or haste ability.
- **Bashir is permanent Starfleet crew.** Friendly fire can still injure him, but it never causes `unAlly()` defection. v0.2.22 also repairs older saves where friendly fire already stripped his ally/follower identity.
- **v0.2.23 fixes cramped stairhead resupply loss.** The protected 3x3 stairhead lane is temporarily reserved before Brogue searches for each cache-item location, so the placement helper searches outward instead of repeatedly proposing forbidden near-stair squares and silently deleting supplies.

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

- Fire / Lightning / Poison: native +3 staffs with separate 20-shot batteries.
- Other staffs: ordinary Brogue capacity/enchantment behavior unless explicitly defined otherwise.
- Power Cells: immediate finite 20-unit reserves with very slow trickle recovery.
- Recharging charm: slow-cycling full-system emergency reset.
- Scrolls of Recharging: rare one-use external resets from normal dungeon generation.

## Bashir: permanent crew

Bashir remains vulnerable. Lightning, fire and other friendly-fire effects may still damage him normally. v0.2.22 changes only the loyalty transition: an accidental hit is not treated as a decision to leave Starfleet.

Vanilla Brogue allies retain their normal behavior. Only Doctor Bashir in the O'Brien variant is protected from the normal `unAlly()` transition. Older saves in which Bashir has already become tracking/fleeing because of this bug are repaired when his monster state updates.

## Stairhead logistics

Auxiliary supplies materialize near designated stairwells as physical floor items, so normal Brogue inventory choices still matter. The full 3x3 area centered on the stair anchor remains an item-free exit zone.

In v0.2.12, the mod asked Brogue for a nearby item square and only afterward rejected squares inside the protected 3x3 lane. On cramped layouts the helper could repeatedly return those same nearest forbidden squares until the retry budget expired, causing individual supplies to be silently deleted. **v0.2.23 fixes this by temporarily marking the 3x3 lane as occupied during the location query and restoring every map flag immediately afterward.** Brogue therefore searches outward naturally for the cache instead of repeatedly returning a forbidden square.

**Periodic resupply occurs every 3 depths:** 3, 6, 9, 12, and so on. A cache is generated only on the first visit to that depth, so returning to a previously visited supply floor cannot duplicate it.

Each periodic cache contains:

- 3 × **Health charm +2**, serving as field first-aid units
- 1 × **ally-support staff +3**, alternating Protection and Haste between caches
- 1 × **Potion of Life** for O'Brien's emergency reserve
- 1 × ration
- 1 × fruit
- 1 × Potion of Levitation
- 2 × poison-gas potions
- 2 × paralysis-gas potions
- 2 × confusion-gas potions

The gas allocation remains finite battlefield-control support; no incineration potion is supplied because the Fire staff remains the ignition source. Fire Immunity and Invisibility are not fixed DS9-cache supplies, and Haste is no longer supplied as a fixed self-buff potion. Those items can still appear through normal Brogue generation.

The initial stairhead cache keeps optional survival supplies but does not duplicate Tunneling, the primary mission staffs, Power Cells, or the two mission rings. Full packs refuse additional pickups normally; carried items are never auto-dropped. Remaining capacity display is clamped at zero rather than becoming negative. Deep water does not eject O'Brien's carried items; other variants retain normal Brogue current behavior.

Normal dungeon weapons, armor, staffs, wands, charms, rings and other loot remain usable. O'Brien is an engineer, not a weapon-restricted class.

## Apply

Start from a clean checkout and run:

```bash
cd ~/Desktop/BrogueCE-O-Brien-src
git fetch origin
git reset --hard origin/master
python3 apply_obrien_mod_v0_2_23.py
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
