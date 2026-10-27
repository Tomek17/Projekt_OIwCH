"""Run one case end to end inside the container: mesh -> config -> SU2_CFD -> results -> QA -> status.

Status: implemented (F2) for meshes from a file (mesh.source: file). Gmsh meshes: not yet.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from nacacfd.airfoil.su2_config import render_config, solver_settings
from nacacfd.config import REPO_ROOT
from nacacfd.qa.report import run_case_gates
from nacacfd.runner.convergence import read_history, read_su2_version, solver_reported_converged
from nacacfd.runner.metadata import collect_metadata, utc_now


class CaseExistsError(RuntimeError):
    """The case directory already has results; deleting results is a human checkpoint."""


def case_name(alpha_deg: float) -> str:
    return f"a{alpha_deg:+06.2f}"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def prepare_mesh(experiment, case_dir: Path) -> Path:
    mesh = experiment.mesh
    if mesh["source"] != "file":
        raise NotImplementedError("TODO F2b: Gmsh meshes (mesh.source: gmsh)")
    src = (REPO_ROOT / mesh["path"]).resolve()
    if not src.exists():
        raise FileNotFoundError(f"{src} not found; run scripts/fetch_meshes.sh")
    digest = _sha256(src)
    if digest != mesh["sha256"]:
        raise ValueError(f"sha256 mismatch for {src}: {digest} != {mesh['sha256']}")
    dst = case_dir / src.name
    shutil.copyfile(src, dst)
    return dst


def run_case(experiment, alpha_deg: float, case_dir) -> dict:
    """Run one case. Solver failures do not raise: they are recorded in results.json and fail the gates."""
    case_dir = Path(case_dir)
    if (case_dir / "results.json").exists():
        raise CaseExistsError(f"{case_dir} already has results; move it away yourself (agents must ask first)")
    case_dir.mkdir(parents=True, exist_ok=True)
    started = utc_now()

    mesh_path = prepare_mesh(experiment, case_dir)
    cfg = render_config(experiment, alpha_deg, mesh_path, case_dir / "config.cfg")
    n_procs = int(solver_settings(experiment)["n_procs"])

    env = dict(os.environ)
    if hasattr(os, "getuid") and os.getuid() == 0:  # Open MPI refuses root unless told explicitly
        env.update(OMPI_ALLOW_RUN_AS_ROOT="1", OMPI_ALLOW_RUN_AS_ROOT_CONFIRM="1")
    cmd = ["mpirun", "-np", str(n_procs), "SU2_CFD", cfg.name] if n_procs > 1 else ["SU2_CFD", cfg.name]
    t0 = time.monotonic()
    with open(case_dir / "solver.log", "w") as log:
        proc = subprocess.run(cmd, cwd=case_dir, stdout=log, stderr=subprocess.STDOUT, env=env)
    wall = time.monotonic() - t0

    results: dict = {"experiment": experiment.name, "case": case_dir.name, "alpha_deg": alpha_deg,
                     "mach": experiment.mach, "reynolds": experiment.reynolds,
                     "turbulence_model": experiment.turbulence_model,
                     "solver_exit_code": proc.returncode, "wall_time_s": round(wall, 2), "n_procs": n_procs}
    hist = case_dir / "history.csv"
    if hist.exists():
        h = read_history(hist)
        results.update({"CL": h["CL"][-1] if h.get("CL") else None,
                        "CD": h["CD"][-1] if h.get("CD") else None,
                        "CM": h["CMz"][-1] if h.get("CMz") else None,
                        "iterations": len(h.get("CL", []))})
    results["solver_reported_converged"] = solver_reported_converged(case_dir / "solver.log")
    (case_dir / "results.json").write_text(json.dumps(results, indent=2) + "\n")

    status = run_case_gates(case_dir, experiment.required_gates)

    meta = collect_metadata(case_dir, started_utc=started, finished_utc=utc_now(), command=cmd,
                            su2=read_su2_version(case_dir / "solver.log"), mesh_file=mesh_path.name,
                            mesh_sha256=experiment.mesh.get("sha256"))
    (case_dir / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    return json.loads((case_dir / "results.json").read_text()) | {"status": status}
