"""Turn an SBoxGate into a plain Qiskit circuit."""

from qiskit import QuantumCircuit, transpile

from revsbox.gate import SBoxGate

# The gate set that to_clifford_t decomposes into.
CLIFFORD_T_BASIS = ("x", "h", "s", "sdg", "t", "tdg", "cx")


def to_nct(gate: SBoxGate) -> QuantumCircuit:
    """Return the circuit exactly as the tool wrote it (NOT, CNOT, CCNOT)."""
    return _as_circuit(gate).decompose("sbox")


def to_clifford_t(gate: SBoxGate) -> QuantumCircuit:
    """Decompose the gate into the gates in CLIFFORD_T_BASIS with Qiskit.

    Optimization level 0 is used, so the result describes the tool's circuit
    and not the result of Qiskit's optimizer. Qiskit does not use ancilla
    qubits for this decomposition.
    """
    return transpile(
        _as_circuit(gate), basis_gates=list(CLIFFORD_T_BASIS), optimization_level=0
    )


def _as_circuit(gate: SBoxGate) -> QuantumCircuit:
    """Put the gate into a circuit of its own."""
    circuit = QuantumCircuit(gate.num_qubits)
    circuit.append(gate, range(gate.num_qubits))
    return circuit
