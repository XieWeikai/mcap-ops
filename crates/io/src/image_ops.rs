use crate::{invalid, Result};
use image::{imageops::FilterType, DynamicImage, ImageFormat, ImageReader, Limits};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::io::Cursor;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct ImageOptions {
    pub max_width: u32,
    pub max_height: u32,
    pub max_pixels: u64,
    pub dark_threshold: u8,
    pub bright_threshold: u8,
}
impl Default for ImageOptions {
    fn default() -> Self {
        Self {
            max_width: 16384,
            max_height: 16384,
            max_pixels: 64_000_000,
            dark_threshold: 10,
            bright_threshold: 245,
        }
    }
}
pub fn decode(bytes: &[u8], options: &ImageOptions) -> Result<DynamicImage> {
    if options.max_width == 0
        || options.max_height == 0
        || options.max_pixels == 0
        || options.dark_threshold >= options.bright_threshold
    {
        return Err(invalid("invalid image limits or exposure thresholds"));
    }
    let mut reader = ImageReader::new(Cursor::new(bytes)).with_guessed_format()?;
    if !matches!(reader.format(), Some(ImageFormat::Png | ImageFormat::Jpeg)) {
        return Err(invalid("only PNG and JPEG are supported"));
    }
    let mut limits = Limits::default();
    limits.max_image_width = Some(options.max_width);
    limits.max_image_height = Some(options.max_height);
    limits.max_alloc = Some(
        options
            .max_pixels
            .checked_mul(16)
            .ok_or_else(|| invalid("image allocation limit overflow"))?,
    );
    reader.limits(limits);
    let decoder = reader.into_decoder()?;
    use image::ImageDecoder;
    let (width, height) = decoder.dimensions();
    if u64::from(width) * u64::from(height) > options.max_pixels {
        return Err(invalid("image exceeds max_pixels"));
    }
    Ok(DynamicImage::from_decoder(decoder)?)
}

#[derive(Clone, Debug, Serialize)]
pub struct ImageQuality {
    pub width: u32,
    pub height: u32,
    pub pixels: u64,
    pub luminance_mean: f64,
    pub luminance_std: f64,
    pub dark_fraction: f64,
    pub bright_fraction: f64,
    pub laplacian_variance: Option<f64>,
    pub rgb_sha256: String,
}
pub fn image_quality(bytes: &[u8], options: &ImageOptions) -> Result<ImageQuality> {
    let rgb = decode(bytes, options)?.into_rgb8();
    let (width, height) = rgb.dimensions();
    let count = u64::from(width) * u64::from(height);
    if count == 0 {
        return Err(invalid("empty image"));
    }
    let mut gray = Vec::with_capacity(count as usize);
    let (mut dark, mut bright) = (0u64, 0u64);
    for pixel in rgb.pixels() {
        let y = 0.2126 * f64::from(pixel[0])
            + 0.7152 * f64::from(pixel[1])
            + 0.0722 * f64::from(pixel[2]);
        gray.push(y);
        dark += u64::from(y <= f64::from(options.dark_threshold));
        bright += u64::from(y >= f64::from(options.bright_threshold));
    }
    let mean = gray
        .chunks(256)
        .map(|chunk| chunk.iter().sum::<f64>())
        .sum::<f64>()
        / count as f64;
    let m2 = gray
        .chunks(256)
        .map(|chunk| chunk.iter().map(|&v| (v - mean) * (v - mean)).sum::<f64>())
        .sum::<f64>();
    let laplacian_variance = if width >= 3 && height >= 3 {
        let w = width as usize;
        let n = (width as usize - 2) * (height as usize - 2);
        let lap = |i: usize| gray[i - w] + gray[i + w] + gray[i - 1] + gray[i + 1] - 4.0 * gray[i];
        let mut sum = 0.0;
        for y in 1..height as usize - 1 {
            for x in 1..w - 1 {
                sum += lap(y * w + x);
            }
        }
        let average = sum / n as f64;
        let mut variance = 0.0;
        for y in 1..height as usize - 1 {
            for x in 1..w - 1 {
                let delta = lap(y * w + x) - average;
                variance += delta * delta;
            }
        }
        Some(variance / n as f64)
    } else {
        None
    };
    let mut hash = Sha256::new();
    hash.update(width.to_le_bytes());
    hash.update(height.to_le_bytes());
    hash.update(rgb.as_raw());
    Ok(ImageQuality {
        width,
        height,
        pixels: count,
        luminance_mean: mean,
        luminance_std: (m2 / count as f64).sqrt(),
        dark_fraction: dark as f64 / count as f64,
        bright_fraction: bright as f64 / count as f64,
        laplacian_variance,
        rgb_sha256: format!("{:x}", hash.finalize()),
    })
}

#[derive(Clone, Copy, Debug)]
pub enum ResizeFilter {
    Nearest,
    Triangle,
    Lanczos3,
}
pub fn transform_image(
    bytes: &[u8],
    options: &ImageOptions,
    crop: Option<[u32; 4]>,
    resize: Option<[u32; 2]>,
    filter: ResizeFilter,
) -> Result<Vec<u8>> {
    let mut image = decode(bytes, options)?;
    if let Some([x, y, width, height]) = crop {
        if width == 0
            || height == 0
            || x.checked_add(width).is_none_or(|v| v > image.width())
            || y.checked_add(height).is_none_or(|v| v > image.height())
        {
            return Err(invalid("crop outside image"));
        }
        image = image.crop_imm(x, y, width, height);
    }
    if let Some([width, height]) = resize {
        if width == 0
            || height == 0
            || width > options.max_width
            || height > options.max_height
            || u64::from(width) * u64::from(height) > options.max_pixels
        {
            return Err(invalid("resize exceeds image limits"));
        }
        image = image.resize_exact(
            width,
            height,
            match filter {
                ResizeFilter::Nearest => FilterType::Nearest,
                ResizeFilter::Triangle => FilterType::Triangle,
                ResizeFilter::Lanczos3 => FilterType::Lanczos3,
            },
        );
    }
    let mut output = Cursor::new(Vec::new());
    image.write_to(&mut output, ImageFormat::Png)?;
    Ok(output.into_inner())
}
