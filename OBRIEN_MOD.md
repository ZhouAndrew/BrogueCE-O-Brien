# O'Brien Must Survive v0.2.31

This repository includes a chained updater for **Brogue CE 1.15.1**. Apply the newest updater to a clean source tree; it runs all earlier O'Brien patches in order.

## v0.2.31 design

- **O'Brien Must Survive now appears under `Play -> Change Mode`** rather than under Change Variant.
- Internally it deliberately retains the historical `VARIANT_OBRIEN_MUST_SURVIVE` enum value. The v0.2.28 tagged save/recording header is unchanged, so existing tagged O'Brien saves keep the same on-disk representation; legacy untagged saves continue to use the existing migration/explicit-selection path.
- Selecting O'Brien forces normal Brogue difficulty mode; choosing Normal, Easy or Wizard while O'Brien is active returns to ordinary Brogue. Rapid and Bullet remain in Change Variant.
- O'Brien keeps normal Brogue fragility: the mod improves equipment, information, mobility, logistics and away-team support rather than turning him into a tank.
- Full tricorder analysis identifies item type, enchantment, runic state and curse state in the O'Brien mission rules.
- **v0.2.30** gives Bashir and the Security Hologram dedicated ally examine text instead of inherited hostile MK_YOU/MK_GOLEM combat previews.
- **v0.2.30** makes beneficial ally-support bolts pass through the Security Hologram normally while hostile reflectable bolts are still reflected.
- **v0.2.30** removes Starfleet-issued caustic gas, consolidates the allocation into a four-shot paralysis-gas magazine, and extends O'Brien Recharging effects to wands and charms as well as staffs.
- **v0.2.30** also gives newly started O'Brien missions one **Scroll of Magic Mapping** and one directional **Wand of Negation** as standard issue.
- **v0.2.31** stages one additional **Scroll of Magic Mapping on every first visit from depth 21 onward** (21, 22, 23, ...), rather than only on the three-depth resupply floors.
- **v0.2.31** gives Bashir a pharmaceutical fabrication cycle: while he is available, he prepares one identified **Potion of Strength every 2000 turns**. If the pack is full, delivery waits until a slot is available instead of deleting the dose or overfilling the pack.
- These two new behaviors are gated behind ruleset generation 31. v0.2.30 and older saves retain their original replay behavior and do not receive retroactive maps or Bashir-made Strength potions.
- To keep historical saves strict-replay compatible, v0.2.30 stores an O'Brien ruleset-generation tag in byte 14 of the existing 36-byte recording header. That byte was zero after the terminated CE 1.15.1 version string in older saves, so pre-v0.2.30 recordings retain their old starting kit and old v0.2.29 gameplay rules during replay; the O'Brien variant ID and all header offsets remain unchanged.
- **v0.2.25** recharge pacing for the marked Fire / Lightning / Poison staffs remains in force.

## v0.2.25 primary-staff recharge pacing

The **Ring of Wisdom is not removed or downgraded**. O'Brien still starts with the identified `+3 Ring of Wisdom`, it is automatically equipped, and it continues to accelerate staff recharge through Brogue's normal `ringWisdomMultiplier()` path.

The change is instead applied to the three marked primary combat staffs:

- Fire remains `20/20` capacity and `+3` effect strength.
- Lightning remains `20/20` capacity and `+3` effect strength.
- Poison remains `20/20` capacity and `+3` effect strength.
- Their passive base recharge duration is now **5000 ticks per charge before Wisdom**, equivalent to the ordinary +1-staff base pacing.
- Wisdom still accelerates that 5000-tick countdown normally.
- Recharging charms, Scrolls of Recharging and Emergency Power Cells still refill the separate 20-shot battery exactly as before.
- Blinking, Tunneling and ordinary dungeon staffs keep their normal Brogue recharge behavior.

This deliberately separates **effect power** from **passive battery recovery**. The primary staffs still hit and scale as +3 staffs, but +3 effect enchantment is no longer also stacked as a second recharge-speed multiplier on top of the +3 Wisdom ring.

