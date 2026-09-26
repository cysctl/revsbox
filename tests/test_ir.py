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
