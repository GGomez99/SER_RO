import pulp
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import random

file = pd.ExcelFile("../data/InputDataTelecomLargeInstance.xlsx")

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


### building fat solution

#building EO to hub
#putting maximum amount of E0 in hubs depending on capacity
#using HCapa to track capacity then reseting for real value
currentHub = 0
currentEO = 0
while currentEO < M:
    if currentHub == N:
        #all hubs saturated, adding randomly
        EOtoH[currentEO] = random.randint(0, N-1)
        currentEO += 1
    elif Uj[currentEO] >= Vk[currentHub]-HCapa[currentHub] > 0:
        #adding even though EO too big
        EOtoH[currentEO] = currentHub
        HCapa[currentHub] += Uj[currentEO]
        #next hub/EO
        currentHub += 1
        currentEO += 1
    elif Uj[currentEO] < Vk[currentHub]-HCapa[currentHub]:
        # adding cause EO can fit
        EOtoH[currentEO] = currentHub
        HCapa[currentHub] += Uj[currentEO]
        # next EO
        currentEO += 1
    else:
        #hub saturated and still space
        #next hub
        currentHub += 1


#reseting HCapa
HCapa = [0 for i in range(N)]

#building customer to EO
currentEO = 0
currentCust = 0
while currentCust < C:
    if EOCapa[currentEO]+1 <= Uj[currentEO] and HCapa[EOtoH[currentEO]]+1 <= Vk[EOtoH[currentEO]]:
        # adding customer to EO
        CtoEO[currentCust] = currentEO
        # update capacity
        EOCapa[currentEO] += 1
        HCapa[EOtoH[currentEO]] += 1
        # next customer
        currentCust += 1
    else:
        # next EO
        currentEO += 1

#Building ring
#already done

def cost():
    sum = 0
    for i in range(C):
        sum += int(CtoEO[i] != -1)*hij[i][CtoEO[i]]
    for j in range(M):
        sum += cjk[j][EOtoH[j]]
    pt = []
    for k in range(N):
        if RingH[k] != -1:
            sum += fk[k]
            if k not in pt:
                sum += int(RingH[k] != -1) * gmk[k][RingH[k]]
                pt.append(k)
    return sum


def printState():
    print("CtoEO : ", CtoEO)
    print("EOtoHub : ", EOtoH)
    print("ring : ", RingH)
    print("cost : ", cost())

def printStateDetailed():
    printState()
    print("capa maxH : ", Vk)
    print("capa Hubs : ", HCapa)
    print("capa maxEO : ", Uj)
    print("capa EO    : ", EOCapa)

costHistory = []
capaHub0 = []
capaEO0 = []
def saveCost():
    costHistory.append(cost())

def saveState():
    global state
    state["CtoEO"] = CtoEO.copy()
    state["EOCapa"] = EOCapa.copy()
    state["HCapa"] = HCapa.copy()
    state["EOtoH"] = EOtoH.copy()
    state["RingH"] = RingH.copy()
    state["cost"] = cost()



def loadState():
    global state
    global CtoEO
    global EOCapa
    global HCapa
    global EOtoH
    global RingH

    CtoEO = state["CtoEO"]
    EOCapa = state["EOCapa"]
    HCapa = state["HCapa"]
    EOtoH = state["EOtoH"]
    RingH = state["RingH"]

def swap(targetType, i, j):
    global stuck

    #print(targetType, " swapping ", i, " and ", j)
    if targetType == 0: #customer swap
        CtoEO[i],CtoEO[j] = CtoEO[j],CtoEO[i]
    elif targetType == 1: #EO swap
        if Uj[i] >= EOCapa[j] and Uj[j] >= EOCapa[i]:
            for c in range(C):
                if CtoEO[c] == j:
                    CtoEO[c] = i
                elif CtoEO[c] == i:
                    CtoEO[c] = j
            #update hub capa
            EOtoH[i], EOtoH[j] = EOtoH[j], EOtoH[i] #swap EO connection to hub
            EOCapa[i], EOCapa[j] = EOCapa[j], EOCapa[i] #swap current EO capacity
        else:
            #print("wrong capacity for EO")
            stuck += 1
    else: #Hub swap
        if Vk[i] >= HCapa[j] and Vk[j] >= HCapa[i]:
            #print("max :", Vk[i], Vk[j])
            #print("current :", HCapa[i], HCapa[j])
            indNotConnected = -1
            if RingH[i] == -1: indNotConnected = i
            elif RingH[j] == -1: indNotConnected = j

            RingH[i], RingH[j] = RingH[j], RingH[i] #swap in ring step1
            HCapa[i], HCapa[j] = HCapa[j], HCapa[i] #swap capacities

            for k in range(N): #swap in ring step2
                if RingH[k] == i and indNotConnected != i:
                    RingH[k] = j
                elif RingH[k] == j and indNotConnected != j:
                    RingH[k] = i

            for e in range(M): #swap hub for EO
                if EOtoH[e] == i: EOtoH[e] = j
                elif EOtoH[e] == j: EOtoH[e] = i


        else:
            #print("wrong capacity for Hub or both disconnected")
            stuck += 1

