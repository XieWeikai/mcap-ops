#!/usr/bin/env python3
"""Publish the committed source tree through a verified, fast-forward Git bundle."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
from remote_config import execution_target

ROOT=Path(__file__).resolve().parents[1]
RECEIVE=r'''
import hashlib,json,os,subprocess,sys
from pathlib import Path
manifest=json.load(sys.stdin)
root=Path(manifest["destination"]);os.chdir(root)
def git(*args):return subprocess.check_output(["git",*args],text=True).strip()
assert git("symbolic-ref","--short","HEAD")=="main"
old=git("rev-parse","HEAD")
subprocess.run(["git","fetch",manifest["bundle"],"main:refs/remotes/author/main"],check=True)
target=git("rev-parse","refs/remotes/author/main")
assert target==manifest["head"]
subprocess.run(["git","merge-base","--is-ancestor",old,target],check=True)
deleted=subprocess.check_output(["git","diff","--name-only","--diff-filter=D","-z",old,target]).decode().split("\0")
for name in filter(None,deleted):
    path=root/name
    if path.exists():
        assert path.is_file() and not path.is_symlink(),name
        original=subprocess.check_output(["git","show",f"{old}:{name}"])
        assert path.read_bytes()==original,f"deleted source changed unexpectedly: {name}"
        dest=root/".artifacts/rsi/superseded"/old/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert dest.read_bytes()==original
        os.replace(path,dest)
for name,expected in manifest["superseded"].items():
    path=root/name
    if path.exists():
        assert path.is_file() and not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
        dest=root/".artifacts/rsi/superseded"/path.name
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert dest.read_bytes()==path.read_bytes()
        os.replace(path,dest)
for name,expected in manifest["files"].items():
    path=root/name
    assert path.is_file() and not path.is_symlink(),name
    assert path.resolve().is_relative_to(root),name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
untracked=subprocess.check_output(["git","ls-files","--others","--exclude-standard","-z"]).decode().split("\0")
assert all(not name or name in manifest["files"] for name in untracked),untracked
subprocess.run(["git","add","--all","--","."],check=True)
assert git("write-tree")==git("rev-parse",target+"^{tree}")
subprocess.run(["git","update-ref","-m","sync verified RSI source tree","refs/heads/main",target,old],check=True)
assert not git("status","--porcelain","--untracked-files=all")
print(json.dumps({"head":target,"tree":git("rev-parse","HEAD^{tree}"),"files":len(manifest["files"]),"clean":True,"target":manifest["target"]}))
'''


def main():
    host,remote=execution_target()
    if subprocess.check_output(["git","status","--porcelain","--untracked-files=all"],cwd=ROOT).strip():
        raise RuntimeError("commit the reviewed tree before publishing")
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    names=subprocess.check_output(["git","ls-files","-z"],cwd=ROOT).decode().split("\0")
    files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names if name}
    superseded={}
    for path in (ROOT/"docs/performance/history").glob("*-initial.json"):
        record=json.loads(path.read_text())
        old=f"docs/performance/results/{record['label']}.json"
        if old not in files:superseded[old]=hashlib.sha256(path.read_bytes()).hexdigest()
    subprocess.run([sys.executable,"scripts/sync_sources.py"],cwd=ROOT,check=True)
    bundle=ROOT/".artifacts/rsi"/f"source-{head[:12]}.bundle"
    subprocess.run(["git","bundle","create",str(bundle),"main"],cwd=ROOT,check=True)
    remote_bundle=f"{remote}/.artifacts/rsi/{bundle.name}"
    subprocess.run(["rsync","-az",str(bundle),f"{host}:{remote_bundle}"],check=True)
    payload={"head":head,"files":files,"superseded":superseded,"bundle":remote_bundle,
             "destination":remote,"target":{"host":host,"destination":remote}}
    result=subprocess.run(["ssh",host,shlex.join(["python3","-c",RECEIVE])],
        input=json.dumps(payload),text=True,check=True,capture_output=True)
    print(result.stdout.strip())
    (ROOT/".artifacts/rsi/sync-receipt.json").write_text(result.stdout)


if __name__=="__main__":main()
