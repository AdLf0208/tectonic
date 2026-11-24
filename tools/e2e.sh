#!/usr/bin/env bash
# In-game check for Tectonic slice 1 (the carried data, not terrain replacement).
#
# The game is built by `ports/tools/launcher-game.sh build tectonic`, which compiles
# this port's flat .hmod (Rust + data) into a Nightly 0a875da game. `eval` its `env`
# for GAME, CTL, CONTROL_GAME, RES, SOCK and E2E_TMP.
#
# Default run (the modded game):
#   - the level opens with no worldgen/data-file refusal;
#   - `/place feature tectonic:underground_river/ice` places **minecraft:ice** at
#     a generated coordinate in The End (the carried 26.3 configured feature),
#     counted server-side with `fill … replace`; the vanilla oak feature is the
#     control that the command path itself works;
#   - `#tectonic:terralith_surface` matches blackstone at a coordinate, proving
#     the carried block tag (with the upstream `_values` defect corrected); an
#     unknown tag id is the differential;
#   - `PASS` + EXIT:0.
#
# Fail-capable legs:
#   GAME=$CONTROL_GAME tools/e2e.sh   # unmodded game: the carried feature id is unknown -> FAIL EXIT:1
#   SELFTEST=1 tools/e2e.sh           # inverted feature assertion (expect no ice) -> FAIL EXIT:1
#   TAG_SELFTEST=1 tools/e2e.sh       # inverted tag assertion -> FAIL EXIT:1
set -euo pipefail
export LC_ALL=C

CAMPAIGN=/home/adlf/Desktop/all_the_mods_10_rust_rewrite
PORT=$CAMPAIGN/ports/tectonic
CTL=${CTL:-}
GAME=${GAME:-}
RES=${RES:-${HORIZON_RES:-/home/adlf/Desktop/horizon/.local/horizon-client/26.3}}
SOCK=${SOCK:-/tmp/opencode/tectonic-e2e.sock}
E2E_TMP=${E2E_TMP:-/tmp/opencode}
SELFTEST=${SELFTEST:-0}
TAG_SELFTEST=${TAG_SELFTEST:-0}

[ -n "$CTL" ] && [ -n "$GAME" ] || { echo "missing CTL/GAME: eval \"\$(ports/tools/launcher-game.sh env tectonic)\"" >&2; exit 1; }
[ -x "$CTL" ] || { echo "missing horizon-ctl: $CTL" >&2; exit 1; }
[ -x "$GAME" ] || { echo "missing horizon-client: $GAME" >&2; exit 1; }
[ -d "$RES/assets" ] || { echo "missing prepared resources: $RES" >&2; exit 1; }

say() { echo "== $* =="; }
fail() { echo "FAIL: $*" >&2; exit 1; }

SCRATCH=$(mktemp -d "$E2E_TMP/tectonic-home.XXXXXX")
export HORIZON_HOME=$SCRATCH/game
export HORIZON_LAUNCHER_HOME=$SCRATCH/launcher
export XDG_DATA_HOME=$SCRATCH/data
export XDG_CONFIG_HOME=$SCRATCH/config
export HORIZON_NO_AUDIO=1
mkdir -p "$(dirname "$SOCK")" "$SCRATCH"
rm -f "$SOCK"
cd "$SCRATCH"

ctl() { "$CTL" --socket "$SOCK" "$@"; }
end() { ctl command "execute in minecraft:the_end run $1"; }

cleanup() {
    rc=$?
    ctl quit >/dev/null 2>&1 || true
    sleep 1
    rm -rf "$SCRATCH" || true
    echo "EXIT:$rc"
}
trap cleanup EXIT

say "launch (offscreen, creative, The End, seed 20261105)"
if ! "$CTL" --socket "$SOCK" launch \
    --game "$GAME" --world TectonicE2E --seed 20261105 --creative --offscreen --wait \
    --game-dir "$SCRATCH/game" --resources "$RES" \
    > "$SCRATCH/launch.json" 2> "$SCRATCH/launch.err"; then
    echo "launch reply: $(cat "$SCRATCH/launch.json" 2>/dev/null)" >&2
    tail -25 "$SCRATCH/game/logs/latest.log" >&2 || true
    fail "the game did not launch"
fi
jq -c '{dimension, creative, ok: .launch.ok}' "$SCRATCH/launch.json" || true
ctl wait-ready 180 || fail "the game did not become ready"

# A carried data pack that cannot decode must not become a silent warning: the
# level has to open cleanly. (Density functions themselves are inert at this
# pin because the terrain-replacement overrides are deliberately not packed.)
LOG=$(ctl logs --lines 8000 2>/dev/null || true)
for bad in "Couldn't parse data file" "invalid world generation field" "Unknown recipe type"; do
    if grep -qi "$bad" <<<"$LOG"; then
        grep -i "$bad" <<<"$LOG" >&2
        fail "the level opened with '$bad' in the log"
    fi
