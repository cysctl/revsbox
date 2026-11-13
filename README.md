# revsbox

[![CI](https://github.com/cysctl/revsbox/actions/workflows/ci.yml/badge.svg)](https://github.com/cysctl/revsbox/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/cysctl/revsbox/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.0%2B-6929C4)](https://qiskit.org)
[![License](https://img.shields.io/github/license/cysctl/revsbox)](LICENSE)

revsbox is a Python library that builds Qiskit circuits from [LIGHTER-R](https://github.com/vdasu/lighter-r) and [DORCIS](https://github.com/matthewchunqed/dorcis-public) S-box synthesis outputs.

It parses the C-like gate descriptions produced by these tools, turns them into Qiskit gates and circuits, computes circuit cost metrics, verifies the circuits against lookup tables, and exports them to OpenQASM 3 or PNG files.

## Installation

revsbox requires Python 3.10 or newer and Qiskit 2.0 or newer. The package is not published on PyPI yet. Clone the repository and install it with `pip`:

```bash
git clone https://github.com/cysctl/revsbox.git
cd revsbox
pip install .
```

To save circuit drawings as PNG files, install the `draw` extra (`matplotlib` and `pylatexenc`):

```bash
pip install ".[draw]"
```

## Input Format and Bit Layout

LIGHTER-R and DORCIS write reversible S-box circuits as C-like statements using three gate types:
- `RNOT1(F[t])`: NOT gate (`x`) on target wire `t`
- `CNOT1(F[a], F[b])`: CNOT gate (`cx`) where the left-hand side of `=` is the target wire and the other argument is the control wire
- `CCNOT2(F[a], F[b], F[c])`: Toffoli gate (`ccx`) where the left-hand side of `=` is the target wire and the other two arguments are the control wires

For example, the file `tests/data/present_lighter_r.c` describes the 4-bit PRESENT S-box (`C56B90AD3EF84712`):

```c
// from : 00FF 0F0F 3333 5555

F[0] = X[1];
F[1] = X[0];
F[2] = X[2];
F[3] = X[3];

F[2] = CNOT1(F[2], F[0]);
F[1] = CCNOT2(F[2], F[0], F[1]);
F[0] = CCNOT2(F[2], F[1], F[0]);
F[2] = CCNOT2(F[3], F[0], F[2]);
F[2] = CNOT1(F[2], F[1]);
F[3] = RNOT1(F[3]);
F[1] = RNOT1(F[1]);
F[0] = CNOT1(F[0], F[2]);
F[2] = CNOT1(F[2], F[3]);
F[3] = CNOT1(F[3], F[1]);
F[1] = CCNOT2(F[2], F[0], F[1]);

X[0] = F[2];
X[1] = F[1];
X[2] = F[0];
X[3] = F[3];
```

In this format:
- `F[j]` is wire `j`, which corresponds to qubit `j` in Qiskit.
- `X[k]` is bit `k` of the S-box input or output, where `X[0]` is the most significant bit and `X[n - 1]` is the least significant bit.

The synthesis tools permute the wires instead of keeping a bit on the same wire from start to finish. `revsbox` does not insert SWAP gates to reorder the qubits. Instead, the parsed `ReversibleCircuit` stores the bit positions in `input_map` and `output_map`:
- Before the circuit runs, input bit `X[k]` is placed on qubit `ir.input_map[k]`.
- After the circuit runs, output bit `X[k]` is read from qubit `ir.output_map[k]`.

In the PRESENT example above, `ir.input_map` is `(1, 0, 2, 3)` and `ir.output_map` is `(2, 1, 0, 3)`.

## Usage

### 1. Parsing and Building an `SBoxGate`

Use `load` to read a circuit file from disk into a `ReversibleCircuit`, then wrap it in `SBoxGate`:

```python
from qiskit import QuantumCircuit

from revsbox.gate import SBoxGate
from revsbox.parser import load

ir = load("tests/data/present_lighter_r.c")
gate = SBoxGate(ir, label="PRESENT")

circuit = QuantumCircuit(gate.num_qubits)
circuit.append(gate, range(gate.num_qubits))
```

If you already have the tool output in a string, use `parse`:

```python
from revsbox.gate import SBoxGate
from revsbox.parser import parse

text = """
F[0] = X[1];
F[1] = X[0];
F[0] = CNOT1(F[1], F[0]);
X[0] = F[1];
X[1] = F[0];
"""

ir = parse(text)
gate = SBoxGate(ir)
```

### 2. Decomposing into NCT, Clifford+T, or Custom Basis Gates

An `SBoxGate` can be turned into a plain `QuantumCircuit` using the exact NCT gates from the file, the Clifford+T gate set, or any basis gate list supported by Qiskit:

```python
from revsbox.decomposition import decompose_gate, to_clifford_t, to_nct
from revsbox.gate import SBoxGate
from revsbox.parser import load

gate = SBoxGate(load("tests/data/present_lighter_r.c"))

# Decompose into the exact NOT (x), CNOT (cx), and CCNOT (ccx) gates from the file
nct_circuit = to_nct(gate)

# Decompose into Clifford+T gates without ancilla qubits
clifford_t_circuit = to_clifford_t(gate, optimization_level=0)

# Let Qiskit's transpiler optimize the Clifford+T circuit (levels 1 to 3)
optimized_circuit = to_clifford_t(gate, optimization_level=2)

# Decompose into a custom basis
custom_circuit = decompose_gate(
    gate,
    ["rz", "sx", "x", "cx"],
    optimization_level=1,
)
```

With `optimization_level=0`, the result directly reflects the tool's circuit. Levels 1 to 3 allow Qiskit's optimizer to simplify and rewrite gates across boundaries.

### 3. Computing Circuit Cost Metrics

Use `nct_metrics`, `clifford_t_metrics`, or `circuit_metrics` to inspect qubit count, gate counts, total gate count, depth, T-count, and T-depth:

```python
from revsbox.decomposition import to_clifford_t
from revsbox.gate import SBoxGate
from revsbox.metrics import circuit_metrics, clifford_t_metrics, nct_metrics
from revsbox.parser import load

gate = SBoxGate(load("tests/data/present_lighter_r.c"))

# Measure the NCT circuit as written by the tool
nct_stats = nct_metrics(gate)

# Measure the circuit after Clifford+T decomposition
ct_stats = clifford_t_metrics(gate, optimization_level=0)

# Measure any Qiskit QuantumCircuit directly
circuit = to_clifford_t(gate, optimization_level=2)
custom_stats = circuit_metrics(circuit)
```

Each function returns a `Metrics` dataclass with `num_qubits`, `gate_counts`, `num_gates`, `depth`, `t_count`, and `t_depth`. Non-gate instructions such as measurements, barriers, and resets are ignored. If a circuit contains non-Clifford+T gates (such as `ccx` in an undecomposed NCT circuit), `t_count` and `t_depth` are `None`.

### 4. Verifying Against an S-Box Lookup Table

`verify` and `run_sbox` test the gate on all $2^n$ classical inputs while respecting `input_map` and `output_map`:

```python
from revsbox.gate import SBoxGate
from revsbox.parser import load
from revsbox.verify import build_verification_circuit, run_sbox, verify

gate = SBoxGate(load("tests/data/present_lighter_r.c"))

# Expected lookup table for the 4-bit PRESENT S-box
present_sbox = (
    0xC,
    0x5,
    0x6,
    0xB,
    0x9,
    0x0,
    0xA,
    0xD,
    0x3,
    0xE,
    0xF,
    0x8,
    0x4,
    0x7,
    0x1,
    0x2,
)

# Check if the gate computes the expected lookup table (returns True or False)
is_correct = verify(gate, present_sbox)

# Run the gate on all inputs and return the computed lookup table as a tuple of ints
computed_table = run_sbox(gate)

# Build the parameterized QuantumCircuit used during verification
verification_circuit = build_verification_circuit(gate)
```

By default, `verify` and `run_sbox` use Qiskit's `StatevectorSampler`. You can pass any Qiskit `BaseSamplerV2` implementation (such as `SamplerV2` from `qiskit-aer`) and specify the number of shots:

```python
from qiskit_aer.primitives import SamplerV2 as AerSamplerV2

from revsbox.gate import SBoxGate
from revsbox.parser import load
from revsbox.verify import verify

gate = SBoxGate(load("tests/data/present_lighter_r.c"))
present_sbox = (
    0xC,
    0x5,
    0x6,
    0xB,
    0x9,
    0x0,
    0xA,
    0xD,
    0x3,
    0xE,
    0xF,
    0x8,
    0x4,
    0x7,
    0x1,
    0x2,
)

is_correct = verify(gate, present_sbox, sampler=AerSamplerV2(), shots=1024)
```

### 5. Exporting to OpenQASM 3 and PNG

Use `to_qasm` and `write_qasm` to export a circuit as OpenQASM 3, and `write_png` to save a circuit diagram:

```python
from revsbox.decomposition import to_nct
from revsbox.export import to_qasm, write_png, write_qasm
from revsbox.gate import SBoxGate
from revsbox.parser import load

gate = SBoxGate(load("tests/data/present_lighter_r.c"))
circuit = to_nct(gate)

# Return OpenQASM 3 text with header comments describing the bit layout
qasm_text = to_qasm(circuit, layout=gate.ir)

# Write OpenQASM 3 text to a file
write_qasm(circuit, "present.qasm", layout=gate.ir)

# Render and save the circuit diagram as a PNG file (requires revsbox[draw])
write_png(circuit, "present.png")
```

When `layout=gate.ir` is provided, `to_qasm` and `write_qasm` prepend comments to the OpenQASM 3 output showing which qubit `q[j]` holds each bit `X[k]` at the input and output of the circuit.

## Development

Clone the repository and install the development dependencies:

```bash
git clone https://github.com/cysctl/revsbox.git
cd revsbox
pip install -e ".[draw]" --group dev
```

Run the test suite:

```bash
python -m pytest
```

Run the linter and formatter checks:

```bash
ruff check .
ruff format --check .
```

## License

Licensed under the [Apache License, Version 2.0](LICENSE).
