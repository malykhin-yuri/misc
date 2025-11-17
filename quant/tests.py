import itertools

import numpy as np

import quant
import bit_utils


def has_diff(state1, state2):
    if state1.N != state2.N:
        raise ValueError("Wrong number of qbits")
    return np.max(np.abs(state1.amp - state2.amp)) > 1e-6

def test_merge_bits_array():
    print("test_merge_bits_array")
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
    print("test_quant_X")
    start_state = quant.State(3)
    X = quant.gate_X(0)
    state = X @ start_state
    if not has_diff(state, start_state):
        raise ValueError("expected state change")
    state = X @ state
    if has_diff(state, start_state):
        raise ValueError("expected same state")
    print('ok')


def test_quant_equations():
    print("test_quant_equations")

    test_states = [
        quant.state_comp([0]),
        quant.state_comp([1]),
        quant.State(1, amp=[0.6, 0.8j]),
    ]
    for state in test_states:
        istate = quant.State(1, amp=state.amp * 1j)
        X = quant.gate_X(0)
        Y = quant.gate_Y(0)
        Z = quant.gate_Z(0)
        H = quant.gate_H(0)

        if has_diff(quant.Circuit([X, X]) @ state, state):
            raise ValueError("expected XX=I")
        if has_diff(quant.Circuit([Y, X]) @ state, Z @ istate):
            raise ValueError("expected XY=iZ")
        if has_diff(quant.Circuit([Z, Y]) @ state, X @ istate):
            raise ValueError("expected YZ=iX")
        if has_diff(quant.Circuit([X, Z]) @ state, Y @ istate):
            raise ValueError("expected ZX=iY")
        if has_diff(quant.Circuit([H, Z, H]) @ state, X @ state):
            raise ValueError("expected HZH=X")

    print("ok")


def test_quant_controlled():
    print("test_quant_controlled")

    for k in range(2, 5):
        ckX_gate = quant.gate_controlled(list(range(k-1)), quant.gate_X(k-1))
        for bits in itertools.product([0, 1], repeat=k):
            state = quant.state_comp(bits)
            expected_bits = bits if any(b == 0 for b in bits[0:(k-1)]) else bits[0:(k-1)] + (1-bits[-1],)
            expected_state = quant.state_comp(expected_bits)
            got_state = ckX_gate @ state
            if has_diff(got_state, expected_state):
                raise ValueError("wrong C^{} X".format(k))

    state = quant.State(2, amp=[0.3**0.5 * np.exp(1j), 0.4**0.5 * np.exp(2j), 0.2**0.5 * np.exp(3j), 0.1**0.5 * np.exp(4j)])
    if has_diff(
        quant.gate_controlled([0], quant.gate_Z(1)) @ state,
        quant.gate_controlled([1], quant.gate_Z(0)) @ state,
    ):
        raise ValueError("expected controlled-Z = Z-controlled")


    cnot = quant.gate_cnot(0, 1)
    V = np.array([[0.6j, 0.8j], [0.8, -0.6]]);
    U = V @ V
    circ1 = quant.Circuit([quant.gate_controlled([0, 1], quant.Gate(U, [2]))])
    circ2 = quant.Circuit([
        quant.gate_controlled([1], quant.Gate(V, [2])),
        cnot,
        quant.gate_controlled([1], quant.Gate(V.conj().T, [2])),
        cnot,
        quant.gate_controlled([0], quant.Gate(V, [2])),
    ])
    for bits in itertools.product([0, 1], repeat=3):
        state = quant.state_comp(bits)
        if has_diff(circ1 @ state, circ2 @ state):
            raise ValueError("expected equality for C^2-U")

    print("ok")


if __name__ == "__main__":
    test_merge_bits_array()
    test_quant_X()
    test_quant_equations()
    test_quant_controlled()
