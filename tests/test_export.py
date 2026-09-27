from pathlib import Path

import pytest
from matplotlib import pyplot
from qiskit import QuantumCircuit, qasm3
from qiskit.quantum_info import Operator

from revsbox.decomposition import to_clifford_t, to_nct
from revsbox.export import to_qasm, write_png, write_qasm
from revsbox.gate import SBoxGate
from revsbox.parser import load

DATA = Path(__file__).parent / "data"

FILES = ["present_lighter_r.c", "present_dorcis_depth.c", "present_dorcis_t_depth.c"]


@pytest.mark.parametrize("file_name", FILES)
@pytest.mark.parametrize("decompose", [to_nct, to_clifford_t])
def test_qasm_loads_back_as_the_same_circuit(file_name, decompose):
    gate = SBoxGate(load(DATA / file_name))
    circuit = decompose(gate)

    loaded = qasm3.loads(to_qasm(circuit, layout=gate.ir))

    assert Operator(loaded).equiv(Operator(circuit))


def test_qasm_without_a_layout_has_no_comments():
    circuit = QuantumCircuit(1)
    circuit.x(0)

    text = to_qasm(circuit)

    assert text.startswith("OPENQASM 3.0;")


def test_layout_comments_describe_the_maps():
    # The LIGHTER-R file has input_map = (1, 0, 2, 3) and
    # output_map = (2, 1, 0, 3).
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))

    text = to_qasm(to_nct(gate), layout=gate.ir)

    assert text.splitlines()[:16] == [
        "// Bit layout of the S-Box circuit.",
        "// X[0] is the most significant bit.",
        "// X[3] is the least significant bit.",
        "//",
        "// Input: before the circuit, put input bit X[k] into this qubit.",
        "//\tX[0] -> q[1]",
        "//\tX[1] -> q[0]",
        "//\tX[2] -> q[2]",
        "//\tX[3] -> q[3]",
        "//",
        "// Output: after the circuit, read output bit X[k] from this qubit.",
        "//\tX[0] <- q[2]",
        "//\tX[1] <- q[1]",
        "//\tX[2] <- q[0]",
        "//\tX[3] <- q[3]",
        "",
    ]
    assert text.splitlines()[16] == "OPENQASM 3.0;"


def test_layout_must_match_the_circuit_size():
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))

    with pytest.raises(ValueError, match="4 wires, but the circuit has 2 qubits"):
        to_qasm(QuantumCircuit(2), layout=gate.ir)


def test_write_qasm_writes_the_same_text(tmp_path):
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))
    circuit = to_nct(gate)
    path = tmp_path / "present.qasm"

    write_qasm(circuit, path, layout=gate.ir)

    assert path.read_text(encoding="utf-8") == to_qasm(circuit, layout=gate.ir)


def test_write_png_writes_a_png_file(tmp_path):
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))
    path = tmp_path / "present.png"

    write_png(to_nct(gate), path)

    # Every PNG file starts with these 8 bytes.
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_write_png_closes_its_figure(tmp_path):
    gate = SBoxGate(load(DATA / "present_lighter_r.c"))
    open_before = len(pyplot.get_fignums())

    write_png(to_nct(gate), tmp_path / "present.png")

    assert len(pyplot.get_fignums()) == open_before