def deleteReplace(type, i):
    global stuck
    #print(type, " delete ", i)
    if type == 0: #delete customer
        totalConnected = 0
        if CtoEO[i] != -1:
            for j in range(C):
                totalConnected += int(CtoEO[j] != -1)
            if (totalConnected-1)/C > alpha:
                #print("totalConnected :", totalConnected, (totalConnected - 1) / C)
                #update EO and Hub capa
                EOCapa[CtoEO[i]] -= 1
                HCapa[EOtoH[CtoEO[i]]] -= 1
                #disconnect customer
                CtoEO[i] = -1
            else:
                #print("below alpha if delete customer")
                stuck += 1
        else:
            #print("customer already deleted")
            stuck += 1

    elif type == 1: #delete EO
        currentCapa = EOCapa[i]
        j = 0
        # cantMoveC = new EO can't accept currentCapa OR Hub of new EO can't accept capa OR Hub of new EO is disconnected OR new EO = EO
        cantMoveC = Uj[j]-EOCapa[j] < currentCapa or Vk[EOtoH[j]] - HCapa[EOtoH[j]] < currentCapa or RingH[EOtoH[j]] < 0 or i == j
        while j < M and cantMoveC:
            j += 1
            if j < M: cantMoveC = Uj[j]-EOCapa[j] < currentCapa or Vk[EOtoH[j]] - HCapa[EOtoH[j]] < currentCapa or RingH[EOtoH[j]] < 0 or i == j

        if not(cantMoveC) and currentCapa > 0:
            #print("moving to", j)
            # move customers to j
            for c in range(C):
                if CtoEO[c] == i:
                    CtoEO[c] = j
            # update capa
            EOCapa[j] += currentCapa
            HCapa[EOtoH[j]] += currentCapa
            HCapa[EOtoH[i]] -= currentCapa
            EOCapa[i] = 0
        else:
            #print("no suitable EO to move customers")
            stuck += 1
    else: #delete hub
        #check connected hub
        nbrConnected = 0
        for k in range(N):
            nbrConnected += int(RingH[k] != -1)
        if nbrConnected > 3:
            currentCapa = HCapa[i]
            j = 0
            cantMoveC = Vk[j] - HCapa[j] < currentCapa or j == i
            while j < N and (cantMoveC or RingH[j] == -1):
                j += 1
                if j < N: cantMoveC = Vk[j] - HCapa[j] < currentCapa or j == i

            #if new hub can accept move EO AND new hub nb < N AND new hub/hub to remove connected
            if not(cantMoveC) and j < N and RingH[j] != -1 and RingH[i] != -1:
                #print("move to hub", j)
                #move EO to hub
                for k in range(M):
                    if EOtoH[k] == i:
                        EOtoH[k] = j
                #update capa
                HCapa[j] += currentCapa
                HCapa[i] = 0
                #disconnect hub
                for k in range(N):
                    if RingH[k] == i:
                        RingH[k] = RingH[i]
                RingH[i] = -1
            else:
                #print("no suitable Hub to move EO")
                stuck += 1
        else:
            #print("can't delete another hub")
            stuck += 1

