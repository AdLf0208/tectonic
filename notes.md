# Tectonic — port notes (first slice)

Skills: superpowers/using-superpowers, brainstorming, writing-plans, test-driven-development, systematic-debugging, verification-before-completion; BeautifulRust/rust-best-practices

**Class + tier:** `content` / `data` (worldgen). Ledger row `ports/ledger.csv`:
`tectonic,Tectonic,content,data,MIT,pending,P1,,ports/tectonic`; source map
`ports/_shared/source-map/atm10-sources.csv:454`. Approach from
`horizon/docs/modpacks.md` §"Tiers" and §"Carry-over": carry the jar's data and
assets, plus the registrar declarations the pin can express; agent code only
where the registrar traits need it. No renderer, no dimension entity, no new
vanilla hook. Owner request 2026-11-24.

**Pin:** Horizon `0a875da91dbb0fdcb7ba8c42c11341aa229af51a` + horizon-mixins
`e59da9094f0c2fdda6c627fe9eff22dec6a906f0`, `api = "0.2"`, game 26.3, package
format `native-1`. Do not repin mid-wave (the new nightly `f1bb66f353cf…` adds
`levels_reset` but R11 refuses the manifest key — see `blocked(level_reset:R11)`).

**Licence: MIT (rank 0).** `META-INF/neoforge.mods.toml` says `license = "MIT"`
(verbatim), and the Modrinth project `lWDHr9jE` declares MIT. The upstream
repository `Apollounknowndev/tectonic` (shallow clone at HEAD
`34241bdb35acda67b5367d49f354c66c05e098e2`, read 2026-11-24) has **no LICENSE
file** at its default branch. Both facts are recorded; no upstream asset is
copied — the jar's `pack.png` is not carried (regenerated icon instead), and
every carried JSON byte is provenance-checked in `PROVENANCE.md`.

**Artifact:** `ports/_shared/licence-cache/tectonic.jar` — 451,757 B, SHA-256
`cf188c70e7dd94f6e3a81cef9fe99f1151f13217809f7576aaedb0c3e6547ae1` (verified
2026-11-24). The Modrinth version file is named `3.0.32-neoforge-26.3`; the
jar's own `neoforge.mods.toml` declares `version = "3.0.28"` and
`versionRange = "[1.21, 1.21.1]"` (the 1.21.1 NeoForge line). Both are recorded;
the jar's declaration is the authority for its contents.

## Jar inventory (measured with `unzip -l`, before any family was chosen)

468 entries. The mod is a **data resource pack plus a Java core**:

| Location | Files | What it is |
|---|---:|---|
| `resourcepacks/tectonic/` | 381 | the data pack this mod registers (pack.mcmeta, pack.png, data/) |
| `dev/worldgen/tectonic/**/*.class` | 71 | Java core: density-function types, mixins, config, command — analysis aid only |
| `META-INF/jarjar/` | 3 | embedded library jars (Apollib, Lithostitched integration) |
| `assets/tectonic/lang/en_us.json` | 1 | mod language file |
| root | 4 | `pack.mcmeta`, `pack.png`, `worldgen.json` (`{"good": true}`), `tectonic.mixins.json` |

### Data pack census (`resourcepacks/tectonic/data/`)

| Registry / folder | Files | Port verdict |
|---|---:|---|
| `tectonic/worldgen/density_function/` | 105 base (130 across all packs) | carried base pack (one registered type: `config_constant`; other types blocked — see Gaps) |
| `tectonic/worldgen/noise/` | 32 base (43 across all packs) | carried |
| `tectonic/worldgen/placed_feature/` | 3 | carried (1.21.1 placement modifiers retained; some are blocked) |
| `tectonic/worldgen/configured_feature/` | 2 | carried, renamed to 26.3 `worldgen/feature/` + state-shape upgrade |
| `data/minecraft/worldgen/density_function/overworld/**` | 26 | **not packed** — terrain replacement, `blocked(level_reset:R11)` |
| `data/minecraft/worldgen/noise/*.json` (2) + `noise_settings/overworld.json` (1) | 3 | **not packed** — terrain replacement, `blocked(level_reset:R11)` |
| `tectonic/tags/block/terralith_surface.json` | 1 | carried (verbatim; `values` is empty upstream — defect recorded) |
| `tectonic/tags/worldgen/world_preset/incompatible.json` | 1 | carried |
| `tectonic/lithostitched/worldgen_modifier/**` | 6 base (9 across all packs) | **not packed** — `blocked(no-lithostitched-registrar)` |
| overlay packs (`terratonic`, `terratonic_26_2`, `26_1`, `26_2`, `clifftree`, `ultrasmooth`, `no_carvers`, `ore_fix`, `experimental.jungle_pillars`) | 8 packs | not packed in slice 1; each is a re-definition of the files above |

