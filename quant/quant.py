import numpy as np

import bit_utils

# quantum state space of system of N qbits is C^{2^N}
# pure state <=> amplitudes array a[x], x=(x_0..x_{N-1}) = 0..2^N-1 (first bit is most significant)

class State:
    def __init__(self, N, amp=None):
        self.N = N
        if amp is None:
            amp = np.zeros(1 << N, dtype=np.complex128)
            amp[0] = 1.0
        self.amp = np.array(amp)


class Gate:
    def __init__(self, U, qbits):
        self.U = U
        self.n = len(qbits)
        self.qbits = qbits


    def apply(self, state):
        N = state.N
        n = self.n

        result = np.zeros(1 << N, dtype=np.complex128)

        for xbase in range(1<<(N-n)):
            merge_array = bit_utils.merge_bits_array(m=N-n, base=xbase, index_list=self.qbits)
            vec = state.amp[merge_array]
            uvec = self.U @ vec
            for uv, j in zip(uvec, merge_array):
                result[j] = uv

        return State(N, result)


def gate_X(k):
    U = np.array([[0, 1], [1, 0]])
    return Gate(U, [k])


def gate_Y(k):
    U = np.array([[0, -1j], [1j, 0]])
    return Gate(U, [k])


def gate_Z(k):
    U = np.array([[1, 0], [0, -1]])
    return Gate(U, [k])


"""Hadamard gate on k-th qbit."""
def gate_H(k):
    U = np.array([[1, 0], [0, -1]])
    return Gate(U, [k])


def gate_phase(k):
    U = np.array([[1, 0], [0, 1j]])
    return Gate(U, [k])


"""Контролируемый k-м кубитом NOT для l-го кубита."""
def gate_cnot(k, l):
    U = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ])
    return Gate(U, [k, l])


"""Обмен k-го и l-го кубитов."""
def gate_swap(k, l):
    U = np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ])
    return Gate(U, [k, l])