## Security Hologram toggle

Press **`C`** in O'Brien Must Survive, or choose **Toggle Security Hologram** from the action menu.

The Security Hologram is an intrinsic away-team system, not an inventory charm or staff, so it consumes no backpack slot. `C` deploys it while offline and deactivates it while online. A manual shutdown preserves its integrity and emitter charge state for later redeployment. Only one projection can be active at a time.

The deployed **Security Hologram** is designed as a mobile rear-guard/bodyguard rather than a replacement player character:

- permanent **Flying** / levitation behavior;
- **180 Integrity (HP)** and defense 80;
- very fast autonomous self-repair: roughly **1 Integrity per 2 turns** while able to regenerate;
- strong close-protection sword profile: **8-14 melee damage**, high accuracy;
- **Lightning emitter: 20/20** finite tactical charges;
- **Poison emitter: 20/20** finite tactical charges;
- both emitter magazines recharge at **1 charge per 35 turns**, a Wisdom-equivalent fast recharge layer;
- the two emitter systems are treated as enchanted/+3-equivalent tactical staffs, but they are internal holographic systems rather than lootable pack items;
- **hostile reflectable bolts** are returned by the `MA_REFLECT_100` defense layer without making the hologram physically invulnerable;
- **beneficial ally-support bolts** (healing, haste, protection and other `BF_TARGET_ALLIES` effects) are explicitly allowed through and affect the hologram normally;
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

- Fire staff: `20/20` storage, `+3` effect strength, v0.2.25 tuned passive recharge pacing
- Lightning staff: `20/20` storage, `+3` effect strength, v0.2.25 tuned passive recharge pacing
- Poison staff: `20/20` storage, `+3` effect strength, v0.2.25 tuned passive recharge pacing
- Blinking staff: `10/10`, capped at 20 spaces in this variant
- Tunneling staff: `3/3`
- **Scroll of Magic Mapping**: one standard-issue map for newly started v0.2.30 missions
- **Wand of Negation**: one native directional anti-magic weapon, with Brogue's normal wand charge generation and v0.2.30 Recharging support
- Three separate **Starfleet Emergency Power Cells**, each `20/20`
- One native **Recharging charm +3**, initially ready
- Ring of Regeneration: `+3`, automatically equipped
- Ring of Wisdom: `+3`, automatically equipped

The two mission rings occupy Brogue's normal two ring slots from turn zero. They are not permanently locked: the player can later replace them using normal Brogue equipment rules.

## 20-shot capacity, +3 effect and recharge pacing are separate

The three primary combat staffs now use three deliberately independent concepts:

- **Starfleet battery capacity: 20 shots**
- **Native Brogue effect enchantment: +3**
- **Passive base recharge duration: 5000 ticks per charge before Wisdom**

Fire, Lightning and Poison therefore retain `20/20` mission storage and +3 effect strength without accidentally behaving like +20 staffs or passively recovering as fast as a normal +3 staff while also wearing a +3 Wisdom ring.

The Ring of Wisdom still accelerates natural staff recharge through Brogue's normal `ringWisdomMultiplier()` path. Capacity does not amplify Wisdom. Enchanting a marked mission staff can improve its native effect enchantment without shrinking its separate 20-shot battery; v0.2.25 intentionally keeps the marked primary staff's passive recharge baseline separate from that effect enchantment.

Bashir's marked poison staff uses the same 20-capacity / +3-effect / tuned-recharge model.

## Native Recharging charm

O'Brien carries a real Brogue **Recharging charm +3**. In O'Brien Must Survive, applying a Recharging charm restores every native rechargeable equipment family in the pack: **staffs, wands and charms**. The used Recharging charm then enters its normal slow cooldown. At +3 the native curve is about 1664 turns, subject to the game's integer timing.

Wands use Brogue's native recharge semantics (a Recharging effect adds charge normally); staffs refill through the existing staff-capacity path; charms are readied through the native charm path. Weapon and armor `charges` fields are deliberately not touched because Brogue uses those fields for auto-identification bookkeeping rather than ammunition.

