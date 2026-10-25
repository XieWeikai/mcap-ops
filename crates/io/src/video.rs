use crate::{invalid, Result};
use serde::Serialize;
use std::{
    ffi::OsStr,
    fs::File,
    io::{Read, Seek, SeekFrom},
    path::Path,
    process::{Command, Stdio},
    time::{Duration, Instant},
};

const MAX_TOOL_OUTPUT: u64 = 2 * 1024 * 1024;

/// No shell interpolation. Temporary files avoid pipe backpressure deadlocks.
fn run_tool(program: &OsStr, args: &[&OsStr], timeout: Duration) -> Result<(String, String)> {
    if timeout.is_zero() || timeout > Duration::from_secs(86_400) {
        return Err(invalid("timeout must be in (0,86400] seconds"));
    }
    let mut stdout = tempfile::tempfile()?;
    let mut stderr = tempfile::tempfile()?;
    let mut child = Command::new(program)
        .args(args)
        .stdin(Stdio::null())
        .stdout(Stdio::from(stdout.try_clone()?))
        .stderr(Stdio::from(stderr.try_clone()?))
        .spawn()?;
    let started = Instant::now();
    let status = loop {
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) => {}
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(error.into());
            }
        }
        let bounded = match (stdout.metadata(), stderr.metadata()) {
            (Ok(a), Ok(b)) => a.len() <= MAX_TOOL_OUTPUT && b.len() <= MAX_TOOL_OUTPUT,
            _ => false,
        };
        if started.elapsed() > timeout || !bounded {
            let _ = child.kill();
            let _ = child.wait();
            return Err(invalid(
                "media tool timed out or exceeded diagnostic output limit",
            ));
        }
        std::thread::sleep(Duration::from_millis(10));
    };
    let read = |file: &mut File| -> Result<String> {
        if file.metadata()?.len() > MAX_TOOL_OUTPUT {
            return Err(invalid("media tool output too large"));
        }
        file.seek(SeekFrom::Start(0))?;
        let mut data = Vec::new();
        file.take(MAX_TOOL_OUTPUT + 1).read_to_end(&mut data)?;
        Ok(String::from_utf8_lossy(&data).into_owned())
    };
    let out = read(&mut stdout)?;
    let err = read(&mut stderr)?;
    if !status.success() {
        return Err(invalid(format!(
            "media tool failed ({status}): {}",
            err.chars().take(4096).collect::<String>()
        )));
    }
    Ok((out, err))
}

fn regular_file(path: &Path) -> Result<()> {
    if !path.is_file() {
        return Err(invalid("video input must be a regular local file"));
    }
    Ok(())
}

pub fn probe_video(
    path: impl AsRef<Path>,
    ffprobe: impl AsRef<OsStr>,
    timeout: Duration,
) -> Result<serde_json::Value> {
    let path = path.as_ref();
    regular_file(path)?;
    let (out, err) = run_tool(
        ffprobe.as_ref(),
        &[
            "-v".as_ref(),
            "error".as_ref(),
            "-protocol_whitelist".as_ref(),
            "file,pipe".as_ref(),
            "-select_streams".as_ref(),
            "v".as_ref(),
            "-show_streams".as_ref(),
            "-show_format".as_ref(),
            "-of".as_ref(),
            "json".as_ref(),
            "-i".as_ref(),
            path.as_os_str(),
        ],
        timeout,
    )?;
    if !err.trim().is_empty() {
        return Err(invalid(format!("ffprobe diagnostics: {err}")));
    }
    let report: serde_json::Value = serde_json::from_str(&out)?;
    if report["streams"].as_array().is_none_or(|v| v.is_empty()) {
        return Err(invalid("no video stream"));
    }
    Ok(report)
}

#[derive(Clone, Debug, Serialize)]
pub struct VideoValidation {
    pub complete: bool,
    pub decoded: bool,
    pub decoded_frames: u64,
    pub elapsed_seconds: f64,
    pub probe: serde_json::Value,
}

/// Complete first-video-stream decoding. This does not certify visual quality.
pub fn validate_video(
    path: impl AsRef<Path>,
    ffmpeg: impl AsRef<OsStr>,
    ffprobe: impl AsRef<OsStr>,
    timeout: Duration,
) -> Result<VideoValidation> {
    let path = path.as_ref();
    let started = Instant::now();
    let probe = probe_video(path, ffprobe, timeout)?;
    let (progress, err) = run_tool(
        ffmpeg.as_ref(),
        &[
            "-nostdin".as_ref(),
            "-v".as_ref(),
            "error".as_ref(),
            "-xerror".as_ref(),
            "-nostats".as_ref(),
            "-progress".as_ref(),
            "pipe:1".as_ref(),
            "-protocol_whitelist".as_ref(),
            "file,pipe".as_ref(),
            "-err_detect".as_ref(),
            "explode".as_ref(),
            "-i".as_ref(),
            path.as_os_str(),
            "-map".as_ref(),
            "0:v:0".as_ref(),
            "-an".as_ref(),
            "-f".as_ref(),
            "null".as_ref(),
            "-".as_ref(),
        ],
        timeout.saturating_sub(started.elapsed()),
    )?;
    if !err.trim().is_empty() {
        return Err(invalid(format!("decode diagnostics: {err}")));
    }
    let decoded_frames = progress
        .lines()
        .rev()
        .filter_map(|line| line.strip_prefix("frame="))
        .filter_map(|v| v.trim().parse::<u64>().ok())
        .next()
        .unwrap_or(0);
    if decoded_frames == 0 || !progress.lines().any(|line| line == "progress=end") {
        return Err(invalid("video produced no frames or no completion marker"));
    }
    Ok(VideoValidation {
        complete: true,
        decoded: true,
        decoded_frames,
        elapsed_seconds: started.elapsed().as_secs_f64(),
        probe,
    })
}
