from common import *

RECIPES=[]
def add(op,fn,method,transform,lesson):RECIPES.append(candidate(op,MCAP,fn,method,transform,lesson))


for size in (4096,16384,32768,131072):
    add('raw_reader','open',f'read MCAP through a {size}-byte buffer',lambda s,n=size:replace(s,
        'BufReader::new(file)',f'BufReader::with_capacity({n},file)'),
        'The prior 64 KiB buffer failed; measure different bounded sizes with CRCs and full-file limits unchanged.')


def raw_cache(sources,kind):
    text=re.sub(r'(?ms)^\s*// TEN_CACHE_START\n.*?^\s*// TEN_CACHE_END\n','',sources[MCAP])
    frozen=original(MCAP);a,b=function_span(frozen,'next');next_fn=frozen[a:b]
    arc="std::sync::Arc<mcap::Channel<'static>>"
    if kind=='arc':
        field=f'Option<({arc},bool)>';initial='None'
        known='self.topic_cache.as_ref().filter(|(channel,_)|std::sync::Arc::ptr_eq(channel,&message.channel)).map(|(_,value)|*value)'
        remember='self.topic_cache=Some((message.channel.clone(),value));'
    elif kind=='map':
        field=f'std::collections::BTreeMap<u16,({arc},bool)>';initial='std::collections::BTreeMap::new()'
        known='self.topic_cache.get(&message.channel.id).filter(|(channel,_)|std::sync::Arc::ptr_eq(channel,&message.channel)).map(|(_,value)|*value)'
        remember='self.topic_cache.insert(message.channel.id,(message.channel.clone(),value));'
    elif kind=='text':
        field='Option<(String,bool)>';initial='None'
        known='self.topic_cache.as_ref().filter(|(topic,_)|topic==&message.channel.topic).map(|(_,value)|*value)'
        remember='self.topic_cache=Some((message.channel.topic.clone(),value));'
    else:
        field='Option<std::collections::HashSet<String>>';initial='topic_cache'
    text=replace(text,'    done: bool,',f'    done: bool,\n    // TEN_CACHE_START\n    topic_cache: {field},\n    // TEN_CACHE_END')
    text=replace(text,'            done: false,',f'            done: false,\n            // TEN_CACHE_START\n            topic_cache: {initial},\n            // TEN_CACHE_END')
    time='''let t=if self.filter.publish_clock {message.publish_time} else {message.log_time};
                        topic_matches && self.filter.start_ns.is_none_or(|s|t>=s) && self.filter.end_ns.is_none_or(|e|t<e)'''
    if kind=='set':
        text=replace(text,'        Ok(Self {','''        // TEN_CACHE_START
        let topic_cache=if filter.topics.len()>=16 {Some(filter.topics.iter().cloned().collect())} else {None};
        // TEN_CACHE_END
        Ok(Self {''')
        expression='''if let Some(topics)=&self.topic_cache {
                        let topic_matches=topics.contains(&message.channel.topic);
                        '''+time+'''
                    } else {self.filter.accepts(&message)}'''
    else:
        expression=f'''if self.filter.topics.is_empty() {{self.filter.accepts(&message)}} else {{
                        let known={known};
                        let topic_matches=known.unwrap_or_else(|| {{
                            let value=self.filter.topics.contains(&message.channel.topic);
                            {remember}
                            value
                        }});
                        {time}
                    }}'''
    next_fn=replace(next_fn,'                    if self.filter.accepts(&message) {',
        f'                    let accepted={expression};\n                    if accepted {{')
    sources[MCAP]=replace_function(text,'next',next_fn)
for kind,method in [('arc','cache topic selection for the last immutable channel'),
                    ('map','cache topic selection by channel identity in a small ordered map'),
                    ('text','cache topic selection for the last exact topic string'),
                    ('set','hash long exact-topic filters once per reader')]:
    RECIPES.append(dict(operator='raw_reader',paths=[MCAP],apply=lambda sources,k=kind:raw_cache(sources,k),
        cases=CASES['raw_reader'],method=method,
        lesson='Cache only topic membership; every message still checks its own clock bounds, CRC path, count limit and source identity. Mixed-channel fixtures guard against single-topic overfitting.',
        hotspot='Repeated exact topic membership scans occur for every selected or rejected message.'))
