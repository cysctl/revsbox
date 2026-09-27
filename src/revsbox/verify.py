"""Check an SBoxGate against a lookup table with any SamplerV2."""

from collections.abc import Sequence
from math import pi

from qiskit.circuit import ParameterVector, QuantumCircuit
from qiskit.primitives import BaseSamplerV2, BindingsArrayLike, StatevectorSampler

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


def run_sbox(
    gate: SBoxGate,
    sampler: BaseSamplerV2 | None = None,
    shots: int = 1,
) -> tuple[int, ...]:
    """Run the gate on every input and return the lookup table it computes.

    Any SamplerV2 works. Without a sampler, Qiskit's StatevectorSampler is
    used. On noisy hardware, use more shots: for each input, the most
    frequent outcome is taken.
    """
    n = gate.num_qubits
    # Custom gates like "sbox" are not kwnown to every simulator, so we
    # replace the gate with its NOT, CNOT, and CCNOT gates first.
    circuit = build_verification_circuit(gate).decompose("sbox")
    # theta[k] gets pi when X[k] is 1, for every input value.
    angles: BindingsArrayLike = {
        f"theta[{k}]": [pi * ((value >> (n - 1 - k)) & 1) for value in range(2**n)]
        for k in range(n)
    }

    sampler = sampler or StatevectorSampler()
    result = sampler.run([(circuit, angles)], shots=shots).result()
    # The results are stored under the name of the classical register.
    bits = result[0].data[circuit.cregs[0].name]

    table = []
    for value in range(2**n):
        counts = bits.get_int_counts(loc=value)
        table.append(max(counts, key=counts.__getitem__))
    return tuple(table)


def verify(
    gate: SBoxGate,
    sbox: Sequence[int],
    sampler: BaseSamplerV2 | None = None,
    shots: int = 1,
) -> bool:
    """Return True if the gate computes the lookup table sbox."""
    if len(sbox) != 2**gate.num_qubits:
        raise ValueError(
            f"The lookup table needs {2**gate.num_qubits} entries, got {len(sbox)}"
        )
    return run_sbox(gate, sampler, shots) == tuple(sbox)
