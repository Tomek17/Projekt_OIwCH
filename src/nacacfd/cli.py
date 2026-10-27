"""Command-line entry point: `nacacfd <command> ...`.

Status: argument parsing works; every command except `validate-config` is a stub (F2+).
"""

from __future__ import annotations

import argparse
import sys

from nacacfd import __version__
from nacacfd.config import load_experiment


def _not_implemented(args: argparse.Namespace) -> int:
    raise NotImplementedError(f"`nacacfd {args.command}` is not implemented yet (see PLAN.md)")


def _validate_config(args: argparse.Namespace) -> int:
    exp = load_experiment(args.experiment)
    print(f"OK: {exp.name}: {exp.airfoil}, {len(exp.alpha_deg)} angle(s), "
          f"Re={exp.reynolds:g}, M={exp.mach:g}, {exp.turbulence_model}, mesh={exp.mesh_level}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nacacfd", description=__doc__)
    parser.add_argument("--version", action="version", version=f"nacacfd {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate-config", help="check an experiment YAML")
    p.add_argument("experiment")
    p.set_defaults(func=_validate_config)

    for name, help_text in [
        ("mesh", "generate geometry and mesh for an experiment"),
        ("run", "run all cases of an experiment (mesh + solve + postprocess + QA)"),
        ("qa", "run QA gates on an existing runs/<experiment> directory"),
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
