"""Cost metrics for S-Box circuits."""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from qiskit import QuantumCircuit
from qiskit.circuit import Gate

from revsbox.decomposition import to_clifford_t, to_nct
from revsbox.gate import SBoxGate

# The gates that count for the T-count and the T-depth.
_T_GATES = frozenset({"t", "tdg"})

# Clifford+T gates bu their Qiskit names. T metrics are only defined for a
# circuit that uses these gates only.
_CLIFFORD_T_GATES = _T_GATES | {
    "id",
    "x",
    "y",
    "z",
    "h",
    "s",
    "sdg",
    "sx",
    "sxdg",
    "cx",
    "cy",
    "cz",
    "swap",
}


@dataclass(frozen=True)
class Metrics:
    """Cost metrics of one quantum circuit.

    Only gates are counted. Measurements, barries, and resets are ignored.

    Attributes:
        num_qubits: The number of qubits in the circuit.
        gate_counts: The number of gates for each gate name (read-only).
        num_gates: The total number of gates.
        depth: The number of gate layers on the longest path.
        t_count: The number of T and T-dagger gates, or None if the circuit
            has gates that are not Clifford+T gates. For example, a Toffoli
            gate hides T gates inside it, so the T cost is not known.
        t_depth: The number of layers of T and T-dagger gates on the longest
            path, or None in the same cases on t_count.
    """

    num_qubits: int
    gate_counts: Mapping[str, int]
    num_gates: int
    depth: int
    t_count: int | None
    t_depth: int | None


def circuit_metrics(circuit: QuantumCircuit) -> Metrics:
    """Measure the gate counts, depth, T-count, and T-depth of a circuit."""
    counts = Counter(
        item.operation.name for item in circuit.data if isinstance(item.operation, Gate)
    )

    t_count = t_depth = None
    if set(counts) <= _CLIFFORD_T_GATES:
        t_count = sum(counts[name] for name in _T_GATES)
        t_depth = circuit.depth(
            filter_function=lambda item: item.operation.name in _T_GATES
        )

    return Metrics(
        num_qubits=circuit.num_qubits,
        gate_counts=MappingProxyType(dict(counts)),
        num_gates=sum(counts.values()),
        depth=circuit.depth(
            filter_function=lambda item: isinstance(item.operation, Gate)
        ),
        t_count=t_count,
        t_depth=t_depth,
    )


def nct_metrics(gate: SBoxGate) -> Metrics:
    """Measure the circuit exactly as the tool worte it (NOT, CNOT, CCNOT).

    The Toffoli gates are not decomposed here, so t_count and t_depth are
    None when the circuit has Toffoli gates. Use clifford_t_metrics for
    the T cost.
    """
    return circuit_metrics(to_nct(gate))


def clifford_t_metrics(gate: SBoxGate) -> Metrics:
    """Measure the circuit after it is decomposed into Clifford+T gates."""
    return circuit_metrics(to_clifford_t(gate))
