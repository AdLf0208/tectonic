//! Tectonic for Horizon 26.3 — the one `impl Hooks` at the crate root.
//!
//! Slice 1 carries the mod's density-function/noise data, features, tags and
//! lang, and registers the one custom density-function type the pin can decode
//! faithfully (`tectonic:config_constant`). All pure values live in
//! [`runtime`]; this file is only the typed glue to the SDK.
use std::sync::Arc;

use mod_api::{self, DensityFunction, DensityFunctionType, Hooks, Registrar, RegistrationContext};

mod runtime;

/// A density function whose value does not depend on position: exactly what
/// upstream's `ConfigConstant` returns (`compute`/`fillArray` both write the
/// configured value, `minValue`/`maxValue` are that value).
struct Constant(f64);

impl DensityFunction for Constant {
    fn range(&self) -> [f32; 2] {
        let v = self.0 as f32;
        [v, v]
    }

    fn varies_with_y(&self) -> bool {
        false
    }

    fn sample(&self, _position: [i32; 3], _seed: i64) -> f32 {
        self.0 as f32
    }
}

/// Reads one `{"type": "tectonic:config_constant", "key": "…"}` node.
struct ConfigConstantType;

impl DensityFunctionType for ConfigConstantType {
    fn decode(&self, json: &str) -> Result<Arc<dyn DensityFunction>, String> {
        let key = runtime::string_field(json, "key")
            .ok_or_else(|| "tectonic:config_constant has no string `key`".to_string())?;
        Ok(Arc::new(Constant(runtime::config_value(key))))
    }
}

#[derive(Default)]
struct Mod;

#[mod_api::horizon_mod]
impl Hooks for Mod {
    fn register(&self, registrar: &mut dyn Registrar, _context: &RegistrationContext) {
        // The id is namespace-qualified by the registrar to `tectonic:config_constant`.
        registrar.register_density_function_type("config_constant", ConfigConstantType);
    }
}
