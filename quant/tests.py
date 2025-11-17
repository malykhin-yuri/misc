import numpy as np

import quant
import bit_utils


def has_diff(state1, state2):
    if state1.N != state2.N:
        raise ValueError("Wrong number of qbits")
    return np.max(np.abs(state1.amp - state2.amp)) > 1e-6

def test_merge_bits_array():
    print('test_merge_bits_array')
    m = 5
    y = 0b01101
    ind = [3, 0]

    expect = [
        0b0010101, # x=00, merged=|0| 0 1 |0| 1 0 1
        0b1010101, # x=01, merged=|1| 0 1 |0| 1 0 1
        0b0011101, # x=10, merged=|0| 0 1 |1| 1 0 1
        0b1011101, # x=11, merged=|1| 0 1 |1| 1 0 1
    ]
    got = bit_utils.merge_bits_array(m, y, ind)
    if got != expect:
        raise ValueError("expected {}, got {}".format(expect, got))
    print('ok')


def test_quant_X():
    print('test_quant_X')
    start_state = quant.State(3)
    X = quant.gate_X(0)
    state = X.apply(start_state)
    if not has_diff(state, start_state):
        raise ValueError("expected state change")
    state = X.apply(state)
    if has_diff(state, start_state):
        raise ValueError("expected same state")
    print('ok')


def test_quant_XYZ():
    print('test_quant_XYZ')
    state = quant.State(1, amp=[0.6, 0.8])
    istate = quant.State(1, amp=state.amp * 1j)
    X = quant.gate_X(0)
    Y = quant.gate_Y(0)
    Z = quant.gate_Z(0)

    if has_diff(X.apply(Y.apply(state)), Z.apply(istate)):
        raise ValueError("expected XY=iZ")
    if has_diff(Y.apply(Z.apply(state)), X.apply(istate)):
        raise ValueError("expected YZ=iX")
    if has_diff(Z.apply(X.apply(state)), Y.apply(istate)):
        raise ValueError("expected ZX=iY")
    print('ok')


if __name__ == "__main__":
    test_merge_bits_array()
    test_quant_X()
    test_quant_XYZ()
