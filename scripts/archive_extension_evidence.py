#!/usr/bin/env python3
"""Archive validation text and profile identities without storing huge raw profiles."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import argparse

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--series',default='extension',help='Evidence namespace under docs/performance')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]*',args.series):
        parser.error('series must start with a lowercase letter/digit and use only a-z0-9_.-')
    if args.series=='initial':
        parser.error('initial-series evidence uses the legacy report layout')
    report=ROOT/'docs/performance'/args.series
    records=sorted((report/'results').glob('*.json'))
    if not records:
        parser.error('series has no measured decisions to archive')
    out=report/'evidence'
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for record in records:
        decision=json.loads(record.read_text())
        label=decision["label"]
        trial=ROOT/".artifacts/rsi/trials"/label
        log=trial/"validation.log"
        assert hashlib.sha256(log.read_bytes()).hexdigest()==decision["validation_sha256"]
        shutil.copyfile(log,out/f"{label}.log")
        profiles=[]
        for path in sorted(trial.iterdir()):
            if path.suffix not in {".prof",".callgrind"}:continue
            item={"file":path.name,"bytes":path.stat().st_size,
                  "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                  "remote_path":f"./.artifacts/rsi/trials/{label}/{path.name}"}
            if path.suffix==".callgrind":
                match=re.search(r"(?m)^summary: (\d+)",path.read_text())
                if match:item["instruction_events"]=int(match.group(1))
            profiles.append(item)
        assert len(profiles)>=2,label
        for name in ["before-profile.txt","profile.txt"]:
            path=trial/name
            if path.exists():
                (out/f"{label}-{name}").write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()[:100])+"\n")
        rows.append({"label":label,"validation_sha256":decision["validation_sha256"],"profiles":profiles})
    (out/"manifest.json").write_text(json.dumps(rows,indent=2)+"\n")
    print(f"Archived validation logs and profile identities for {len(rows)} experiments")


if __name__=="__main__":main()
