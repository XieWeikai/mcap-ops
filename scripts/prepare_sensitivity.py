#!/usr/bin/env python3
"""Build a separate public-interface workload comparison against the extension baseline."""
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE="bc58f81bb2c3dc43676450ee6685d8015fb99081"
OUT=ROOT/".artifacts/rsi/extension/sensitivity"


def main():
    files=subprocess.check_output(["git","ls-tree","-r","--name-only",BASE,"crates/core"],cwd=ROOT,text=True).splitlines()
    for name in files:
        if not (name.startswith("crates/core/src/") or name == "crates/core/Cargo.toml"):continue
        content=subprocess.check_output(["git","show",f"{BASE}:{name}"],cwd=ROOT)
        dest=OUT/"reference"/name.removeprefix("crates/core/")
        if name.endswith("Cargo.toml"):
            value=content.decode().replace('name = "mcap-ops-core"','name = "mcap-ops-sensitivity-reference"')
            for field,literal in [("version",'"0.1.0"'),("edition",'"2021"'),("rust-version",'"1.90"'),("license",'"MIT"')]:
                value=re.sub(rf"(?m)^{re.escape(field)}\.workspace = true$",f"{field} = {literal}",value)
            value=value.replace("serde.workspace = true",'serde = {version="1",features=["derive"]}')
            value=value.replace("thiserror.workspace = true",'thiserror = "2"')
            content=value.encode()
        if dest.exists():assert dest.read_bytes()==content,"immutable reference changed"
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
    (OUT/"src").mkdir(parents=True,exist_ok=True)
    (OUT/"src/main.rs").write_bytes((ROOT/"benchmarks/sensitivity.rs").read_bytes())
    (OUT/"Cargo.toml").write_text(f'''[package]
name="rsi-sensitivity"
version="0.0.0"
edition="2021"
[workspace]
[dependencies]
before={{package="mcap-ops-sensitivity-reference",path="reference"}}
after={{package="mcap-ops-core",path="{ROOT}/crates/core"}}
serde_json="1"
[profile.release]
debug=1
''')
    for side in ["before","after"]:
        wrapper=OUT/side
        wrapper.write_text(f'#!/bin/sh\nexec "{ROOT}/target/reference/release/rsi-sensitivity" {side} "$@"\n')
        wrapper.chmod(0o755)
    print(OUT)


if __name__=="__main__":main()
