pub mod arena;
pub mod contention_pool;
mod error;
mod functions;
pub mod mem;
pub mod sort;

#[cfg(target_family = "wasm")]
pub mod wasm;

pub use functions::*;

#[cfg(not(feature = "bigidx"))]
pub type IdxSize = u32;
#[cfg(feature = "bigidx")]
pub type IdxSize = u64;