Total data-pack JSON files: 228 (all packs). The **base** pack — the only one
carried — has 105 density functions + 32 noise + 2 configured features +
3 placed features + 2 tags = 144 files. Counts were re-read from the jar, not
from any catalogue; `tools/carry.py --check` fixes them as a data contract.

### Density-function type census (all carried + blocked files)

`minecraft:mul` 112 · `minecraft:add` 112 · `minecraft:spline` 65 ·
`minecraft:flat_cache` 50 · `minecraft:noise` 47 · `minecraft:cache_2d` 36 ·
`minecraft:range_choice` 27 · `minecraft:abs` 24 · **`tectonic:config_constant`
23** · `minecraft:clamp` 22 · **`tectonic:config_noise` 7** ·
`lithostitched:fast_noise` 5 · **`tectonic:invert` 1** · **`tectonic:config_clamp`
1** · `minecraft:find_top_surface` 1 · plus vanilla arithmetic/range/blend
nodes. No biome, structure, block, item, model, recipe or loot file exists in
the jar — those families are **not ported because they are not in the artefact**
(`blocked(not-in-artefact)` is not even needed; this is a census fact).

### Java core behaviour extracted from the public repo (analysis aid)

Repo `Apollounknowndev/tectonic`, commit `34241bdb…` (read 2026-11-24). Files
read: `TectonicTags.java`, `config/ConfigState.java` (default values and the
`getValue`/`getNoiseState` switches), `config/object/{HeightLimits,NoiseState}.java`,
`worldgen/densityfunction/{ConfigConstant,ConfigNoise,Invert,ConfigClamp}.java`
(21.1 source line, matching the jar's class set), `tectonic.mixins.json`. No
code was translated; the Rust rewrite uses the observed semantics:
`config_constant` returns the configured `getValue(key)`; `invert` returns `1/x`;
`config_clamp` clamps input between two child densities; `config_noise` samples
a named noise with scale/shift/multiplier/offset. The mod's own mixins
(`NoiseBasedChunkGeneratorMixin`, `ChunkAccessMixin`, `BiomeMixin`, …) replace
vanilla terrain and cannot be expressed at this pin (see Gaps).

## Upstream defects fixed

1. **`tectonic:terralith_surface` block tag ships `"values": []`** with its six
   members (yellow_terracotta, red_sand, blackstone, smooth_basalt, gravel,
   calcite) in a non-standard `_values` field
   (`resourcepacks/tectonic/data/tectonic/tags/block/terralith_surface.json`).
   The Java core reads `TectonicTags.TERRALITH_SURFACE` in `BlendingDataMixin`,
   and the mod's resource-condition system (not carried) is what would promote
   `_values`. This port has no such system, so `tools/carry.py` adopts the
   declared members into `values` — the smallest change that makes the mod's
   own data mean what it says. A user can now query the tag in game; the e2e
   proves it. Upstream report worth filing? no (the field is deliberate on
   1.21.1's side).

## Gaps / blocked symbols (measured, not guessed)

- **`blocked(level_reset:R11)`** — terrain replacement. Two measurements:
  1. `ports/_shared/sdk/0a875da/surface.json` has **0** matches for
     `levels_reset`, `RuntimeLevels::reset_vanilla`, `can_survive_v2`,
     `may_place_on_v2` or `can_sustain_plant_v2` (grep, 2026-11-24). The additive
     nightly `f1bb66f353cf…` is not our pin and ten agents build against ours.
  2. The registry's R11 refuses a `[native] level_reset` manifest key
     (`var/autopilot/PLAN.md` §"Three worldgen projects evaluated", 2026-11-24).
  The jar's 27 vanilla `data/minecraft/worldgen/**` override files and its
  `NoiseBasedChunkGeneratorMixin`/`ChunkAccessMixin` are therefore **not
  packed**; carrying them without a level reset would silently change a saved
  world's terrain on reload, which is not the mod's documented behaviour.

- **`blocked(no-nested-density-decode)`** — three of the four custom density
  function types (`tectonic:invert`, `tectonic:config_clamp`,
  `tectonic:config_noise`) wrap child density functions or sample a named noise.
  The pin's whole custom-type surface is
  `fn decode(&self, json: &str) -> Result<Arc<dyn DensityFunction>, String>`
  (`ports/_shared/sdk/0a875da/api-source/crates/horizon-mod-vocab/src/world/density_function.rs:15-20`);
  there is no helper to decode a nested node or to sample a named noise, and no
  `Noise` handle in `surface.json`. `tectonic:config_constant` **is** expressible
  (plain key → value) and is registered in slice 1.

- **`blocked(no-placement-modifier-registrar)`** — the `overlay.ore_fix` pack
  uses `tectonic:height_stabilized_count` (11 placed-feature files) and the
  placed features use `lithostitched:condition` / `lithostitched:noise_slope`.
  `surface.json` has `Registrar::register_structure_type`,
  `register_density_function_type`, `register_biome_source` and
  `register_chunk_generator`, but **no** placement-modifier or feature-type
  registrar (0 matches; the same gap `yungsextras` measured). The overlay is
  not packed.

- **`blocked(no-lithostitched-registrar)`** — 9 `data/tectonic/lithostitched/`
  worldgen modifiers have no decoder at this pin.

- **Not in the artefact:** no biome, structure, block, item, model, recipe, loot
  or advancement files. The brief's generic list (biome source/modifiers/
  regions, structures, models) is deliberately **not** invented here.

- **Deferred to a later slice:** config presets/GUI/command (Java mixins + a
  client screen), the eight overlay packs, the `_values` tag defect, and any
  attempt to flatten terrain replacement into a biome hack.

## Coverage table

| Family in the jar | State | Evidence / reason |
|---|---|---|
| density function data (130 files) | carried | `data/tectonic/worldgen/density_function/`; unit data-contract test |
| noise data (43 files) | carried | `data/tectonic/worldgen/noise/` |
| `tectonic:config_constant` density type | registered | `src/runtime.rs` default table + `src/lib.rs` `Hooks::register` |
| `tectonic:config_noise`, `invert`, `config_clamp` | `blocked(no-nested-density-decode)` | trait signature, no child decode / noise handle |
| configured + placed features (4 files) | carried | 1.21.1 → 26.3 shape upgrade, in-game `/place feature` assertion |
| tags (2 files) | carried | verbatim; empty `values` is upstream's state |
| lang (`en_us.json`) | carried | `assets/tectonic/lang/en_us.json` |
| vanilla overworld noise/noise-settings overrides (27 files) | `blocked(level_reset:R11)` | two measurements above |
| `tectonic:height_stabilized_count` overlay (11 files) | `blocked(no-placement-modifier-registrar)` | no registrar for placement modifiers |
| Lithostitched modifiers (9 files) | `blocked(no-lithostitched-registrar)` | no decoder at this pin |
| Java mixins / config GUI / command / jarjar libs | not ported (out of tier) | code in the Java core, no equivalent hook |

## Verification (fresh, 2026-11-24)

Pin `0a875da…`, mixins `e59da909…`, package **`tectonic.hmod` 68,761 B,
SHA-256 `d90204c996bbeef08dfdf54b2ed345124dadfda4c49ffae8e886fe9e155e945f`,
153 entries**. Full table in [`VALIDATION.md`](VALIDATION.md).

- `tools/carry.py --check` was **red before the carry** (8 problems: 0 density
  functions, 0 noise, 0 features, 0 placed features, 0 tags, no lang, no
  registered type, 25 missing config keys) and **green after** (144 files + 1
  lang, 25 keys, 26.3 shapes, blocked families absent).
- A Rust data-contract test was red first with `wrong default for ocean_depth`
  (1 failed / 4 passed) with one default broken, then green **5 passed** after
  restoring the upstream value. `cargo clippy --all-targets -- -D warnings`
  clean, `rustfmt --check` clean.
- `cargo horizon-mod check` (source): *13 API items, Made for 0a875da*.
  Package check: *0.1.0, native-1/0a875da…, 68,761 bytes, sha d90204c9…*.
- `fits --build 0a875da`: **`0a875da  made for`**. `fits --build 0b14f8a`:
  **red, naming 7 removed symbols** (`register_density_function_type`,
  `DensityFunction::{range,sample,varies_with_y}`, `DensityFunctionType::decode`,
  the `DensityFunction`/`DensityFunctionType` traits) — the expected result for
  an API added at our pin, not a package defect.
- `verify-sdk-package.py tectonic` → **1/1**; `check-e2e-logs.py tectonic-e2e
  --strict` → `logs=4 ok=4 missing-exit=0 bad-exit=0`; `check-skills.py --notes
  ports/tectonic --strict` → PASS.

### In-game `ctl` transcript (The End, seed 20261105, offscreen, creative)

```
vanilla control: /place feature minecraft:oak -> Successfully filled 4 block(s)
ctl command "place feature tectonic:underground_river/ice 40 83 40"
   -> Placed "tectonic:underground_river/ice" at 40, 83, 40
ctl command "fill 30 79 30 50 95 50 minecraft:air replace minecraft:ice"
   -> Successfully filled 1 block(s)          # ice at a generated coordinate
ctl command "execute if block 50 80 50 #tectonic:terralith_surface"
   -> {"chat":["Test passed"],"ok":true}       # carried block tag
ctl command "execute if block 50 80 50 #tectonic:no_such_tag"
   -> "Unknown block tag 'tectonic:no_such_tag'"   # registry differential
PASS: carried feature placed minecraft:ice and the carried tag matched blackstone
EXIT:0
```

Fail-capable legs: the same leg on the **unmodded control game** ends
`FAIL: … Can't find element 'tectonic:underground_river/ice' in registry
'minecraft:worldgen/feature'` + `EXIT:1`;
`SELFTEST=1` (invert the ice assertion) ends `FAIL: SELFTEST: the ice is
present` + `EXIT:1`; `TAG_SELFTEST=1` ends `FAIL: TAG_SELFTEST: the tag matched`
+ `EXIT:1`. Logs: `ports/_shared/evidence/tectonic-e2e/e2e{,-control,-selftest,-tag-selftest}.log`.

Note on `BUILD_LOCAL=1`: it was set **only** for the launcher game build and
the e2e legs, because `tools/e2e.sh` names the local absolute campaign root and
the launcher + managed Nightly install exist only on this machine. Every
compile/test/check/build step ran without it and forwarded to the repaired
remote automatically.

### Coverage of the in-game assertion

| family | assertion | result |
|---|---|---|
| carried configured feature | `/place feature tectonic:underground_river/ice` → 1 `minecraft:ice` | tested |
| carried block tag | `execute if block 50 80 50 #tectonic:terralith_surface` → `Test passed` | tested |
| registry differential | unknown tag id → `Unknown block tag` | tested |
| density data + `config_constant` type | data-contract test, unit test, `check`, `fits` | tested (no terrain claim) |
| terrain replacement | `blocked(level_reset:R11)` | not packed, two measurements above |

## Next slice

**Family:** wire `tectonic:config_noise` into a registered density function by
extending the SDK-shaped decoder with a child-node decode helper, then prove
one carried noise-dependent density function samples a different value from a
constant control.

**Gap line:** from this document, *"`tectonic:config_noise`, `invert`,
`config_clamp` — `blocked(no-nested-density-decode)`: the SDK's custom-type
`decode` receives raw JSON but offers no way to decode a child node or sample a
named noise"* (7 `config_noise` nodes are in the base pack, plus 1 `invert` and
1 `config_clamp` in the blocked vanilla-override set).

**Tier fit:** `data` worldgen — the family is already in the artefact; only the
registrar glue is missing. No new hook, renderer or dimension is needed; the
work is to add a pure JSON child-decoder in `runtime.rs` (with red-first tests)
and a noise sampler that stays deterministic on worldgen worker threads. If the
SDK still has no noise handle at the next pin, the slice stays
`blocked(no-nested-density-decode)` and re-records that measurement instead of
inventing a sampler.

**Concrete `ctl` assertion:** with a `/tectonic density <id> <x> <y> <z>`
diagnostic command registered on the port's own `register_commands` hook (a
faithful analogue of upstream's `TectonicCommand`), read
`tectonic:__constants/noise/continents` at `[0, 64, 0]` with seed 20261105 and
assert the parsed value is **not** the `config_constant` fall-through `0.0`
(the vanilla control: the same command id is unknown on `CONTROL_GAME`;
`SELFTEST=1` flips the assertion to expect `0.0` and must exit 1). This proves a
named-noise density function is decoded and sampled, not merely carried.