def add(type):
    #print(type, "Adding")
    if type == 0:
        firstC = np.nonzero(np.array(CtoEO) == -1)
        if len(firstC[0]) > 0:
            i = firstC[0][0]
            k = 0
            foundHub = False
            while k < N and not(foundHub):
                if (HCapa[k] < Vk[k] and RingH[k] >= 0):
                    #print("found potential hub", k, " : ", HCapa[k], "/", Vk[k])
                    j = 0
                    while j < M and not(EOCapa[j] < Uj[j] and EOtoH[j] == k):
                        j += 1
                    if j < M:
                        #print("found Office", j, " : ", EOCapa[j], "/", Uj[j])
                        EOCapa[j] += 1
                        HCapa[k] += 1
                        CtoEO[i] = j
                        foundHub = True
                    #else: print("couldnt find EO in hub")
                k += 1
            #if k >= N: print("couldnt find hub")
        #else: print("no disconnected customers")

    elif type == 2:
        firstH = np.nonzero(np.array(RingH) == -1)
        if len(firstH[0]) > 0:
            h = firstH[0][0]
            k = 0
            while k < N and RingH[k] == -1:
                k += 1
            if k<N:
                RingH[h] = RingH[k]
                RingH[k] = h
            else: print("couldnt find connected hub (not normal)")

        #else: print("no disconnected hub")



def diversify(i):
    bound = [C, M, N]
    for j in range(i//2): add(random.randint(0, 1)*2)
    for j in range(i):
        type = random.randint(0, 2)
        swap(type, random.randint(0, bound[type]-1), random.randint(0, bound[type]-1))

printState()
print("-------------------------Calculating-------------------------")

stuckLimit = 3500
minScore = cost()
saveState()
minState = state
iter = 1000000

for i in range(iter):

    if (i%(iter/100) == 0):
        bar = [" " if j > i*20/iter-1 else "=" for j in range(20)]
        print("\r "+str(i*100/iter)+" % ["+"".join(bar)+"] current min score : "+str(minScore), end='')
    move = random.randint(0, 1)
    type = random.randint(0, 2)
    bound = [C, M, N]
    saveState()

    #do move
    #print(RingH)
    #print(HCapa)

    for h in range(N):
        if RingH[h] == -1 and HCapa[h] > 0:
            print("-------------------------error -1 and capaH > 0-------------------------")
        if HCapa[h] < 0:
            print("++++++++++++++++++++++++++error capaH <0++++++++++++++++++++++++++++++++")
        capaH = 0
        for j in range(M):
            if EOtoH[j] == h:
                capaH += EOCapa[j]
        if capaH > Vk[h]:
            print('==========================error capaH > max==============================')
        if capaH != HCapa[h]:
            print('================error calculated hcapa != HCapa[] for ',h,'==============')


    #print(EOtoH)
    #print(EOCapa)

    if move == 0: swap(type, random.randint(0, bound[type]-1), random.randint(0, bound[type]-1))
    if move == 1: deleteReplace(type, random.randint(0, bound[type]-1))

    #test if better solution
    newCost = cost()
    if newCost > state["cost"]:
        loadState()
        stuck += 1
    saveCost()

    #diverisfy if stuck too much
    if stuck > stuckLimit or i == iter-1:
        currentScore = cost()
        if minScore > currentScore:
            minScore = currentScore
            saveState()
            minState = state.copy()
        diversify(20)
        stuck = 0

def graph(c, m, n):
    fr = []
    to = []
    il = []
    val = []

    for i, j in zip(c, range(len(c))):
        if i != 0:
            fr.append('c' + str(j + 1))
            to.append('m' + str(i))
            il.append('c' + str(j + 1))
            val.append('c')

    for i, j in zip(m, range(len(m))):
        if i != 0:
            fr.append('m' + str(j + 1))
            to.append('n' + str(i))
            il.append('m' + str(j + 1))
            val.append('m')

    for i, j in zip(n, range(len(n))):
        if i != 0:
            fr.append('n' + str(j + 1))
            to.append('n' + str(i))

            il.append('n' + str(j + 1))
            val.append('n')

    df = pd.DataFrame({'from': fr, 'to': to})

    carac = pd.DataFrame({'ID': il, 'myvalue': val})

    G = nx.from_pandas_edgelist(df, 'from', 'to', create_using=nx.Graph())

    G.nodes()

    carac = carac.set_index('ID')
    carac = carac.reindex(G.nodes())

    carac['myvalue'] = pd.Categorical(carac['myvalue'])
    carac['myvalue'].cat.codes

    nx.draw(G, with_labels=True, node_color=carac['myvalue'].cat.codes, cmap=plt.cm.Set1, node_size=200)
    plt.draw()

print("")

state = minState
print(minState)
print(state)
loadState()
printState()
graph(np.array(CtoEO)+1, np.array(EOtoH)+1, np.array(RingH)+1)
plt.figure()
plt.plot([i for i in range(len(costHistory))], costHistory)
plt.show()
