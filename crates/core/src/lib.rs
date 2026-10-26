//! File-independent operators. All timestamps are integer nanoseconds.
pub mod filter;
pub mod quality;
pub mod sampling;
pub mod selection;
pub mod time;

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum Error {
    #[error("invalid argument: {0}")]
    Invalid(String),
    #[error("timestamp arithmetic overflow")]
    Overflow,
}

pub type Result<T> = std::result::Result<T, Error>;

pub(crate) fn invalid(message: impl Into<String>) -> Error {
    Error::Invalid(message.into())
}

/// An owned, row-major signal. Quality failures remain inspectable.
#[derive(Clone, Debug)]
pub struct Signal {
    timestamps: Vec<i64>,
    values: Vec<f64>,
    channels: usize,
}

impl Signal {
    pub fn new(timestamps: Vec<i64>, values: Vec<f64>, channels: usize) -> Result<Self> {
        if channels == 0 || timestamps.len().checked_mul(channels) != Some(values.len()) {
            return Err(invalid(
                "values must have shape (timestamps.len(), channels > 0)",
            ));
        }
        Ok(Self {
            timestamps,
            values,
            channels,
        })
    }
    /// Consume the signal and transfer its owned row-major buffers without copying.
    /// Returns (nanosecond timestamps, flat values, channel count).
    pub fn into_parts(self) -> (Vec<i64>, Vec<f64>, usize) {
        (self.timestamps, self.values, self.channels)
    }
    pub fn timestamps(&self) -> &[i64] {
        &self.timestamps
    }
    pub fn values(&self) -> &[f64] {
        &self.values
    }
    pub fn channels(&self) -> usize {
        self.channels
    }
    pub fn len(&self) -> usize {
        self.timestamps.len()
    }
    pub fn is_empty(&self) -> bool {
        self.timestamps.is_empty()
    }
    pub fn row(&self, index: usize) -> &[f64] {
        &self.values[index * self.channels..(index + 1) * self.channels]
    }
    pub fn require_ordered(&self) -> Result<()> {
        time::require_strict(self.timestamps())
    }
}

/// Descriptive metadata; no implicit unit/frame conversion is performed.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SignalSpec {
    pub name: String,
    pub kind: SignalKind,
    pub channels: usize,
    pub unit: Option<String>,
    pub frame: Option<String>,
    pub timestamp_source: String,
    pub required: bool,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SignalKind {
    Continuous,
    QuaternionXyzw,
    Command,
    Discrete,
    Event,
}
