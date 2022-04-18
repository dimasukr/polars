pub mod arena;
pub mod contention_pool;
mod error;
pub mod mem;
pub mod sort;
mod functions;

pub use functions::*;

#[cfg(not(feature = "bigidx"))]
pub type IdxSize = u32;
#[cfg(feature = "bigidx")]
pub type IdxSize = u64;
