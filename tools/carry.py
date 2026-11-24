#!/usr/bin/env python3
"""Carry Tectonic's expressible data from the cached jar into a 26.3 content tree.

The jar's data lives in `resourcepacks/tectonic/`. This tool copies the families the
current pin can express (density functions, noise, configured/placed features,
tags, lang) and upgrades the two features to 26.3's shape (the registry folder
`worldgen/configured_feature/` became `worldgen/feature/`, and a block state is
now `{"id": ..., "properties": {...}}` instead of `{"Name": ..., "Properties": {...}}`).

`--check` is the data-contract test: before `--write` it fails (the tree is
empty), and afterwards it fixes the exact counts, the type census and the
26.3 shapes. It is run in the e2e so a re-carry cannot silently change the data.

Nothing here copies Java code, Mojang files or any art. The jar's `pack.png`
is deliberately not carried; the port's icon is generated separately.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT.parent.parent
JAR = CAMPAIGN / "ports/_shared/licence-cache/tectonic.jar"
PACK = "resourcepacks/tectonic/"

# The custom density-function types named by the carried data, and the one this
# slice actually registers. Keep in sync with src/runtime.rs::custom_types().
NAMED_CUSTOM_TYPES = {
    "tectonic:config_constant",
    "tectonic:config_noise",
    "tectonic:invert",
    "tectonic:config_clamp",
}
REGISTERED_TYPES = {"tectonic:config_constant"}
# Named by the carried data but deliberately not registered: each has a
# `blocked(<symbol>)` row in notes.md with its measurement.
BLOCKED_TYPES = {
    "tectonic:config_noise", "tectonic:invert", "tectonic:config_clamp",
    "lithostitched:fast_noise", "lithostitched:condition",
    "lithostitched:noise_slope", "tectonic:height_stabilized_count",
}

# Exact census of the base data pack's families (measured from the jar). The
# 130/43 totals in notes.md include the eight optional overlay packs, which are
# not carried in this slice.
EXPECTED = {
    "worldgen/density_function": 105,
    "worldgen/noise": 32,
    "worldgen/feature": 2,
    "worldgen/placed_feature": 3,
    "tags": 2,
}

# The config_constant keys named by the carried density functions. The runtime
# table must know every one of them (see src/runtime.rs).
CONFIG_KEYS = {
    "cheese_additive", "cheese_enabled", "continents", "deep_ocean_depth",
    "depth_cutoff_size", "depth_cutoff_start", "elevation_boost",
    "erosion", "flat_terrain_skew", "island", "jungle_pillars",
    "lava_tunnels", "max_y", "min_y", "noodle_additive", "noodle_enabled",
    "ocean_depth", "ocean_offset", "ridge", "rolling_hills",
    "spaghetti_enabled", "temperature", "underground_rivers",
    "vegetation", "vertical_scale",
}


def state_26(node):
    """1.21.1 block-state `{Name, Properties}` -> 26.3 `{id, properties}`."""
    if not isinstance(node, dict):
        return node
    out = {}
    for key, value in node.items():
        if key == "Name":
            out["id"] = value
        elif key == "Properties":
            out["properties"] = {
                k: str(v).lower() if isinstance(v, bool) else str(v)
                for k, v in value.items()
            }
        else:
            out[key] = state_26(value) if isinstance(value, (dict, list)) else value
    if isinstance(node.get("type"), str) and node["type"] == "minecraft:simple_state_provider":
        return state_26(node["state"])
    if out.get("type") == "minecraft:matching_blocks" and isinstance(out.get("blocks"), str):
        # 26.3's block predicate names a tag; vanilla ships `minecraft:air` as one.
        return {"type": "minecraft:matching_block_tag", "tag": out["blocks"]}
    return out


def upgrade_feature(doc):
    """A 1.21.1 configured feature -> the 26.3 `worldgen/feature/` shape."""
    if not isinstance(doc, dict) or "config" not in doc:
        return doc  # already upgraded
    out = {"type": doc["type"]}
    out.update(doc["config"])
    kind = doc["type"]
    if kind == "minecraft:simple_block":
        out["to_place"] = state_26(out["to_place"])
    elif kind == "minecraft:block_column":
        out["layers"] = [
            {**layer, "provider": state_26(layer["provider"])}
            for layer in out["layers"]
        ]
    for key in ("to_place", "allowed_placement", "predicate"):
        if key in out:
            out[key] = state_26(out[key])
    if "layers" in out:
        for layer in out["layers"]:
            for key in ("allowed_placement", "predicate"):
                if key in layer:
                    layer[key] = state_26(layer[key])
    return out


def read_jar():
    with zipfile.ZipFile(JAR) as zf:
        names = zf.namelist()
        def body(name):
            return zf.read(name).decode("utf-8")
        return names, body


def carried_paths(names):
    """(jar path, destination relative to the port) for every carried file."""
    out = []
    base = PACK + "data/tectonic/"
    for name in names:
        if not name.startswith(base) or not name.endswith(".json"):
            continue
        rel = name[len(base):]
        if rel.startswith("lithostitched/"):
            continue
        if rel.startswith("worldgen/configured_feature/"):
            dest = "data/tectonic/worldgen/feature/" + rel.split("/", 2)[2]
        elif rel.startswith(("worldgen/density_function/", "worldgen/noise/",
                             "worldgen/placed_feature/", "tags/")):
            dest = "data/tectonic/" + rel
        else:
            continue
        out.append((name, dest))
    if "assets/tectonic/lang/en_us.json" in names:
        out.append(("assets/tectonic/lang/en_us.json",
                    "assets/tectonic/lang/en_us.json"))
    return out


def write_tree():
    with zipfile.ZipFile(JAR) as zf:
        paths = carried_paths(zf.namelist())
        texts = {src: zf.read(src).decode("utf-8") for src, _ in paths}
    changed = 0
    for src, dest in paths:
        text = texts[src]
        if src.startswith(base := PACK + "data/tectonic/") and \
                src[len(base):].startswith("worldgen/configured_feature/"):
            text = json.dumps(upgrade_feature(json.loads(text)), indent=2,
                              sort_keys=True) + "\n"
        if dest == "data/tectonic/tags/block/terralith_surface.json":
            # Upstream defect: the six members are in a non-standard `_values`
            # field while `values` is empty. This port has no resource-condition
            # system to promote them, so it adopts the declared members.
            doc = json.loads(text)
            if not doc.get("values") and isinstance(doc.get("_values"), list):
                doc["values"] = doc["_values"]
                text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
        target = ROOT / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        changed += 1
    print(f"carried {changed} files into {ROOT}")


def check_tree():
    problems = []
    for folder, want in EXPECTED.items():
        files = list((ROOT / "data/tectonic" / folder).rglob("*.json"))
        if len(files) != want:
            problems.append(f"data/tectonic/{folder}: {len(files)} files, expected {want}")

    lang = ROOT / "assets/tectonic/lang/en_us.json"
    if not lang.is_file():
        problems.append("assets/tectonic/lang/en_us.json is missing")

    named, keys, seen_types = set(), set(), set()
    for path in (ROOT / "data/tectonic").rglob("*.json"):
        try:
            doc = json.loads(path.read_text())
        except Exception as exc:
            problems.append(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")
            continue
        def walk(node):
            if isinstance(node, dict):
                if "type" in node and isinstance(node["type"], str):
                    seen_types.add(node["type"])
                if node.get("type") in NAMED_CUSTOM_TYPES and isinstance(node.get("key"), str):
                    named.add(node["type"])
                    keys.add(node["key"])
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
        walk(doc)

    for kind in sorted(named - REGISTERED_TYPES - BLOCKED_TYPES):
        problems.append(
            f"density type {kind} is named by carried data but neither registered "
            "nor explicitly recorded as blocked")
    for kind in sorted(REGISTERED_TYPES - named):
        problems.append(f"registered density type {kind} is not named by any carried file")
    missing_keys = CONFIG_KEYS - keys
    if missing_keys:
        problems.append(f"config_constant keys absent from carried data: {sorted(missing_keys)}")

    for path in (ROOT / "data/tectonic/worldgen/feature").rglob("*.json"):
        text = path.read_text()
        if '"Name"' in text or '"Properties"' in text:
            problems.append(f"{path.relative_to(ROOT)}: 1.21.1 block-state shape, not 26.3")
    if (ROOT / "data/tectonic/worldgen/configured_feature").exists():
        problems.append("worldgen/configured_feature: 26.3 reads worldgen/feature")

    # The blocked families must NOT be packed: applying them without a level
    # reset would rewrite a saved world's terrain.
    for banned in ("data/minecraft", "data/tectonic/lithostitched"):
        if (ROOT / banned).exists():
            problems.append(f"{banned}: packed but this pin cannot apply it (blocked)")

    if problems:
        for p in problems:
            print(f"FAIL {p}")
        print(f"carry contract FAILED: {len(problems)} problem(s)")
        return 1
    total = sum(len(list((ROOT / "data/tectonic" / f).rglob("*.json")))
                for f in EXPECTED)
    print(f"OK    {total} carried worldgen/tag files + 1 lang file; "
          f"types={sorted(named)}; keys={len(keys)}; 26.3 shapes; blocked families absent")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if args.write:
        write_tree()
    if args.check or not args.write:
        return check_tree()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
