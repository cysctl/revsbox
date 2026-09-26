import dataclasses

import pytest

from revsbox.ir import Operation, ReversibleCircuit

IDENTITY = (0, 1, 2, 3)


def test_ccnot_stores_target_and_controls():
    op = Operation(target=1, controls=(2, 0))

    assert op.target == 1
    assert op.controls == (2, 0)


def test_not_has_no_controls_by_default():
    op = Operation(target=3)

    assert op.controls == ()


def test_operation_is_immutable():
    op = Operation(target=0)

    with pytest.raises(dataclasses.FrozenInstanceError):
        op.target = 1


@pytest.mark.parametrize("controls", [(1,), (0, 1)])
def test_target_cannot_be_a_control(controls):
    with pytest.raises(ValueError, match="target"):
        Operation(target=1, controls=controls)


def test_controls_must_be_unique():
    with pytest.raises(ValueError, match="unique"):
        Operation(target=0, controls=(2, 2))


@pytest.mark.parametrize(("target", "controls"), [(-1, ()), (0, (-2,))])
def test_wire_indexes_cannot_be_negative(target, controls):
    with pytest.raises(ValueError, match="negative"):
        Operation(target=target, controls=controls)


def test_circuit_stores_maps_and_operations():
    ops = (Operation(2, (0,)), Operation(3))

    circuit = ReversibleCircuit(
        num_wires=4,
        input_map=(1, 0, 2, 3),
        output_map=IDENTITY,
        operations=ops,
    )

    assert circuit.input_map == (1, 0, 2, 3)
    assert circuit.output_map == IDENTITY
    assert circuit.operations == ops


def test_circuit_needs_at_least_one_wire():
    with pytest.raises(ValueError, match="at least 1"):
        ReversibleCircuit(num_wires=0, input_map=(), output_map=())


@pytest.mark.parametrize("bad_map", [(1, 1, 2, 3), (0, 1, 2), (0, 1, 2, 4)])
def test_input_map_must_be_a_permutation(bad_map):
    with pytest.raises(ValueError, match="input_map"):
        ReversibleCircuit(num_wires=4, input_map=bad_map, output_map=IDENTITY)


def test_output_map_must_be_a_permutation():
    with pytest.raises(ValueError, match="output_map"):
        ReversibleCircuit(num_wires=4, input_map=IDENTITY, output_map=(0, 0, 1, 2))


@pytest.mark.parametrize("op", [Operation(4), Operation(0, (4,))])
def test_operations_must_fit_in_the_circuit(op):
    with pytest.raises(ValueError, match="uses wire 4"):
        ReversibleCircuit(
            num_wires=4,
            input_map=IDENTITY,
            output_map=IDENTITY,
            operations=(op,),
        )
