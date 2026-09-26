"""Representation for reversible S-Box circuits."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Operation:
    """A reversible gate that flips target when all controls are 1.

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


@dataclass(frozen=True)
class ReversibleCircuit:
    """A reversible circuit read from a LIGHTER-R or DORCIS output file.

    input_map[k] is the wire that holds X[k] at the start, and
    output_map[k] is the wire that holds X[k] at the end.
    """

    num_wires: int
    input_map: tuple[int, ...]
    output_map: tuple[int, ...]
    operations: tuple[Operation, ...] = ()

    def __post_init__(self) -> None:
        if self.num_wires < 1:
            raise ValueError(
                f"The number of wires must be at least 1: {self.num_wires}"
            )

        _check_permutation("input_map", self.input_map, self.num_wires)
        _check_permutation("output_map", self.output_map, self.num_wires)

        for index, op in enumerate(self.operations):
            highest = max((op.target, *op.controls))
            if highest >= self.num_wires:
                raise ValueError(
                    f"Operation {index} uses wire {highest}, "
                    f"but the circuit has only {self.num_wires} wires."
                )


def _check_permutation(name: str, mapping: tuple[int, ...], num_wires: int) -> None:
    """Raise ValueError if mapping does not use each wire exactly once."""
    if sorted(mapping) != list(range(num_wires)):
        raise ValueError(
            f"{name} must contain each wire from 0 to {num_wires - 1} "
            f"exactly once: {mapping}"
        )
