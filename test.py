import math
import matplotlib.pyplot as plt
import numpy as np


def bindingE(A, N, Z=2):
    if (A == 0):
        E = 0
    elif (N == 2):
        E = 15.8 * A - 18.3 * math.pow(A, 2 / 3) - 0.714 * Z * (Z - 1) / math.pow(A, 1 / 3) + 12 / math.pow(A, 1 / 2)
    elif (N % 2 == 0):
        E = 15.8 * A - 18.3 * math.pow(A, 2 / 3) - 0.714 * Z * (Z - 1) / math.pow(A, 1 / 3) - 23.2 * (
                N - Z) ** 2 / A + 12 / math.pow(A, 1 / 2)
    else:
        E = 15.8 * A - 18.3 * math.pow(A, 2 / 3) - 0.714 * Z * (Z - 1) / math.pow(A, 1 / 3) - 23.2 * (N - Z) ** 2 / A

    print(E, "A is:", A, "Z is:", Z)
    return E


if __name__ == '__main__':
    x = np.array([0, 1, 2, 3, 4])
    y = np.array([bindingE(0, -2, 2), bindingE(1, -1, 2), bindingE(2, 0, 2), bindingE(3, 1, 2), bindingE(4, 2, 2)])

    plt.plot(x, y, 'o', color='black')
    plt.xlabel("Mass number")
    plt.ylabel("Binding energy E_B(MeV)")
    plt.xlim(0, 5)
    plt.ylim(-220, 30)
    plt.show()
