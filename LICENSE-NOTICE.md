# Licence notice — `tectonic` (Tectonic)

This port carries data from **Tectonic** (mod id `tectonic`), authored by
**Apollo** (`Apollounknowndev`).

## Upstream project

- Repository: <https://github.com/Apollounknowndev/tectonic> — shallow clone read
  at commit `34241bdb35acda67b5367d49f354c66c05e098e2` on 2026-11-24.
- Modrinth project `lWDHr9jE` (<https://modrinth.com/mod/tectonic>).
- The port's own repository (`https://github.com/AdLf0208/tectonic`) is where
  this Rust rewrite's source lives; it is **not** the upstream project.

## What the artefacts declare — read, not guessed

| Evidence | Value |
|---|---|
| Jar `META-INF/neoforge.mods.toml` → `license` | `MIT` (verbatim) |
| Modrinth project `lWDHr9jE` licence field | `MIT` |
| Upstream repository default branch | **no LICENSE/COPYING/NOTICE file** |
| Jar contents (`unzip -l`) | no `LICENSE`/`COPYING`/`NOTICE` file of its own |

Both facts are recorded: the code and data are **MIT → rank 0 (permissive)**,
and the upstream repo has no licence file. Because MIT requires the copyright
and permission notice to travel with every copy or substantial portion, this
port ships `LICENSE` (the MIT text attributed to Apollo) and this notice. The
jar's `pack.png` is **not** carried, so no upstream art is redistributed.

## What travels with this package

- `data/tectonic/worldgen/{density_function,noise,feature,placed_feature}/` —
  the base data pack's 143 worldgen JSON files, re-typed to 26.3 where needed.
- `data/tectonic/tags/` — two tag files (one with the upstream `_values` defect
  corrected, recorded in `notes.md`).
- `assets/tectonic/lang/en_us.json` — the language file.
- `src/` — the clean-room Rust glue that registers `tectonic:config_constant`.

No Java source, no Mojang file, no `.class` file and no art from the jar is
shipped. The cached jar under `ports/_shared/licence-cache/` is evidence and is
never packed.

## Obligations that follow from MIT

Redistribution and modification are permitted; the notice travels with the
package; the software is provided **as is**, without warranty. The port is a
**partial** implementation: terrain replacement is explicitly `blocked`, as
recorded in `notes.md`, and is not claimed as ported behaviour.
