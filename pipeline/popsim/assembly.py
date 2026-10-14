"""The published default assembly.

Its seed is not chosen by us: it is derived from the drand public randomness beacon
(https://drand.love, mainnet "default" chain) at a time fixed in advance, so anyone can
verify that the 150 people were not cherry-picked:

    seed = first 8 hex digits of the beacon's randomness, as an unsigned 32-bit integer

`popsim seed --at <ISO time>` records the beacon round in assemblies/default.seed.json
(committed); `popsim assembly` draws the assembly with that seed using the TypeScript
CLI - the same code the website runs - and writes assemblies/default.json plus a copy
named after the model version.
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess

import httpx

from . import paths

DRAND = "https://api.drand.sh"
SEED_FILE = paths.ROOT / "assemblies" / "default.seed.json"
ASSEMBLY_SIZE = 150


def seed_from_drand(at: str) -> dict:
    when = dt.datetime.fromisoformat(at.replace("Z", "+00:00"))
    with httpx.Client(timeout=30) as client:
        info = client.get(f"{DRAND}/info").json()
        rnd = int((when.timestamp() - info["genesis_time"]) // info["period"]) + 1
        beacon = client.get(f"{DRAND}/public/{rnd}").json()
    record = {
        "beacon": "drand mainnet (beaconID: default)",
        "chain_hash": info["hash"],
        "time": when.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "round": beacon["round"],
        "randomness": beacon["randomness"],
        "derivation": "seed = int(randomness[:8], 16)",
        "seed": int(beacon["randomness"][:8], 16),
        "verify": f"{DRAND}/public/{beacon['round']}",
    }
    SEED_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEED_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def _draw(seed: int, out) -> None:
    cmd = [
        "npx", "--prefix", str(paths.ROOT / "packages" / "sampler"), "tsx",
        str(paths.ROOT / "packages" / "sampler" / "src" / "cli.ts"),
        "--model", str(paths.BUILD / "model.json"), "--seed", str(seed), "--n", str(ASSEMBLY_SIZE),
        "--format", "assembly", "--templates", str(paths.ROOT / "templates"), "--out", str(out),
    ]
    subprocess.run(cmd, check=True, cwd=paths.ROOT)


def make_assembly(seed: int | None = None) -> dict:
    if seed is None:
        seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))["seed"]
    out = paths.ROOT / "assemblies" / "default.json"
    _draw(seed, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    shutil.copyfile(out, out.with_name(f"default-{data['model_version']}.json"))
    return data


def check_assembly() -> bool:
    """Redraw the published assembly from its recorded seed and compare it byte for byte."""
    import tempfile
    from pathlib import Path

    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))["seed"]
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "assembly.json"
        _draw(seed, out)
        return out.read_bytes() == (paths.ROOT / "assemblies" / "default.json").read_bytes()