RECIPES += [hint('raw_reader',MCAP,'accepts',k) for k in ('always','never')]


add('mcap_inspect','inspect_mcap','accumulate per-channel clocks in a hash map',lambda s:s.replace('BTreeMap','std::collections::HashMap'),
    'Final channel ordering comes from the complete u16 scan, so the accumulator container need not provide ordering.')
def inspect_sorted(s):
    frozen=original(MCAP);a,b=function_span(frozen,'inspect_mcap');s=frozen[a:b]
    s=replace(s,'let mut times: BTreeMap<u16, (Vec<i64>, Vec<i64>, u64)> = BTreeMap::new();',
        'let mut times:Vec<(u16,(Vec<i64>,Vec<i64>,u64))>=Vec::new();')
    s=replace(s,'let (logs, pubs, bytes) = times.entry(message.channel.id).or_default();',
        '''let index=match times.binary_search_by_key(&message.channel.id,|(id,_)|*id) {
            Ok(i)=>i,Err(i)=>{times.insert(i,(message.channel.id,Default::default()));i}
        };
        let (logs,pubs,bytes)=&mut times[index].1;''')
    return replace(s,'times.remove(&id).unwrap_or_default()',
        'times.binary_search_by_key(&id,|(id,_)|*id).ok().map(|i|std::mem::take(&mut times[i].1)).unwrap_or_default()')
add('mcap_inspect','inspect_mcap','store channel accumulators in a sorted compact vector',inspect_sorted,
    'Keep storage proportional to present channels rather than allocating a 65536-slot table for sparse IDs.')
def inspect_same_clocks(s):
    s=replace(s,'(Vec<i64>, Vec<i64>, u64)','(Vec<i64>, Option<Vec<i64>>, u64)')
    s=replace(s,'''        logs.push(log);
        pubs.push(publish);''','''        if publish!=log || pubs.is_some() {pubs.get_or_insert_with(||logs.clone()).push(publish);}
        logs.push(log);''')
    s=replace(s,'        channels.push(ChannelReport {',
        '''        let log_time=inspect_time(&logs,max_gap_ns)?;
        let publish_time=match pubs {Some(pubs)=>inspect_time(&pubs,max_gap_ns)?,None=>log_time.clone()};
        channels.push(ChannelReport {''')
    s=replace(s,'log_time: inspect_time(&logs, max_gap_ns)?,','log_time,')
    return replace(s,'publish_time: inspect_time(&pubs, max_gap_ns)?,','publish_time,')
add('mcap_inspect','inspect_mcap','materialize a publish-clock vector only after it differs',inspect_same_clocks,
    'The old post-hoc equality scan failed; avoid the duplicate vector during ingestion and clone prior logs exactly at the first divergence.')
def inspect_reserve(s,size):
    frozen=original(MCAP);a,b=function_span(frozen,'inspect_mcap');s=frozen[a:b]
    return replace(s,'times.entry(message.channel.id).or_default()',
        f'times.entry(message.channel.id).or_insert_with(||(Vec::with_capacity({size}),Vec::with_capacity({size}),0))')
for size in (8,32):
    add('mcap_inspect','inspect_mcap',f'reserve {size} clock points for each observed channel',lambda s,n=size:inspect_reserve(s,n),
        'Keep initial per-channel memory small and proportional to observed channels while measuring growth overhead.')
def inspect_chunks(s,width):
    if 'let slots:' in s:
        s=re.sub(r'\.step_by\(\d+\)',f'.step_by({width})',s)
        return re.sub(r'slots:\s*\[_;\s*\d+\]',f'slots: [_; {width}]',s)
    s=replace(s,'''    for id in 0..=u16::MAX {
        let Some(channel) = reader.reader.get_channel(id) else {
            continue;
        };''',f'''    for base in (0u32..65536).step_by({width}) {{
        let slots: [_; {width}]=std::array::from_fn(|index|reader.reader.get_channel((base+index as u32) as u16));
        for (offset,channel) in slots.into_iter().enumerate() {{
        let id=(base+offset as u32) as u16;
        let Some(channel)=channel else {{continue;}};''')
    return replace(s,'    }\n    Ok(McapReport {','        }\n    }\n    Ok(McapReport {')
