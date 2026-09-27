from pathlib import Path

import pytest
from qiskit.primitives import StatevectorSampler

from revsbox.gate import SBoxGate
from revsbox.parser import load
from revsbox.verify import build_verification_circuit, run_sbox, verify

DATA = Path(__file__).parent / "data"

# The PRESENT S-Box lookup table (the same string we give to the tools).
PRESENT = tuple(int(digit, 16) for digit in "C56B90AD3EF84712")

FILES = ["present_lighter_r.c", "present_dorcis_depth.c", "present_dorcis_t_depth.c"]


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


@pytest.mark.parametrize("file_name", FILES)
def test_run_sbox_measures_the_present_table(file_name):
    gate = SBoxGate(load(DATA / file_name))

    assert run_sbox(gate) == PRESENT


class SpySampler(StatevectorSampler):
    """A StatevectorSampler that remembers how it was called."""

    def __init__(self):
        super().__init__()
        self.calls = []

    def run(self, pubs, *, shots=None):
        self.calls.append(shots)
        return super().run(pubs, shots=shots)


def test_run_sbox_uses_the_given_sampler_and_shots():
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))
    sampler = SpySampler()

    table = run_sbox(gate, sampler=sampler, shots=10)

    assert table == PRESENT
    assert sampler.calls == [10]


def test_verify_accepts_the_right_table():
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))

    assert verify(gate, PRESENT)


def test_verify_rejects_a_wrong_table():
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))
    # Swap the outputs of input 0 and 1.
    wrong = (PRESENT[1], PRESENT[0], *PRESENT[2:])

    assert not verify(gate, wrong)


def test_verify_rejects_a_table_of_the_wrong_length():
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))

    with pytest.raises(ValueError, match="needs 16 entries, got 3"):
        verify(gate, (1, 2, 3))
