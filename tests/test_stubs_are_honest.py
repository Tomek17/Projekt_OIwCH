"""Every unimplemented function must raise NotImplementedError instead of returning something fake.

When a function is implemented, remove it from this list in the same commit and add real tests.
"""

import importlib

import pytest

STUBS = {
    "nacacfd.airfoil.naca": ["naca5_coordinates"],
    "nacacfd.runner.sweep": ["run_sweep"],
    "nacacfd.postprocess.polars": ["collect_polar"],
    "nacacfd.postprocess.plots": ["plot_polar"],
    "nacacfd.postprocess.compare": ["load_reference", "deviations"],
    "nacacfd.qa.validation": ["check_validation"],
}

CASES = [(m, f) for m, fs in STUBS.items() for f in fs]


@pytest.mark.parametrize("module,func", CASES)
def test_stub_raises_not_implemented(module, func):
    fn = getattr(importlib.import_module(module), func)
    n_args = fn.__code__.co_argcount - len(fn.__defaults__ or ())
    with pytest.raises(NotImplementedError):
        fn(*([None] * n_args))


@pytest.mark.parametrize("command", ["mesh", "report"])
def test_cli_stub_commands_raise(command):
    from nacacfd.cli import main

    with pytest.raises(NotImplementedError):
        main([command, "x"])


def test_cli_validate_config_works(repo_root, capsys):
    from nacacfd.cli import main

    assert main(["validate-config", str(repo_root / "experiments" / "naca0012_a5_smoke.yaml")]) == 0
    assert "OK: naca0012_a5_smoke" in capsys.readouterr().out
