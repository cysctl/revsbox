"""Parse LIGHTER-R and DORCIS output files into a ReversibleCircuit."""

import re

from revsbox.ir import Operation, ReversibleCircuit

_INPUT = re.compile(r"F\[(\d+)\]\s*=\s*X\[(\d+)\]\s*;")
_OUTPUT = re.compile(r"X\[(\d+)\]\s*=\s*F\[(\d+)\]\s*;")
_GATE = re.compile(r"F\[(\d+)\]\s*=\s*(\w+)\((.*)\)\s*;")
_ARG = re.compile(r"F\[(\d+)\]")

# Number of controls for each gate name.
_GATE_CONTROLS = {"RNOT1": 0, "CNOT1": 1, "CCNOT2": 2}


class ParseError(ValueError):
    """Raised when the text is not a valid LIGHTER-R or DORCIS output."""


def parse(text: str) -> ReversibleCircuit:
    """Parse the text of a LIGHTER-R or DORCIS output file."""
    inputs: dict[int, int] = {}
    outputs: dict[int, int] = {}
    operations: list[Operation] = []

    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        if match := _INPUT.fullmatch(line):
            wire, bit = map(int, match.groups())
            _add_mapping(inputs, bit, wire, number)
        elif match := _OUTPUT.fullmatch(line):
            bit, wire = map(int, match.groups())
            _add_mapping(outputs, bit, wire, number)
        elif match := _GATE.fullmatch(line):
            operations.append(_parse_gate(match, number))
        else:
            raise ParseError(f"Line {number}: cannot parse {line!r}")

    if not inputs:
        raise ParseError("No input lines found (like 'F[0] = X[0];')")

    num_wires = len(inputs)
    _check_bits("Input", inputs, num_wires)
    _check_bits("Output", outputs, num_wires)

    try:
        return ReversibleCircuit(
            num_wires=num_wires,
            input_map=tuple(inputs[bit] for bit in range(num_wires)),
            output_map=tuple(outputs[bit] for bit in range(num_wires)),
            operations=tuple(operations),
        )
    except ValueError as error:
        raise ParseError(str(error)) from error


def _parse_gate(match: re.Match[str], number: int) -> Operation:
    """Build an Operation from a matched gate line."""
    target, name, arg_text = int(match[1]), match[2], match[3]
    if name not in _GATE_CONTROLS:
        raise ParseError(f"Line {number}: unknown gate {name!r}")

    args: list[int] = []
    for part in arg_text.split(","):
        arg_match = _ARG.fullmatch(part.strip())
        if arg_match is None:
            raise ParseError(f"Line {number}: bad arguments {arg_text!r}")
        args.append(int(arg_match[1]))

    expected = _GATE_CONTROLS[name] + 1
    if len(args) != expected:
        raise ParseError(
            f"Line {number}: wrong number of arguments for {name}: "
            f"expected {expected}, got {len(args)}"
        )
    if len(set(args)) != len(args):
        raise ParseError(f"Line {number}: repeated wire in {name} arguments")
    if target not in args:
        raise ParseError(
            f"Line {number}: target F[{target}] is not an argument of {name}"
        )

    controls = tuple(arg for arg in args if arg != target)
    return Operation(target, controls)


def _add_mapping(mapping: dict[int, int], bit: int, wire: int, number: int) -> None:
    """Store that X[bit] is on the given wire, and reject a repeated bit."""
    if bit in mapping:
        raise ParseError(f"Line {number}: X[{bit}] is mapped twice")
    mapping[bit] = wire


def _check_bits(kind: str, mapping: dict[int, int], num_wires: int) -> None:
    """Raise ParseError unless the mapping covers X[0] to X[num_wires - 1]."""
    if set(mapping) != set(range(num_wires)):
        raise ParseError(
            f"{kind} lines must map X[0] to X[{num_wires - 1}] exactly once, "
            f"found bits {sorted(mapping)}"
        )
