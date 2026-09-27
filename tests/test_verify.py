from pathlib import Path

import pytest

from revsbox.gate import SBoxGate
from revsbox.parser import load
from revsbox.verify import build_verification_circuit

DATA = Path(__file__).parent / "data"


@pytest.fixture
def circuit():
    # The LIGHTER-R file has different input and output maps:
    # input_map = (1, 0, 2, 3) and output_map = (2, 1, 0, 3).
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))
    return build_verification_circuit(gate)


def test_circuit_has_one_parameter_per_bit(circuit):
    assert circuit.num_qubits == 4
    assert circuit.num_clbits == 4
    assert [parameter.name for parameter in circuit.parameters] == [
        "theta[0]",
        "theta[1]",
        "theta[2]",
        "theta[3]",
    ]


def test_rx_gates_follow_the_input_map(circuit):
    rx_gates = [
        (item.operation.params[0].name, circuit.find_bit(item.qubits[0]).index)
        for item in circuit.data
        if item.operation.name == "rx"
    ]

    assert rx_gates == [
        ("theta[0]", 1),
        ("theta[1]", 0),
        ("theta[2]", 2),
        ("theta[3]", 3),
    ]


def test_sbox_gate_acts_on_all_qubits(circuit):
    (sbox,) = [item for item in circuit.data if item.operation.name == "sbox"]

    assert [circuit.find_bit(q).index for q in sbox.qubits] == [0, 1, 2, 3]


def test_x0_is_measured_into_the_highest_clbit(circuit):
    measurements = [
        (circuit.find_bit(item.qubits[0]).index, circuit.find_bit(item.clbits[0]).index)
        for item in circuit.data
        if item.operation.name == "measure"
    ]

    # X[0] ends on qubit 2 and goes to clbit 3, X[1] ends on qubit 1 and goes
    # to clbit 2, and so on.
    assert measurements == [(2, 3), (1, 2), (0, 1), (3, 0)]