for size in (8,32):
    add('mcap_inspect','inspect_mcap',f'group complete channel lookups in blocks of {size}',lambda s,n=size:inspect_chunks(s,n),
        'The library exposes get_channel but no channel iterator; preserve empty channels and all IDs while exposing independent lookups.')
RECIPES += [hint('mcap_inspect',MCAP,'inspect_mcap',k) for k in ('always','never')]
add('mcap_inspect','inspect_mcap','reserve report storage for observed channel count',lambda s:replace(s,
    'let mut channels = Vec::new();','let mut channels = Vec::with_capacity(times.len());'),
    'Observed channels provide a bounded lower estimate; empty channels are still discovered and emitted by the full scan.')


def json_nested(s):
    a=s.index('        let lookup =');b=s.index('        let timestamp_ns',a)
    return s[:a]+'''        let lookup=|pointer:&str| {
            if let Some(path)=pointer.strip_prefix('/') {
                if !path.contains('~') {
                    let mut value=&payload;
                    for token in path.split('/') {
                        value=match value {
                            serde_json::Value::Object(object)=>object.get(token)?,
                            serde_json::Value::Array(array)=>{
                                if token.starts_with('+') || (token.starts_with('0') && token.len()>1) {return None;}
                                array.get(token.parse::<usize>().ok()?)?
                            },_=>return None,
                        };
                    }
                    return Some(value);
                }
            }
            payload.pointer(pointer)
        };
'''+s[b:]
add('json_decode','decode','traverse unescaped JSON pointer segments without allocating strings',json_nested,
    'The flat-pointer fast path helped; extend it to nested object/array segments while retaining RFC6901 escapes and index rules.')
add('json_decode','decode','reserve each resolved numeric array before flattening it',lambda s:replace(s,
    '            if let Some(array) = value.as_array() {',
    '            if let Some(array) = value.as_array() {\n                values.reserve(array.len());'),
    'Payload array lengths are already known and bounded by the decoded record; avoid repeated output-vector growth.')
add('json_decode','decode','parse known UTF-8 JSON through the string parser',lambda s:replace(s,
    'let payload: serde_json::Value = serde_json::from_slice(&message.data)?;',
    '''let payload:serde_json::Value=match std::str::from_utf8(&message.data) {
            Ok(text)=>serde_json::from_str(text)?,Err(_)=>serde_json::from_slice(&message.data)?,
        };'''),'Keep the original byte-parser errors for invalid UTF-8; measure the string parser only when UTF-8 validation succeeds.')
def json_single_array(s):
    return replace(s,'        let mut values =', '''        if self.fields.len()==1 {
            let pointer=&self.fields[0];
            if let Some(array)=lookup(pointer).and_then(|v|v.as_array()).filter(|v|v.len()==self.channels) {
                let values=array.iter().map(|v|v.as_f64()).collect::<Option<Vec<_>>>()
                    .ok_or_else(||invalid(format!("nonnumeric array at {pointer}")))?;
                return Ok(vec![DecodedSample{timestamp_ns,values}]);
            }
        }
        let mut values =''')
add('json_decode','decode','collect a single correctly sized numeric array directly',json_single_array,
    'Preserve validation and error precedence; only the common one-field array path skips generic flattening bookkeeping.')
for size in (8,16,64):
    add('json_decode','decode',f'cap initial decoded-field capacity at {size}',
        lambda s,n=size:replace(s,'let mut values = Vec::new();',f'let mut values = Vec::with_capacity(self.channels.min({n}));'),
        'The prior broad reserve failed on short arrays; compare bounded capacities with a 64-channel payload case.')
RECIPES += [hint('json_decode',MCAP,'decode',k) for k in ('always','never')]
add('json_decode','decode','detect reserved JSON pointer characters with byte searches',lambda s:replace(s,
    "!key.contains(['/', '~'])", "!key.as_bytes().contains(&b'/') && !key.as_bytes().contains(&b'~')"),
    'Reserved pointer syntax is ASCII; retain Unicode keys unchanged while comparing byte-search lowering.')


