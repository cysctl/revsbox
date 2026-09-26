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
