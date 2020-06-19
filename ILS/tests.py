import pulp
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import random

file = pd.ExcelFile("C:/Users/guyll/Documents/IMT/A1S2/SER/RO/InputDataTelecomLargeInstance.xlsx")

### Importation des données
C = pd.read_excel(file, 'C').columns[0]
M = pd.read_excel(file, 'M').columns[0]
alpha = pd.read_excel(file, 'alpha').columns[0]
N = pd.read_excel(file, 'N').columns[0]
hij = pd.read_excel(file, 'CustToTargetAllocCost(hij)', header=None).to_numpy()
cjk = pd.read_excel(file, 'TargetToSteinerAllocCost(cjk)', header=None).to_numpy()
gmk = pd.read_excel(file, 'SteinerToSteinerConnctCost(gkm)', header=None).to_numpy()
fk = pd.read_excel(file, 'SteinerFixedCost(fk)', header=None)[0].values
Uj = pd.read_excel(file, 'TargetCapicity(Uj)', header=None)[0].values #End office capacity
Vk = pd.read_excel(file, 'SteinerCapacity(Vk)', header=None)[0].values #Hub capacity
print("C M N alpha : ", C, M, N, alpha)
print("Uj : ", Uj)
print("Vk : ", Vk)
#print("hij : ", hij)
#print("cjk : ", cjk)
#print("gmk : ", gmk)
#print("fk : ", fk)

global state
global CtoEO
global EOCapa
global HCapa
global EOtoH
global RingH
global stuck

stuck = 0
state = {
    "CtoEO": [],
    "EOCapa": [],
    "HCapa": [],
    "EOtoH": [],
    "RingH": [],
    "cost": 0
}

CtoEO = [-1 for i in range(C)]
EOCapa = [0 for i in range(M)]
HCapa = [0 for i in range(N)]
EOtoH = [0 for i in range(M)]
RingH = [(i+1)%N for i in range(N)]

def cost():
    sum = 0
    for i in range(C):
        print("Adding ", i, CtoEO[i], hij[i][CtoEO[i]])
        sum += int(CtoEO[i] != -1)*hij[i][CtoEO[i]]
    for j in range(M):
        print("Adding ", j, EOtoH[j], cjk[j][EOtoH[j]])
        sum += cjk[j][EOtoH[j]]
    pt = []
    for k in range(N):
        if RingH[k] != -1:
            print("adding", k, fk[k])
            sum += fk[k]
            if k not in pt:
                print("adding co hub", k, RingH[k])
                sum += int(RingH[k] != -1)*gmk[k][RingH[k]]
                pt.append(k)
    return sum

CtoEO = [2, 9, 5, 14, 5, 2, 7, 5, 9, 14, 14, 9, 2, 14, 2, 5, 4, 5, 2, 9, 9, 7, 9, 5, 5, 2, 5, 4, 5, 7, 8, 4, 8, 9, 5, 9, 4, 4, 9, 4, 8, 9, 5, 2, 2, 4, 8, 5, 8, 8]
EOtoHub = [3, 7, 7, 7, 5, 4, 7, 3, 3, 8, 4, 7, 3, 7, 7]
RingH = [-1, -1, -1, 8, 3, 4, -1, 5, 7, -1]


print("pulp : ", cost())