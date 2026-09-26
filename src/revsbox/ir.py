"""Representation for reversible S-Box circuits."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Operation:
    """
    A reversible gate that flips target when all controls are 1.

    No controls is a NOT gate, one control is a CNOT gate, and
    two controls is a CCNOT (Toffoli) gate.
    """

    target: int
    controls: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        wires = (self.target, *self.controls)
        if min(wires) < 0:
            raise ValueError(f"Wire indexes cannot be negative: {wires}")
        if self.target in self.controls:
            raise ValueError(f"The target wire {self.target} cannot also be a control.")
        if len(set(self.controls)) != len(self.controls):
            raise ValueError(f"Control wires must be unique: {self.controls}")
