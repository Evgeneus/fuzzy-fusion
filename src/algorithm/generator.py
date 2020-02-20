import numpy as np
from collections import Counter


def compute_clusters(c_Psi):
    M = len(c_Psi)
    mv_res = np.zeros(M)
    conf_label = np.zeros(M)  # array with potential confused labels
    # prepare data
    for obj, votes in enumerate(c_Psi):
        votes = zip(*votes)[1]
        counter = Counter(votes)
        most_common2 = counter.most_common(2)
        mv_res[obj] = most_common2[0][0]
        if len(most_common2) >= 2:
            conf_label[obj] = most_common2[1][0]
        else:
            conf_label[obj] = np.nan

    # compute clusters
    Cl = {}
    for obj in range(M):
        other_label = conf_label[obj]
        if np.isnan(other_label):
            continue
        other_obj_candidates = np.where(mv_res == other_label)[0]
        if len(other_obj_candidates) == 0:
            continue
        other_obj = np.random.choice(other_obj_candidates, 1, replace=False)[0]
        Cl[obj] = {'id': obj, 'other': other_obj}

    return Cl


def synthesize(N, M, V, density, conf_prob, s_acc):
    """
    Generates synthetic data.
    :param N: number of sources
    :param M: number of objects
    :param V: number of values per object
    :param density:
    :param accuracy:
    :param conf_prob:
    :return:

    Psi: observations without confusions
    c_Psi: observations with simulated confusions
    """
    # generate ground truth
    GT = {}
    for obj in range(M):
        GT[obj] = np.random.randint(0, V)

    # generate observations
    Psi = [[] for obj in range(M)]
    for obj in range(M):
        for s in range(N):
            if s_acc:
                accuracy = s_acc
            else:
                # accuracy = np.random.uniform(0.7, 1.0)
                accuracy = 0.9
            if np.random.rand() < density:
                if np.random.rand() < accuracy:
                    Psi[obj].append((s, GT[obj]))
                else:
                    others = range(V)
                    others.remove(GT[obj])
                    Psi[obj].append((s, np.random.choice(others)))

    # generate clusters and confusions: clusters are half object to another half
    Cl = {}
    for obj in range(M/2):
        Cl[obj] = {'id': obj, 'other': M/2 + obj}
        Cl[M / 2 + obj] = {'id': M/2 + obj, 'other': obj}
    c_Psi = [[] for obj in range(M)]
    GT_G = {}
    for obj in range(M):
        GT_G[obj] = {}
    for obj in range(M):
        if obj in Cl:
            for s, val in Psi[obj]:
                # check if source should confuse objects and hasn't voted already voted on the 'other' object in the cluster
                # -> generate a confusion
                # TO Document:
                if (np.random.rand() >= conf_prob) and (s not in [x[0] for x in c_Psi[Cl[obj]['other']]]):
                    c_Psi[Cl[obj]['other']].append((s, val))
                    GT_G[Cl[obj]['other']][s] = 0
                elif (s not in [x[0] for x in c_Psi[obj]]):
                    c_Psi[obj].append((s, val))
                    GT_G[obj][s] = 1
                elif (s in [x[0] for x in c_Psi[obj]]) and (s not in [x[0] for x in c_Psi[Cl[obj]['other']]]):
                    c_Psi[Cl[obj]['other']].append((s, val))
                    GT_G[Cl[obj]['other']][s] = 0
        else:
            # never get into this part if the object not into a cluster
            for s, val in Psi[obj]:
                c_Psi[obj].append((s, val))
                GT_G[obj][s] = 1

    # ensure that every object has at least one vote
    for obj in range(M):
        if len(c_Psi[obj]) == 0:
            s = np.random.randint(0, N)
            if np.random.rand() < accuracy:
                c_Psi[obj].append((s, GT[obj]))
            else:
                others = range(V)
                others.remove(GT[obj])
                c_Psi[obj].append((s, np.random.choice(others)))
            GT_G[obj][s] = 1

    Cl = compute_clusters(c_Psi)

    return GT, GT_G, Cl, c_Psi
