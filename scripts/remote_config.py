"""Read execution coordinates from local-only configuration or environment."""
import json
import os
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]


def execution_target(host=None, destination=None):
    path = ROOT / ".mcap-ops.local.json"
    config = json.loads(path.read_text()) if path.exists() else {}
    host = host or os.environ.get("MCAP_OPS_TEST_HOST") or config.get("host")
    destination = (
        destination or os.environ.get("MCAP_OPS_TEST_ROOT") or config.get("destination")
    )
    if not isinstance(host, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.@:-]*", host):
        raise ValueError("Set MCAP_OPS_TEST_HOST or host in .mcap-ops.local.json to an SSH destination")
    if (
        not isinstance(destination, str)
        or not re.fullmatch(r"/[a-zA-Z0-9_./-]+", destination)
        or ".." in PurePosixPath(destination).parts
        or str(PurePosixPath(destination)) == "/"
    ):
        raise ValueError("Set MCAP_OPS_TEST_ROOT or destination to an absolute project path without spaces")
    return host, str(PurePosixPath(destination))
