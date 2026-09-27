"""Check an SBoxGate against a lookup table with any SamplerV2."""

from qiskit.circuit import ParameterVector, QuantumCircuit

from revsbox.gate import SBoxGate


def build_verification_circuit(gate: SBoxGate) -> QuantumCircuit:
    """Build a circuit that runs the gate on one classical input.

    Parameter theta[k] sets X[k]: 0 gives bit 0, and pi gives bit 1.
    X[k] is measured into classical bit n - 1 - k, so the measured
    integer is the S-Box output, with X[0] as the most significant bit.
    """
    n = gate.num_qubits
    theta = ParameterVector("theta", n)
    circuit = QuantumCircuit(n, n)
    for k, wire in enumerate(gate.ir.input_map):
        circuit.rx(theta[k], wire)
    circuit.append(gate, range(n))
    for k, wire in enumerate(gate.ir.output_map):
        circuit.measure(wire, n - 1 - k)
    return circuit
