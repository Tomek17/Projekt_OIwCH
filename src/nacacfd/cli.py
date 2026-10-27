"""Command-line entry point: `nacacfd <command> ...`.

Status: `validate-config`, `run` (file meshes) and `qa` implemented; `mesh` and `report` are stubs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nacacfd import __version__
from nacacfd.config import REPO_ROOT, load_experiment


def _not_implemented(args: argparse.Namespace) -> int:
    raise NotImplementedError(f"`nacacfd {args.command}` is not implemented yet (see PLAN.md)")


def _validate_config(args: argparse.Namespace) -> int:
    exp = load_experiment(args.experiment)
    print(f"OK: {exp.name}: {exp.airfoil}, {len(exp.alpha_deg)} angle(s), "
          f"Re={exp.reynolds:g}, M={exp.mach:g}, {exp.turbulence_model}, mesh={exp.mesh_level}")
    return 0


def _run(args: argparse.Namespace) -> int:
    from nacacfd.runner.case import case_name, run_case

    exp = load_experiment(args.target)
    out = Path(args.runs_dir) / exp.name
    worst = 0
    levels = exp.mesh_levels or [None]
    for alpha in exp.alpha_deg:
        for level in levels:
            name = case_name(alpha) + (f"_{level}" if level else "")
            r = run_case(exp, alpha, out / name, level)
            print(f"{exp.name}/{name}: status={r['status']} CL={r.get('CL')} CD={r.get('CD')} "
                  f"CM={r.get('CM')} iterations={r.get('iterations')} wall={r['wall_time_s']} s", flush=True)
            worst = worst or int(r["status"] != "valid")
    if exp.mesh_levels and "gci" in exp.required_gates:
        worst = _gci_for(exp, out) or worst
    return worst


def _gci_for(exp, out: Path) -> int:
    from nacacfd.config import load_thresholds
    from nacacfd.qa.gci import check_gci
    from nacacfd.qa.report import run_case_gates
    from nacacfd.runner.case import case_name

    thr = load_thresholds()
    worst = 0
    for alpha in exp.alpha_deg:
        g = check_gci(out, thr, case_name(alpha), levels=("fine", "medium", "coarse"))
        print(f"GCI {case_name(alpha)}: {g.outcome.value} {g.reason}", flush=True)
        for level in exp.mesh_levels:
            case = out / f"{case_name(alpha)}_{level}"
            (case / "experiment_gates.json").write_text(json.dumps([g.to_dict()], indent=2) + "\n")
            status = run_case_gates(case, exp.required_gates, thr)
            print(f"  {case.name}: {status}")
            worst = worst or int(status != "valid")
    return worst


def _gci(args: argparse.Namespace) -> int:
    exp = load_experiment(args.target)
    return _gci_for(exp, Path(args.runs_dir) / exp.name)


def _qa(args: argparse.Namespace) -> int:
    from nacacfd.qa.report import run_case_gates

    exp_dir = Path(args.target)
    worst = 0
    for case_dir in sorted(p for p in exp_dir.iterdir() if (p / "results.json").exists()):
        required = json.loads((case_dir / "qa_report.json").read_text())["required"] \
            if (case_dir / "qa_report.json").exists() else []
        status = run_case_gates(case_dir, required)
        print(f"{case_dir}: {status}")
        worst = worst or int(status != "valid")
    return worst


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nacacfd", description=__doc__)
    parser.add_argument("--version", action="version", version=f"nacacfd {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate-config", help="check an experiment YAML")
    p.add_argument("experiment")
    p.set_defaults(func=_validate_config)

    p = sub.add_parser("run", help="run all cases of an experiment (mesh + solve + QA); exit 1 unless all valid")
    p.add_argument("target")
    p.add_argument("--runs-dir", default=str(REPO_ROOT / "runs"))
    p.set_defaults(func=_run)

    p = sub.add_parser("gci", help="grid study: compute the GCI gate for an experiment with mesh_levels")
    p.add_argument("target")
    p.add_argument("--runs-dir", default=str(REPO_ROOT / "runs"))
    p.set_defaults(func=_gci)

    p = sub.add_parser("qa", help="re-run per-case QA gates on runs/<experiment>")
    p.add_argument("target")
    p.set_defaults(func=_qa)

    for name, help_text in [
        ("mesh", "generate geometry and mesh for an experiment"),
        ("report", "build polars, tables and figures from runs/<experiment>"),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("target")
        p.set_defaults(func=_not_implemented)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
