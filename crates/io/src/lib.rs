//! Read-only source adapters and explicit media transformations.
pub mod image_ops;
pub mod mcap_ops;
pub mod video;

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error(transparent)] Io(#[from] std::io::Error),
    #[error(transparent)] Mcap(#[from] mcap::McapError),
    #[error(transparent)] Core(#[from] mcap_ops_core::Error),
    #[error(transparent)] Json(#[from] serde_json::Error),
    #[error(transparent)] Image(#[from] image::ImageError),
    #[error("{0}")] Invalid(String),
}
pub type Result<T> = std::result::Result<T,Error>;
pub(crate) fn invalid(message:impl Into<String>)->Error {Error::Invalid(message.into())}
