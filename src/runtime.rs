//! Pure logic for the Tectonic port: the default config table the carried
//! `tectonic:config_constant` density functions read, and the tiny JSON field
//! extractor that names a key. No `mod_api` or game types live here, so the
//! numbers are testable with `cargo test` alone.

/// The value a `tectonic:config_constant` node returns for one config key.
///
/// Upstream's `ConfigState.getValue(String)` switches on the key and returns
/// the default state's field; keys that belong to the noise-state table fall
/// through to `default -> 0`. The values below are the upstream defaults read
/// from `config/ConfigState.java` at commit `34241bdb…` (the 1.21.1 source line
/// that matches the cached jar), not invented tuning values. The port has no
/// config file or GUI at this pin, so the defaults are fixed.
pub const CONFIG_DEFAULTS: &[(&str, f64)] = &[
    // GlobalTerrain
    ("vertical_scale", 1.125),
    ("elevation_boost", 0.0),
    ("min_y", -64.0),
    ("max_y", 320.0),
    ("lava_tunnels", 1.0), // upstream boolean `true` -> 1
    // Continents
    ("ocean_offset", -0.8),
    ("underground_rivers", -1.0), // upstream boolean `true` -> -1
    ("flat_terrain_skew", 0.1),
    ("rolling_hills", 1.0),
    ("jungle_pillars", 1.0),
    // Oceans
    ("ocean_depth", -0.22),
    ("deep_ocean_depth", -0.45),
    // Caves
    ("depth_cutoff_start", 0.1),
    ("depth_cutoff_size", 0.1),
    ("cheese_enabled", 1.0),
    ("cheese_additive", 0.27),
    ("noodle_enabled", 1.0),
    ("noodle_additive", -0.075),
    // Noise-state keys: upstream `getValue` has no case, so it returns 0.
    ("continents", 0.0),
    ("erosion", 0.0),
    ("ridge", 0.0),
    ("temperature", 0.0),
    ("vegetation", 0.0),
    ("island", 0.0),
    // Upstream `test("ore_fix")` is not a `getValue` key either.
    ("spaghetti_enabled", 0.0),
];

/// Every custom density-function type named by the carried data.
#[cfg(test)]
pub const NAMED_CUSTOM_TYPES: &[&str] = &[
    "tectonic:config_constant",
    "tectonic:config_noise",
    "tectonic:invert",
    "tectonic:config_clamp",
];

/// The types this slice actually registers at the pin.
#[cfg(test)]
pub const REGISTERED_TYPES: &[&str] = &["tectonic:config_constant"];

/// Look up one config key, mirroring upstream's fall-through to `0.0`.
#[must_use]
pub fn config_value(key: &str) -> f64 {
    CONFIG_DEFAULTS
        .iter()
        .find(|(name, _)| *name == key)
        .map_or(0.0, |(_, value)| *value)
}

/// Extract the value of a simple string field from a density JSON object.
///
/// The SDK hands a `DensityFunctionType` the whole `{"type": …, "key": …}`
/// object as text and exports no JSON parser (and R9 forbids `serde_json`).
/// A config key is a plain identifier, so a small scoped scan is enough and
/// needs no dependency. Returns `None` when the field is absent, malformed or
/// carries an escape (upstream keys never do).
#[must_use]
pub fn string_field<'a>(json: &'a str, field: &str) -> Option<&'a str> {
    let needle = format!("\"{field}\"");
    let start = json.find(&needle)? + needle.len();
    let rest = json.get(start..)?.trim_start();
    let rest = rest.strip_prefix(':')?.trim_start();
    let body = rest.strip_prefix('"')?;
    let end = body.find(['"', '\\'])?;
    (body.as_bytes()[end] == b'"').then(|| &body[..end])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_key_named_by_the_carried_data_has_a_default() {
        // The 25 keys the data-contract tool extracted from the jar. A typo or
        // a dropped default must fail here, not silently sample 0 in game.
        let keys = [
            "cheese_additive",
            "cheese_enabled",
            "continents",
            "deep_ocean_depth",
            "depth_cutoff_size",
            "depth_cutoff_start",
            "elevation_boost",
            "erosion",
            "flat_terrain_skew",
            "island",
            "jungle_pillars",
            "lava_tunnels",
            "max_y",
            "min_y",
            "noodle_additive",
            "noodle_enabled",
            "ocean_depth",
            "ocean_offset",
            "ridge",
            "rolling_hills",
            "spaghetti_enabled",
            "temperature",
            "underground_rivers",
            "vegetation",
            "vertical_scale",
        ];
        for key in keys {
            assert!(
                CONFIG_DEFAULTS.iter().any(|(name, _)| *name == key),
                "config default for {key} is missing"
            );
        }
        assert_eq!(
            CONFIG_DEFAULTS.len(),
            keys.len(),
            "table has an unexpected key"
        );
    }

    #[test]
    fn defaults_match_the_upstream_config_state() {
        let cases = [
            ("vertical_scale", 1.125),
            ("ocean_offset", -0.8),
            ("underground_rivers", -1.0),
            ("ocean_depth", -0.22),
            ("deep_ocean_depth", -0.45),
            ("cheese_additive", 0.27),
            ("noodle_additive", -0.075),
            ("min_y", -64.0),
            ("max_y", 320.0),
        ];
        for (key, want) in cases {
            assert_eq!(config_value(key), want, "wrong default for {key}");
        }
    }

    #[test]
    fn unknown_key_falls_through_to_zero() {
        assert_eq!(config_value("not_a_tectonic_key"), 0.0);
    }

    #[test]
    fn string_field_reads_a_density_function_key() {
        let json = r#"{"type": "tectonic:config_constant", "key": "ocean_depth"}"#;
        assert_eq!(string_field(json, "key"), Some("ocean_depth"));
        assert_eq!(string_field(json, "type"), Some("tectonic:config_constant"));
        assert_eq!(string_field(json, "absent"), None);
    }

    #[test]
    fn every_named_type_is_registered_or_known_blocked() {
        // Keeps the Rust declaration and the data-contract census in sync.
        let blocked = [
            "tectonic:config_noise",
            "tectonic:invert",
            "tectonic:config_clamp",
        ];
        for name in NAMED_CUSTOM_TYPES {
            assert!(
                REGISTERED_TYPES.contains(name) || blocked.contains(name),
                "{name} is neither registered nor recorded as blocked"
            );
        }
    }
}
