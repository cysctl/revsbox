from collections import Counter
from pathlib import Path
from typing import cast

import pytest
from qiskit import QuantumCircuit

from revsbox.decomposition import CLIFFORD_T_BASIS
from revsbox.gate import SBoxGate
from revsbox.ir import ReversibleCircuit
from revsbox.metrics import (
    circuit_metrics,
    clifford_t_metrics,
    nct_metrics,
)
from revsbox.parser import load

DATA = Path(__file__).parent / "data"

FILES = ["present_lighter_r.c", "present_dorcis_depth.c", "present_dorcis_t_depth.c"]

# The Qiskit gate name for each number of controls.
GATE_NAMES = {0: "x", 1: "cx", 2: "ccx"}


def nct_depth(circuit: ReversibleCircuit) -> int:
    """Compute the depth from the IR: a gate starts when all its wires are free."""
    free_at = [0] * circuit.num_wires
    for op in circuit.operations:
        wires = (op.target, *op.controls)
        layer = max(free_at[wire] for wire in wires) + 1
        for wire in wires:
            free_at[wire] = layer
    return max(free_at)


def test_circuit_metrics_on_a_small_circuit():
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.t(0)
    circuit.t(1)
    circuit.cx(0, 1)
    circuit.tdg(1)

    metrics = circuit_metrics(circuit)

    assert metrics.num_qubits == 2
    assert metrics.gate_counts == {"t": 2, "h": 1, "cx": 1, "tdg": 1}
    assert metrics.num_gates == 5
    assert metrics.depth == 4
    assert metrics.t_count == 3
    # t(0) and t(1) are in the same layer, and tdg(1) comes after the cx.
    assert metrics.t_depth == 2


def test_circuit_metrics_ignore_measurements_and_barries():
    circuit = QuantumCircuit(1, 1)
    circuit.t(0)
    circuit.barrier()
    circuit.measure(0, 0)

    metrics = circuit_metrics(circuit)

    assert metrics.gate_counts == {"t": 1}
    assert metrics.num_gates == 1
    assert metrics.depth == 1
    assert metrics.t_count == 1
    assert metrics.t_depth == 1


def test_t_metrics_are_defined_for_any_clifford_gates():
    circuit = QuantumCircuit(2)
    circuit.z(0)
    circuit.cz(0, 1)
    circuit.t(1)

    metrics = circuit_metrics(circuit)

    assert metrics.t_count == 1
    assert metrics.t_depth == 1


def test_t_metrics_are_none_outside_clifford_t():
    circuit = QuantumCircuit(3)
    circuit.t(0)
    circuit.ccx(0, 1, 2)

    metrics = circuit_metrics(circuit)

    # The Toffoli hides T gates inside it, so the T cost is not known.
    assert metrics.t_count is None
    assert metrics.t_depth is None


def test_gate_counts_are_read_only():
    circuit = QuantumCircuit(1)
    circuit.x(0)

    metrics = circuit_metrics(circuit)

    # Pretend it is a normal dict and try to change it.
    with pytest.raises(TypeError):
        cast(dict, metrics.gate_counts)["x"] = 5


@pytest.mark.parametrize("file_name", FILES)
def test_nct_metrics_match_the_tool_file(file_name):
    circuit = load(DATA / file_name)
    expected = Counter(GATE_NAMES[len(op.controls)] for op in circuit.operations)

    metrics = nct_metrics(SBoxGate(circuit))

    assert metrics.num_qubits == circuit.num_wires
    assert metrics.gate_counts == expected
    assert metrics.num_gates == len(circuit.operations)
    assert metrics.depth == nct_depth(circuit)


@pytest.mark.parametrize("file_name", FILES)
def test_nct_metrics_have_no_t_cost(file_name):
    metrics = nct_metrics(SBoxGate(load(DATA / file_name)))

    assert metrics.t_count is None
    assert metrics.t_depth is None


@pytest.mark.parametrize("file_name", FILES)
def test_clifford_t_metrics_use_only_the_basis(file_name):
    circuit = load(DATA / file_name)
    toffolis = sum(1 for op in circuit.operations if len(op.controls) == 2)

    metrics = clifford_t_metrics(SBoxGate(circuit))

    assert metrics.num_qubits == circuit.num_wires
    assert set(metrics.gate_counts) <= set(CLIFFORD_T_BASIS)
    # Qiskit uses 7 T and T-dagger gates for each Toffoli.
    assert metrics.t_count == 7 * toffolis
    assert metrics.t_depth is not None
    assert 0 < metrics.t_depth <= 7 * toffolis