done
echo "the level opened without a data-file refusal"

say "The End arena (stone floor at y=79, air above)"
end "forceload add -16 -16 96 80" >/dev/null
end "tp @s 8.5 80 8.5" >/dev/null
ctl wait 40
end "fill -16 79 -16 80 79 80 minecraft:stone" >/dev/null
for y in 80 81 82 83 84 85 86 87 88 89 90; do end "fill -16 $y -16 80 $y 80 minecraft:air" >/dev/null; done
end "difficulty peaceful" >/dev/null
end "gamerule spawn_mobs false" >/dev/null
ctl wait 5

say "carried configured feature places minecraft:ice at a generated coordinate"
# The command path itself must work: vanilla's oak feature places oak_log.
ctl command "place feature minecraft:oak 20 83 20" >/dev/null \
    || fail "the vanilla oak control feature did not place"
ctl wait 5
vanilla_count=$(ctl command "fill 15 79 15 25 95 25 minecraft:air replace minecraft:oak_log" \
    | jq -r '.chat[0] // ""')
echo "vanilla control: /place feature minecraft:oak -> $vanilla_count"
grep -q 'Successfully filled' <<<"$vanilla_count" || fail "the vanilla control placed no oak_log"

reply=$(ctl command "place feature tectonic:underground_river/ice 40 83 40" 2>&1 || true)
echo "tectonic feature reply: $(echo "$reply" | jq -r '.chat[0] // .' 2>/dev/null | head -c 120)"
grep -qi 'Placed' <<<"$reply" || fail "the carried feature id did not place: $reply"
ctl wait 5
ice=$(ctl command "fill 30 79 30 50 95 50 minecraft:air replace minecraft:ice" \
    | jq -r '.chat[0] // ""')
echo "carried feature: minecraft:ice -> $ice"
if [ "$SELFTEST" = 1 ]; then
    # Inverted assertion: the ice MUST be absent. It is present, so this leg fails.
    grep -q 'Successfully filled' <<<"$ice" \
        && fail "SELFTEST: the ice is present; the inverted assertion expected none"
    echo "SELFTEST: no ice (unexpected)"
else
    grep -q 'Successfully filled' <<<"$ice" || fail "the carried feature placed no minecraft:ice ($ice)"
fi

say "carried block tag #tectonic:terralith_surface matches blackstone"
end "setblock 50 80 50 minecraft:blackstone" >/dev/null
ctl wait 5
tag_reply=$(ctl command "execute if block 50 80 50 #tectonic:terralith_surface" 2>&1 || true)
echo "tag reply: $(echo "$tag_reply" | jq -c . 2>/dev/null | head -c 160)"
tag_chat=$(echo "$tag_reply" | jq -r '.chat[0] // ""' 2>/dev/null || echo "")
if [ "$TAG_SELFTEST" = 1 ]; then
    grep -q 'Test passed' <<<"$tag_chat" \
        && fail "TAG_SELFTEST: the tag matched; the inverted assertion expected no match"
    echo "TAG_SELFTEST: no match (unexpected)"
else
    grep -q 'Test passed' <<<"$tag_chat" || fail "the carried tag did not match blackstone: $tag_reply"
fi
# Differential: an unknown tag id is refused by the registry. `ctl command`
# answers ok:true even for a refused command, so the chat text is the assertion.
unknown=$(ctl command "execute if block 50 80 50 #tectonic:no_such_tag" 2>&1 || true)
unknown_chat=$(echo "$unknown" | jq -r '.chat[0] // ""' 2>/dev/null || echo "")
echo "unknown tag differential: $unknown_chat"
grep -q 'Unknown block tag' <<<"$unknown_chat" \
    || fail "an unknown tag id was not refused by the registry: $unknown"

say "carried data summary"
echo "density_function=$(find "$PORT/data/tectonic/worldgen/density_function" -name '*.json' | wc -l) " \
     "noise=$(find "$PORT/data/tectonic/worldgen/noise" -name '*.json' | wc -l) " \
     "feature=$(find "$PORT/data/tectonic/worldgen/feature" -name '*.json' | wc -l) " \
     "placed_feature=$(find "$PORT/data/tectonic/worldgen/placed_feature" -name '*.json' | wc -l) " \
     "tags=$(find "$PORT/data/tectonic/tags" -name '*.json' | wc -l)"

echo "PASS: carried feature placed minecraft:ice and the carried tag matched blackstone"
