from common import *

WRAPPER='python/mcap_ops/__init__.py'
RECIPES=[]
def add(fn,method,transform,lesson):
    item=candidate('python_bridge',PYTHON,fn,method,transform,lesson)
    item['python']=True;RECIPES.append(item)


add('numpy_values','write canonical non-finite outputs with branchless selection',lambda s:replace(s,
    '''        if !value.is_finite() {
            *value = f64::NAN;
        }''','''        *value=if value.is_finite() {*value} else {f64::NAN};'''),
    'Preserve canonical NaNs and independent owned outputs while testing vectorizable stores.')
def numpy_blocks(s,size):
    a=s.index('    for value in &mut values {');b=s.index('    values.into_pyarray',a)
    steps=''.join(f'        row[{i}]=if row[{i}].is_finite() {{row[{i}]}} else {{f64::NAN}};\n' for i in range(size))
    return s[:a]+f'''    let mut chunks=values.chunks_exact_mut({size});
    for row in chunks.by_ref() {{
{steps}    }}
    for value in chunks.into_remainder() {{if !value.is_finite() {{*value=f64::NAN;}}}}
'''+s[b:]
for size in (4,8):
    add('numpy_values',f'sanitize NumPy output values in {size}-element blocks',lambda s,n=size:numpy_blocks(s,n),
        'Keep exact non-finite handling; compare bounded loop unrolling on both large and small public calls.')
add('numpy_values','bypass the sanitizing write pass for all-finite outputs',lambda s:replace(
    replace(s,'    for value in &mut values {','    if !values.iter().all(|v|v.is_finite()) {\n    for value in &mut values {'),
    '    values.into_pyarray(py)','    }\n    values.into_pyarray(py)'),
    'Most transformed outputs are finite; preserve the full fallback for any NaN or infinity.')
add('filtered_dict','use static Python filter-mode names instead of formatting',lambda s:replace(s,
    'format!("{:?}", result.mode).to_lowercase()',
    'match result.mode {filter::FilterMode::Causal=>"causal",filter::FilterMode::Centered=>"centered"}'),
    'The enum has two fixed public spellings; avoid a temporary formatted lowercase String.')
def intern_keys(sources):
    text,count=re.subn(r'\.set_item\("([a-z_]+)"',lambda m:f'.set_item(pyo3::intern!(py,"{m.group(1)}")',sources[PYTHON])
    assert count>10
    sources[PYTHON]=text
RECIPES.append(dict(operator='python_bridge',paths=[PYTHON],apply=intern_keys,python=True,cases=CASES['python_bridge'],
    method='intern fixed Python result-dictionary keys',
    lesson='Reuse the installed PyO3 intern macro for a bounded set of static keys; preserve result order and values.',
    hotspot='Every small public call constructs the same Python key strings repeatedly.'))
add('signal_from_arrays','copy strided inputs through ndarray standard-layout ownership',lambda s:replace(s,
    '        array.iter().copied().collect()',
    '''        let (flat,offset)=array.as_standard_layout().into_owned().into_raw_vec_and_offset();
        debug_assert_eq!(offset.unwrap_or(0),0);
        flat'''),
    'Keep input snapshots and logical row-major order; compare ndarray copying with scalar iteration for strided and reversed views.')
RECIPES += [dict(hint('python_bridge',PYTHON,'numpy_values',k),python=True) for k in ('always','never')]
def numpy_import(sources):
    text=replace(sources[WRAPPER],'import json\n','import json\nimport numpy as np\n')
    sources[WRAPPER]=text.replace('    import numpy as np\n','')
RECIPES.append(dict(operator='python_bridge',paths=[WRAPPER],apply=numpy_import,python=True,cases=CASES['python_bridge'],
    method='reuse the NumPy module binding across public wrapper calls',
    lesson='NumPy is already a required dependency; remove repeated local imports without changing exports or normalization.',
    hotspot='Small wrapper calls repeat module import lookups before normalizing already native arrays.'))
