# Tectonic — a Horizon 26.3 port

> Tectonic shapes Minecraft's terrain into grander, more varied continents and
> caves. Upstream: <https://github.com/Apollounknowndev/tectonic> (Apollo, MIT).

This is a **clean-room Rust rewrite** of Tectonic for Horizon (Minecraft Java
26.3), pinned to SDK `0a875da91dbb0fdcb7ba8c42c11341aa229af51a` and horizon-mixins
`e59da9094f0c2fdda6c627fe9eff22dec6a906f0`.

## What this version implements

- Carries the base data pack's density functions (105), noise files (32),
  configured and placed features (5), tags (2) and the language file.
- Upgrades the configured features from 1.21.1's `worldgen/configured_feature/`
  to 26.3's `worldgen/feature/` and re-shapes their block states. The carried
  `tectonic:terralith_surface` tag's non-standard `_values` are promoted into
  `values` (recorded as an upstream defect fix).
- Registers the `tectonic:config_constant` density-function type from Rust,
  with upstream's default config values in a pure, unit-tested table.

## What it does **not** implement

- **Terrain replacement** — `blocked(level_reset:R11)`: the pin has no
  `levels_reset`/`RuntimeLevels::reset_vanilla` surface and R11 refuses the
  manifest key. The vanilla `data/minecraft/worldgen/**` overrides and the
  Java mixins are deliberately not packed. This is not a biome hack.
- `tectonic:config_noise`, `tectonic:invert` and `tectonic:config_clamp` —
  `blocked(no-nested-density-decode)`: the SDK's custom-type `decode` receives
  raw JSON but offers no way to decode a child node or sample a named noise.
- The `height_stabilized_count` placement modifier and Lithostitched worldgen
  modifiers — `blocked(no-placement-modifier-registrar)` /
  `blocked(no-lithostitched-registrar)`.
- The config screen, presets, command and the eight optional overlay packs.

## Install

Build against the pinned SDK (`cargo horizon-mod build`) and install the
resulting `tectonic.hmod` with a Horizon launcher that uses the same pin. A
data pack that cannot decode never rewrites an existing world's terrain here:
only the expressible families are carried. See `notes.md` for the full
inventory, the coverage table and the verification evidence.

## Layout

```
horizon-mod.toml       the flat SDK manifest (api = "0.2", [native] pins)
Cargo.toml             SDK-only dependency (registry rule R9)
src/lib.rs             the one impl Hooks: register() for the density type
src/runtime.rs         pure config defaults + JSON key reader (unit tested)
data/tectonic/         the carried, upgraded data pack
assets/tectonic/lang/  the carried language file
tools/carry.py         jar -> 26.3 carry and its --check data contract
tools/e2e.sh           in-game, fail-capable assertions
```
