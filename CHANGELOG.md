## v0.1.0 (2026-11-13)

### Feat

- **export**: write PNG drawings
- **export**: write OpenQASM 3 files with the bit layout
- **metrics**: accept an optimization level in clifford_t_metrics
- **decomposition**: let users choose basis gates and optimization level
- **metrics**: add NCT and Clifford+T circuit metrics
- **verify**: run and verify gates with any SamplerV2
- **verify**: build the verification circuit
- **gate**: add SBoxGate built from a reversible circuit
- **parser**: load output files from a path
- **parser**: reject missing and repeated wire mappings
- **parser**: reject invalid gate lines
- **parser**: parse wire maps and gate lines
- **ir**: add ReversibleCircuit dataclass
- **ir**: validate Operation wire indexes
- **ir**: add Operation dataclass

### Refactor

- move circuit decomposition into its own module
