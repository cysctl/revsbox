from pathlib import Path

import pytest

from revsbox.ir import Operation, ReversibleCircuit
from revsbox.parser import ParseError, load, parse

DATA = Path(__file__).parent / "data"

# The PRESENT S-Box lookup table (the same string we give to the tools).
PRESENT = tuple(int(digit, 16) for digit in "C56B90AD3EF84712")

# Three wires, both CNOT argument orders, one CCNOT, and one NOT.
SMALL = """\
F[0] = X[2];
F[1] = X[0];
F[2] = X[1];

F[2] = CNOT1(F[2], F[0]);
F[0] = CNOT1(F[1], F[0]);
F[1] = CCNOT2(F[0], F[2], F[1]);
F[0] = RNOT1(F[0]);

X[0] = F[1];
X[1] = F[2];
X[2] = F[0];
"""

# A valid 3-wire file. The gate line goes on line 4.
TEMPLATE = """\
F[0] = X[0];
F[1] = X[1];
F[2] = X[2];
{gate_line}
X[0] = F[0];
X[1] = F[1];
X[2] = F[2];
"""


def test_parse_reads_maps_and_operations():
    circuit = parse(SMALL)

    assert circuit.num_wires == 3
    # The maps are indexed by bit: input_map[k] is the wire that holds X[k].
    # Here X[0] starts on F[1], X[1] on F[2], and X[2] on F[0].
    assert circuit.input_map == (1, 2, 0)
    assert circuit.output_map == (1, 2, 0)
    assert circuit.operations == (
        Operation(2, (0,)),
        Operation(0, (1,)),
        Operation(1, (0, 2)),
        Operation(0),
    )


def test_parse_ignores_comment_lines():
    text = "// from : 00FF 0F0F 3333 \n" + SMALL + "//to : 9B70\n// Cost: 4\n"

    assert parse(text) == parse(SMALL)


def test_parse_rejects_unknown_lines():
    with pytest.raises(ParseError, match="Line 2"):
        parse("F[0] = X[0];\nhello world\n")


@pytest.mark.parametrize(
    ("gate_line", "message"),
    [
        ("F[0] = FOO1(F[0]);", "unknown gate 'FOO1'"),
        ("F[0] = CNOT1(F[0], X[1]);", "bad arguments"),
        ("F[0] = CNOT1(F[0], F[1], F[2]);", "wrong number of arguments"),
        ("F[0] = RNOT1(F[0], F[1]);", "wrong number of arguments"),
        ("F[1] = CNOT1(F[1], F[1]);", "repeated wire"),
        ("F[0] = CNOT1(F[1], F[2]);", "not an argument"),
    ],
)
def test_parse_rejects_bad_gate_lines(gate_line, message):
    text = TEMPLATE.format(gate_line=gate_line)

    with pytest.raises(ParseError, match=f"^Line 4: .*{message}"):
        parse(text)


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        pytest.param([], "No input lines", id="no-input-lines"),
        pytest.param(
            ["F[0] = X[0];", "F[1] = X[0];", "X[0] = F[0];", "X[1] = F[1];"],
            "^Line 2: .*mapped twice",
            id="repeated-input-bit",
        ),
        pytest.param(
            ["F[0] = X[0];", "F[1] = X[1];", "X[0] = F[0];", "X[0] = F[1];"],
            "^Line 4: .*mapped twice",
            id="repeated-output-bit",
        ),
        pytest.param(
            ["F[0] = X[0];", "F[1] = X[2];", "X[0] = F[0];", "X[1] = F[1];"],
            "Input lines must map",
            id="missing-input-bit",
        ),
        pytest.param(
            ["F[0] = X[0];", "F[1] = X[1];", "X[0] = F[0];"],
            "Output lines must map",
            id="missing-output-bit",
        ),
        pytest.param(
            [
                "F[0] = X[0];",
                "F[1] = X[1];",
                "X[0] = F[0];",
                "X[1] = F[1];",
                "X[2] = F[1];",
            ],
            "Output lines must map",
            id="extra-output-bit",
        ),
        pytest.param(
            ["F[0] = X[0];", "F[0] = X[1];", "X[0] = F[0];", "X[1] = F[1];"],
            "input_map",
            id="repeated-input-wire",
        ),
        pytest.param(
            [
                "F[0] = X[0];",
                "F[1] = X[1];",
                "F[5] = RNOT1(F[5]);",
                "X[0] = F[0];",
                "X[1] = F[1];",
            ],
            "uses wire 5",
            id="gate-wire-out-of-range",
        ),
    ],
)
def test_parse_rejects_bad_wire_maps(lines, message):
    text = "\n".join(lines) + "\n"

    with pytest.raises(ParseError, match=message):
        parse(text)


def evaluate(circuit: ReversibleCircuit, value: int) -> int:
    """Run a circuit on classical bits. X[0] is the most significant bit."""
    n = circuit.num_wires
    wires = [0] * n
    for k, wire in enumerate(circuit.input_map):
        wires[wire] = (value >> (n - 1 - k)) & 1
    for op in circuit.operations:
        if all(wires[control] for control in op.controls):
            wires[op.target] ^= 1
    return sum(wires[wire] << (n - 1 - k) for k, wire in enumerate(circuit.output_map))


def test_load_reads_the_lighter_r_file():
    circuit = load(DATA / "present_lighter_r.c")

    assert circuit.num_wires == 4
    assert circuit.input_map == (1, 0, 2, 3)
    assert circuit.output_map == (2, 1, 0, 3)
    assert len(circuit.operations) == 11


@pytest.mark.parametrize(
    "file_name",
    ["present_lighter_r.c", "present_dorcis_depth.c", "present_dorcis_t_depth.c"],
)
def test_real_files_compute_the_present_sbox(file_name):
    circuit = load(DATA / file_name)

    assert tuple(evaluate(circuit, value) for value in range(16)) == PRESENT


def test_load_adds_the_file_name_to_errors(tmp_path):
    path = tmp_path / "broken.c"
    path.write_text("hello\n", encoding="utf-8")

    with pytest.raises(ParseError, match="broken.c: Line 1"):
        load(path)
