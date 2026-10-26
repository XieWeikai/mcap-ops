#!/usr/bin/env python3
"""Materialize the campaign-start source with the completed benchmark harness on reference-linux."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE='9de19ead5df7444a9074c71028129b88970ba6ba'
OUT=ROOT/'.artifacts/rsi/per-op10/baseline'


def main():
    files=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    selected=[name for name in files if name in {'Cargo.toml','Cargo.lock','pyproject.toml','README.md','LICENSE'}
              or name.startswith('python/mcap_ops/') or (name.startswith('crates/') and (name.endswith('Cargo.toml') or '/src/' in name))]
    hashes={}
    for name in selected:
        content=subprocess.check_output(['git','show',f'{BASE}:{name}'],cwd=ROOT)
        path=OUT/name
        if path.exists():assert path.read_bytes()==content,f'immutable baseline changed: {name}'
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        hashes[name]=hashlib.sha256(content).hexdigest()
    name='crates/io/examples/operator_benchmark.rs'
    content=(ROOT/name).read_bytes();path=OUT/name
    if path.exists():assert path.read_bytes()==content,'benchmark harness changed after baseline freeze'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
    manifest={'source_commit':BASE,'source_sha256':hashes,'benchmark_sha256':hashlib.sha256(content).hexdigest(),
              'profile':'same Cargo workspace release profile; CARGO_PROFILE_RELEASE_DEBUG=1'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(OUT)


if __name__=='__main__':main()
