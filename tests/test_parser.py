import pytest

from revsbox.ir import Operation
from revsbox.parser import ParseError, parse

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
