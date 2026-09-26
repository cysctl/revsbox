"""Parse LIGHTER-R and DORCIS output files into a ReversibleCircuit."""

import re

from revsbox.ir import Operation, ReversibleCircuit

_INPUT = re.compile(r"F\[(\d+)\]\s*=\s*X\[(\d+)\]\s*;")
_OUTPUT = re.compile(r"X\[(\d+)\]\s*=\s*F\[(\d+)\]\s*;")
_GATE = re.compile(r"F\[(\d+)\]\s*=\s*(\w+)\((.*)\)\s*;")
_ARG = re.compile(r"F\[(\d+)\]")


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
            inputs[bit] = wire
        elif match := _OUTPUT.fullmatch(line):
            bit, wire = map(int, match.groups())
            outputs[bit] = wire
        elif match := _GATE.fullmatch(line):
            operations.append(_parse_gate(match))
        else:
            raise ParseError(f"Line {number}: cannot parse {line!r}")

    num_wires = len(inputs)
    return ReversibleCircuit(
        num_wires=num_wires,
        input_map=tuple(inputs[bit] for bit in range(num_wires)),
        output_map=tuple(outputs[bit] for bit in range(num_wires)),
        operations=tuple(operations),
    )


def _parse_gate(match: re.Match[str]) -> Operation:
    """Build an Operation from a matched gate line."""
    target = int(match[1])
    args = [int(arg) for arg in _ARG.findall(match[3])]
    controls = tuple(arg for arg in args if arg != target)
    return Operation(target, controls)
