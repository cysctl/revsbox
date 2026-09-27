"""A Qiskit gate built from a reversible S-Box circuit."""

from qiskit.circuit import Gate, QuantumCircuit

from revsbox.ir import ReversibleCircuit


class SBoxGate(Gate):
    """A Qiskit gate that applies a reversible S-Box circuit.

    Qubit j is wire F[j] of the tool output, and the gates keep the file order.
    The gate does not reorder bits: X[k] starts on qubit ir.input_map[k] and
    ends on qubit ir.output_map[k], where X[0] is the most significant bit.
    """

    def __init__(self, ir: ReversibleCircuit, label: str | None = None) -> None:
        self.ir = ir
        super().__init__("sbox", ir.num_wires, [], label=label)

    def _define(self) -> None:
        circuit = QuantumCircuit(self.num_qubits, name=self.name)
        for op in self.ir.operations:
            if not op.controls:
                circuit.x(op.target)
            elif len(op.controls) == 1:
                circuit.cx(op.controls[0], op.target)
            elif len(op.controls) == 2:
                circuit.ccx(op.controls[0], op.controls[1], op.target)
            else:
                circuit.mcx(list(op.controls), op.target)
        self.definition = circuit