Activating the native Recharging charm also refills the three marked Starfleet Emergency Power Cells to `20/20`. Naturally found Recharging charms gain the same O'Brien-only full-system behavior. Naturally found Scrolls of Recharging remain ordinary one-use scrolls and, in O'Brien mode, also recharge staffs, wands and charms while refilling marked Power Cells.

For the three marked primary combat staffs, Recharging fills the independent battery to `20/20`; it does not reinterpret capacity as enchantment and is unaffected by the v0.2.25 passive-recharge pacing change.

## Starfleet Emergency Power Cells

The three Power Cells are finite high-discharge emergency batteries. Each stores **20 charge-units**. Applying a Cell lets O'Brien choose one staff and immediately transfer only the energy required, up to the Cell's remaining reserve and the target staff's capacity.

Power Cells passively recover only **1 charge-unit per 100 turns**, so a completely empty Cell needs about 2000 turns to recover to `20/20`. This trickle charge is based only on elapsed player time: **Wisdom does not accelerate it, and Reaping does not feed it**.

The energy model is therefore layered:

- O'Brien Fire / Lightning / Poison: +3 effect staffs with separate 20-shot batteries and a 5000-tick passive base recharge interval before Wisdom.
- Bashir Poison: same finite marked-staff model.
- HSO Lightning / Poison: internal 20-shot tactical emitter magazines with fast 35-turn recharge.
- Other staffs: ordinary Brogue capacity/enchantment/recharge behavior unless explicitly defined otherwise.
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
- 1 x **paralysis-gas magazine with 4 canisters**
- 2 x confusion-gas potions

Starfleet fixed resupply no longer issues caustic/poison gas in newly started v0.2.30 missions. Historical pre-v0.2.30 recordings reconstruct their original poison/paralysis/confusion cache layout for replay compatibility. The paralysis canisters use a javelin-style magazine marker: the whole issued stack occupies one pack slot, throwing consumes one canister at a time, and dropping the magazine drops it as a unit. Ordinary dungeon caustic-gas items are not deleted or renumbered, so old saves that already contain them remain valid. Random dungeon generation is otherwise unchanged.

The gas allocation remains finite battlefield-control support; no incineration potion is supplied because the Fire staff remains the ignition source. Fire Immunity and Invisibility are not fixed DS9-cache supplies, and Haste is no longer supplied as a fixed self-buff potion. Those items can still appear through normal Brogue generation.

The initial stairhead cache keeps optional survival supplies but does not duplicate Tunneling, the primary mission staffs, Power Cells, or the two mission rings. Full packs refuse additional pickups normally; carried items are never auto-dropped. Remaining capacity display is clamped at zero rather than becoming negative. Deep water does not eject O'Brien's carried items; other variants retain normal Brogue current behavior.

Normal dungeon weapons, armor, staffs, wands, charms, rings and other loot remain usable. O'Brien is an engineer, not a weapon-restricted class.

## Apply

Start from a clean checkout and run:

```bash
cd ~/Desktop/BrogueCE-O-Brien-src
git fetch origin
git reset --hard origin/master
python3 apply_obrien_mod_v0_2_31.py
make -B
./brogue
```

Use the repository's `./brogue` launcher rather than running `./bin/brogue` from the repository root. The launcher changes into `bin/` first so the game can find `bin/assets/tiles.png` correctly.

No special `CPPFLAGS` are required.

Then select:

`Play -> Change Mode -> O'Brien Must Survive`

Normal, Easy and Wizard remain available in the same Change Mode dialog. Selecting one of them while O'Brien is active leaves the O'Brien mission rules and returns to ordinary Brogue.

## Command line

For backward compatibility, command-line selection keeps the historical variant spelling even though the title-screen UI now presents O'Brien under Change Mode:

```bash
./brogue --variant obrien_must_survive
```

or:

```bash
./brogue --variant obrien
```
