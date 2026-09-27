"""Write S-Box circuits to files."""

from os import PathLike
from pathlib import Path

from qiskit import QuantumCircuit, qasm3

from revsbox.ir import ReversibleCircuit


def to_qasm(circuit: QuantumCircuit, *, layout: ReversibleCircuit | None = None) -> str:
    """Return the circuit as OpenQASM 3 text.

    With layout, comments at the top say which qubit holds each bit X[k]
    before and after the circuit. The tools do not keep a bit on the same
    qubit, so the circuit cannot be read correctly without this. The circuit
    must use qubit j for wire F[j], like the circuits from to_nct and
    to_clifford_t.
    """
    text = qasm3.dumps(circuit)
    if layout is None:
        return text
    if layout.num_wires != circuit.num_qubits:
        raise ValueError(
            f"The layout has {layout.num_wires} wires, "
            f"but the circuit has {circuit.num_qubits} qubits."
        )
    return _layout_comment(layout) + text


def write_qasm(
    circuit: QuantumCircuit,
    path: str | PathLike[str],
    *,
    layout: ReversibleCircuit | None = None,
) -> None:
    """Write the circuit to an OpenQASM 3 file. See to_qasm."""
    Path(path).write_text(to_qasm(circuit, layout=layout), encoding="utf-8")


def _layout_comment(layout: ReversibleCircuit) -> str:
    """Describe where each bit X[k] is, as OpenQASM comment lines."""
    last = layout.num_wires - 1
    lines = [
        "// Bit layout of the S-Box circuit.",
        "// X[0] is the most significant bit.",
        f"// X[{last}] is the least significant bit.",
        "//",
        "// Input: before the circuit, put input bit X[k] into this qubit.",
        *(f"//\tX[{k}] -> q[{wire}]" for k, wire in enumerate(layout.input_map)),
        "//",
        "// Output: after the circuit, read output bit X[k] from this qubit.",
        *(f"//\tX[{k}] <- q[{wire}]" for k, wire in enumerate(layout.output_map)),
        "",
    ]
    return "\n".join(lines) + "\n"
