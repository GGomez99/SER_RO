import pulp
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

file = pd.ExcelFile("../data/InputDataTelecomSmallInstance.xlsx")

### Importation des données
C = pd.read_excel(file, 'C').columns[0]
M = pd.read_excel(file, 'M').columns[0]
alpha = pd.read_excel(file, 'alpha').columns[0]
N = pd.read_excel(file, 'N').columns[0]
hij = pd.read_excel(file, 'CustToTargetAllocCost(hij)', header=None).to_numpy()
cjk = pd.read_excel(file, 'TargetToSteinerAllocCost(cjk)', header=None).to_numpy()
gmk = pd.read_excel(file, 'SteinerToSteinerConnctCost(gkm)', header=None).to_numpy()
fk = pd.read_excel(file, 'SteinerFixedCost(fk)', header=None)[0].values
Uj = pd.read_excel(file, 'TargetCapicity(Uj)', header=None)[0].values
Vk = pd.read_excel(file, 'SteinerCapacity(Vk)', header=None)[0].values

subsets = [list(x) for i in range(3, N + 1) for x in itertools.combinations(list(range(N)), i)]

# Initialisation des 4 jeux de variables X, Y, Z et L
x_var = pulp.LpVariable.dicts('x', [(i, j) for i in range(C) for j in range(M)],
                              lowBound=0,
                              upBound=1,
                              cat="Binary")

y_var = pulp.LpVariable.dicts('y', [(i, j) for i in range(M) for j in range(N)],
                              lowBound=0,
                              upBound=1,
                              cat="Binary")

z_var = pulp.LpVariable.dicts('z', [(i, j) for i in range(N) for j in range(i + 1, N)],
                              lowBound=0,
                              upBound=1,
                              cat="Binary")

l_var = pulp.LpVariable.dicts('l', [i for i in range(N)],
                              lowBound=0,
                              upBound=1,
                              cat="Binary")

c_var = pulp.LpVariable.dicts('c', [(i, j, k) for i in range(C) for j in range(M) for k in range(N)],
                              lowBound=0,
                              upBound=1,
                              cat="Binary")

# Création du problème
problem = pulp.LpProblem("read_thread", pulp.LpMinimize)

# Fonction de cout
problem += pulp.lpSum(hij[i][j] * x_var[(i, j)] for i in range(C) for j in range(M)) + pulp.lpSum(
    cjk[j][k] * y_var[(j, k)] for j in range(M) for k in range(N)) + pulp.lpSum(
    fk[k] * l_var[k] for k in range(N)) + pulp.lpSum(
    gmk[k][m] * z_var[(k, m)] for k in range(N) for m in range(k + 1, N))

# Constraint 1
for i in range(C): problem += pulp.lpSum(x_var[(i, j)] for j in range(M)) <= 1

# Constraint 2
for j in range(M): problem += pulp.lpSum(y_var[(j, k)] for k in range(N)) == 1

# Constraint 3
for j in range(M):
    for k in range(N):
        problem += y_var[(j, k)] <= l_var[k]

# Constraint 4
for k in range(N):
    problem += pulp.lpSum(z_var[(k, m)] if (k, m) in z_var else z_var[(m, k)] for m in range(N) if k != m) == 2 * l_var[
        k]

# Constraint 5
for subset in subsets:
    problem += pulp.lpSum(z_var[(m, k)] for m in subset for k in subset if m < k) <= len(subset)

# Constraint 6
for j in range(N): problem += pulp.lpSum(x_var[(i, j)] for i in range(C)) <= Uj[j]

# Constraint 7
for i in range(C):
    for j in range(M):
        for k in range(N):
            problem += c_var[(i, j, k)] <= x_var[(i, j)]
            problem += c_var[(i, j, k)] <= y_var[(j, k)]
            problem += c_var[(i, j, k)] >= x_var[(i, j)] + y_var[(j, k)] - 1

for k in range(N):
    problem += pulp.lpSum(c_var[(i, j, k)] for i in range(C) for j in range(M)) <= Vk[k]

# Constraint 8
problem += pulp.lpSum(l_var[k] for k in range(N)) >= 3

# Constraint 9
problem += pulp.lpSum(x_var[(i, j)] for i in range(C) for j in range(M)) >= alpha * C

# Constraint 10
# In the varialbles definition


problem.solve()
print(pulp.LpStatus[problem.status])
for v in problem.variables():
    if (v.varValue == 1.0):
        print(v.name, v.varValue)

print(pulp.value(problem.objective))


def graph():
    fr = []
    to = []
    il = []
    val = []

    for v in problem.variables():
        if v.varValue == 1.0:
            if ('l' not in v.name and 'c' not in v.name):
                t = eval(v.name.replace('_', '').replace('x', '').replace('y', '').replace('z', ''))
                fr.append(v.name[0] + str(t[0]))

                if 'x' in v.name:
                    to.append('y' + str(t[1]))
                if 'y' in v.name:
                    to.append('z' + str(t[1]))
                if 'z' in v.name:
                    to.append('z' + str(t[1]))

                if not (v.name[0] + str(t[0])) in il:
                    il.append((v.name[0] + str(t[0])))
                    val.append(v.name[0])

                if not ('z' + str(t[1])) in il:
                    il.append('z' + str(t[1]))
                    val.append('z')

    df = pd.DataFrame({'from': fr, 'to': to})

    carac = pd.DataFrame({'ID': il, 'myvalue': val})

    G = nx.from_pandas_edgelist(df, 'from', 'to', create_using=nx.Graph())

    G.nodes()

    carac = carac.set_index('ID')
    carac = carac.reindex(G.nodes())

    carac['myvalue'] = pd.Categorical(carac['myvalue'])
    nx.draw(G, with_labels=True, node_color=carac['myvalue'].cat.codes, cmap=plt.cm.Set1, node_size=200)

graph()
plt.show()