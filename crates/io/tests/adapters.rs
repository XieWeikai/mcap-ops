use mcap_ops_io::{mcap_ops::*,image_ops::*,video::*};
use std::{collections::BTreeMap,fs::File,io::Cursor,time::Duration};

fn fixture(path:&std::path::Path,encoding:&str) {
    let mut writer=mcap::WriteOptions::new().compression(None).create(File::create(path).unwrap()).unwrap();
    let schema=writer.add_schema("Test","jsonschema",br#"{"type":"object"}"#).unwrap();
    let channel=writer.add_channel(schema,"/state",encoding,&BTreeMap::new()).unwrap();
    writer.add_channel(0,"/empty","json",&BTreeMap::new()).unwrap();
    for (i,t) in [100u64,300,200].into_iter().enumerate() {
        writer.write_to_known_channel(&mcap::records::MessageHeader{channel_id:channel,sequence:i as u32,log_time:t,publish_time:t+1},
            format!(r#"{{"q":[{},{}],"t":{}}}"#,i,i+1,t+10).as_bytes()).unwrap();
    }
    writer.finish().unwrap();
}

#[test]
fn mcap_inspection_preserves_order_and_empty_channels() {
    let dir=tempfile::tempdir().unwrap();let path=dir.path().join("sample.mcap");fixture(&path,"json");
    let report=inspect_mcap(&path,MessageFilter::default(),ReadLimits::default(),150).unwrap();
    assert_eq!((report.scanned_messages,report.selected_messages),(3,3));
    assert_eq!(report.channels.len(),2);
    let state=report.channels.iter().find(|c|c.topic=="/state").unwrap();
    assert_eq!(state.log_time.reversals,1);assert_eq!(state.log_time.gaps,1);
    assert!(report.complete);
}

#[test]
fn topic_and_half_open_time_filter() {
    let dir=tempfile::tempdir().unwrap();let path=dir.path().join("sample.mcap");fixture(&path,"json");
    let filter=MessageFilter{topics:vec!["/state".into()],start_ns:Some(200),end_ns:Some(300),publish_clock:false};
    let messages=RawReader::open(&path,filter,ReadLimits::default()).unwrap().collect::<Result<Vec<_>,_>>().unwrap();
    assert_eq!(messages.len(),1);assert_eq!(messages[0].log_time,200);
}

#[test]
fn explicit_json_fields_and_payload_clock() {
    let dir=tempfile::tempdir().unwrap();let path=dir.path().join("sample.mcap");fixture(&path,"json");
    let spec=JsonSignalSpec{topic:"/state".into(),fields:vec!["/q".into()],channels:2,timestamp_pointer:Some("/t".into()),publish_clock:false};
    let s=read_signal(&path,MessageFilter::default(),ReadLimits::default(),&spec,10).unwrap();
    assert_eq!(s.timestamps(),&[110,310,210]);assert_eq!(s.values(),&[0.,1.,1.,2.,2.,3.]);
    assert!(s.require_ordered().is_err());
}

#[test]
fn unknown_encoding_and_schema_mismatch_fail_explicitly() {
    let dir=tempfile::tempdir().unwrap();let path=dir.path().join("sample.mcap");fixture(&path,"cdr");
    let spec=JsonSignalSpec{topic:"/state".into(),fields:vec!["/q".into()],channels:2,timestamp_pointer:None,publish_clock:false};
    assert!(read_signal(&path,MessageFilter::default(),ReadLimits::default(),&spec,10).is_err());
    assert!(inspect_mcap(&path,MessageFilter::default(),ReadLimits::default(),1000).is_ok());
}

#[test]
fn partial_scan_does_not_claim_success() {
    let dir=tempfile::tempdir().unwrap();let path=dir.path().join("sample.mcap");fixture(&path,"json");
    assert!(inspect_mcap(&path,MessageFilter::default(),ReadLimits{max_messages:1,..Default::default()},1000).is_err());
    let mut bytes=std::fs::read(&path).unwrap();bytes.truncate(bytes.len()-12);
    let bad=dir.path().join("bad.mcap");std::fs::write(&bad,bytes).unwrap();
    assert!(inspect_mcap(&bad,MessageFilter::default(),ReadLimits::default(),1000).is_err());
}

#[test]
fn corrupted_payload_is_caught_by_crc() {
    let dir=tempfile::tempdir().unwrap();let path=dir.path().join("sample.mcap");fixture(&path,"json");
    let mut bytes=std::fs::read(&path).unwrap();
    let index=bytes.windows(5).position(|v|v==b"\"q\":[").unwrap();bytes[index]=b'x';
    std::fs::write(&path,bytes).unwrap();
    assert!(inspect_mcap(&path,MessageFilter::default(),ReadLimits::default(),1000).is_err());
}

fn image_bytes(width:u32,height:u32)->Vec<u8> {
    let image=image::RgbImage::from_fn(width,height,|x,y|image::Rgb(if (x+y)%2==0 {[0,0,0]} else {[255,255,255]}));
    let mut out=Cursor::new(Vec::new());image::DynamicImage::ImageRgb8(image).write_to(&mut out,image::ImageFormat::Png).unwrap();out.into_inner()
}

#[test]
fn image_quality_and_geometry_are_real() {
    let bytes=image_bytes(8,8);let q=image_quality(&bytes,&ImageOptions::default()).unwrap();
    assert_eq!((q.width,q.height),(8,8));
    assert!((q.dark_fraction-0.5).abs()<1e-12);
    assert!((q.bright_fraction-0.5).abs()<1e-12);
    assert!(q.laplacian_variance.unwrap()>1000.);
    let transformed=transform_image(&bytes,&ImageOptions::default(),Some([0,0,4,4]),Some([2,2]),ResizeFilter::Nearest).unwrap();
    assert_eq!(image_quality(&transformed,&ImageOptions::default()).unwrap().width,2);
}

#[test]
fn image_limits_and_bad_crop_are_errors() {
    let bytes=image_bytes(8,8);
    assert!(image_quality(&bytes,&ImageOptions{max_pixels:32,..Default::default()}).is_err());
    assert!(transform_image(&bytes,&ImageOptions::default(),Some([7,7,4,4]),None,ResizeFilter::Nearest).is_err());
    assert!(image_quality(b"not png",&ImageOptions::default()).is_err());
}

#[test]
fn generated_video_is_fully_decoded() {
    let dir=tempfile::tempdir().unwrap();let path=dir.path().join("small.mkv");
    let output=std::process::Command::new("ffmpeg").args(["-nostdin","-v","error","-f","lavfi","-i","testsrc=size=64x48:rate=10","-frames:v","10","-c:v","ffv1"])
        .arg(&path).output().expect("FFmpeg required for the remote acceptance suite");
    assert!(output.status.success(),"{}",String::from_utf8_lossy(&output.stderr));
    let report=validate_video(&path,"ffmpeg","ffprobe",Duration::from_secs(30)).unwrap();
    assert!(report.complete && report.decoded);assert_eq!(report.decoded_frames,10);
    assert_eq!(report.probe["streams"][0]["width"],64);
}

#[test]
fn corrupt_media_and_missing_executable_fail() {
    let dir=tempfile::tempdir().unwrap();let path=dir.path().join("bad.mp4");std::fs::write(&path,b"bad").unwrap();
    assert!(probe_video(&path,"ffprobe",Duration::from_secs(5)).is_err());
    assert!(probe_video(&path,"/nonexistent/mcap-ops-ffprobe",Duration::from_secs(1)).is_err());
}
