"""Common result type for all QA gates.

Status: implemented and unit-tested in F0.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class GateOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_RUN = "not_run"  # never counts as passed


@dataclass(frozen=True)
class GateResult:
    """Outcome of one gate for one case (or one study, for GCI).

    value/threshold are what was measured and what it was compared with;
    evidence points to the file(s) the value was computed from;
    reason is a short human-readable explanation, required for FAIL and NOT_RUN.
    """

    name: str
    outcome: GateOutcome
    value: Any = None
    threshold: Any = None
    evidence: str | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.outcome is not GateOutcome.PASS and not self.reason:
            raise ValueError(f"gate '{self.name}': a {self.outcome.value} result needs a reason")

    @property
    def passed(self) -> bool:
        return self.outcome is GateOutcome.PASS

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["outcome"] = self.outcome.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GateResult":
        return cls(
            name=d["name"],
            outcome=GateOutcome(d["outcome"]),
            value=d.get("value"),
            threshold=d.get("threshold"),
            evidence=d.get("evidence"),
            reason=d.get("reason", ""),
        )
