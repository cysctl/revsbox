from pathlib import Path

import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

from revsbox.decomposition import CLIFFORD_T_BASIS, to_clifford_t, to_nct
from revsbox.gate import SBoxGate
from revsbox.parser import load

DATA = Path(__file__).parent / "data"

FILES = ["present_lighter_r.c", "present_dorcis_depth.c", "present_dorcis_t_depth.c"]


def as_circuit(gate: SBoxGate) -> QuantumCircuit:
    circuit = QuantumCircuit(gate.num_qubits)
    circuit.append(gate, range(gate.num_qubits))
    return circuit


@pytest.mark.parametrize("file_name", FILES)
def test_to_nct_uses_only_the_tool_gates(file_name):
    gate = SBoxGate(load(DATA / file_name))

    circuit = to_nct(gate)

    assert set(circuit.count_ops()) <= {"x", "cx", "ccx"}
    assert Operator(circuit).equiv(Operator(as_circuit(gate)))


@pytest.mark.parametrize("file_name", FILES)
def test_to_clifford_t_uses_only_the_basis(file_name):
    gate = SBoxGate(load(DATA / file_name))

    circuit = to_clifford_t(gate)

    assert set(circuit.count_ops()) <= set(CLIFFORD_T_BASIS)
    assert Operator(circuit).equiv(Operator(as_circuit(gate)))
