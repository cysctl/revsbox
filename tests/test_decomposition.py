from pathlib import Path

import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

from revsbox import decomposition
from revsbox.decomposition import (
    CLIFFORD_T_BASIS,
    decompose_gate,
    to_clifford_t,
    to_nct,
)
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


@pytest.mark.parametrize("basis_gates", [("u", "cx"), ("rz", "sx", "x", "cx")])
def test_decompose_gate_uses_the_given_basis(basis_gates):
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))

    circuit = decompose_gate(gate, basis_gates)

    assert set(circuit.count_ops()) <= set(basis_gates)
    assert Operator(circuit).equiv(Operator(as_circuit(gate)))


@pytest.mark.parametrize("level", [1, 2, 3])
def test_optimized_circuits_stay_correct_and_do_not_grow(level):
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))
    plain = to_clifford_t(gate)

    optimized = to_clifford_t(gate, optimization_level=level)

    assert Operator(optimized).equiv(Operator(as_circuit(gate)))
    assert optimized.size() <= plain.size()


def test_optimization_level_reaches_qiskit(monkeypatch):
    calls = []

    def spy_transpile(circuit, **options):
        calls.append(options)
        return circuit

    monkeypatch.setattr(decomposition, "transpile", spy_transpile)
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))

    to_clifford_t(gate, optimization_level=2)

    assert calls == [{"basis_gates": list(CLIFFORD_T_BASIS), "optimization_level": 2}]
