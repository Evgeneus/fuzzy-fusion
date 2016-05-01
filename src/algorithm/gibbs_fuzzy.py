import numpy as np
import random
import copy
from scipy.stats import beta
import pandas as pd

max_rounds = 30
possible_values = [0, 1]
alpha1, alpha2 = 1, 1
beta1, beta2 = 1, 1
gamma1, gamma2 = 1, 1


def init_var(data):
    s_ind = sorted(data.S.drop_duplicates())
    s_number = len(s_ind)
    obj_index_list = sorted(data.O.drop_duplicates())
    var_index = [obj_index_list, s_ind]
    accuracy_list = [random.uniform(0.6, 0.95) for i in range(s_number)]
    pi_init = random.uniform(0.7, 1)
    g_values = np.random.binomial(1, pi_init, len(data))
    obj_values = [random.choice(possible_values) for i in range(len(obj_index_list))]
    pi_prob = [pi_init]*(len(obj_index_list)/2)

    init_prob = []
    l = len(possible_values)
    for obj_index in obj_index_list:
        init_prob.append([1./l]*l)

    counts = []
    for s in s_ind:
        psi_ind_list = []
        counts_list = []
        for psi in data[data.S == s].iterrows():
            psi_ind = psi[0]
            psi_ind_list.append(psi_ind)
            psi = psi[1]
            if g_values[psi_ind] == 1:
                if psi.V == obj_values[psi.O]:
                    counts_list.append(1)
                else:
                    counts_list.append(0)
            else:
                if psi.O % 2 == 0:
                    if psi.V == obj_values[psi.O+1]:
                        counts_list.append(1)
                    else:
                        counts_list.append(0)
                else:
                    if psi.V == obj_values[psi.O-1]:
                        counts_list.append(1)
                    else:
                        counts_list.append(0)
        counts.append(pd.DataFrame(counts_list, columns=['c']).set_index([psi_ind_list]))

    return [var_index, g_values, obj_values, counts, init_prob, pi_prob, accuracy_list]


def get_o(o_ind, g_values, obj_values, counts, data, prob, accuracy_list):
    l_p = []
    l_c = []
    if o_ind % 2 == 0:
        cl = [o_ind, o_ind+1]
    else:
        cl = [o_ind-1, o_ind]
    psi_cl = data[data.O.isin(cl)]
    s_in_cluster = list(psi_cl.S.drop_duplicates())
    for v in possible_values:
        counts_v = copy.deepcopy(counts)
        l_p.append(prob[o_ind][v])
        for s in s_in_cluster:
            n_p, n_m = 0, 0
            for psi in psi_cl[psi_cl.S == s].iterrows():
                psi_ind = psi[0]
                psi = psi[1]
                c_old = counts_v[s].at[psi_ind, 'c']
                if g_values[psi_ind] == 1 and psi.O == o_ind:
                    c_new = 1 if psi.V == v else 0
                    if c_new != c_old:
                        counts_v[s].at[psi_ind, 'c'] = c_new

                    if c_new == 1:
                        n_p += 1
                    else:
                        n_m += 1
                elif psi.O != o_ind and g_values[psi_ind] == 0:
                    c_new = 1 if psi.V == v else 0
                    if c_new != c_old:
                        counts_v[s].at[psi_ind, 'c'] = c_new

                    if c_new == 1:
                        n_p += 1
                    else:
                        n_m += 1
            s_counts = [n_m, n_p]
            if any(s_counts):
                accuracy = accuracy_list[s]
                l_p[v] *= accuracy**n_p*(1-accuracy)**n_m
        # l_p.append(pr_v)
        l_c.append(counts_v)
    norm_const = sum(l_p)
    l_p[0] /= norm_const
    l_p[1] /= norm_const
    v_new = np.random.binomial(1, l_p[1], 1)[0]
    counts_new = l_c[v_new]

    return [v_new, counts_new, l_p]


