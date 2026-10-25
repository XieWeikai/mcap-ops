#!/usr/bin/env python3
"""Materialize the immutable reference and isolated differential-test workspace."""
from pathlib import Path
import re
import subprocess

REV = "66248dacb608859d2cbd0f9f27227c65013a8027"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".artifacts/rsi"


def main():
    for name in ("core", "io"):
        dest = OUT / "reference" / name
        prefix = f"crates/{name}/"
        files = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", REV, prefix], cwd=ROOT, text=True
        ).splitlines()
        for filename in files:
            if not filename.startswith(prefix + "src/") and filename != prefix + "Cargo.toml":
                continue
            target = dest / filename[len(prefix):]
            content = subprocess.check_output(["git", "show", f"{REV}:{filename}"], cwd=ROOT)
            if filename.endswith("Cargo.toml"):
                text = content.decode().replace(f'name = "mcap-ops-{name}"', f'name = "mcap-ops-reference-{name}"')
                for field, value in (("version", '"0.1.0"'), ("edition", '"2021"'),
                                     ("rust-version", '"1.90"'), ("license", '"MIT"')):
                    text = re.sub(rf"(?m)^{re.escape(field)}\.workspace = true$",
                                  f"{field} = {value}", text)
                text = text.replace("serde.workspace = true", 'serde = {version="1", features=["derive"]}')
                text = text.replace("serde_json.workspace = true", 'serde_json = "1"')
                text = text.replace("thiserror.workspace = true", 'thiserror = "2"')
                text = text.replace("mcap-ops-core.workspace = true",
                    'mcap-ops-core = {package="mcap-ops-reference-core", path="../core"}')
                content = text.encode()
            if target.exists() and target.read_bytes() != content and target.name != "Cargo.toml":
                raise RuntimeError(f"immutable reference changed: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    validation = OUT / "validation"
    (validation / "src").mkdir(parents=True, exist_ok=True)
    (validation / "Cargo.toml").write_text('''[package]
name = "rsi-equivalence"
version = "0.0.0"
edition = "2021"
[workspace]
[dependencies]
before = {package="mcap-ops-reference-core", path="../reference/core"}
after = {package="mcap-ops-core", path="../../../crates/core"}
before_io = {package="mcap-ops-reference-io", path="../reference/io"}
after_io = {package="mcap-ops-io", path="../../../crates/io"}
serde_json = "1"
image = {version="0.25", default-features=false, features=["png","jpeg"]}
mcap = "0.26"
tempfile = "3"
[profile.release]
debug = 0
''')
    (validation / "src/main.rs").write_bytes((ROOT / "benchmarks/equivalence.rs").read_bytes())
    print(f"Reference {REV}; validation workspace: {validation}")


if __name__ == "__main__":
    main()
