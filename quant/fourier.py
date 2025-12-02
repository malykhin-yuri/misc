import numpy as np

import quant


"""n-qbit Fourier transform."""
def get_fourier_circuit(n):
    R = [None] * (n + 1)
    for k in range(n + 1):
        R[k] = np.array([[1, 0], [0, np.exp(2*np.pi*1j/2**k)]])

    gates = []

    for j in range(n):
        gates.append(quant.gate_H(j))
        for k in range(j + 1, n):
            Rg = quant.gate_controlled([k], quant.Gate(R[k+1], [j]))
            gates.append(Rg)

    for j in range(n // 2):
        gates.append(quant.gate_swap(j, n-1-j))

    return quant.Circuit(gates)
