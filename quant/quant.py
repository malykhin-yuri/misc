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


# computational basis
def state_comp(bits):
    N = len(bits)
    amp = np.zeros(1 << N, dtype=np.complex128)

    x = sum(1 << (N - 1 - j) for j, b in enumerate(bits) if b)
    amp[x] = 1
    return State(N, amp)


class Gate:
    def __init__(self, U, qbits):
        self.U = np.array(U, dtype=np.complex128)
        self.n = len(qbits)
        self.qbits = qbits


    def apply(self, state):
        N = state.N
        n = self.n
        if n > N:
            raise ValueError("Gate has more qbits than state")

        result = np.zeros(1 << N, dtype=np.complex128)

        for xbase in range(1<<(N-n)):
            merge_array = bit_utils.merge_bits_array(m=N-n, base=xbase, index_list=self.qbits)
            vec = state.amp[merge_array]
            uvec = self.U @ vec
            for uv, j in zip(uvec, merge_array):
                result[j] = uv

        return State(N, result)


    def __matmul__(self, state):
        if not isinstance(state, State):
            return NotImplemented
        return self.apply(state)


class Circuit:
    def __init__(self, gates):
        self.gates = gates

    def __matmul__(self, state):
        for g in self.gates:
            state = g @ state
        return state


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
    U = np.array([[1, 1], [1, -1]]) * 2**(-0.5)
    return Gate(U, [k])


def gate_phase(k):
    U = np.array([[1, 0], [0, 1j]])
    return Gate(U, [k])


"""Обмен k-го и l-го кубитов."""
def gate_swap(k, l):
    U = np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ])
    return Gate(U, [k, l])


"""Контролируемый заданными кубитами гейт."""
def gate_controlled(cqbits, gate):
    if set(cqbits) & set(gate.qbits):
        raise ValueError("Controlled qbit in gate qbits!")

    c = len(cqbits)
    n = gate.n
    gate_size = 1 << n
    size = 1 << (n + c)
    V = np.zeros(shape=(size, size), dtype=np.complex128)

    for i in range(size - gate_size):
        V[i][i] = 1

    for i in range(gate_size):
        for j in range(gate_size):
            V[size - gate_size + i][size - gate_size + j] = gate.U[i, j]

    return Gate(V, cqbits + gate.qbits)


def gate_cnot(k, l):
    return gate_controlled([k], gate_X(l))
