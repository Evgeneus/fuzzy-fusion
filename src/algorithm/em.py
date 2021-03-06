import math
import numpy as np
from numpy.random import beta
from collections import defaultdict
from util import invert


def expectation_maximization(N, M, Psi, alpha=(4, 1)):
    """
    The expectation maximization method (EM) from "Data Fusion: Resolving Conflicts from Multiple Sources"
    Dong et al., 2013. It iteratively estimates the probs of objects, then
    the accuracies of sources until a convergence is reached.

    :param N:
    :param M:
    :param Psi:
    :return:
    """
    inv_Psi = invert(N, M, Psi)
    # convergence eps
    eps = 0.001
    iter_max = 100
    # init accuracies
    # A = [np.random.uniform(0.7, 1.0) for s in range(N)]
    A = beta(alpha[0], alpha[1], N)
    iter = 0
    while iter != iter_max:
        # E-step
        p = []
        for obj in range(M):
            # a pass to detect all values of an object
            C = defaultdict(float)
            for s, val in Psi[obj]:
                C[val] = 0.0
            # total number of values
            V = len(C)

            # a pass to compute value confidences
            for s, val in Psi[obj]:
                for v in C.keys():
                    if v == val:
                        if A[s] == 0.: A[s] = 0.5
                        C[v] += math.log(A[s])
                    else:
                        if A[s] == 1.: A[s] = 0.95
                        C[v] += math.log((1-A[s])/(V-1))

            # compute probs
            # normalize
            norm = 0.0
            for val in C.keys():
                norm += math.exp(C[val])
            for val in C.keys():
                C[val] = math.exp(C[val])/norm
            p.append(C)

        # M-step
        A_new = [np.average([p[obj][val] for obj, val in x]) for x in inv_Psi]

        # convergence check
        if sum(abs(np.subtract(A, A_new))) < eps:
            A = A_new
            break
        else:
            A = A_new

        iter += 1
    return A, p