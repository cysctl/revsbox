"""Turn an SBoxGate into a plain Qiskit circuit."""

from collections.abc import Sequence

from qiskit import QuantumCircuit, transpile

from revsbox.gate import SBoxGate

# The gate set that to_clifford_t decomposes into.
CLIFFORD_T_BASIS = ("x", "h", "s", "sdg", "t", "tdg", "cx")


def to_nct(gate: SBoxGate) -> QuantumCircuit:
    """Return the circuit exactly as the tool wrote it (NOT, CNOT, CCNOT)."""
    return _as_circuit(gate).decompose("sbox")


def decompose_gate(
    gate: SBoxGate,
    basis_gates: Sequence[str],
    *,
    optimization_level: int = 0,
) -> QuantumCircuit:
    """Decompose the gate into the given basis gates with Qiskit.

    With optimization level 0, the result describes the tool's circuit.
    Levels 1 to 3 let Qiskit's optimizer change the circuit, so the result is
    no longer the tool's circuit alone. Qiskit raises an error if the level
    is not 0 to 3, or if the basis gates cannot express the circuit.
    """
    return transpile(
        _as_circuit(gate),
        basis_gates=list(basis_gates),
        optimization_level=optimization_level,
    )


def to_clifford_t(gate: SBoxGate, optimization_level: int = 0) -> QuantumCircuit:
    """Decompose the gate into the gates in CLIFFORD_T_BASIS with Qiskit.

    Qiskit does not use ancilla qubits for this decomposition. See
    decompose_gate for the meaning of optimization_level.
    """
    return decompose_gate(gate, CLIFFORD_T_BASIS, optimization_level=optimization_level)


def _as_circuit(gate: SBoxGate) -> QuantumCircuit:
    """Put the gate into a circuit of its own."""
    circuit = QuantumCircuit(gate.num_qubits)
    circuit.append(gate, range(gate.num_qubits))
    return circuit