def read_reserve(s,size):
    s=replace(s,'    if decoder.channels() == 0 || max_samples == 0 {',
        '    let initial_channels=decoder.channels();\n    if initial_channels == 0 || max_samples == 0 {')
    s=replace(s,'let mut timestamps = Vec::new();',f'let mut timestamps = Vec::with_capacity(max_samples.min({size}));')
    return replace(s,'let mut values = Vec::new();',f'let mut values = Vec::with_capacity(max_samples.min({size}).saturating_mul(initial_channels).min(65536));')
for size in (512,1024,8192):
    add('mcap_read_signal','read_signal',f'bound initial decoded signal capacity to {size} samples',lambda s,n=size:read_reserve(s,n),
        'The prior 4096-sample reserve did not help; sweep different bounded allocations across single/multi-channel files.')
add('mcap_read_signal','read_signal','copy decoded row slices into accumulated values',lambda s:replace(s,
    'values.extend(sample.values);','values.extend_from_slice(&sample.values);'),
    'Compare slice extension with consuming Vec iteration; keep every decoded row and channel-count check.')
add('mcap_read_signal','read_signal','reuse the first decoded value vector as output storage',lambda s:replace(s,
    'values.extend(sample.values);','if values.is_empty() {values=sample.values;} else {values.extend(sample.values);}'),
    'Transfer already owned storage once instead of allocating a second initial vector.')
def read_batch_reserve(s):
    s=replace(s,'    if decoder.channels() == 0 || max_samples == 0 {',
        '    let initial_channels=decoder.channels();\n    if initial_channels == 0 || max_samples == 0 {')
    return replace(s,'        for sample in decoder.decode(&item?)? {', '''        let batch=decoder.decode(&item?)?;
        let reserve=batch.len().min(max_samples.saturating_sub(timestamps.len())).min(1024);
        timestamps.reserve(reserve);
        values.reserve(reserve.saturating_mul(initial_channels).min(65536));
        for sample in batch {''')
add('mcap_read_signal','read_signal','reserve bounded space for each decoded message batch',read_batch_reserve,
    'Respect remaining sample limits before reserving; retain per-sample errors and exact source iteration.')
add('mcap_read_signal','read_signal','consume decoded messages through a borrowed cursor iterator',lambda s:replace(s,
    '    for item in RawReader::open(path, filter, limits)? {',
    '    let mut reader=RawReader::open(path,filter,limits)?;\n    for item in std::iter::from_fn(||reader.next()) {'),
    'Measure iterator lowering without early termination or changing full-file validation.')
RECIPES += [hint('mcap_read_signal',MCAP,'read_signal',k) for k in ('always','never')]
def read_fold(s):
    frozen=original(MCAP);a,b=function_span(frozen,'read_signal');s=frozen[a:b]
    a=s.index('    let mut timestamps =');b=s.index('    if timestamps.is_empty()',a)
    middle=s[a:b]
    loop=middle[middle.index('        for sample'):]
    loop=loop[:loop.rfind('    }')]
    return s[:a]+'''    let (timestamps,values)=RawReader::open(path,filter,limits)?.try_fold((Vec::new(),Vec::new()),|(mut timestamps,mut values),item| {
'''+loop+'''        Ok::<_,crate::Error>((timestamps,values))
    })?;
'''+s[b:]
add('mcap_read_signal','read_signal','accumulate decoded samples through a fallible fold',read_fold,
    'Keep the shared decoder seam and all errors, while comparing ownership-aware iteration with the ordinary loop.')


# Container alternatives can make the original import unused; repair that shared seam once.
for recipe in RECIPES:
    apply=recipe['apply']
    def with_imports(sources,apply=apply):
        apply(sources)
        text=sources[MCAP].replace('    collections::BTreeMap,\n','')
        if re.search(r'(?<!:)\bBTreeMap\b',text):
            text=replace(text,'use std::{','use std::{\n    collections::BTreeMap,')
        sources[MCAP]=text
    recipe['apply']=with_imports
