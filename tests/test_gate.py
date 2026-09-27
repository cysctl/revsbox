from pathlib import Path

import pytest
from qiskit.quantum_info import Statevector

from revsbox.gate import SBoxGate
from revsbox.ir import Operation, ReversibleCircuit
from revsbox.parser import load

DATA = Path(__file__).parent / "data"

# The PRESENT S-Box lookup table (the same string we give to the tools).
PRESENT = tuple(int(digit, 16) for digit in "C56B90AD3EF84712")

# Four wires with one gate of each size: NOT, CNOT, CCNOT, and 3 controls.
MIXED = ReversibleCircuit(
    num_wires=4,
    input_map=(0, 1, 2, 3),
    output_map=(0, 1, 2, 3),
    operations=(
        Operation(0),
        Operation(2, (1,)),
        Operation(1, (0, 2)),
        Operation(3, (0, 1, 2)),
    ),
)


def run_gate(gate: SBoxGate, value: int) -> int:
    """Apply the gate to one input value, using the file's bit layout.

    X[k] is bit k of the value counted from the most significant bit.
    It hoes to qubit input_map[k] and is read back from qubit output_map[k].
    """
    n = gate.num_qubits
    index = 0
    for k, wire in enumerate(gate.ir.input_map):
        index |= ((value >> (n - 1 - k)) & 1) << wire

    state = Statevector.from_int(index, 2**n).evolve(gate)
    (outcome,) = state.probabilities_dict()
    result = int(outcome, 2)

    output = 0
    for k, wire in enumerate(gate.ir.output_map):
        output |= ((result >> wire) & 1) << (n - 1 - k)
    return output


def test_gate_has_one_qubit_per_wire():
    gate = SBoxGate(MIXED)

    assert gate.name == "sbox"
    assert gate.num_qubits == 4
    assert gate.ir is MIXED


def test_definition_keeps_the_file_order():
    gate = SBoxGate(MIXED)
    definition = gate.definition

    gates = [
        (item.operation.name, [definition.find_bit(q).index for q in item.qubits])
        for item in definition.data
    ]

    assert gates == [
        ("x", [0]),
        ("cx", [1, 2]),
        ("ccx", [0, 2, 1]),
        ("mcx", [0, 1, 2, 3]),
    ]


@pytest.mark.parametrize(
    "file_name",
    ["present_lighter_r.c", "present_dorcis_depth.c", "present_dorcis_t_depth.c"],
)
def test_gate_computes_the_present_sbox(file_name):
    gate = SBoxGate(load(DATA / file_name))

    assert tuple(run_gate(gate, value) for value in range(16)) == PRESENT