def get_g(g_ind, g_prev, pi_prob, obj_values, accuracy_list, counts, data):
    l_p = []
    psi = data.iloc[g_ind]
    s = psi.S
    accuracy = accuracy_list[s]
    cluster = psi.O/2
    for g in possible_values:
        pr_pi = pi_prob[cluster]**g*(1-pi_prob[cluster])**(1-g)
        if g == 1:
            if psi.V == obj_values[psi.O]:
                pr_pi *= accuracy
            else:
                pr_pi *= 1-accuracy
        else:
            if psi.O % 2 == 0:
                if psi.V == obj_values[psi.O+1]:
                    pr_pi *= accuracy
                else:
                    pr_pi *= 1-accuracy
            else:
                if psi.V == obj_values[psi.O-1]:
                    pr_pi *= accuracy
                else:
                    pr_pi *= 1-accuracy
        l_p.append(pr_pi)
    norm_const = sum(l_p)
    l_p[0] /= norm_const
    l_p[1] /= norm_const
    g_new = np.random.binomial(1, l_p[1], 1)[0]
    if g_new != g_prev:
        if g_new == 1:
            if psi.V == obj_values[psi.O]:
                counts[s].at[g_ind, 'c'] = 1
            else:
                counts[s].at[g_ind, 'c'] = 0
        else:
            if psi.O % 2 == 0:
                if psi.V == obj_values[psi.O+1]:
                    counts[s].at[g_ind, 'c'] = 1
                else:
                    counts[s].at[g_ind, 'c'] = 0
            else:
                if psi.V == obj_values[psi.O-1]:
                    counts[s].at[g_ind, 'c'] = 1
                else:
                    counts[s].at[g_ind, 'c'] = 0

    return g_new


def get_pi(cl_ind, g_values, data):
    cl = [cl_ind*2, cl_ind*2+1]
    psi_cl_list = list(data[data.O.isin(cl)].index)
    count_p = 0
    count_m = 0
    for g_ind in psi_cl_list:
        g = g_values[g_ind]
        if g == 1:
            count_p += 1
        else:
            count_m += 1
    pi_new = beta.rvs(count_p + gamma1, count_m + gamma2, size=1)[0]

    return pi_new


def get_a(s_counts):
    count_p = len(s_counts[s_counts.c == 1])
    count_m = len(s_counts[s_counts.c == 0])
    a_new = beta.rvs(count_p + alpha1, count_m + alpha2, size=1)[0]

    return a_new


def get_dist_metric(data, truth_obj_list, prob):
    prob_gt = []
    val = []
    l = len(possible_values)
    for obj_index in range(len(data.O.drop_duplicates())):
        val.append(possible_values)
        prob_gt.append([0]*l)
    for obj_ind, v_true in enumerate(truth_obj_list):
        for v_ind, v in enumerate(val[obj_ind]):
            if v == v_true:
                prob_gt[obj_ind][v_ind] = 1
    prob_gt_vector = []
    prob_vector = []
    for i in range(len(prob_gt)):
        prob_gt_vector += prob_gt[i]
        prob_vector += prob[i]
    dist_metric = np.dot(prob_gt_vector, prob_vector)
    dist_metric_norm = dist_metric/len(prob_gt)

    return dist_metric_norm


def gibbs_fuzzy(data, truth_obj_list):
    dist_list = []
    iter_list = []
    pi_prob_all = []
    accuracy_all = []
    for round in range(5):
        var_index, g_values, obj_values, counts, prob, pi_prob, accuracy_list = init_var(data=data)
        iter_number = 0
        dist_temp = []
        while iter_number < max_rounds:
            for o_ind in var_index[0]:
                obj_values[o_ind], counts, prob[o_ind] = get_o(o_ind=o_ind, g_values=g_values,
                                                               obj_values=obj_values, counts=counts,
                                                               data=data, prob=prob, accuracy_list=accuracy_list)

            for g_ind in range(len(g_values)):
                g_prev = g_values[g_ind]
                g_values[g_ind] = get_g(g_ind=g_ind, g_prev=g_prev, pi_prob=pi_prob, obj_values=obj_values,
                                        accuracy_list=accuracy_list, counts=counts, data=data)

            for cl_ind in range(len(pi_prob)):
                pi_prob[cl_ind] = get_pi(cl_ind=cl_ind, g_values=g_values, data=data)

            for s_ind in var_index[1]:
                s_counts = counts[s_ind]
                accuracy_list[s_ind] = get_a(s_counts=s_counts)
            iter_number += 1
            dist_metric = get_dist_metric(data=data, truth_obj_list=truth_obj_list, prob=prob)
            dist_temp.append(dist_metric)

        pi_prob_all.append(pi_prob)
        accuracy_all.append(accuracy_list)
        dist_metric = np.mean(dist_temp[-10:])
        dist_list.append(dist_metric)
        iter_list.append(iter_number)

    accuracy_mean = []
    accuracy_df = pd.DataFrame(data=accuracy_all)
    for s in range(len(accuracy_list)):
        accuracy_mean.append(np.mean(accuracy_df[s]))
    pi_df = pd.DataFrame(data=pi_prob_all)
    pi_mean = []
    for pi in range(len(pi_prob)):
        pi_mean.append(np.mean(pi_df[pi]))
    return [np.mean(dist_list), np.mean(iter_list), accuracy_mean, pi_mean]
