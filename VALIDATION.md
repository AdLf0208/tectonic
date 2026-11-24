# Tectonic — validation record (first slice, v0.1.0)

Pin **`0a875da91dbb0fdcb7ba8c42c11341aa229af51a`**, mixins
`e59da9094f0c2fdda6c627fe9eff22dec6a906f0`, game 26.3 (Nightly
`nightly-2026-11-20-0a875da`), launcher 0.2.92, `api = "0.2"`.

**Version 0.1.0** — a first publication: the campaign template's starting
version. `0.2.0` is reserved for the first behaviour slice after publication;
this slice is the initial carry and registration, with no prior record to
supersede. Cargo's version and the manifest's version agree at 0.1.0.

## The deliverable

| | |
|---|---|
| package | `ports/tectonic/tectonic.hmod` |
| size | **68,761 B** |
| SHA-256 | `d90204c996bbeef08dfdf54b2ed345124dadfda4c49ffae8e886fe9e155e945f` |
| version | **0.1.0** (manifest + `Cargo.toml`) |
| entries | **153** (144 carried worldgen/tag files + 1 lang + manifest/Cargo/src/docs/uses.json) |
| packed `Cargo.lock` | none |
| runtime | `src/runtime.rs` byte-identical in the tree and in the package (`2cee0dd4…`) |

## Gates (fresh, against the delivered bytes)

| gate | command | result | log |
|---|---|---|---|
| data contract (red) | `python3 tools/carry.py --check` before the carry | **FAIL**, 8 problems | `evidence/tectonic/carry-contract-red.log` |
| data contract (green) | `python3 tools/carry.py --check` | green: 144 files + 1 lang, 25 keys, 26.3 shapes, blocked families absent | `evidence/tectonic/carry-contract.log` |
| unit tests (red) | `cargo test --offline`, one default broken | **1 failed**, `wrong default for ocean_depth` | `evidence/tectonic/unit-test-red.log` |
| unit tests | `cargo test --offline` | **5 passed**, 0 failed | `evidence/tectonic/sdk-test.log` |
| lints | `cargo clippy --all-targets --offline -- -D warnings` | exit 0, 0 warnings | `evidence/tectonic/sdk-clippy.log` |
| format | `rustfmt --edition 2024 --check src/{lib,runtime}.rs` | clean | — |
| SDK check (source) | `cargo horizon-mod check` | *13 API items; Made for 0a875da* | `evidence/tectonic/sdk-check.log` |
| package check | `cargo horizon-mod check tectonic.hmod` | *0.1.0, native-1/0a875da…, 68,761 bytes* | `evidence/tectonic/sdk-package-check.log` |
| fits (pin) | `cargo horizon-mod fits tectonic.hmod --build 0a875da` | *0a875da made for*, exit 0 | `evidence/tectonic/sdk-fits.log` |
| fits (other build) | `cargo horizon-mod fits tectonic.hmod --build 0b14f8a` | **exit 1, red naming 7 removed symbols** — the density-function registration API exists at our pin only; this is the expected proof the check is not a tautology (PLAN.md "A red `fits --build <other>` is not automatically a failure") | `evidence/tectonic/sdk-fits-other.log` |
| package gate | `verify-sdk-package.py tectonic` | **1/1** | — |
| skipped gates | `check-recipe-types.py`, `check-manifest-deps.py` | no recipe types, no other registry mod named in code | — |

Every Rust step ran through `ports/tools/build-slot.sh` with
`CARGO_INCREMENTAL=0`, no `--target-dir`. Compile/test/check/build steps
**forwarded to the repaired remote automatically**; only the launcher game
build and the e2e legs were local (`BUILD_LOCAL=1`) because the launcher binary
and its managed Nightly install live on this machine.

## In-game legs (`ports/_shared/evidence/tectonic-e2e/`)

| leg | result | log |
|---|---|---|
| modded game (default) | **PASS** + `EXIT:0` — `/place feature tectonic:underground_river/ice` → `Successfully filled 1 block(s)` of `minecraft:ice`; `#tectonic:terralith_surface` → `Test passed` on blackstone; unknown tag id → `Unknown block tag` | `e2e.log` |
| control (the same Nightly, no mod) | **FAIL** + `EXIT:1` — `Can't find element 'tectonic:underground_river/ice' in registry 'minecraft:worldgen/feature'` | `e2e-control.log` |
| feature selftest (inverted ice assertion) | **FAIL** + `EXIT:1` — `SELFTEST: the ice is present` | `e2e-selftest.log` |
| tag selftest (inverted tag assertion) | **FAIL** + `EXIT:1` — `TAG_SELFTEST: the tag matched` | `e2e-tag-selftest.log` |
| log gate | `check-e2e-logs.py tectonic-e2e --strict` → `logs=4 ok=4 missing-exit=0 bad-exit=0` | — |

`BUILD_LOCAL=1` was used **only** on the launcher game build and these four e2e
legs: `tools/e2e.sh` names the local absolute campaign root and the launcher
plus its managed Nightly install exist only on this machine. Every compile,
test, check and package-build step ran without the flag and forwarded to the
repaired remote automatically. The first attempt with `build-slot.sh e2e` was a
harness mismatch (the legacy e2e-guard expects `tools/horizon.py`, which SDK
ports do not have) and is recorded in `ports/_shared/evidence/e2e-guard/`; the
four legs above all used `build-slot.sh run --step e2e`, as the migrated ports do.

The package was **not changed** after its sha was recorded; the only tree edits
after the final build were to `notes.md`/`VALIDATION.md` (not packed) and the
`e2e.sh` differential fix (not packed). `verify-sdk-package.py tectonic` still
reports **1/1** and `package matches the tree` green after all edits.

## Re-run

```sh
# ladder (each a separate lease; compile steps forward automatically)
ports/tools/build-slot.sh run --job TEC --port ports/tectonic --step test  -- cargo test --offline
ports/tools/build-slot.sh run --job TEC --port ports/tectonic --step lint  -- cargo clippy --all-targets --offline -- -D warnings
ports/tools/build-slot.sh run --job TEC --port ports/tectonic --step check -- cargo horizon-mod check
ports/tools/build-slot.sh run --job TEC --port ports/tectonic --step build -- bash -c 'rm -f Cargo.lock && cargo horizon-mod build && cp target/horizon-mod/tectonic.hmod tectonic.hmod'
# the game is local-only (launcher + managed Nightly install)
BUILD_LOCAL=1 ports/tools/build-slot.sh run --job TEC --port ports/tectonic --step build -- ports/tools/launcher-game.sh build tectonic
BUILD_LOCAL=1 ports/tools/build-slot.sh e2e --job TEC --port ports/tectonic -- \
    bash -lc 'cd ports/tectonic && eval "$(/home/adlf/Desktop/all_the_mods_10_rust_rewrite/ports/tools/launcher-game.sh env tectonic)" && tools/e2e.sh'
```
