use crate::{invalid, Result};
use mcap::{io::MessageReader, sans_io::LinearReaderOptions, Message};
use mcap_ops_core::{
    time::{inspect_time, TimeStats},
    Signal,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs::{File, Metadata},
    io::BufReader,
    path::{Path, PathBuf},
};

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct MessageFilter {
    /// Exact topic matches. Empty selects all topics.
    pub topics: Vec<String>,
    /// Half-open interval in the selected MCAP clock.
    pub start_ns: Option<u64>,
    pub end_ns: Option<u64>,
    pub publish_clock: bool,
}
impl MessageFilter {
    fn validate(&self) -> Result<()> {
        if self.start_ns.zip(self.end_ns).is_some_and(|(a, b)| a > b) {
            return Err(invalid("filter start exceeds end"));
        }
        Ok(())
    }
    fn accepts(&self, m: &Message<'_>) -> bool {
        let t = if self.publish_clock {
            m.publish_time
        } else {
            m.log_time
        };
        (self.topics.is_empty() || self.topics.contains(&m.channel.topic))
            && self.start_ns.is_none_or(|s| t >= s)
            && self.end_ns.is_none_or(|e| t < e)
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct ReadLimits {
    pub max_record_bytes: usize,
    pub max_messages: usize,
}
impl Default for ReadLimits {
    fn default() -> Self {
        Self {
            max_record_bytes: 64 * 1024 * 1024,
            max_messages: 10_000_000,
        }
    }
}

/// Streaming, original-file-order iteration. Early stopping is not full-file validation.
pub struct RawReader {
    reader: MessageReader<BufReader<File>>,
    path: PathBuf,
    before: Metadata,
    filter: MessageFilter,
    limits: ReadLimits,
    seen: usize,
    done: bool,
    // Membership is reusable only while the immutable channel identity is unchanged.
    topic_cache: std::collections::BTreeMap<u16, (std::sync::Arc<mcap::Channel<'static>>, bool)>,
}
impl RawReader {
    pub fn open(path: impl AsRef<Path>, filter: MessageFilter, limits: ReadLimits) -> Result<Self> {
        filter.validate()?;
        if limits.max_messages == 0 || limits.max_record_bytes == 0 {
            return Err(invalid("read limits must be positive"));
        }
        let path = path.as_ref().to_path_buf();
        let file = File::open(&path)?;
        let before = file.metadata()?;
        if !before.is_file() {
            return Err(invalid("MCAP input must be a regular file"));
        }
        let options = LinearReaderOptions::default()
            .with_prevalidate_chunk_crcs(true)
            .with_validate_data_section_crc(true)
            .with_validate_summary_section_crc(true)
            .with_check_finishes_after_end_magic(true)
            .with_record_length_limit(limits.max_record_bytes);
        Ok(Self {
            reader: MessageReader::new_with_options(BufReader::new(file), options),
            path,
            before,
            filter,
            limits,
            seen: 0,
            done: false,
            topic_cache: std::collections::BTreeMap::new(),
        })
    }
    fn unchanged(&self) -> Result<()> {
        let now = std::fs::metadata(&self.path)?;
        if self.before.len() != now.len() || self.before.modified()? != now.modified()? {
            return Err(invalid("source changed during reading"));
        }
        #[cfg(unix)]
        {
            use std::os::unix::fs::MetadataExt;
            if self.before.ino() != now.ino()
                || self.before.dev() != now.dev()
                || self.before.ctime() != now.ctime()
                || self.before.ctime_nsec() != now.ctime_nsec()
            {
                return Err(invalid("source identity changed during reading"));
            }
        }
        Ok(())
    }
}
impl Iterator for RawReader {
    type Item = Result<Message<'static>>;
    fn next(&mut self) -> Option<Self::Item> {
        if self.done {
            return None;
        }
        loop {
            match self.reader.next() {
                Some(Ok(message)) => {
                    self.seen += 1;
                    if self.seen > self.limits.max_messages {
                        self.done = true;
                        return Some(Err(invalid(
                            "MCAP exceeds max_messages; no complete report produced",
                        )));
                    }
                    let accepted = if self.filter.topics.len() <= 1 {
                        self.filter.accepts(&message)
                    } else {
                        let known = self
                            .topic_cache
                            .get(&message.channel.id)
                            .filter(|(channel, _)| {
                                std::sync::Arc::ptr_eq(channel, &message.channel)
                            })
                            .map(|(_, value)| *value);
                        let topic_matches = known.unwrap_or_else(|| {
                            let value = self.filter.topics.contains(&message.channel.topic);
                            self.topic_cache
                                .insert(message.channel.id, (message.channel.clone(), value));
                            value
                        });
                        let t = if self.filter.publish_clock {
                            message.publish_time
                        } else {
                            message.log_time
                        };
                        topic_matches
                            && self.filter.start_ns.is_none_or(|s| t >= s)
                            && self.filter.end_ns.is_none_or(|e| t < e)
                    };
                    if accepted {
                        return Some(Ok(message));
                    }
                }
                Some(Err(error)) => {
                    self.done = true;
                    return Some(Err(error.into()));
                }
                None => {
                    self.done = true;
                    return self.unchanged().err().map(Err);
                }
            }
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct ChannelReport {
    pub channel_id: u16,
    pub topic: String,
    pub message_encoding: String,
    pub schema_name: Option<String>,
    pub schema_encoding: Option<String>,
    pub schema_sha256: Option<String>,
    pub payload_bytes: u64,
    pub log_time: TimeStats,
    pub publish_time: TimeStats,
}
#[derive(Clone, Debug, Serialize)]
pub struct McapReport {
    pub format: String,
    pub operator_version: String,
    pub source: String,
    pub file_bytes: u64,
    pub scanned_messages: usize,
    pub selected_messages: usize,
    pub complete: bool,
    pub crc_validation: String,
    pub filter: MessageFilter,
    pub channels: Vec<ChannelReport>,
}

pub fn inspect_mcap(
    path: impl AsRef<Path>,
    filter: MessageFilter,
    limits: ReadLimits,
    max_gap_ns: i64,
) -> Result<McapReport> {
    if max_gap_ns < 0 {
        return Err(invalid("max_gap_ns must be nonnegative"));
    }
    let path = path.as_ref();
    let mut reader = RawReader::open(path, filter.clone(), limits)?;
    let mut times: BTreeMap<u16, (Vec<i64>, Vec<i64>, u64)> = BTreeMap::new();
    let mut selected = 0;
    for item in reader.by_ref() {
        let message = item?;
        selected += 1;
        let log =
            i64::try_from(message.log_time).map_err(|_| invalid("log timestamp exceeds int64"))?;
        let publish = i64::try_from(message.publish_time)
            .map_err(|_| invalid("publish timestamp exceeds int64"))?;
        let (logs, pubs, bytes) = times.entry(message.channel.id).or_default();
        logs.push(log);
        pubs.push(publish);
        *bytes += message.data.len() as u64;
    }
    let mut channels = Vec::new();
    for id in 0..=u16::MAX {
        let Some(channel) = reader.reader.get_channel(id) else {
            continue;
        };
        if !filter.topics.is_empty() && !filter.topics.contains(&channel.topic) {
            continue;
        }
        let (logs, pubs, payload_bytes) = times.remove(&id).unwrap_or_default();
        channels.push(ChannelReport {
            channel_id: id,
            topic: channel.topic.clone(),
            message_encoding: channel.message_encoding.clone(),
            schema_name: channel.schema.as_ref().map(|s| s.name.clone()),
            schema_encoding: channel.schema.as_ref().map(|s| s.encoding.clone()),
            schema_sha256: channel
                .schema
                .as_ref()
                .map(|s| format!("{:x}", Sha256::digest(&s.data))),
            payload_bytes,
            log_time: inspect_time(&logs, max_gap_ns)?,
            publish_time: inspect_time(&pubs, max_gap_ns)?,
        });
    }
    Ok(McapReport {
        format: "mcap-ops-inspection-v1".into(),
        operator_version: env!("CARGO_PKG_VERSION").into(),
        source: path.display().to_string(),
        file_bytes: reader.before.len(),
        scanned_messages: reader.seen,
        selected_messages: selected,
        complete: true,
        crc_validation: "present chunk/data/summary CRCs; zero CRC means absent".into(),
        filter,
        channels,
    })
}

#[derive(Clone, Debug)]
pub struct DecodedSample {
    pub timestamp_ns: i64,
    pub values: Vec<f64>,
}
/// Source-specific payload semantics stay behind this seam.
pub trait SignalDecoder {
    fn channels(&self) -> usize;
    fn decode(&self, message: &Message<'_>) -> Result<Vec<DecodedSample>>;
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct JsonSignalSpec {
    pub topic: String,
    /// RFC 6901 JSON pointers; each resolves to a number or a flat numeric array.
    pub fields: Vec<String>,
    pub channels: usize,
    /// Optional integer-nanosecond payload pointer; otherwise use selected MCAP clock.
    #[serde(default)]
    pub timestamp_pointer: Option<String>,
    #[serde(default)]
    pub publish_clock: bool,
}
impl SignalDecoder for JsonSignalSpec {
    fn channels(&self) -> usize {
        self.channels
    }
    fn decode(&self, message: &Message<'_>) -> Result<Vec<DecodedSample>> {
        if message.channel.topic != self.topic {
            return Ok(Vec::new());
        }
        if message.channel.message_encoding != "json" {
            return Err(invalid("JSON decoder requires message_encoding=json; use a schema adapter for CDR/Protobuf"));
        }
        if self.fields.is_empty()
            || self.channels == 0
            || self.fields.iter().any(|p| !p.starts_with('/'))
        {
            return Err(invalid(
                "nonempty JSON pointers and positive channels required",
            ));
        }
        let payload: serde_json::Value = serde_json::from_slice(&message.data)?;
        let lookup = |pointer: &str| {
            if let Some(path) = pointer.strip_prefix('/') {
                if !path.contains('~') {
                    let mut value = &payload;
                    for token in path.split('/') {
                        value = match value {
                            serde_json::Value::Object(object) => object.get(token)?,
                            serde_json::Value::Array(array) => {
                                if token.starts_with('+')
                                    || (token.starts_with('0') && token.len() > 1)
                                {
                                    return None;
                                }
                                array.get(token.parse::<usize>().ok()?)?
                            }
                            _ => return None,
                        };
                    }
                    return Some(value);
                }
            }
            payload.pointer(pointer)
        };
        let timestamp_ns = if let Some(pointer) = &self.timestamp_pointer {
            lookup(pointer)
                .and_then(|v| v.as_i64())
                .ok_or_else(|| invalid("timestamp pointer must resolve to int64 nanoseconds"))?
        } else {
            i64::try_from(if self.publish_clock {
                message.publish_time
            } else {
                message.log_time
            })
            .map_err(|_| invalid("MCAP timestamp exceeds int64"))?
        };
        let mut values = Vec::new();
        for pointer in &self.fields {
            let value =
                lookup(pointer).ok_or_else(|| invalid(format!("missing field {pointer}")))?;
            if let Some(array) = value.as_array() {
                for v in array {
                    values.push(
                        v.as_f64()
                            .ok_or_else(|| invalid(format!("nonnumeric array at {pointer}")))?,
                    );
                }
            } else {
                values.push(
                    value
                        .as_f64()
                        .ok_or_else(|| invalid(format!("nonnumeric field {pointer}")))?,
                );
            }
        }
        if values.len() != self.channels {
            return Err(invalid(format!(
                "decoded {} channels, expected {}",
                values.len(),
                self.channels
            )));
        }
        Ok(vec![DecodedSample {
            timestamp_ns,
            values,
        }])
    }
}

pub fn read_signal(
    path: impl AsRef<Path>,
    filter: MessageFilter,
    limits: ReadLimits,
    decoder: &dyn SignalDecoder,
    max_samples: usize,
) -> Result<Signal> {
    if decoder.channels() == 0 || max_samples == 0 {
        return Err(invalid("positive channels and max_samples required"));
    }
    let mut timestamps = Vec::new();
    let mut values = Vec::new();
    for item in RawReader::open(path, filter, limits)? {
        for sample in decoder.decode(&item?)? {
            if timestamps.len() >= max_samples {
                return Err(invalid("decoded signal exceeds max_samples"));
            }
            if sample.values.len() != decoder.channels() {
                return Err(invalid("decoder returned inconsistent channel count"));
            }
            timestamps.push(sample.timestamp_ns);
            values.extend(sample.values);
        }
    }
    if timestamps.is_empty() {
        return Err(invalid("no decoded samples matched the requested signal"));
    }
    Ok(Signal::new(timestamps, values, decoder.channels())?)
}
