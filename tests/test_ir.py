import dataclasses

import pytest

from revsbox.ir import Operation


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
